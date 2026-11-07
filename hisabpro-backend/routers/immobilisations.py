# -*- coding: utf-8 -*-
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json
from typing import List

from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, text, or_
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, requiert_ecriture, requiert_admin
import models, schemas
from services.immobilisations_reconciliation_service import (
    CATEGORY_ACCOUNTS, analyser_reconciliation, analyser_immo,
    comptes_recommandes, construire_lignes_reclassement,
    construire_lignes_acquisition_reconstituee, construire_lignes_reprise_ouverture,
    construire_lignes_correction_dotation, money as recon_money,
    _references_amortissement_patterns, _ecriture_acquisition,
)
from services.immobilisations_service import (
    D, ZERO, money, coefficient_degressif,
    calculer_tableau_amortissement, situation_a_date, dotation_sur_periode,
    ventilation_acquisition, resultat_cession,
)
from services.tva_regles_service import qualification_valide, valider_tva
from services.exercices_service import (
    ensure_exercice, trouver_exercice_pour_date, verifier_date_ecriture,
)
from services.auxiliaire_service import (
    rattacher_ligne_auxiliaire, generer_code_auxiliaire,
)
from services.immobilisations_verrou_service import verrouiller_registre


def _proteger_mutation_registre(request: Request, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        verrouiller_registre(db, current_user["societe_id"])


router = APIRouter(prefix="/api/immobilisations", tags=["immobilisations"],
                   dependencies=[Depends(_proteger_mutation_registre)])


def _journal_tresorerie(compte: str):
    return models.JournalEnum.CA if str(compte or "").startswith("516") else models.JournalEnum.BQ


def _get_immo(db: Session, societe_id: int, immo_id: int, *, ecriture: bool = False):
    if ecriture:
        verrouiller_registre(db, societe_id)
        cle = f"hisabpro:immobilisation:{societe_id}:{immo_id}"
        if not db.scalar(text("SELECT pg_try_advisory_xact_lock(hashtextextended(:cle,0))"), {"cle": cle}):
            raise HTTPException(409, "Une opération sur cette immobilisation est en cours. Réessayez.")
    q = db.query(models.Immobilisation).filter_by(id=immo_id, societe_id=societe_id)
    # Le lot annuel peut avoir préchargé un ancien plan avant le verrou.
    immo = (q.populate_existing() if ecriture else q).first()
    if not immo:
        raise HTTPException(404, "Immobilisation introuvable")
    return immo


def _a_dotation(db: Session, societe_id: int, immo_id: int):
    patterns = _references_amortissement_patterns(immo_id)
    return db.query(models.Ecriture.id).filter(
        models.Ecriture.societe_id == societe_id,
        or_(*(models.Ecriture.reference.like(p) for p in patterns)),
    ).first() is not None


def _verifier_selection_unique(items):
    ids = [item.immo_id for item in items]
    if len(ids) != len(set(ids)):
        raise HTTPException(400, "Sélectionnez chaque immobilisation une seule fois.")




def _nettoyer_nom_tiers(nom: str | None) -> str:
    return " ".join((nom or "").strip().split())


def _resoudre_fournisseur(db: Session, societe_id: int, tiers_id: int | None, nom: str | None):
    """Retourne un tiers fournisseur existant ou le crée à la volée.

    - un tiers explicitement sélectionné est validé dans la société courante ;
    - un nom saisi est rapproché par nom exact insensible à la casse ;
    - un client existant portant exactement ce nom devient ``les_deux`` ;
    - sinon un nouveau fournisseur minimal est créé.
    """
    nom_propre = _nettoyer_nom_tiers(nom)
    tiers = None

    if tiers_id is not None:
        tiers = db.query(models.Tiers).filter_by(
            id=tiers_id, societe_id=societe_id, actif=True
        ).first()
        if not tiers:
            raise HTTPException(400, "Le fournisseur sélectionné n'existe pas dans cette société")
    elif nom_propre:
        tiers = db.query(models.Tiers).filter(
            models.Tiers.societe_id == societe_id,
            models.Tiers.actif == True,  # noqa: E712
            func.lower(func.trim(models.Tiers.nom)) == nom_propre.lower(),
        ).order_by(models.Tiers.id.asc()).first()

    if tiers:
        if tiers.type == "client":
            tiers.type = "les_deux"
        elif tiers.type not in {"fournisseur", "les_deux"}:
            tiers.type = "fournisseur"
        if not getattr(tiers, "code_aux_fournisseur", None):
            tiers.code_aux_fournisseur = generer_code_auxiliaire(tiers.id, "fournisseur")
        return tiers

    if not nom_propre:
        return None

    tiers = models.Tiers(
        societe_id=societe_id,
        type="fournisseur",
        nom=nom_propre,
        compte_fournisseur="4411",
        assujetti_tva=True,
        delai_paiement=60,
        actif=True,
    )
    db.add(tiers)
    db.flush()
    tiers.code_aux_fournisseur = generer_code_auxiliaire(tiers.id, "fournisseur")
    return tiers


def _check_exercice_ouvert(db: Session, societe_id: int, annee: int):
    from routers.cloture import exercice_est_clos
    if exercice_est_clos(db, societe_id, annee):
        raise HTTPException(423, f"Exercice {annee} clôturé : opération impossible sur cette période.")


def _exercice_ouvert_pour_date(db: Session, societe_id: int, d: date, action: str = "comptabiliser"):
    try:
        return verifier_date_ecriture(db, societe_id, d, action=action)
    except ValueError as exc:
        msg = str(exc)
        raise HTTPException(423 if "clôtur" in msg.lower() or "ferm" in msg.lower() else 409, msg) from exc


def _ligne_dotation_exercice(db: Session, societe_id: int, immo, annee: int, date_arret: date | None = None):
    """Dotation théorique d'une immobilisation sur les bornes réelles d'un exercice.

    Le moteur d'amortissement calcule un cumul à une date donnée. La différence
    de cumul entre l'ouverture et la clôture de l'exercice permet de conserver
    exactement le même calcul pour un exercice civil ou décalé.
    """
    ex = ensure_exercice(db, societe_id, annee)
    return _calcul_dotation_exercice(immo, ex, date_arret)


def _calcul_dotation_exercice(immo, ex, date_arret=None):
    """Calcul partagé sans création d'exercice ou de période."""
    fin = min(ex.date_fin, date_arret) if date_arret else ex.date_fin
    if fin < ex.date_debut:
        return None
    calc = dotation_sur_periode(immo, ex.date_debut, fin)
    cumul_fin = money(calc["cumul_fin"])
    dotation = money(calc["dotation"])
    if dotation <= ZERO:
        return None
    return {
        "annee": ex.annee,
        "debut_periode": ex.date_debut,
        "fin_periode": fin,
        "dotation": dotation,
        "cumul": cumul_fin,
    }


def _montant_dotation_ecriture(ecriture, compte_dotation: str) -> Decimal:
    total = ZERO
    for ligne in ecriture.lignes or []:
        if ligne.compte == compte_dotation:
            total += D(ligne.debit) - D(ligne.credit)
    return money(total)


def _creer_ecriture_dotation(db: Session, societe_id: int, immo, ligne_plan: dict, date_ecriture: date):
    annee = ligne_plan["annee"]
    ref = f"AM-{annee}-{immo.id}"
    # Commun aux générations individuelle, par lot, clôture et sortie.
    # Un contrôle d'existence effectué avant ce verrou peut être périmé.
    cle = f"hisabpro:dotation:{societe_id}:{immo.id}:{annee}"
    if not db.scalar(text("SELECT pg_try_advisory_xact_lock(hashtextextended(:cle,0))"), {"cle": cle}):
        raise HTTPException(409, "Une génération de dotation est en cours. Réessayez.")
    existe = db.query(models.Ecriture).filter(
        models.Ecriture.societe_id == societe_id,
        models.Ecriture.reference.in_([ref, f"RECON-AMORT-{annee}-{immo.id}"]),
    ).first()
    if existe:
        if existe.reference != ref:
            raise HTTPException(409, f"Une correction d'amortissement existe déjà pour {annee} (écriture {existe.id}). Contrôlez-la avant toute nouvelle dotation.")
        raise HTTPException(409, f"La dotation {annee} existe déjà (écriture {existe.id}).")
    ecriture = models.Ecriture(
        societe_id=societe_id,
        date=date_ecriture,
        journal=models.JournalEnum.AM,
        libelle=f"Dotation aux amortissements — {immo.designation} {annee}",
        reference=ref,
        exercice=annee,
        source="immobilisation",
    )
    db.add(ecriture)
    db.flush()
    dotation = money(ligne_plan["dotation"])
    db.add(models.LigneEcriture(
        ecriture_id=ecriture.id,
        compte=immo.compte_dotation,
        libelle=f"Dotation amort. — {immo.designation}",
        debit=dotation,
        credit=ZERO,
    ))
    db.add(models.LigneEcriture(
        ecriture_id=ecriture.id,
        compte=immo.compte_amort,
        libelle=f"Amort. cumulé — {immo.designation}",
        debit=ZERO,
        credit=dotation,
    ))
    return ecriture


def _serialiser_immo(immo, date_reference: date | None = None):
    vent = ventilation_acquisition(immo.prix_acquisition_ht, immo.taux_tva, immo.tva_recuperable_pct)
    reference = date_reference or date.today()
    if immo.date_sortie and immo.date_sortie < reference:
        reference = immo.date_sortie
    sit = situation_a_date(immo, reference)
    data = {c.name: getattr(immo, c.name) for c in immo.__table__.columns}
    data.update({
        "tva_acquisition": vent["tva_totale"],
        "tva_recuperable": vent["tva_recuperable"],
        "tva_non_recuperable": vent["tva_non_recuperable"],
        "total_ttc": vent["ttc"],
        "cumul_amortissement": sit["cumul"],
        "vnc_actuelle": sit["vnc"],
    })
    return data


@router.get("", response_model=List[schemas.ImmobilisationOut])
def lister(
    inclure_sorties: bool = Query(True),
    current_user=Depends(get_current_user),
    db: Session=Depends(get_db),
):
    q = db.query(models.Immobilisation).filter_by(societe_id=current_user["societe_id"])
    if not inclure_sorties:
        q = q.filter(models.Immobilisation.actif == True)  # noqa: E712
    immos = q.order_by(models.Immobilisation.date_acquisition.desc(), models.Immobilisation.id.desc()).all()
    return [_serialiser_immo(i) for i in immos]


class ReconciliationHistoriqueItemIn(BaseModel):
    immo_id: int
    categorie_cible: str


class ReconciliationHistoriqueIn(BaseModel):
    exercice: int
    items: list[ReconciliationHistoriqueItemIn]


class ReconstitutionAcquisitionItemIn(BaseModel):
    immo_id: int
    mode: str  # dette_acquisition | tresorerie | autre | reprise_anterieure
    compte_contrepartie: str


class ReconstitutionAcquisitionsIn(BaseModel):
    exercice: int
    items: list[ReconstitutionAcquisitionItemIn]


class CorrectionAmortissementsIn(BaseModel):
    exercice: int
    immo_ids: list[int] | None = None


def _compte_bilan_valide(compte: str) -> str:
    c = str(compte or "").strip()
    if len(c) < 3 or len(c) > 10 or not c.isdigit() or c[0] not in "12345":
        raise HTTPException(400, f"Compte de contrepartie invalide : {c or '(vide)'}. Utilisez un compte de bilan (classe 1 à 5).")
    return c


def _assert_date_ouverte(db: Session, societe_id: int, ex, d: date):
    if d < ex.date_debut or d > ex.date_fin:
        raise HTTPException(400, f"La date {d.isoformat()} n'appartient pas à l'exercice {ex.annee}.")
    periode = db.query(models.PeriodeComptable).filter(
        models.PeriodeComptable.exercice_id == ex.id,
        models.PeriodeComptable.date_debut <= d,
        models.PeriodeComptable.date_fin >= d,
    ).first()
    if periode and periode.statut == "fermee":
        raise HTTPException(423, f"La période {periode.libelle} est fermée : rouvrez-la avant la reconstitution historique.")


def _exercice_et_periode_fin_ouverts(db: Session, societe_id: int, exercice: int):
    from routers.cloture import exercice_est_clos
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=exercice).first()
    if not ex:
        raise HTTPException(404, f"Exercice {exercice} introuvable")
    if ex.statut == "cloture" or exercice_est_clos(db, societe_id, exercice):
        raise HTTPException(423, f"Exercice {exercice} clôturé : rouvrez-le avant une réconciliation historique.")
    periode = db.query(models.PeriodeComptable).filter(
        models.PeriodeComptable.exercice_id == ex.id,
        models.PeriodeComptable.date_debut <= ex.date_fin,
        models.PeriodeComptable.date_fin >= ex.date_fin,
    ).first()
    if periode and periode.statut == "fermee":
        raise HTTPException(423, f"La période {periode.libelle} est fermée : rouvrez-la avant de générer les reclassements.")
    return ex


@router.get("/reconciliation-historique")
def reconciliation_historique(
    exercice: int,
    current_user=Depends(get_current_user),
    db: Session=Depends(get_db),
):
    from routers.cloture import exercice_est_clos
    societe_id = current_user["societe_id"]
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=exercice).first()
    if not ex:
        raise HTTPException(404, f"Exercice {exercice} introuvable")
    data = analyser_reconciliation(db, models, societe_id, exercice, ex.date_fin)
    data["exercice_statut"] = ex.statut
    data["peut_reclasser"] = ex.statut != "cloture" and not exercice_est_clos(db, societe_id, exercice)
    data["categories"] = list(CATEGORY_ACCOUNTS.keys())
    data["note"] = (
        "HisabPro ne crée aucune acquisition, dette, TVA ou reprise d'antériorité manquante automatiquement. "
        "Le reclassement déplace seulement des montants déjà comptabilisés entre comptes, à valeur constante."
    )
    return data


@router.post("/reconciliation-historique/reclasser")
def reclasser_historique(
    data: ReconciliationHistoriqueIn,
    current_user=Depends(requiert_admin),
    db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    ex = _exercice_et_periode_fin_ouverts(db, societe_id, data.exercice)
    if not data.items:
        raise HTTPException(400, "Sélectionnez au moins une immobilisation à reclasser")
    _verifier_selection_unique(data.items)

    generees = []
    sans_ecriture = []
    for choix in data.items:
        if choix.categorie_cible not in CATEGORY_ACCOUNTS:
            raise HTTPException(400, f"Catégorie cible invalide : {choix.categorie_cible}")
        immo = _get_immo(db, societe_id, choix.immo_id, ecriture=True)
        if immo.date_acquisition > ex.date_fin:
            raise HTTPException(400, f"{immo.designation} n'appartient pas encore à l'exercice {data.exercice}")

        ref = f"RECLASS-IMMO-{data.exercice}-{immo.id}"
        existe = db.query(models.Ecriture).filter_by(societe_id=societe_id, reference=ref).first()
        if existe:
            raise HTTPException(409, f"Un reclassement existe déjà pour {immo.designation} (écriture {existe.id}).")

        diagnostic = analyser_immo(db, models, immo, societe_id, data.exercice)
        cible = comptes_recommandes(choix.categorie_cible)
        lignes = construire_lignes_reclassement(diagnostic, cible, data.exercice)

        # Le registre est corrigé dans la même transaction que l'OD. Pour les
        # immobilisations sans montant comptabilisé à reclasser, aucune écriture
        # artificielle n'est créée : le diagnostic continuera à signaler le brut
        # ou l'antériorité manquante.
        immo.categorie = choix.categorie_cible
        immo.compte_immo = cible["compte_immo"]
        immo.compte_amort = cible["compte_amort"]
        immo.compte_dotation = cible["compte_dotation"]

        if not lignes:
            sans_ecriture.append({"immo_id": immo.id, "designation": immo.designation})
            continue

        ecriture = models.Ecriture(
            societe_id=societe_id,
            date=ex.date_fin,
            journal=models.JournalEnum.OD,
            libelle=f"Réconciliation historique immobilisation — {immo.designation}",
            reference=ref,
            exercice=data.exercice,
            source="immobilisation",
        )
        db.add(ecriture); db.flush()
        for compte, debit, credit, libelle in lignes:
            db.add(models.LigneEcriture(
                ecriture_id=ecriture.id, compte=compte,
                libelle=f"{libelle} — {immo.designation}",
                debit=recon_money(debit), credit=recon_money(credit),
            ))
        generees.append({
            "immo_id": immo.id, "designation": immo.designation,
            "ecriture_id": ecriture.id, "nb_lignes": len(lignes),
        })

    db.commit()
    return {
        "message": "Reclassements historiques générés en brouillon. Contrôlez-les puis validez-les dans le Journal.",
        "nb_ecritures": len(generees),
        "generees": generees,
        "sans_ecriture": sans_ecriture,
        "attention": "Les acquisitions/TVA/antériorités manquantes ne sont pas créées par cette action.",
    }


@router.post("/reconciliation-historique/reconstituer-acquisitions")
def reconstituer_acquisitions_historique(
    data: ReconstitutionAcquisitionsIn,
    current_user=Depends(requiert_admin),
    db: Session=Depends(get_db),
):
    """Reconstitue uniquement des acquisitions explicitement confirmées.

    - acquisition de N : le registre fournit les montants HT/TVA/TTC, mais
      l'utilisateur choisit explicitement la contrepartie (dette, trésorerie ou autre) ;
    - acquisition antérieure : reprise au 01/01/N, sans TVA, avec amortissements
      antérieurs et compte de contrepartie d'ouverture explicitement fourni.
    """
    societe_id = current_user["societe_id"]
    ex = _exercice_et_periode_fin_ouverts(db, societe_id, data.exercice)
    if not data.items:
        raise HTTPException(400, "Sélectionnez au moins une acquisition à reconstituer")
    _verifier_selection_unique(data.items)

    generees = []
    for choix in data.items:
        immo = _get_immo(db, societe_id, choix.immo_id, ecriture=True)
        diagnostic = analyser_immo(db, models, immo, societe_id, data.exercice)
        statut = diagnostic["acquisition"]["statut"]
        if not statut.startswith("manquante"):
            raise HTTPException(409, f"{immo.designation} : l'acquisition n'est plus manquante.")

        contrepartie = _compte_bilan_valide(choix.compte_contrepartie)
        cible = comptes_recommandes(immo.categorie)
        compte_immo = cible["compte_immo"]
        compte_amort = cible["compte_amort"]

        if statut == "manquante_exercice":
            if choix.mode not in {"dette_acquisition", "tresorerie", "autre"}:
                raise HTTPException(400, f"{immo.designation} : mode de reconstitution invalide pour une acquisition {data.exercice}.")
            d = immo.date_acquisition
            _assert_date_ouverte(db, societe_id, ex, d)
            acq = diagnostic["acquisition"]
            lignes = construire_lignes_acquisition_reconstituee(
                acq["brut_registre"], acq["tva_recuperable_registre"], acq["ttc_registre"],
                compte_immo, acq["compte_tva"], contrepartie,
            )
            ref = f"RECON-ACQ-{data.exercice}-{immo.id}"
            libelle = f"Reconstitution acquisition historique — {immo.designation}"
            journal = models.JournalEnum.OD
        elif statut == "manquante_anterieure":
            if choix.mode != "reprise_anterieure":
                raise HTTPException(400, f"{immo.designation} : une acquisition antérieure doit être reprise comme solde d'ouverture.")
            d = ex.date_debut
            _assert_date_ouverte(db, societe_id, ex, d)
            acq = diagnostic["acquisition"]
            lignes = construire_lignes_reprise_ouverture(
                acq["brut_registre"], acq["amortissement_ouverture_suggere"],
                compte_immo, compte_amort, contrepartie,
            )
            ref = f"RECON-OPEN-{data.exercice}-{immo.id}"
            libelle = f"Reprise d'ouverture immobilisation antérieure — {immo.designation}"
            journal = models.JournalEnum.AN
        else:
            raise HTTPException(400, f"{immo.designation} : statut {statut} non pris en charge.")

        existe = db.query(models.Ecriture).filter_by(societe_id=societe_id, reference=ref).first()
        if existe:
            raise HTTPException(409, f"Une reconstitution existe déjà pour {immo.designation} (écriture {existe.id}).")

        ecriture = models.Ecriture(
            societe_id=societe_id, date=d, journal=journal,
            libelle=libelle, reference=ref, exercice=data.exercice,
            source="immobilisation",
        )
        db.add(ecriture); db.flush()
        for compte, debit, credit, lib in lignes:
            ligne_obj = models.LigneEcriture(
                ecriture_id=ecriture.id, compte=compte, libelle=f"{lib} — {immo.designation}",
                debit=recon_money(debit), credit=recon_money(credit),
            )
            if getattr(immo, "fournisseur_tiers_id", None):
                rattacher_ligne_auxiliaire(
                    db, societe_id, ligne_obj,
                    tiers_id=immo.fournisseur_tiers_id, nature="fournisseur",
                )
            db.add(ligne_obj)

        immo.ecriture_acquisition_id = ecriture.id
        immo.compte_immo = compte_immo
        immo.compte_amort = compte_amort
        immo.compte_dotation = cible["compte_dotation"]
        if statut == "manquante_exercice" and choix.mode == "tresorerie":
            immo.date_paiement = d
            immo.compte_reglement = contrepartie
            immo.ecriture_paiement_id = ecriture.id

        generees.append({
            "immo_id": immo.id, "designation": immo.designation,
            "ecriture_id": ecriture.id, "reference": ref,
            "type": "reprise_ouverture" if statut == "manquante_anterieure" else "acquisition_exercice",
        })

    db.commit()
    return {
        "message": "Reconstitutions générées en brouillon. Contrôlez-les puis validez-les dans le Journal.",
        "nb_ecritures": len(generees), "generees": generees,
        "attention": "Aucune contrepartie n'a été devinée par HisabPro : les comptes utilisés sont ceux confirmés dans l'assistant.",
    }


@router.post("/reconciliation-historique/corriger-amortissements")
def corriger_amortissements_historique(
    data: CorrectionAmortissementsIn,
    current_user=Depends(requiert_admin),
    db: Session=Depends(get_db),
):
    """Ramène la dotation de N au montant du plan, sans réécrire les exercices antérieurs."""
    societe_id = current_user["societe_id"]
    ex = _exercice_et_periode_fin_ouverts(db, societe_id, data.exercice)
    _assert_date_ouverte(db, societe_id, ex, ex.date_fin)
    q = db.query(models.Immobilisation).filter(
        models.Immobilisation.societe_id == societe_id,
        models.Immobilisation.date_acquisition <= ex.date_fin,
    )
    if data.immo_ids:
        q = q.filter(models.Immobilisation.id.in_(data.immo_ids))
    immos = q.order_by(models.Immobilisation.id).all()

    generees = []
    ignorees = []
    for immo in immos:
        immo = _get_immo(db, societe_id, immo.id, ecriture=True)
        diagnostic = analyser_immo(db, models, immo, societe_id, data.exercice)
        if diagnostic["acquisition"]["statut"].startswith("manquante"):
            ignorees.append({"immo_id": immo.id, "designation": immo.designation, "raison": "acquisition encore manquante"})
            continue
        ecart = recon_money(
            Decimal(str(diagnostic["amortissement"]["attendu_exercice"]))
            - Decimal(str(diagnostic["amortissement"]["comptabilise_exercice"]))
        )
        lignes = construire_lignes_correction_dotation(ecart, immo.compte_amort, immo.compte_dotation)
        if not lignes:
            ignorees.append({"immo_id": immo.id, "designation": immo.designation, "raison": "dotation de l'exercice déjà correcte"})
            continue
        ref = f"RECON-AMORT-{data.exercice}-{immo.id}"
        existe = db.query(models.Ecriture).filter_by(societe_id=societe_id, reference=ref).first()
        if existe:
            ignorees.append({"immo_id": immo.id, "designation": immo.designation, "raison": f"correction déjà créée ({existe.id})"})
            continue
        ecriture = models.Ecriture(
            societe_id=societe_id, date=ex.date_fin, journal=models.JournalEnum.AM,
            libelle=f"Correction amortissement historique — {immo.designation}",
            reference=ref, exercice=data.exercice, source="immobilisation",
        )
        db.add(ecriture); db.flush()
        for compte, debit, credit, lib in lignes:
            db.add(models.LigneEcriture(
                ecriture_id=ecriture.id, compte=compte,
                libelle=f"{lib} — {immo.designation}", debit=recon_money(debit), credit=recon_money(credit),
            ))
        generees.append({"immo_id": immo.id, "designation": immo.designation, "ecriture_id": ecriture.id, "ecart_dotation": float(ecart)})

    db.commit()
    return {
        "message": "Corrections d'amortissement générées en brouillon.",
        "nb_ecritures": len(generees), "generees": generees, "ignorees": ignorees,
        "attention": "Seule la dotation de l'exercice courant est corrigée ; les exercices antérieurs ne sont jamais réécrits.",
    }


@router.post("", response_model=schemas.ImmobilisationOut, status_code=201)
def creer(
    data: schemas.ImmobilisationCreate,
    generer_ecriture: bool = True,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    exercice_acquisition = _exercice_ouvert_pour_date(db, societe_id, data.date_acquisition, "enregistrer")

    if data.date_acquisition > date.today():
        raise HTTPException(400, "La date d'acquisition ne peut pas être future")
    if data.date_paiement and data.date_paiement > date.today():
        raise HTTPException(400, "La date de paiement ne peut pas être future")

    try:
        qualification_tva = qualification_valide(data.qualification_tva)
        taux_tva = valider_tva(data.date_acquisition, data.taux_tva, qualification_tva)
        tva_recuperable_pct = data.tva_recuperable_pct if qualification_tva == "taxable" else Decimal("0")
        vent = ventilation_acquisition(data.prix_acquisition_ht, taux_tva, tva_recuperable_pct)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    if data.valeur_residuelle > vent["cout_entree"]:
        raise HTTPException(400, "La valeur résiduelle ne peut pas dépasser le coût d'entrée comptable")

    fournisseur_tiers = _resoudre_fournisseur(
        db, societe_id, data.fournisseur_tiers_id, data.fournisseur
    )
    fournisseur_nom = fournisseur_tiers.nom if fournisseur_tiers else _nettoyer_nom_tiers(data.fournisseur) or None

    coeff = coefficient_degressif(data.duree_amort) if data.methode == "degressif" else None

    immo = models.Immobilisation(
        societe_id=societe_id,
        designation=data.designation,
        reference=data.reference,
        categorie=data.categorie,
        date_acquisition=data.date_acquisition,
        date_mise_en_service=data.date_mise_en_service or data.date_acquisition,
        prix_acquisition_ht=vent["prix_ht"],
        taux_tva=D(taux_tva),
        qualification_tva=qualification_tva,
        tva_recuperable_pct=D(tva_recuperable_pct),
        valeur_brute=vent["cout_entree"],
        valeur_residuelle=money(data.valeur_residuelle),
        fournisseur=fournisseur_nom,
        fournisseur_tiers_id=fournisseur_tiers.id if fournisseur_tiers else None,
        date_paiement=data.date_paiement,
        tva_suivie_directement=True,
        amortissable=data.amortissable,
        duree_amort=data.duree_amort if data.amortissable else None,
        methode=data.methode,
        taux_degressif=coeff if data.methode == "degressif" else None,
        vehicule_tourisme=data.vehicule_tourisme,
        compte_immo=data.compte_immo,
        compte_amort=data.compte_amort,
        compte_dotation=data.compte_dotation,
        compte_tva=data.compte_tva,
        compte_fournisseur=data.compte_fournisseur,
        compte_reglement=data.compte_reglement,
        compte_produit_cession="7512" if (str(data.compte_immo).startswith("22") or (data.categorie or "").strip().lower() == "logiciel") else "7513",
        compte_vna_cession="6512" if (str(data.compte_immo).startswith("22") or (data.categorie or "").strip().lower() == "logiciel") else "6513",
        notes=data.notes,
        actif=True,
    )
    db.add(immo)
    db.flush()

    if generer_ecriture:
        ecriture = models.Ecriture(
            societe_id=societe_id,
            date=data.date_acquisition,
            journal=models.JournalEnum.AC,
            libelle=f"Acquisition immobilisation — {data.designation}",
            reference=f"ACQ-{exercice_acquisition.annee}-{immo.id}",
            exercice=exercice_acquisition.annee,
            source="immobilisation",
        )
        db.add(ecriture)
        db.flush()
        db.add(models.LigneEcriture(
            ecriture_id=ecriture.id, compte=data.compte_immo,
            libelle=f"Acquisition {data.designation}", debit=vent["cout_entree"], credit=ZERO,
        ))
        if vent["tva_recuperable"] > ZERO:
            db.add(models.LigneEcriture(
                ecriture_id=ecriture.id, compte=data.compte_tva,
                libelle=f"TVA récupérable sur immobilisation — {data.designation}",
                debit=vent["tva_recuperable"], credit=ZERO,
            ))
        ligne_fournisseur = models.LigneEcriture(
            ecriture_id=ecriture.id, compte=data.compte_fournisseur,
            libelle=f"Dette acquisition immobilisation — {fournisseur_nom or data.designation}",
            debit=ZERO, credit=vent["ttc"],
        )
        if fournisseur_tiers:
            rattacher_ligne_auxiliaire(
                db, societe_id, ligne_fournisseur, tiers=fournisseur_tiers, nature="fournisseur"
            )
        db.add(ligne_fournisseur)
        immo.ecriture_acquisition_id = ecriture.id

        if data.date_paiement:
            exercice_paiement = _exercice_ouvert_pour_date(db, societe_id, data.date_paiement, "enregistrer")
            paiement = models.Ecriture(
                societe_id=societe_id,
                date=data.date_paiement,
                journal=_journal_tresorerie(data.compte_reglement),
                libelle=f"Paiement immobilisation — {data.designation}",
                reference=f"PAY-IMMO-{immo.id}",
                exercice=exercice_paiement.annee,
                source="immobilisation",
            )
            db.add(paiement)
            db.flush()
            ligne_fournisseur_paiement = models.LigneEcriture(
                ecriture_id=paiement.id, compte=data.compte_fournisseur,
                libelle=f"Règlement dette immobilisation — {data.designation}",
                debit=vent["ttc"], credit=ZERO,
            )
            if fournisseur_tiers:
                rattacher_ligne_auxiliaire(
                    db, societe_id, ligne_fournisseur_paiement, tiers=fournisseur_tiers, nature="fournisseur"
                )
            db.add(ligne_fournisseur_paiement)
            db.add(models.LigneEcriture(
                ecriture_id=paiement.id, compte=data.compte_reglement,
                libelle=f"Paiement immobilisation — {data.designation}",
                debit=ZERO, credit=vent["ttc"],
            ))
            immo.ecriture_paiement_id = paiement.id

    db.commit()
    db.refresh(immo)
    return _serialiser_immo(immo)


@router.post("/{immo_id}/payer")
def payer_acquisition(
    immo_id: int,
    data: schemas.ImmobilisationPaiementIn,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    immo = _get_immo(db, societe_id, immo_id, ecriture=True)
    if immo.date_paiement or immo.ecriture_paiement_id:
        raise HTTPException(409, "Cette acquisition est déjà marquée comme payée")
    if data.date_paiement < immo.date_acquisition:
        raise HTTPException(400, "Le paiement ne peut pas précéder l'acquisition")
    if data.date_paiement > date.today():
        raise HTTPException(400, "La date de paiement ne peut pas être future")
    if not immo.ecriture_acquisition_id:
        raise HTTPException(409, "L'écriture d'acquisition doit être générée avant le paiement")
    exercice_paiement = _exercice_ouvert_pour_date(db, societe_id, data.date_paiement, "enregistrer")

    vent = ventilation_acquisition(immo.prix_acquisition_ht, immo.taux_tva, immo.tva_recuperable_pct)
    compte = data.compte_reglement or immo.compte_reglement or "5141"
    ecriture = models.Ecriture(
        societe_id=societe_id, date=data.date_paiement, journal=_journal_tresorerie(compte),
        libelle=f"Paiement immobilisation — {immo.designation}",
        reference=data.reference or f"PAY-IMMO-{immo.id}", exercice=exercice_paiement.annee,
        source="immobilisation",
    )
    db.add(ecriture); db.flush()
    ligne_fournisseur = models.LigneEcriture(
        ecriture_id=ecriture.id, compte=immo.compte_fournisseur,
        libelle=f"Règlement dette immobilisation — {immo.designation}", debit=vent["ttc"], credit=ZERO
    )
    if getattr(immo, "fournisseur_tiers_id", None):
        rattacher_ligne_auxiliaire(
            db, societe_id, ligne_fournisseur,
            tiers_id=immo.fournisseur_tiers_id, nature="fournisseur",
        )
    db.add(ligne_fournisseur)
    db.add(models.LigneEcriture(ecriture_id=ecriture.id, compte=compte,
        libelle=f"Paiement immobilisation — {immo.designation}", debit=ZERO, credit=vent["ttc"]))
    immo.date_paiement = data.date_paiement
    immo.compte_reglement = compte
    immo.ecriture_paiement_id = ecriture.id
    db.commit()
    return {"message": "Acquisition marquée payée", "ecriture_id": ecriture.id, "date_paiement": data.date_paiement}


@router.get("/{immo_id}/tableau")
def tableau_amortissement(
    immo_id: int,
    current_user=Depends(get_current_user),
    db: Session=Depends(get_db),
):
    immo = _get_immo(db, current_user["societe_id"], immo_id)
    try:
        tableau = calculer_tableau_amortissement(immo)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {
        "immobilisation": _serialiser_immo(immo),
        "tableau": [
            {**l,
             "debut_periode": l["debut_periode"].isoformat(),
             "fin_periode": l["fin_periode"].isoformat(),
             "base_debut": float(l["base_debut"]), "prorata": float(l["prorata"]),
             "dotation": float(l["dotation"]), "cumul": float(l["cumul"]),
             "valeur_nette": float(l["valeur_nette"]), "taux_effectif": float(l["taux_effectif"]),
             **({"coefficient": float(l["coefficient"])} if "coefficient" in l else {})}
            for l in tableau
        ],
    }


@router.post("/{immo_id}/generer-ecriture")
def generer_ecriture_amortissement(
    immo_id: int,
    annee: int,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    immo = _get_immo(db, societe_id, immo_id, ecriture=True)
    if not immo.amortissable:
        raise HTTPException(400, "Cette immobilisation n'est pas amortissable")
    _check_exercice_ouvert(db, societe_id, annee)

    ref = f"AM-{annee}-{immo.id}"
    existe = db.query(models.Ecriture).filter_by(societe_id=societe_id, reference=ref).first()
    if existe:
        raise HTTPException(409, f"La dotation {annee} existe déjà (écriture {existe.id}).")

    ligne = _ligne_dotation_exercice(db, societe_id, immo, annee)
    if not ligne or money(ligne["dotation"]) <= ZERO:
        raise HTTPException(400, f"Aucune dotation pour l'exercice {annee}")
    date_ecriture = ligne["fin_periode"]
    ecriture = _creer_ecriture_dotation(db, societe_id, immo, ligne, date_ecriture)
    db.commit()
    return {"message": f"Écriture générée pour {annee}", "ecriture_id": ecriture.id, "dotation": float(money(ligne["dotation"]))}


@router.post("/generer-dotations-annee")
def generer_dotations_annee(
    annee: int,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    # Aussi appelée directement depuis le routeur de préparation de clôture.
    verrouiller_registre(db, societe_id)
    _check_exercice_ouvert(db, societe_id, annee)
    ex = ensure_exercice(db, societe_id, annee)
    immos = db.query(models.Immobilisation).filter(
        models.Immobilisation.societe_id == societe_id,
        models.Immobilisation.amortissable == True,  # noqa: E712
        models.Immobilisation.date_mise_en_service <= ex.date_fin,
    ).filter(
        (models.Immobilisation.date_sortie == None) | (models.Immobilisation.date_sortie >= ex.date_debut)  # noqa: E711
    ).order_by(models.Immobilisation.id).all()

    generees, ignorees = [], []
    total = ZERO
    for immo in immos:
        immo = _get_immo(db, societe_id, immo.id, ecriture=True)
        if (not immo.amortissable or immo.date_mise_en_service > ex.date_fin
                or (immo.date_sortie is not None and immo.date_sortie < ex.date_debut)):
            continue
        ligne = _ligne_dotation_exercice(db, societe_id, immo, annee)
        if not ligne or money(ligne["dotation"]) <= ZERO:
            continue
        ref = f"AM-{annee}-{immo.id}"
        if db.query(models.Ecriture).filter_by(societe_id=societe_id, reference=ref).first():
            ignorees.append(immo.designation)
            continue
        ecriture = _creer_ecriture_dotation(db, societe_id, immo, ligne, ligne["fin_periode"])
        generees.append(immo.designation)
        total += money(ligne["dotation"])
    db.commit()
    return {
        "annee": annee, "nb_generees": len(generees), "nb_ignorees": len(ignorees),
        "total_dotation": float(money(total)), "generees": generees, "ignorees": ignorees,
    }


def _verifier_dates_sortie(immo, data):
    if not immo.actif or immo.date_sortie:
        raise HTTPException(409, "Cette immobilisation est déjà sortie du registre")
    if data.date_sortie < immo.date_mise_en_service:
        raise HTTPException(400, "La sortie ne peut pas précéder la mise en service")
    if data.date_sortie > date.today():
        raise HTTPException(400, "La date de sortie ne peut pas être future")


def _preparer_dotations_sortie(db, societe_id, immo, data, *, materialiser_calendrier=False):
    """Préparation commune ; seule l'écriture conserve l'initialisation historique."""

    # Une reprise explicite remplace les soldes antérieurs à son ouverture :
    # les annuités couvertes ne doivent pas être recréées lors de la sortie.
    debut_reprise = None
    acquisition = _ecriture_acquisition(db, models, immo, societe_id)
    if acquisition and acquisition.reference == f"RECON-OPEN-{acquisition.exercice}-{immo.id}":
        ex_reprise = db.query(models.ExerciceComptable).filter_by(
            societe_id=societe_id, annee=acquisition.exercice).first()
        if (not acquisition.est_validee or not ex_reprise
                or acquisition.date != ex_reprise.date_debut
                or acquisition.journal != models.JournalEnum.AN):
            raise HTTPException(409,
                "Contrôlez puis validez la reprise d'ouverture à la date de début de son exercice avant la sortie.")
        debut_reprise = acquisition.date
        if data.date_sortie < debut_reprise:
            raise HTTPException(409, "La sortie ne peut pas précéder la reprise d'ouverture comptabilisée.")

    # Recalcul du plan par exercices comptables réels (civil ou décalé), arrêté à la sortie.
    q_exercices = db.query(models.ExerciceComptable).filter(
        models.ExerciceComptable.societe_id == societe_id,
        models.ExerciceComptable.date_fin >= immo.date_mise_en_service,
        models.ExerciceComptable.date_debut <= data.date_sortie,
    )
    if debut_reprise:
        q_exercices = q_exercices.filter(models.ExerciceComptable.date_fin >= debut_reprise)
    exercices_immo = q_exercices.order_by(models.ExerciceComptable.date_debut.asc()).all()
    dotations = []
    for ex_dotation in exercices_immo:
        ligne = (_ligne_dotation_exercice(db, societe_id, immo, ex_dotation.annee, data.date_sortie)
                 if materialiser_calendrier else _calcul_dotation_exercice(immo, ex_dotation, data.date_sortie))
        if not ligne or money(ligne["dotation"]) <= ZERO:
            continue
        annee = ex_dotation.annee
        ref = f"AM-{annee}-{immo.id}"
        existe = db.query(models.Ecriture).filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.reference.in_([ref, f"RECON-AMORT-{annee}-{immo.id}"]),
            models.Ecriture.exercice == annee,
        ).all()
        if existe:
            reel = money(sum((_montant_dotation_ecriture(e, immo.compte_dotation) for e in existe), ZERO))
            attendu = money(ligne["dotation"])
            if abs(reel - attendu) > Decimal("0.01"):
                raise HTTPException(409,
                    f"La dotation {annee} déjà comptabilisée ({reel} MAD) diffère de la dotation attendue "
                    f"à la date de sortie ({attendu} MAD). Corriger/reprendre cette dotation avant la sortie.")
        else:
            _check_exercice_ouvert(db, societe_id, annee)
        dotations.append({"ligne": ligne, "existantes": existe})
    return debut_reprise, dotations


def _empreinte_sortie(immo, data, dotations):
    contenu = {
        "version": "APERCU_SORTIE_927",
        "immobilisation": {c.name: getattr(immo, c.name) for c in immo.__table__.columns},
        "demande": data.model_dump(mode="json", exclude={"empreinte_apercu"}),
        "montants": {"situation": resultat_cession(immo, data.date_sortie, data.prix_cession_ht), "tva": _tva_sortie(data)},
        "dotations": [{"ligne": d["ligne"], "existantes": [
            {"id": e.id, "date": e.date, "est_validee": e.est_validee,
             "lignes": [{"id": l.id, "compte": l.compte, "debit": l.debit, "credit": l.credit} for l in sorted(e.lignes, key=lambda l: l.id)]}
            for e in sorted(d["existantes"], key=lambda e: e.id)]} for d in dotations],
    }
    return hashlib.sha256(json.dumps(contenu, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str, allow_nan=False).encode('utf8')).hexdigest()


def _tva_sortie(data):
    prix = money(data.prix_cession_ht)
    if data.type_sortie != "cession":
        return prix, ZERO, "hors_champ", ZERO, ZERO
    try:
        qualification = qualification_valide(data.qualification_tva_cession)
        taux = D(valider_tva(data.date_sortie, data.taux_tva_cession, qualification))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    tva = money(prix * taux / Decimal("100"))
    return prix, taux, qualification, tva, money(prix + tva)


@router.post("/{immo_id}/sortie/apercu")
def apercu_sortie_immobilisation(immo_id: int, data: schemas.ImmobilisationSortieIn,
                               current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    """Aucun exercice, période, dotation ou écriture créé par ce calcul."""
    societe_id = current_user["societe_id"]
    immo = _get_immo(db, societe_id, immo_id)
    _verifier_dates_sortie(immo, data)
    ex = trouver_exercice_pour_date(db, societe_id, data.date_sortie, creer_si_absent=False)
    if not ex:
        raise HTTPException(409, "Paramétrez l’exercice de sortie avant de demander l’aperçu ; aucun exercice n’a été créé.")
    if ex.statut == 'cloture':
        raise HTTPException(423, "Exercice de sortie clôturé : aucun aperçu de nouvelle sortie.")
    _check_exercice_ouvert(db, societe_id, ex.annee)
    periode = db.query(models.PeriodeComptable).filter(
        models.PeriodeComptable.exercice_id == ex.id,
        models.PeriodeComptable.date_debut <= data.date_sortie,
        models.PeriodeComptable.date_fin >= data.date_sortie,
    ).first()
    if not periode or periode.statut != "ouverte":
        raise HTTPException(423, "La période de sortie est absente ou non ouverte ; aucun calendrier n’a été modifié.")
    for champ in ['valeur_brute', 'valeur_residuelle']:
        valeur = getattr(immo, champ, None)
        if valeur is None or not D(valeur).is_finite():
            raise HTTPException(409, "Valeurs de l’immobilisation incomplètes ou non finies ; aucun montant de remplacement.")
    if immo.amortissable and (not immo.duree_amort or immo.duree_amort <= 0 or immo.methode not in {'lineaire','degressif'}):
        raise HTTPException(409, "Durée ou méthode d’amortissement à compléter avant le calcul.")
    debut_reprise, dotations = _preparer_dotations_sortie(db, societe_id, immo, data)
    sit = resultat_cession(immo, data.date_sortie, data.prix_cession_ht)
    prix, taux, qualification, tva, ttc = _tva_sortie(data)
    return {
        "mode": "APERCU_SORTIE_NON_COMPTABILISE", "immo_id": immo.id, "date_sortie": data.date_sortie,
        "type_sortie": data.type_sortie, "methode": immo.methode,
        "convention": ("Bien déclaré non amortissable." if not immo.amortissable else
                       "Convention interne linéaire 30/360, bornes inclusives : le jour de sortie compte."
                       if immo.methode == "lineaire" else "Moteur dégressif existant, calcul par mois ; convention à examiner avec le plan."),
        "valeur_brute": money(immo.valeur_brute), "cumul_amortissement": sit['cumul_amortissement'],
        "vnc": sit['vnc'], "prix_cession_ht": prix, "tva_cession": tva, "ttc_cession": ttc,
        "resultat_cession": money(prix - sit['vnc']),
        "dotations": [{**d['ligne'], "etat": "déjà comptabilisée" if d['existantes'] else "à comptabiliser",
                       "ecriture_ids": [e.id for e in d['existantes']]} for d in dotations],
        "debut_reprise": debut_reprise, "empreinte_apercu": _empreinte_sortie(immo, data, dotations),
        "avertissement": "Aperçu selon les paramètres et l’historique actuels, sans écriture comptable. La convention et la qualification/régularisation de TVA restent à contrôler ; cet aperçu ne valide pas la conformité fiscale. Les contrôles sont rejoués lors de l’enregistrement.",
    }


@router.post("/{immo_id}/sortie")
def sortir_immobilisation(
    immo_id: int,
    data: schemas.ImmobilisationSortieIn,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    immo = _get_immo(db, societe_id, immo_id, ecriture=True)
    _verifier_dates_sortie(immo, data)
    exercice_sortie = _exercice_ouvert_pour_date(db, societe_id, data.date_sortie, "enregistrer")
    debut_reprise, dotations = _preparer_dotations_sortie(db, societe_id, immo, data, materialiser_calendrier=True)
    if data.empreinte_apercu and data.empreinte_apercu != _empreinte_sortie(immo, data, dotations):
        raise HTTPException(409, "Les paramètres ou les sources ont changé depuis l’aperçu. Recalculez l’aperçu avant de comptabiliser.")
    for d in dotations:
        if not d['existantes']:
            _creer_ecriture_dotation(db, societe_id, immo, d['ligne'], d['ligne']['fin_periode'])

    sit = resultat_cession(immo, data.date_sortie, data.prix_cession_ht)
    cumul = money(sit["cumul_amortissement"])
    vnc = money(sit["vnc"])
    if debut_reprise:
        # Session sans autoflush : inclure les lignes de dotation créées dans
        # cette transaction. Un refus annule aussi ces lignes, sans commit.
        db.flush()
        diagnostic = analyser_immo(db, models, immo, societe_id, exercice_sortie.annee)
        comptabilise = money(diagnostic["amortissement"]["comptabilise_cumule"])
        if abs(comptabilise - cumul) > Decimal("0.01"):
            raise HTTPException(409,
                f"Le cumul d'amortissement comptabilisé ({comptabilise} MAD) ne correspond pas "
                f"au cumul à la sortie ({cumul} MAD). Rapprochez l'historique de reprise avant la sortie.")

    # Sortie du bilan : 28x + VNA 6513 / 2xx.
    sortie = models.Ecriture(
        societe_id=societe_id, date=data.date_sortie, journal=models.JournalEnum.OD,
        libelle=f"Sortie immobilisation — {immo.designation}",
        reference=f"SORTIE-IMMO-{immo.id}", exercice=exercice_sortie.annee, source="immobilisation",
    )
    db.add(sortie); db.flush()
    if cumul > ZERO:
        db.add(models.LigneEcriture(ecriture_id=sortie.id, compte=immo.compte_amort,
            libelle=f"Reprise amortissements cumulés — {immo.designation}", debit=cumul, credit=ZERO))
    if vnc > ZERO:
        db.add(models.LigneEcriture(ecriture_id=sortie.id, compte=immo.compte_vna_cession,
            libelle=f"VNA immobilisation sortie — {immo.designation}", debit=vnc, credit=ZERO))
    db.add(models.LigneEcriture(ecriture_id=sortie.id, compte=immo.compte_immo,
        libelle=f"Sortie valeur brute — {immo.designation}", debit=ZERO, credit=money(immo.valeur_brute)))
    immo.ecriture_sortie_id = sortie.id

    tva_cession = ZERO
    ttc_cession = ZERO
    ecriture_cession = None
    ecriture_enc = None
    societe = db.query(models.Societe).filter_by(id=societe_id).first()

    if data.type_sortie == "cession":
        prix, taux, qualification_cession, tva_cession, ttc_cession = _tva_sortie(data)
        ecriture_cession = models.Ecriture(
            societe_id=societe_id, date=data.date_sortie, journal=models.JournalEnum.VT,
            libelle=f"Cession immobilisation — {immo.designation}",
            reference=data.reference or f"CESSION-IMMO-{immo.id}", exercice=exercice_sortie.annee,
            source="immobilisation",
        )
        db.add(ecriture_cession); db.flush()
        db.add(models.LigneEcriture(ecriture_id=ecriture_cession.id, compte=immo.compte_creance_cession,
            libelle=f"Créance cession — {immo.designation}", debit=ttc_cession, credit=ZERO))
        db.add(models.LigneEcriture(ecriture_id=ecriture_cession.id, compte=immo.compte_produit_cession,
            libelle=f"Produit cession — {immo.designation}", debit=ZERO, credit=prix))
        if tva_cession > ZERO:
            db.add(models.LigneEcriture(ecriture_id=ecriture_cession.id, compte=immo.compte_tva_cession,
                libelle=f"TVA cession — {immo.designation}", debit=ZERO, credit=tva_cession))
        immo.ecriture_cession_id = ecriture_cession.id
        immo.prix_cession_ht = prix
        immo.taux_tva_cession = taux
        immo.qualification_tva_cession = qualification_cession
        immo.regime_tva_cession = (getattr(societe, "regime_tva", None) or "encaissement").lower()

        if data.encaissement_immediat:
            enc_date = data.date_encaissement or data.date_sortie
            exercice_encaissement = _exercice_ouvert_pour_date(db, societe_id, enc_date, "enregistrer")
            ecriture_enc = models.Ecriture(
                societe_id=societe_id, date=enc_date, journal=_journal_tresorerie(data.compte_tresorerie),
                libelle=f"Encaissement cession — {immo.designation}",
                reference=f"ENC-CESSION-{immo.id}", exercice=exercice_encaissement.annee, source="immobilisation",
            )
            db.add(ecriture_enc); db.flush()
            db.add(models.LigneEcriture(ecriture_id=ecriture_enc.id, compte=data.compte_tresorerie,
                libelle=f"Encaissement cession — {immo.designation}", debit=ttc_cession, credit=ZERO))
            db.add(models.LigneEcriture(ecriture_id=ecriture_enc.id, compte=immo.compte_creance_cession,
                libelle=f"Solde créance cession — {immo.designation}", debit=ZERO, credit=ttc_cession))
            immo.date_encaissement_cession = enc_date
            immo.ecriture_encaissement_cession_id = ecriture_enc.id

    immo.date_sortie = data.date_sortie
    immo.type_sortie = data.type_sortie
    immo.actif = False
    db.commit()
    return {
        "message": "Cession comptabilisée" if data.type_sortie == "cession" else "Mise au rebut comptabilisée",
        "type_sortie": data.type_sortie,
        "date_sortie": data.date_sortie,
        "cumul_amortissement": float(cumul), "vnc": float(vnc),
        "prix_cession_ht": float(money(data.prix_cession_ht)),
        "tva_cession": float(tva_cession), "ttc_cession": float(ttc_cession),
        "resultat_cession": float(money(data.prix_cession_ht) - vnc) if data.type_sortie == "cession" else float(-vnc),
        "ecriture_sortie_id": sortie.id,
        "ecriture_cession_id": ecriture_cession.id if ecriture_cession else None,
        "ecriture_encaissement_id": ecriture_enc.id if ecriture_enc else None,
    }


@router.post("/{immo_id}/encaisser-cession")
def encaisser_cession(
    immo_id: int,
    data: schemas.ImmobilisationEncaissementCessionIn,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    immo = _get_immo(db, societe_id, immo_id, ecriture=True)
    if immo.type_sortie != "cession" or not immo.ecriture_cession_id:
        raise HTTPException(409, "Cette immobilisation n'a pas de cession à encaisser")
    if immo.date_encaissement_cession or immo.ecriture_encaissement_cession_id:
        raise HTTPException(409, "Cette cession est déjà encaissée")
    if data.date_encaissement < immo.date_sortie:
        raise HTTPException(400, "L'encaissement ne peut pas précéder la cession")
    if data.date_encaissement > date.today():
        raise HTTPException(400, "La date d'encaissement ne peut pas être future")
    exercice_encaissement = _exercice_ouvert_pour_date(db, societe_id, data.date_encaissement, "enregistrer")

    prix = money(immo.prix_cession_ht)
    tva = money(prix * D(immo.taux_tva_cession or 0) / Decimal("100"))
    ttc = money(prix + tva)
    ecriture = models.Ecriture(
        societe_id=societe_id, date=data.date_encaissement, journal=_journal_tresorerie(data.compte_tresorerie),
        libelle=f"Encaissement cession — {immo.designation}",
        reference=data.reference or f"ENC-CESSION-{immo.id}", exercice=exercice_encaissement.annee,
        source="immobilisation",
    )
    db.add(ecriture); db.flush()
    db.add(models.LigneEcriture(ecriture_id=ecriture.id, compte=data.compte_tresorerie,
        libelle=f"Encaissement cession — {immo.designation}", debit=ttc, credit=ZERO))
    db.add(models.LigneEcriture(ecriture_id=ecriture.id, compte=immo.compte_creance_cession,
        libelle=f"Solde créance cession — {immo.designation}", debit=ZERO, credit=ttc))
    immo.date_encaissement_cession = data.date_encaissement
    immo.ecriture_encaissement_cession_id = ecriture.id
    db.commit()
    return {"message": "Cession encaissée", "ecriture_id": ecriture.id, "date_encaissement": data.date_encaissement}


@router.patch("/{immo_id}", response_model=schemas.ImmobilisationOut)
def modifier(
    immo_id: int,
    data: schemas.ImmobilisationUpdate,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    immo = _get_immo(db, societe_id, immo_id, ecriture=True)
    if immo.date_sortie:
        raise HTTPException(409, "Une immobilisation sortie ne peut plus être modifiée")

    changements = data.model_dump(exclude_none=True)

    # Le fournisseur peut être recherché/créé sans modifier les données financières
    # déjà comptabilisées. Si seul le nom change, on ne conserve pas par erreur un
    # ancien fournisseur_tiers_id.
    champs_fournisseur = data.model_fields_set.intersection({"fournisseur", "fournisseur_tiers_id"})
    if champs_fournisseur:
        fournisseur_id = data.fournisseur_tiers_id if "fournisseur_tiers_id" in data.model_fields_set else None
        fournisseur_nom = data.fournisseur if "fournisseur" in data.model_fields_set else immo.fournisseur
        fournisseur_tiers = _resoudre_fournisseur(db, societe_id, fournisseur_id, fournisseur_nom)
        immo.fournisseur = fournisseur_tiers.nom if fournisseur_tiers else _nettoyer_nom_tiers(fournisseur_nom) or None
        immo.fournisseur_tiers_id = fournisseur_tiers.id if fournisseur_tiers else None
        changements.pop("fournisseur", None)
        changements.pop("fournisseur_tiers_id", None)

    champs_acquisition = {"prix_acquisition_ht", "taux_tva", "qualification_tva", "tva_recuperable_pct", "compte_immo", "compte_tva", "compte_fournisseur"}
    if immo.ecriture_acquisition_id and champs_acquisition.intersection(changements):
        raise HTTPException(409, "Les données financières d'acquisition sont verrouillées car l'écriture d'acquisition existe")

    champs_plan = {"date_mise_en_service", "amortissable", "duree_amort", "methode", "taux_degressif", "valeur_residuelle", "compte_amort", "compte_dotation"}
    has_dotation = _a_dotation(db, societe_id, immo.id)
    if has_dotation and champs_plan.intersection(changements):
        raise HTTPException(409, "Le plan d'amortissement est verrouillé car des dotations ont déjà été comptabilisées")

    for k, v in changements.items():
        setattr(immo, k, v)

    if not immo.ecriture_acquisition_id and champs_acquisition.intersection(changements):
        try:
            qualification = qualification_valide(getattr(immo, "qualification_tva", "taxable"))
            taux = valider_tva(immo.date_acquisition, immo.taux_tva, qualification)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        immo.taux_tva = D(taux)
        if qualification != "taxable":
            immo.tva_recuperable_pct = ZERO
        vent = ventilation_acquisition(immo.prix_acquisition_ht, immo.taux_tva, immo.tva_recuperable_pct)
        immo.valeur_brute = vent["cout_entree"]

    # Revalidation métier du plan après modification.
    if immo.date_mise_en_service < immo.date_acquisition:
        raise HTTPException(400, "La mise en service ne peut pas précéder l'acquisition")
    if D(immo.valeur_residuelle) < ZERO or D(immo.valeur_residuelle) > D(immo.valeur_brute):
        raise HTTPException(400, "La valeur résiduelle doit être comprise entre 0 et la valeur brute")
    if (immo.categorie or "").strip().lower() == "terrain" or immo.compte_immo in {"2311", "2312", "2313", "2318"}:
        immo.amortissable = False
        immo.duree_amort = None
    if immo.amortissable and (not immo.duree_amort or immo.duree_amort <= 0):
        raise HTTPException(400, "Une immobilisation amortissable doit avoir une durée positive")
    if immo.methode == "degressif":
        if immo.duree_amort < 3 or immo.vehicule_tourisme or immo.compte_immo.startswith("232") or immo.compte_immo in {"2311", "2312", "2313", "2318"}:
            raise HTTPException(400, "Le dégressif n'est pas applicable à cette immobilisation")
        immo.taux_degressif = coefficient_degressif(immo.duree_amort)
    else:
        immo.taux_degressif = None

    db.commit(); db.refresh(immo)
    return _serialiser_immo(immo)


@router.delete("/{immo_id}", status_code=204)
def supprimer(
    immo_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    immo = _get_immo(db, current_user["societe_id"], immo_id, ecriture=True)
    if immo.ecriture_acquisition_id or _a_dotation(db, current_user["societe_id"], immo.id):
        raise HTTPException(409, "Une immobilisation comptabilisée ne se supprime pas : utilisez Cession ou Mise au rebut")
    immo.actif = False
    db.commit()
