# -*- coding: utf-8 -*-
"""
Clôture d'exercice comptable et génération des à-nouveaux.

Principe (CGNC) :
  1. On calcule le solde de chaque compte mouvementé sur l'exercice N.
  2. Comptes de gestion (classes 6 et 7) : on les solde via la cascade CGNC
     de classe 8 (8100/8300/8400/8500/8600/8800), puis vers 1191/1199.
  3. Comptes de bilan (classes 1 à 5) : leurs soldes de fin d'exercice sont reportés
     en « à-nouveaux » sur l'exercice N+1 via une écriture au journal AN, résultat inclus.
  4. L'exercice N est marqué clos : verrouillage de la saisie sur cette période.

COMPTA.3 : la clôture est définitive. Toute correction ultérieure passe par
une écriture sur une période ouverte, sans supprimer l'historique de clôture.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, or_, func

from database import get_db
from auth import get_current_user, requiert_ecriture, requiert_admin
import models
from services.cloture_service import (
    construire_ajustement, contrepasser, construire_ligne_soldage,
    construire_cascade_resultat, TYPES_AJUSTEMENT, money,
)
from services.exercices_service import (
    ensure_exercice, preparer_exercice_suivant, marquer_exercice_cloture,
    verifier_date_ecriture, activer_periodes_de_travail,
)
from services.stock_service import etat_stock_cloture
from services.livre_inventaire_service import etat_rapprochement_immobilisations
from services.fec_exercice_service import controler_fec_exercice
from services.fec_service import auxiliaire_fec
from services.affectation_resultat_service import calculer_contraintes_affectation
from services.immobilisations_verrou_service import verrouiller_registre
from services.exercice_verrou_service import verrouiller_deficits_fiscaux
from services.plan_comptable import libelle_compte

router = APIRouter(prefix="/api/cloture", tags=["cloture"])
from routers.cloture_prorata import router as prorata_documentaire
router.include_router(prorata_documentaire)
from routers.cloture_contrepassations import router as contrepassations_ouverture
from routers.cloture_reprises import router as reprises_provisions
router.include_router(reprises_provisions)
router.include_router(contrepassations_ouverture)


def exercice_est_clos(db: Session, societe_id: int, exercice: int) -> bool:
    return db.query(models.ClotureExercice).filter_by(
        societe_id=societe_id, exercice=exercice).first() is not None


class AffectationResultatIn(BaseModel):
    date_decision: date
    date_affectation: date
    reference_decision: str
    organe_decision: str
    reserve_legale: Decimal = Decimal("0.00")
    autres_reserves: Decimal = Decimal("0.00")
    report_a_nouveau: Decimal = Decimal("0.00")
    dividendes: Decimal = Decimal("0.00")

    @field_validator("reference_decision", "organe_decision")
    @classmethod
    def texte_decision_non_vide(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("La référence et l'organe de décision sont obligatoires.")
        return v

    @field_validator("reserve_legale", "autres_reserves", "report_a_nouveau", "dividendes")
    @classmethod
    def montant_non_negatif(cls, v):
        v = money(v)
        if v < 0:
            raise ValueError("Les montants d'affectation doivent être positifs ou nuls.")
        return v


def _soldes_comptes(db: Session, societe_id: int, exercice: int, exclure_cloture: bool = True, validees_seulement: bool = False):
    """Retourne {compte: solde signé} en Decimal (débit - crédit cumulés).

    Après clôture, l'écriture CLOTURE-N solde les classes 6/7. Pour continuer à
    afficher le résultat historique réel, on l'exclut par défaut des soldes de
    consultation.
    """
    soldes = {}
    q = (
        db.query(models.Ecriture)
        .options(joinedload(models.Ecriture.lignes))
        .filter(models.Ecriture.societe_id == societe_id,
                models.Ecriture.exercice == exercice)
    )
    if exclure_cloture:
        # Les pièces sans référence externe restent incluses dans la balance.
        # SQL NOT LIKE NULL éliminait auparavant les OD sans justificatif.
        q = q.filter(or_(
            models.Ecriture.reference.is_(None),
            ~models.Ecriture.reference.like(f"CLOTURE-{exercice}%"),
        ))
    if validees_seulement:
        q = q.filter(models.Ecriture.est_validee.is_(True))
    for ec in q.all():
        for l in ec.lignes:
            d = money(l.debit)
            c = money(l.credit)
            soldes[l.compte] = money(soldes.get(l.compte, Decimal("0.00")) + d - c)
    return soldes


def _resultat_cloture_effectif(db: Session, societe_id: int, exercice: int) -> Decimal:
    """Résultat net issu des écritures économiques, hors clôture technique.

    Cette lecture permet aussi de conserver un résultat cohérent lorsqu'une
    correction historique append-only (par exemple l'IS oublié avant clôture)
    a été ajoutée sans réécrire la trace de clôture d'origine.
    """
    soldes = _soldes_comptes(
        db, societe_id, exercice, exclure_cloture=True, validees_seulement=True
    )
    total_charges = sum((s for c, s in soldes.items() if c.startswith("6")), Decimal("0.00"))
    total_produits = sum((-s for c, s in soldes.items() if c.startswith("7")), Decimal("0.00"))
    return money(total_produits - total_charges)


def _lignes_bilan_a_reporter(db: Session, societe_id: int, exercice: int, *, validees_seulement=False):
    """Reporte les identités auxiliaires prouvées, jamais le nom actuel du tiers.

    Avis CNC n°24 §2.5 : soldes individuels et collectif restent rapprochables.
    Source : https://www.finances.gov.ma/fr/pages/detail-actualite.aspx?fiche=6558
    Un collectif net nul peut conserver des soldes individuels opposés.
    """
    q = db.query(models.Ecriture).options(
        joinedload(models.Ecriture.lignes).joinedload(models.LigneEcriture.auxiliaire_complements)
    ).filter(models.Ecriture.societe_id == societe_id, models.Ecriture.exercice == exercice,
        or_(models.Ecriture.reference.is_(None), ~models.Ecriture.reference.like(f"CLOTURE-{exercice}%")))
    if validees_seulement:
        q = q.filter(models.Ecriture.est_validee.is_(True))
    groupes = {}
    for ec in q.order_by(models.Ecriture.date, models.Ecriture.id).all():
        for ligne in sorted(ec.lignes, key=lambda l: l.id):
            compte = ligne.compte or ""
            if not compte or compte[0] not in "12345":
                continue
            tiers_id, nature, numero, libelle = auxiliaire_fec(ligne)
            if validees_seulement and compte.startswith(("3421", "4411")) and not (tiers_id and numero and libelle):
                raise HTTPException(409, f"À-nouveaux impossibles : auxiliaire non documenté sur le compte {compte}.")
            cle = (compte, tiers_id, nature, numero)
            groupe = groupes.setdefault(cle, {"solde": Decimal("0.00"), "libelle": libelle})
            groupe["solde"] = money(groupe["solde"] + money(ligne.debit) - money(ligne.credit))
            # Le dernier libellé comptable enregistré pour cette même identité
            # est conservé ; renommer le tiers vivant ne modifie pas le report.
            groupe["libelle"] = libelle
    resultat = []
    for (compte, tiers_id, nature, numero), groupe in sorted(groupes.items(),
            key=lambda item: (item[0][0], item[0][3] or "", item[0][1] or 0, item[0][2] or "")):
        solde = groupe["solde"]
        if solde == 0:
            continue
        resultat.append({"compte": compte, "debit": max(solde, Decimal("0.00")),
            "credit": max(-solde, Decimal("0.00")), "tiers_id": tiers_id,
            "nature_auxiliaire": nature or None, "compte_auxiliaire_snapshot": numero or None,
            "libelle_auxiliaire_snapshot": groupe["libelle"] or None})
    return resultat


def _etat_is_cloture(db: Session, societe_id: int, exercice: int, current_user, resultat_courant=None):
    """Prépare le contrôle IS utilisé par l'écran et la clôture définitive."""
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    if not societe or (societe.regime_fiscal or "is") != "is":
        return {"applicable": False, "coherente": True, "a_comptabiliser": 0.0}

    try:
        # Import local : évite de coupler le chargement des deux routers au démarrage.
        from routers.fiscalite import situation_is
        situation = situation_is(exercice, current_user=current_user, db=db)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return {"applicable": True, "coherente": False, "erreur": detail}

    compta = situation.get("comptabilisation_is") or {}
    attendu = money(compta.get("attendu"))
    comptabilise = money(compta.get("comptabilise"))
    absente = bool(compta.get("absente"))
    coherente = bool(compta.get("coherente"))
    deficits = situation.get("deficits") or {}
    deficits_a_confirmer = (
        money(deficits.get("total_propose")) > 0
        and not bool(deficits.get("confirmation_a_jour"))
    )

    courant = money(resultat_courant) if resultat_courant is not None else _resultat_cloture_effectif(db, societe_id, exercice)
    a_comptabiliser = attendu if absente else Decimal("0.00")
    resultat_apres = money(courant - a_comptabiliser) if (coherente or absente) else None
    return {
        "applicable": True,
        "attendu": float(attendu),
        "comptabilise": float(comptabilise),
        "compte_charge_attendu": compta.get("compte_charge_attendu"),
        "nature_impot": compta.get("nature_impot"),
        "absente": absente,
        "coherente": coherente,
        "a_comptabiliser": float(a_comptabiliser),
        "resultat_comptable_avant_is": float(money((situation.get("source_comptable") or {}).get("resultat_comptable_avant_is"))),
        "resultat_net_apres_is": float(resultat_apres) if resultat_apres is not None else None,
        "deficits_a_confirmer": deficits_a_confirmer,
    }


def _comptabiliser_is_cloture(db: Session, societe_id: int, exercice_obj, etat_is: dict, current_user):
    """Comptabilise l'impôt courant dans la transaction de clôture.

    IS : 6701 / 4453 ; cotisation minimale : 6705 / 4453.
    L'écriture est créée avant la cascade de résultat ; tout échec ultérieur de
    clôture annule donc aussi cette comptabilisation.
    """
    montant = money(etat_is.get("a_comptabiliser"))
    if montant <= 0:
        return None
    compte_charge = etat_is.get("compte_charge_attendu") or "6701"
    nature = etat_is.get("nature_impot") or "IS"
    reference = f"CALCUL-IS-{exercice_obj.annee}"
    deja = db.query(models.Ecriture).filter_by(
        societe_id=societe_id, exercice=exercice_obj.annee, reference=reference
    ).first()
    if deja:
        raise HTTPException(409,
            f"Une écriture {reference} existe déjà mais le rapprochement IS n'est pas cohérent. "
            "Contrôlez cette écriture avant de clôturer.")

    libelle = (
        f"Cotisation minimale — exercice {exercice_obj.annee}"
        if nature == "CM" else f"Impôt sur les bénéfices — exercice {exercice_obj.annee}"
    )
    db.execute(text("SELECT set_config('hisabpro.audit_actor_id', :v, true)"),
               {"v": str(current_user.get("id") or "")})
    db.execute(text("SELECT set_config('hisabpro.audit_motif', :v, true)"),
               {"v": f"Comptabilisation automatique de l'impôt courant avant clôture {exercice_obj.annee}"})
    ecriture = models.Ecriture(
        societe_id=societe_id,
        date=exercice_obj.date_fin,
        date_piece=exercice_obj.date_fin,
        journal=models.JournalEnum.OD,
        libelle=libelle,
        reference=reference,
        exercice=exercice_obj.annee,
        source="fiscalite_is",
        est_validee=False,
        lignes=[
            models.LigneEcriture(compte=compte_charge, libelle=libelle, debit=montant, credit=0),
            models.LigneEcriture(compte="4453", libelle=libelle, debit=0, credit=montant),
        ],
    )
    db.add(ecriture)
    db.flush()
    ecriture.est_validee = True
    ecriture.date_validation = datetime.now()
    ecriture.validee_par = current_user.get("id")
    db.flush()
    return ecriture


def _decision_affectation(db: Session, societe_id: int, exercice_origine: int):
    if not hasattr(models, "DecisionAffectationResultat"):
        return None
    return db.query(models.DecisionAffectationResultat).filter_by(
        societe_id=societe_id, exercice_origine=exercice_origine
    ).first()


def _ecriture_affectation_legacy(db: Session, societe_id: int, exercice_origine: int):
    """Compatibilité avec les affectations 051 antérieures à la table de décision."""
    return db.query(models.Ecriture).filter(
        models.Ecriture.societe_id == societe_id,
        models.Ecriture.reference == f"AFFECT-RESULTAT-{exercice_origine}",
        models.Ecriture.est_validee.is_(True),
    ).order_by(models.Ecriture.exercice, models.Ecriture.id).first()


def _ecriture_reclassement_instance(db: Session, societe_id: int, exercice_origine: int):
    return db.query(models.Ecriture).filter(
        models.Ecriture.societe_id == societe_id,
        models.Ecriture.reference == f"INSTANCE-AFFECT-{exercice_origine}",
        models.Ecriture.est_validee.is_(True),
    ).order_by(models.Ecriture.id.desc()).first()


def _exercice_ouvert_affectation(db: Session, societe_id: int, annee_min: int):
    return db.query(models.ExerciceComptable).filter(
        models.ExerciceComptable.societe_id == societe_id,
        models.ExerciceComptable.annee >= annee_min,
        models.ExerciceComptable.statut == "ouvert",
    ).order_by(models.ExerciceComptable.annee).first()


def _etat_affectation_resultat(db: Session, societe_id: int, exercice_origine: int, cloture=None):
    """État normatif de l'affectation d'un résultat clôturé.

    Tant que N+1 reste ouvert, le résultat de N demeure en 1191/1199. Si N+1
    est clôturé sans décision, la clôture 052 le reclasse en 1181/1189 ; le
    même assistant peut ensuite comptabiliser une décision tardive depuis le
    premier exercice ouvert, sans perdre le lien avec l'exercice d'origine.
    """
    cloture = cloture or db.query(models.ClotureExercice).filter_by(
        societe_id=societe_id, exercice=exercice_origine
    ).first()
    if not cloture:
        return None

    resultat = _resultat_cloture_effectif(db, societe_id, exercice_origine)
    type_resultat = "benefice" if resultat > 0 else ("perte" if resultat < 0 else "nul")
    decision = _decision_affectation(db, societe_id, exercice_origine)
    legacy = None if decision else _ecriture_affectation_legacy(db, societe_id, exercice_origine)
    if decision or legacy or resultat == 0:
        ecriture = decision.ecriture if decision else legacy
        exercice_affectation = (
            decision.exercice_comptabilisation if decision else
            (ecriture.exercice if ecriture else exercice_origine + 1)
        )
        return {
            "exercice_origine": exercice_origine,
            "exercice_affectation": exercice_affectation,
            "resultat_origine": float(resultat),
            "type_resultat": type_resultat,
            "compte_source": getattr(decision, "compte_source", None),
            "montant_restant": 0.0,
            "montant_a_ventiler": 0.0,
            "affecte": True,
            "exercice_affectation_disponible": True,
            "ecriture_affectation_id": ecriture.id if ecriture else None,
            "date_affectation": (decision.date_comptabilisation.isoformat() if decision else (ecriture.date.isoformat() if ecriture else None)),
            "date_decision": decision.date_decision.isoformat() if decision else None,
            "reference_decision": decision.reference_decision if decision else None,
            "organe_decision": decision.organe_decision if decision else None,
            "decision_tracee": bool(decision),
            "legacy": bool(legacy and not decision),
        }

    reclassement = _ecriture_reclassement_instance(db, societe_id, exercice_origine)
    compte_source = ("1181" if resultat > 0 else "1189") if reclassement else ("1191" if resultat > 0 else "1199")
    annee_min = (reclassement.exercice + 1) if reclassement else (exercice_origine + 1)
    ex = _exercice_ouvert_affectation(db, societe_id, annee_min)
    base = {
        "exercice_origine": exercice_origine,
        "exercice_affectation": ex.annee if ex else annee_min,
        "resultat_origine": float(resultat),
        "type_resultat": type_resultat,
        "compte_source": compte_source,
        "montant_restant": float(abs(resultat)),
        "affecte": False,
        "exercice_affectation_disponible": bool(ex),
        "reclasse_en_instance": bool(reclassement),
        "ecriture_reclassement_id": reclassement.id if reclassement else None,
        "decision_tracee": False,
    }
    if not ex:
        return base

    base.update({"date_debut": ex.date_debut.isoformat(), "date_fin": ex.date_fin.isoformat()})
    if resultat > 0:
        soldes = _soldes_comptes(db, societe_id, ex.annee, validees_seulement=True)
        societe = db.query(models.Societe).filter_by(id=societe_id).first()
        contraintes = calculer_contraintes_affectation(
            resultat_beneficiaire=abs(resultat),
            forme_juridique=getattr(societe, "forme_juridique", None),
            capital_social=getattr(societe, "capital_social", 0),
            reserve_legale_avant=max(-money(soldes.get("1140", 0)), Decimal("0.00")),
            report_deficitaire=max(money(soldes.get("1169", 0)), Decimal("0.00")),
            resultat_instance_deficitaire=max(money(soldes.get("1189", 0)), Decimal("0.00")),
            report_beneficiaire=max(-money(soldes.get("1161", 0)), Decimal("0.00")),
        )
        regle = contraintes["regle"]
        base.update({
            "forme_juridique": getattr(societe, "forme_juridique", None),
            "capital_social": float(money(getattr(societe, "capital_social", 0))),
            "forme_juridique_supportee": bool(contraintes["forme_supportee"]),
            "referentiel_reserve_legale": regle["referentiel"] if regle else None,
            "taux_reserve_legale": float(regle["taux"]) if regle else None,
            "plafond_ratio_reserve_legale": float(regle["plafond_ratio"]) if regle else None,
            "pertes_anterieures": float(contraintes["pertes_anterieures"]),
            "pertes_a_apurer": float(contraintes["pertes_a_apurer"]),
            "reserve_legale_avant": float(contraintes["reserve_legale_avant"]),
            "reserve_legale_minimale": float(contraintes["reserve_legale_minimale"]),
            "plafond_reserve_legale": float(contraintes["plafond_reserve_legale"]) if contraintes["plafond_reserve_legale"] is not None else None,
            "dividendes_max_sur_resultat": float(contraintes["dividendes_max_sur_resultat"]),
            "benefice_distribuable_indicatif": float(contraintes["benefice_distribuable_indicatif"]),
            "montant_a_ventiler": float(contraintes["affectable_apres_pertes"]),
        })
    else:
        base["montant_a_ventiler"] = float(abs(resultat))
    return base


def _reclasser_resultat_non_affecte(db: Session, societe_id: int, exercice: int, current_user):
    """À la clôture de N+1, vire le résultat N non affecté de 119 vers 118.

    Le CGNC distingue le résultat de l'exercice (119) du résultat net des
    exercices antérieurs encore en instance d'affectation (118). Cette
    écriture est générée avant la détermination du résultat courant afin que
    les à-nouveaux de l'exercice suivant portent la bonne rubrique.
    """
    origine = exercice - 1
    cloture_origine = db.query(models.ClotureExercice).filter_by(
        societe_id=societe_id, exercice=origine
    ).first()
    if not cloture_origine:
        return None
    resultat = _resultat_cloture_effectif(db, societe_id, origine)
    if abs(resultat) <= Decimal("0.005"):
        return None
    if _decision_affectation(db, societe_id, origine) or _ecriture_affectation_legacy(db, societe_id, origine):
        return None
    deja = _ecriture_reclassement_instance(db, societe_id, origine)
    if deja:
        return deja

    soldes = _soldes_comptes(db, societe_id, exercice, validees_seulement=True)
    attendu = abs(resultat)
    if resultat > 0:
        disponible = max(-money(soldes.get("1191", 0)), Decimal("0.00"))
        source, cible = "1191", "1181"
        lignes = [
            models.LigneEcriture(compte=source, libelle=f"Résultat {origine} non affecté — transfert en instance", debit=attendu, credit=0),
            models.LigneEcriture(compte=cible, libelle=f"Résultat {origine} en instance d'affectation", debit=0, credit=attendu),
        ]
    else:
        disponible = max(money(soldes.get("1199", 0)), Decimal("0.00"))
        source, cible = "1199", "1189"
        lignes = [
            models.LigneEcriture(compte=cible, libelle=f"Perte {origine} en instance d'affectation", debit=attendu, credit=0),
            models.LigneEcriture(compte=source, libelle=f"Perte {origine} non affectée — transfert en instance", debit=0, credit=attendu),
        ]
    if abs(disponible - attendu) > Decimal("0.01"):
        raise HTTPException(409,
            f"Clôture bloquée : le résultat {origine} non affecté doit être reclassé de {source} vers {cible}, "
            f"mais le solde disponible ({disponible:.2f} MAD) ne correspond pas au résultat clôturé "
            f"({attendu:.2f} MAD). Contrôlez les écritures manuelles sur {source}.")

    ex = ensure_exercice(db, societe_id, exercice)
    ecriture = models.Ecriture(
        societe_id=societe_id, date=ex.date_fin, date_piece=ex.date_fin,
        journal=models.JournalEnum.OD,
        libelle=f"Résultat {origine} non affecté — virement 119 vers 118",
        reference=f"INSTANCE-AFFECT-{origine}", exercice=exercice, source="cloture",
        est_validee=False, lignes=lignes,
    )
    db.add(ecriture)
    db.flush()
    ecriture.est_validee = True
    ecriture.date_validation = datetime.now()
    ecriture.validee_par = current_user.get("id")
    db.flush()
    return ecriture


def _dotations_manquantes(db: Session, societe_id: int, exercice: int):
    """Immobilisations dont la dotation de l'exercice n'a pas encore été comptabilisée.

    Clôturer sans ces dotations fausse le résultat et le bilan, et l'exercice se
    retrouve verrouillé avec des comptes incorrects. On les détecte donc AVANT.
    """
    from services.immobilisations_service import dotation_sur_periode

    ex = ensure_exercice(db, societe_id, exercice)
    manquantes, total = [], Decimal("0.00")
    immos = db.query(models.Immobilisation).filter(
        models.Immobilisation.societe_id == societe_id,
        models.Immobilisation.amortissable == True,  # noqa: E712
        models.Immobilisation.date_mise_en_service <= ex.date_fin,
        (models.Immobilisation.date_sortie == None) | (models.Immobilisation.date_sortie >= ex.date_debut),  # noqa: E711
    ).all()

    for immo in immos:
        try:
            fin = min(ex.date_fin, immo.date_sortie) if immo.date_sortie else ex.date_fin
            calc = dotation_sur_periode(immo, ex.date_debut, fin)
            dotation = money(calc["dotation"])
        except Exception:
            continue
        if dotation <= 0:
            continue                      # rien à amortir sur cet exercice

        ref = f"AM-{exercice}-{immo.id}"
        deja = db.query(models.Ecriture).filter_by(
            societe_id=societe_id, reference=ref).first()
        if deja:
            continue                      # dotation déjà comptabilisée

        # Une correction historique peut déjà porter toute la dotation de N.
        # Reconnaître le montant réel, jamais la seule présence d'une référence,
        # sans créer une seconde charge ni réécrire la pièce existante.
        correction = db.query(func.coalesce(func.sum(
            models.LigneEcriture.debit - models.LigneEcriture.credit), 0)).join(
            models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id
        ).filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.reference == f"RECON-AMORT-{exercice}-{immo.id}",
            models.LigneEcriture.compte.like("6%"),
        ).scalar()
        if money(correction) == dotation:
            continue

        manquantes.append({
            "immobilisation_id": immo.id,
            "designation": immo.designation,
            "valeur_brute": immo.valeur_brute or 0,
            "dotation": round(dotation, 2),
            "compte_dotation": immo.compte_dotation,
            "compte_amort": immo.compte_amort,
        })
        total += dotation

    return manquantes, round(total, 2)


class AjustementInventaireIn(BaseModel):
    type: str
    libelle: str = Field(max_length=300)
    montant: Decimal
    compte_activite: Optional[str] = Field(default=None, max_length=10)
    compte_contrepartie: Optional[str] = Field(default=None, max_length=10)

    @field_validator("libelle")
    @classmethod
    def libelle_non_vide(cls, v):
        if not (v or "").strip():
            raise ValueError("Le libellé est obligatoire.")
        return v.strip()


def _ajustement_out(a, db: Session):
    ec = db.query(models.Ecriture).filter_by(id=a.ecriture_id).first() if a.ecriture_id else None
    cp = db.query(models.Ecriture).filter_by(id=a.contrepassation_id).first() if a.contrepassation_id else None
    return {
        "id": a.id, "exercice": a.exercice, "type": a.type, "libelle": a.libelle,
        "montant": float(a.montant or 0), "compte_activite": a.compte_activite,
        "compte_contrepartie": a.compte_contrepartie, "ecriture_id": a.ecriture_id,
        "contrepassation_id": a.contrepassation_id,
        "date": ec.date.isoformat() if ec else None,
        "contrepassation_date": cp.date.isoformat() if cp else None,
        "est_validee": bool(ec.est_validee) if ec else False,
        "contrepassation_validee": bool(cp.est_validee) if cp else False,
        "auto_contrepassation": a.type in {"cca", "pca", "fnp", "fae"},
    }


@router.get("/ajustements")
def liste_ajustements_inventaire(
    exercice: int = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(models.AjustementInventaire).filter_by(
        societe_id=current_user["societe_id"], exercice=exercice
    ).order_by(models.AjustementInventaire.id.desc()).all()
    return [_ajustement_out(a, db) for a in rows]


@router.get("/types-ajustements")
def types_ajustements(current_user=Depends(get_current_user)):
    return [{"type": k, **v} for k, v in TYPES_AJUSTEMENT.items()]


@router.post("/ajustements/apercu")
def apercu_ajustement_inventaire(
    data: AjustementInventaireIn,
    exercice: int = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lecture seule : aucun exercice, ajustement ou brouillon n'est préparé."""
    sid = current_user["societe_id"]
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=sid, annee=exercice).first()
    if not ex:
        raise HTTPException(404, "Exercice introuvable. Préparez son calendrier avant l'aperçu.")
    try:
        lignes, auto_reverse, comptes = construire_ajustement(
            data.type, data.montant, data.compte_activite, data.compte_contrepartie)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "exercice": exercice, "date": ex.date_fin.isoformat(), "journal": "OD",
        "libelle": data.libelle, "montant": str(money(data.montant)), **comptes,
        "contrepassation_date": (ex.date_fin + timedelta(days=1)).isoformat() if auto_reverse else None,
        "lignes": [{**l, "libelle_compte": libelle_compte(l["compte"], db, sid),
                    "debit": str(l["debit"]), "credit": str(l["credit"])} for l in lignes],
    }


@router.post("/ajustements")
def creer_ajustement_inventaire(
    data: AjustementInventaireIn,
    exercice: int = Query(...),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    exercice_obj = ensure_exercice(db, societe_id, exercice)
    if exercice_est_clos(db, societe_id, exercice):
        raise HTTPException(423, f"Exercice {exercice} clôturé : ajustement impossible.")

    # Contrôle applicatif AVANT le flush. Le trigger PostgreSQL reste la dernière
    # barrière de sécurité, mais l'API doit renvoyer une erreur métier lisible au
    # lieu de laisser remonter une exception SQL qui devient "Failed to fetch".
    try:
        verifier_date_ecriture(db, societe_id, exercice_obj.date_fin, action="enregistrer")
    except ValueError as exc:
        raise HTTPException(423, str(exc))

    try:
        lignes, auto_reverse, comptes = construire_ajustement(
            data.type, data.montant, data.compte_activite, data.compte_contrepartie
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    # Une écriture de cut-off avec contrepassation doit être atomique : si la
    # période d'ouverture N+1 est déjà fermée, on refuse l'ajustement entier.
    exercice_suivant = None
    if auto_reverse:
        try:
            exercice_suivant = preparer_exercice_suivant(db, societe_id, exercice_obj)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        try:
            verifier_date_ecriture(db, societe_id, exercice_suivant.date_debut, action="enregistrer")
        except ValueError as exc:
            raise HTTPException(423, str(exc))

    ajustement = models.AjustementInventaire(
        societe_id=societe_id, exercice=exercice, type=data.type, libelle=data.libelle,
        montant=money(data.montant), compte_activite=comptes["compte_activite"],
        compte_contrepartie=comptes["compte_contrepartie"],
    )
    db.add(ajustement)
    db.flush()

    ref = f"INV-{data.type.upper()}-{exercice}-{ajustement.id}"
    ecriture = models.Ecriture(
        societe_id=societe_id, date=exercice_obj.date_fin, journal="OD",
        libelle=data.libelle, reference=ref, exercice=exercice, source="inventaire",
        lignes=[models.LigneEcriture(**l) for l in lignes],
    )
    db.add(ecriture)
    db.flush()
    ajustement.ecriture_id = ecriture.id

    if auto_reverse:
        lignes_cp = contrepasser(lignes)
        cp = models.Ecriture(
            societe_id=societe_id, date=exercice_suivant.date_debut, journal="OD",
            libelle=f"Contrepassation — {data.libelle}", reference=f"CP-{ref}",
            exercice=exercice_suivant.annee, source="inventaire",
            lignes=[models.LigneEcriture(**l) for l in lignes_cp],
        )
        db.add(cp)
        db.flush()
        ajustement.contrepassation_id = cp.id

    db.commit()
    db.refresh(ajustement)
    return _ajustement_out(ajustement, db)


@router.delete("/ajustements/{ajustement_id}")
def supprimer_ajustement_inventaire(
    ajustement_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    a = db.query(models.AjustementInventaire).filter_by(
        id=ajustement_id, societe_id=societe_id).first()
    if not a:
        raise HTTPException(404, "Ajustement introuvable.")
    if exercice_est_clos(db, societe_id, a.exercice):
        raise HTTPException(423, f"Exercice {a.exercice} clôturé : suppression impossible.")

    ecritures = []
    for eid in (a.ecriture_id, a.contrepassation_id):
        if eid:
            ec = db.query(models.Ecriture).filter_by(id=eid, societe_id=societe_id).first()
            if ec:
                if ec.est_validee:
                    raise HTTPException(409,
                        "L'écriture générée est définitive. L'ajustement ne peut plus être supprimé ; "
                        "corrigez-le par une contrepassation traçable dans le Journal.")
                ecritures.append(ec)
    db.delete(a)
    db.flush()
    for ec in ecritures:
        db.delete(ec)
    db.commit()
    return {"message": "Ajustement et écritures associées supprimés."}


def _documents_non_comptabilises(db: Session, societe_id: int, exercice_obj):
    """Documents métier définitifs qui devraient avoir alimenté la comptabilité.

    FACT-C / F-030 : une clôture ne peut pas masquer une facture, un avoir, un
    règlement ou un acompte définitif resté hors journal. Les contrôles reposent
    sur les dates réelles de l'exercice afin de rester corrects avec un exercice
    non strictement calendaire.
    """
    debut, fin = exercice_obj.date_debut, exercice_obj.date_fin

    factures = db.query(models.Facture).filter(
        models.Facture.societe_id == societe_id,
        models.Facture.date >= debut, models.Facture.date <= fin,
        models.Facture.est_validee == True,  # noqa: E712
        models.Facture.est_proforma == False,  # noqa: E712
        models.Facture.est_comptabilisee == False,  # noqa: E712
    ).order_by(models.Facture.date, models.Facture.id).all()

    avoirs = db.query(models.Avoir).filter(
        models.Avoir.societe_id == societe_id,
        models.Avoir.date >= debut, models.Avoir.date <= fin,
        models.Avoir.statut != "annule",
        models.Avoir.est_comptabilisee == False,  # noqa: E712
    ).order_by(models.Avoir.date, models.Avoir.id).all()

    reglements = db.query(models.Reglement).filter(
        models.Reglement.societe_id == societe_id,
        models.Reglement.date >= debut, models.Reglement.date <= fin,
        models.Reglement.statut.notin_(["rejete", "annule"]),
        models.Reglement.est_comptabilisee == False,  # noqa: E712
    ).order_by(models.Reglement.date, models.Reglement.id).all()

    acomptes = db.query(models.Acompte).filter(
        models.Acompte.societe_id == societe_id,
        models.Acompte.date >= debut, models.Acompte.date <= fin,
        models.Acompte.statut != "annule",
        models.Acompte.est_comptabilisee == False,  # noqa: E712
    ).order_by(models.Acompte.date, models.Acompte.id).all()

    imputations = db.query(models.ImputationAcompte).filter(
        models.ImputationAcompte.societe_id == societe_id,
        models.ImputationAcompte.date_imputation >= debut,
        models.ImputationAcompte.date_imputation <= fin,
        models.ImputationAcompte.statut == "active",
        models.ImputationAcompte.est_comptabilisee == False,  # noqa: E712
    ).order_by(models.ImputationAcompte.date_imputation, models.ImputationAcompte.id).all()

    details = []
    details += [{"type": "facture", "id": x.id, "numero": x.numero or f"#{x.id}", "date": x.date.isoformat()} for x in factures]
    details += [{"type": "avoir", "id": x.id, "numero": x.numero, "date": x.date.isoformat()} for x in avoirs]
    details += [{"type": "reglement", "id": x.id, "numero": x.numero or x.reference or f"#{x.id}", "date": x.date.isoformat()} for x in reglements]
    details += [{"type": "acompte", "id": x.id, "numero": x.numero, "date": x.date.isoformat()} for x in acomptes]
    details += [{"type": "imputation_acompte", "id": x.id, "numero": f"IMP-{x.id}", "date": x.date_imputation.isoformat()} for x in imputations]
    return details


@router.get("/etat")
def etat_cloture(
    exercice: int = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """État de clôture d'un exercice + aperçu du résultat qui serait dégagé."""
    societe_id = current_user["societe_id"]
    exercice_obj = ensure_exercice(db, societe_id, exercice)
    cloture = db.query(models.ClotureExercice).filter_by(
        societe_id=societe_id, exercice=exercice).first()

    soldes = _soldes_comptes(db, societe_id, exercice)
    # Résultat = produits (classe 7, solde créditeur) − charges (classe 6, solde débiteur)
    total_charges = sum(s for c, s in soldes.items() if c.startswith("6"))
    total_produits = sum(-s for c, s in soldes.items() if c.startswith("7"))
    resultat = total_produits - total_charges

    nb_ecritures = db.query(models.Ecriture).filter_by(
        societe_id=societe_id, exercice=exercice).count()

    # équilibre global
    total_debit = sum(s for s in soldes.values() if s > 0)
    total_credit = sum(-s for s in soldes.values() if s < 0)

    # Compte d'imputation du résultat (1191 bénéfice / 1199 perte)
    compte_resultat = "1191" if resultat >= 0 else "1199"

    # Dotations aux amortissements non encore comptabilisées pour cet exercice
    dotations, total_dot = _dotations_manquantes(db, societe_id, exercice)

    # Une clôture ne doit pas incorporer des écritures encore en brouillon.
    brouillons_q = db.query(models.Ecriture).filter_by(
        societe_id=societe_id, exercice=exercice, est_validee=False)
    nb_brouillons = brouillons_q.count()
    brouillons = [{
        "id": e.id, "date": e.date.isoformat(), "journal": e.journal.value if hasattr(e.journal, "value") else str(e.journal),
        "reference": e.reference, "libelle": e.libelle, "source": e.source,
    } for e in brouillons_q.order_by(models.Ecriture.date, models.Ecriture.id).limit(10).all()]

    ajustements = db.query(models.AjustementInventaire).filter_by(
        societe_id=societe_id, exercice=exercice).count()

    # Aperçu des à-nouveaux : soldes de bilan (classes 1-5) reportés sur N+1, résultat inclus
    apercu_an = []
    for ligne in _lignes_bilan_a_reporter(db, societe_id, exercice):
        apercu_an.append({**ligne, "debit": float(ligne["debit"]), "credit": float(ligne["credit"])})
    if abs(resultat) > Decimal("0.005"):
        apercu_an.append({
            "compte": compte_resultat,
            "debit": float(money(-resultat)) if resultat < 0 else 0.0,
            "credit": float(money(resultat)) if resultat >= 0 else 0.0,
            "resultat": True,
        })
    total_an_debit = round(sum(l["debit"] for l in apercu_an), 2)
    total_an_credit = round(sum(l["credit"] for l in apercu_an), 2)
    stock_cloture = etat_stock_cloture(db, societe_id, exercice_obj)
    immobilisations_rapprochement = etat_rapprochement_immobilisations(
        db, societe_id, exercice, exercice_obj.date_fin, soldes=soldes
    )
    documents_non_comptabilises = _documents_non_comptabilises(db, societe_id, exercice_obj)
    fec_controle = controler_fec_exercice(db, societe_id, exercice)
    affectation_resultat = _etat_affectation_resultat(db, societe_id, exercice, cloture) if cloture else None
    fiscalite_is = _etat_is_cloture(
        db, societe_id, exercice, current_user, resultat_courant=resultat
    )

    # Prévisualisation 052 : à la clôture de N, le résultat N-1 resté sans
    # décision doit quitter 119 pour 118 (résultat en instance d'affectation).
    resultat_anterieur_a_reclasser = None
    if not cloture:
        origine = exercice - 1
        cl_prev = db.query(models.ClotureExercice).filter_by(societe_id=societe_id, exercice=origine).first()
        r_prev = _resultat_cloture_effectif(db, societe_id, origine) if cl_prev else Decimal("0.00")
        if cl_prev and abs(r_prev) > Decimal("0.005"):
            if not _decision_affectation(db, societe_id, origine) and not _ecriture_affectation_legacy(db, societe_id, origine) and not _ecriture_reclassement_instance(db, societe_id, origine):
                r = r_prev
                resultat_anterieur_a_reclasser = {
                    "exercice_origine": origine,
                    "montant": float(abs(r)),
                    "compte_source": "1191" if r > 0 else "1199",
                    "compte_cible": "1181" if r > 0 else "1189",
                }

    return {
        "exercice": exercice,
        "date_debut": exercice_obj.date_debut.isoformat(),
        "date_fin": exercice_obj.date_fin.isoformat(),
        "date_fin_atteinte": date.today() >= exercice_obj.date_fin,
        "est_clos": cloture is not None,
        "date_cloture": cloture.date_cloture.isoformat() if cloture else None,
        "nb_ecritures": nb_ecritures,
        "total_charges": float(money(total_charges)),
        "total_produits": float(money(total_produits)),
        "resultat_net": float(money(resultat)),
        "type_resultat": "bénéfice" if resultat > 0 else ("perte" if resultat < 0 else "nul"),
        "compte_resultat": compte_resultat,
        "equilibre": abs(total_debit - total_credit) < Decimal("0.01"),
        "ecart": float(money(total_debit - total_credit)),
        "apercu_a_nouveaux": apercu_an,
        "total_an_debit": total_an_debit,
        "total_an_credit": total_an_credit,
        # Amortissements : clôturer sans les dotations fausserait le résultat
        "dotations_manquantes": dotations,
        "nb_dotations_manquantes": len(dotations),
        "total_dotations_manquantes": total_dot,
        "nb_ecritures_brouillon": nb_brouillons,
        "ecritures_brouillon": brouillons,
        "nb_ajustements_inventaire": ajustements,
        "stock_cloture": stock_cloture,
        "immobilisations_rapprochement": immobilisations_rapprochement,
        "nb_documents_non_comptabilises": len(documents_non_comptabilises),
        "documents_non_comptabilises": documents_non_comptabilises[:50],
        "affectation_resultat": affectation_resultat,
        "resultat_anterieur_a_reclasser": resultat_anterieur_a_reclasser,
        "fiscalite_is": fiscalite_is,
        "fec_controle": {
            "conforme": bool(fec_controle.get("conforme_export")),
            "nb_bloquants": int(fec_controle.get("nb_bloquants", 0)),
            "nb_avertissements": int(fec_controle.get("nb_avertissements", 0)),
            "bloquants": (fec_controle.get("bloquants") or [])[:20],
        },
    }


@router.post("/cloturer")
def cloturer_exercice(
    exercice: int = Query(...),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    # Une modification du stock déficitaire touche aussi les autres exercices.
    verrouiller_deficits_fiscaux(db, societe_id)
    # Avant tout calcul et avant les verrous d'exercice : garder le registre
    # stable, créations comprises, jusqu'au commit/rollback de clôture.
    verrouiller_registre(db, societe_id, exclusif=True)
    # Même périmètre que097, dès le début du calcul : un paramètre TVA ne
    # peut changer entre les contrôles, les écritures et le commit de clôture.
    # Built-in PostgreSQL : ne dépend pas de l'existence d'une ligne exercice.
    cle_tva = f"hisabpro:tva-cloture:{societe_id}:{exercice}"
    if not db.scalar(text("SELECT pg_try_advisory_xact_lock(hashtextextended(:cle,0))"), {"cle": cle_tva}):
        raise HTTPException(409, "Une opération TVA/clôture est en cours. Réessayez.")
    exercice_obj = ensure_exercice(db, societe_id, exercice)

    if exercice_est_clos(db, societe_id, exercice):
        raise HTTPException(400, f"L'exercice {exercice} est déjà clôturé.")

    # AUDIT FINAL 056 : une clôture définitive ne peut intervenir avant la
    # date de fin paramétrée de l'exercice. Cela évite de produire des
    # écritures de clôture datées dans le futur et de verrouiller prématurément
    # une période qui doit encore recevoir des opérations.
    if date.today() < exercice_obj.date_fin:
        raise HTTPException(409,
            f"Clôture prématurée interdite : l'exercice se termine le "
            f"{exercice_obj.date_fin.isoformat()}. La clôture définitive ne peut être "
            "lancée qu'à compter de cette date.")

    try:
        exercice_suivant = preparer_exercice_suivant(db, societe_id, exercice_obj)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

    ouverture_attendue = exercice_obj.date_fin + timedelta(days=1)
    if exercice_suivant.date_debut != ouverture_attendue:
        raise HTTPException(409,
            f"Continuité des exercices : l'exercice {exercice_suivant.annee} débute le "
            f"{exercice_suivant.date_debut.isoformat()} au lieu du {ouverture_attendue.isoformat()}. "
            "Vérifiez ses dates dans les paramètres des exercices avant de clôturer. "
            "Aucune date existante n'a été modifiée automatiquement.")

    soldes = _soldes_comptes(db, societe_id, exercice)
    if not soldes:
        raise HTTPException(400, f"Aucune écriture sur l'exercice {exercice} : rien à clôturer.")

    nb_brouillons = db.query(models.Ecriture).filter_by(
        societe_id=societe_id, exercice=exercice, est_validee=False).count()
    if nb_brouillons:
        raise HTTPException(400,
            f"{nb_brouillons} écriture(s) sont encore en brouillon sur {exercice}. "
            "Validez-les dans le Journal avant de clôturer l'exercice.")

    # COMPTA 051 : la clôture est irréversible ; un FEC non conforme ne peut
    # donc plus être découvert après coup. Les mêmes contrôles que l'export FEC
    # sont exécutés ici avant toute écriture technique de clôture.
    fec_controle = controler_fec_exercice(db, societe_id, exercice)
    if not fec_controle.get("conforme_export"):
        raise HTTPException(409, detail={
            "message": (
                f"Clôture bloquée : le FEC {exercice} comporte "
                f"{fec_controle.get('nb_bloquants', 0)} anomalie(s) bloquante(s). "
                "Corrigez-les depuis le contrôle FEC avant de clôturer."
            ),
            "controle_fec": fec_controle,
        })

    documents_non_comptabilises = _documents_non_comptabilises(db, societe_id, exercice_obj)
    if documents_non_comptabilises:
        apercu = ", ".join(
            f"{d['type']} {d['numero']}" for d in documents_non_comptabilises[:5]
        )
        suite = f" et {len(documents_non_comptabilises) - 5} autre(s)" if len(documents_non_comptabilises) > 5 else ""
        raise HTTPException(409,
            f"{len(documents_non_comptabilises)} document(s) métier définitif(s) n'ont pas encore été comptabilisés : "
            f"{apercu}{suite}. Comptabilisez-les avant de clôturer afin que le journal reflète toute l'activité.")

    # Contrôle d'équilibre global (une compta équilibrée est un prérequis)
    total_debit = sum(s for s in soldes.values() if s > 0)
    total_credit = sum(-s for s in soldes.values() if s < 0)
    if abs(total_debit - total_credit) > Decimal("0.01"):
        raise HTTPException(400,
            f"Comptabilité déséquilibrée (écart {total_debit - total_credit:+.2f} MAD). "
            "Corrigez les écritures avant de clôturer.")

    # Les dotations aux amortissements doivent être passées AVANT la clôture :
    # sans elles, le résultat est surévalué et le bilan faux, et l'exercice
    # se retrouve verrouillé avec des comptes incorrects.
    dotations, total_dot = _dotations_manquantes(db, societe_id, exercice)
    if dotations:
        noms = ", ".join(d["designation"] for d in dotations[:4])
        suite = f" et {len(dotations) - 4} autre(s)" if len(dotations) > 4 else ""
        raise HTTPException(400,
            f"{len(dotations)} dotation(s) aux amortissements n'ont pas été comptabilisées "
            f"pour {exercice} ({total_dot:,.2f} MAD) : {noms}{suite}. "
            "Générez-les depuis le module Immobilisations avant de clôturer, "
            "sinon le résultat et le bilan seront faux.")

    # Stock : lorsque la société gère des articles stockables, la clôture exige
    # un comptage physique au dernier jour et un rapprochement du stock BRUT avec
    # les comptes 31xx. Les dépréciations 391x restent séparées.
    stock = etat_stock_cloture(db, societe_id, exercice_obj)
    if stock.get('valorisation_complete') is False:
        raise HTTPException(400, "Valorisation historique de stock à vérifier avant la clôture.")
    if stock.get("inventaire_requis") and not stock.get("inventaire_valide"):
        raise HTTPException(400,
            f"Aucun inventaire physique de stock validé au {exercice_obj.date_fin.isoformat()}. "
            "Validez le comptage de clôture dans Inventaire avant de clôturer.")
    if stock.get("inventaire_requis") and not stock.get("stock_rapproche"):
        raise HTTPException(400,
            f"Stock non rapproché : physique brut {stock['valeur_physique_brute']:.2f} MAD, "
            f"comptable brut {stock['valeur_comptable_brute']:.2f} MAD, "
            f"écart {stock['ecart_brut']:.2f} MAD. "
            "Générez puis validez l'écriture de stock de clôture.")

    # Immobilisations : le registre métier doit correspondre aux comptes bruts
    # et aux amortissements cumulés configurés. On contrôle les deux séparément
    # afin que deux erreurs de sens opposé ne puissent pas se compenser en VNC.
    immo_rap = etat_rapprochement_immobilisations(
        db, societe_id, exercice, exercice_obj.date_fin, soldes=soldes
    )
    if not immo_rap.get("rapproche", False):
        raise HTTPException(400,
            "Immobilisations non rapprochées : "
            f"brut registre {immo_rap.get('brut_module', 0):.2f} MAD / "
            f"comptabilité {immo_rap.get('brut_comptable', 0):.2f} MAD ; "
            f"amortissements registre {immo_rap.get('amortissements_module', 0):.2f} MAD / "
            f"comptabilité {immo_rap.get('amortissements_comptables', 0):.2f} MAD. "
            "Rapprochez les immobilisations avant de clôturer.")

    # PATCH 101 — l'impôt courant doit être constaté AVANT la détermination
    # du résultat net. S'il est absent, HisabPro le comptabilise dans la même
    # transaction de clôture ; s'il existe mais ne recoupe pas le calcul fiscal,
    # la clôture est bloquée plutôt que de créer un doublon ou un ajustement aveugle.
    fiscalite_is = _etat_is_cloture(db, societe_id, exercice, current_user)
    if fiscalite_is.get("applicable"):
        if fiscalite_is.get("erreur"):
            raise HTTPException(409, f"Clôture bloquée par le calcul IS : {fiscalite_is['erreur']}")
        if fiscalite_is.get("deficits_a_confirmer"):
            raise HTTPException(409,
                "Clôture bloquée : confirmez d'abord l'imputation des déficits fiscaux proposée pour cet exercice.")
        if not fiscalite_is.get("coherente"):
            if fiscalite_is.get("absente"):
                _comptabiliser_is_cloture(db, societe_id, exercice_obj, fiscalite_is, current_user)
                # Le résultat et les à-nouveaux doivent intégrer immédiatement
                # l'écriture 6701/6705 -> 4453.
                soldes = _soldes_comptes(db, societe_id, exercice)
            else:
                raise HTTPException(409,
                    "Clôture bloquée : la comptabilisation de l'impôt courant ne correspond pas au calcul fiscal. "
                    f"Attendu {fiscalite_is.get('attendu', 0):.2f} MAD sur {fiscalite_is.get('compte_charge_attendu')}; "
                    f"comptabilisé {fiscalite_is.get('comptabilise', 0):.2f} MAD. Corrigez par une écriture auditée avant clôture.")

    # COMPTA 052 — avant de calculer le résultat courant, tout résultat de N-1
    # encore en 119 est viré vers 118. L'opération reste dans la transaction de
    # clôture : si un contrôle ultérieur échoue, elle est intégralement annulée.
    reclassement_instance = _reclasser_resultat_non_affecte(
        db, societe_id, exercice, current_user
    )
    if reclassement_instance:
        # Le FEC final doit également intégrer cette écriture normative générée
        # par HisabPro ; on ne se contente pas du contrôle effectué avant elle.
        fec_apres_reclassement = controler_fec_exercice(db, societe_id, exercice)
        if not fec_apres_reclassement.get("conforme_export"):
            db.rollback()
            raise HTTPException(409, detail={
                "message": (
                    f"Clôture bloquée après reclassement 119→118 : le FEC {exercice} comporte "
                    f"{fec_apres_reclassement.get('nb_bloquants', 0)} anomalie(s) bloquante(s)."
                ),
                "controle_fec": fec_apres_reclassement,
            })
        # Les à-nouveaux doivent porter 118 et non l'ancien 119.
        soldes = _soldes_comptes(db, societe_id, exercice)

    # ── 1. Détermination du résultat via la cascade CGNC de classe 8 ─────────
    # 61/71 -> 8100 ; 63/73 -> 8300 ; 8100+8300 -> 8400
    # 65/75 -> 8500 ; 8400+8500 -> 8600 ; 8600+67 -> 8800
    # 8800 -> 1191 (bénéfice) / 1199 (perte).
    try:
        lignes_resultat_data, resultat, compte_resultat = construire_cascade_resultat(soldes)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(500, f"{exc}. Clôture annulée.")

    lignes_resultat = [models.LigneEcriture(**l) for l in lignes_resultat_data]

    ecriture_resultat = None
    if lignes_resultat:
        # Avis n°24 CNC : écritures de clôture dans le journal dédié CL.
        ecriture_resultat = models.Ecriture(
            societe_id=societe_id, date=exercice_obj.date_fin, date_piece=exercice_obj.date_fin,
            journal=models.JournalEnum.CL,
            libelle=f"Détermination du résultat {exercice}",
            reference=f"CLOTURE-{exercice}", exercice=exercice, source="cloture",
            est_validee=False,
            lignes=lignes_resultat,
        )
        db.add(ecriture_resultat)
        db.flush()  # lignes constituées avant numérotation définitive (COMPTA.3)
        ecriture_resultat.est_validee = True
        ecriture_resultat.date_validation = datetime.now()
        ecriture_resultat.validee_par = current_user["id"]
        db.flush()

    # ── 2. Écriture d'à-nouveaux sur N+1 : report des comptes de bilan ────────
    # Soldes de bilan APRÈS affectation du résultat : classes 1-5, plus le résultat
    lignes_an = []
    for ligne in _lignes_bilan_a_reporter(db, societe_id, exercice, validees_seulement=True):
        lignes_an.append(models.LigneEcriture(**ligne, libelle=f"À-nouveau {exercice_suivant.annee}"))

    # Report du résultat au passif (1191 bénéfice au crédit, 1199 perte au débit)
    if compte_resultat and abs(resultat) > Decimal("0.005"):
        if resultat > 0:
            lignes_an.append(models.LigneEcriture(
                compte=compte_resultat, libelle=f"Report résultat {exercice}",
                debit=0, credit=resultat))
        else:
            lignes_an.append(models.LigneEcriture(
                compte=compte_resultat, libelle=f"Report résultat {exercice}",
                debit=-resultat, credit=0))

    # L'écriture d'à-nouveaux doit être enregistrée dans une période N+1 ouverte.
    # L'activation est faite dans la même transaction : si la clôture échoue ensuite,
    # le changement de statut est intégralement annulé par le rollback.
    if exercice_suivant.statut != "cloture":
        exercice_suivant.statut = "ouvert"
        activer_periodes_de_travail(db, exercice_suivant)
        db.flush()

    ecriture_an = None
    if lignes_an:
        # Vérifier l'équilibre de l'écriture d'à-nouveaux
        d = sum((money(l.debit) for l in lignes_an), Decimal("0.00"))
        c = sum((money(l.credit) for l in lignes_an), Decimal("0.00"))
        if abs(d - c) > Decimal("0.01"):
            db.rollback()
            raise HTTPException(500,
                f"Écriture d'à-nouveaux déséquilibrée (écart {d - c:+.2f}). Clôture annulée.")
        ecriture_an = models.Ecriture(
            societe_id=societe_id, date=exercice_suivant.date_debut, date_piece=exercice_suivant.date_debut,
            journal="AN",
            libelle=f"À-nouveaux — report de l'exercice {exercice}",
            reference=f"AN-{exercice_suivant.annee}", exercice=exercice_suivant.annee, source="cloture",
            est_validee=False,
            lignes=lignes_an,
        )
        db.add(ecriture_an)
        db.flush()  # lignes constituées avant numérotation définitive (COMPTA.3)
        ecriture_an.est_validee = True
        ecriture_an.date_validation = datetime.now()
        ecriture_an.validee_par = current_user["id"]
        db.flush()

    # AUDIT FINAL 056 : le premier contrôle FEC précède nécessairement les
    # écritures techniques de clôture. Rejouer le contrôle après leur génération
    # garantit que l'état qui va être verrouillé est lui-même conforme (journal
    # CL, séquence, date de validation, équilibre, comptes, justificatif, etc.).
    fec_final = controler_fec_exercice(db, societe_id, exercice)
    if not fec_final.get("conforme_export"):
        db.rollback()
        raise HTTPException(409, detail={
            "message": (
                f"Clôture annulée : le contrôle FEC final de {exercice} comporte "
                f"{fec_final.get('nb_bloquants', 0)} anomalie(s) bloquante(s) après "
                "génération des écritures techniques de clôture."
            ),
            "controle_fec": fec_final,
        })

    # ── 3. Marquer l'exercice clos ────────────────────────────────────────────
    cloture = models.ClotureExercice(
        societe_id=societe_id, exercice=exercice, resultat_net=resultat,
        ecriture_an_id=ecriture_an.id if ecriture_an else None,
        ecriture_resultat_id=ecriture_resultat.id if ecriture_resultat else None,
    )
    db.add(cloture)
    # Les changements de statut des périodes sont historisés par la migration
    # COMPTA.3 ; on transmet l'acteur au trigger PostgreSQL.
    db.execute(text("SELECT set_config('hisabpro.audit_actor_id', :v, true)"),
               {"v": str(current_user.get("id") or "")})
    db.execute(text("SELECT set_config('hisabpro.audit_motif', :v, true)"),
               {"v": f"Clôture définitive de l'exercice {exercice}"})
    marquer_exercice_cloture(db, societe_id, exercice, True)

    db.commit()

    return {
        "message": f"Exercice {exercice} clôturé.",
        "resultat_net": float(resultat),
        "type_resultat": "bénéfice" if resultat > 0 else ("perte" if resultat < 0 else "nul"),
        "a_nouveaux_sur": exercice_suivant.annee,
        "nb_lignes_an": len(lignes_an),
    }


@router.post("/affecter-resultat")
def affecter_resultat(
    data: AffectationResultatIn,
    exercice_origine: int = Query(...),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Comptabilise une décision d'affectation avec contrôles juridiques 052.

    La décision sociale est tracée séparément de l'écriture comptable et le
    justificatif correspondant devient la référence prioritaire du FEC.
    """
    societe_id = current_user["societe_id"]
    cloture = db.query(models.ClotureExercice).filter_by(
        societe_id=societe_id, exercice=exercice_origine
    ).first()
    if not cloture:
        raise HTTPException(409, f"L'exercice {exercice_origine} doit être clôturé avant l'affectation du résultat.")

    etat = _etat_affectation_resultat(db, societe_id, exercice_origine, cloture)
    if not etat or etat.get("affecte"):
        raise HTTPException(409, "Le résultat de cet exercice est déjà affecté.")
    if not etat.get("exercice_affectation_disponible"):
        raise HTTPException(409, "Aucun exercice ouvert n'est disponible pour comptabiliser cette décision d'affectation.")

    exercice_affectation = int(etat["exercice_affectation"])
    ex_cible = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=exercice_affectation
    ).first()
    ex_origine = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=exercice_origine
    ).first()
    if not ex_cible or ex_cible.statut != "ouvert":
        raise HTTPException(409, f"L'exercice {exercice_affectation} doit être ouvert pour comptabiliser l'affectation.")

    try:
        ex_date = verifier_date_ecriture(
            db, societe_id, data.date_affectation,
            action="enregistrer l'affectation du résultat",
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    if ex_date.annee != exercice_affectation:
        raise HTTPException(400,
            f"La date de comptabilisation doit appartenir à l'exercice {exercice_affectation} "
            f"({ex_cible.date_debut.isoformat()} au {ex_cible.date_fin.isoformat()}).")
    if data.date_decision < ex_cible.date_debut or data.date_decision > ex_cible.date_fin:
        raise HTTPException(400,
            f"La date de décision doit appartenir à l'exercice {exercice_affectation} "
            f"({ex_cible.date_debut.isoformat()} au {ex_cible.date_fin.isoformat()}).")
    if ex_origine and data.date_decision <= ex_origine.date_fin:
        raise HTTPException(400, "La décision d'affectation doit être postérieure à la clôture de l'exercice d'origine.")
    if data.date_affectation < data.date_decision:
        raise HTTPException(400, "La comptabilisation ne peut pas être antérieure à la décision d'affectation.")

    reference = f"AFFECT-RESULTAT-{exercice_origine}"
    if _ecriture_affectation_legacy(db, societe_id, exercice_origine) or _decision_affectation(db, societe_id, exercice_origine):
        raise HTTPException(409, "Une affectation définitive existe déjà pour ce résultat.")

    resultat = _resultat_cloture_effectif(db, societe_id, exercice_origine)
    restant = abs(resultat)
    compte_source = etat.get("compte_source") or ("1191" if resultat > 0 else "1199")
    soldes_valides = _soldes_comptes(
        db, societe_id, exercice_affectation, validees_seulement=True
    )
    if resultat > 0:
        disponible_source = max(-money(soldes_valides.get(compte_source, 0)), Decimal("0.00"))
    elif resultat < 0:
        disponible_source = max(money(soldes_valides.get(compte_source, 0)), Decimal("0.00"))
    else:
        raise HTTPException(409, "Résultat nul : aucune affectation n'est nécessaire.")
    if disponible_source + Decimal("0.01") < restant:
        raise HTTPException(409,
            f"Solde {compte_source} insuffisant dans {exercice_affectation} : "
            f"{disponible_source:.2f} MAD disponibles pour {restant:.2f} MAD à affecter.")

    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    reserve_avant = max(-money(soldes_valides.get("1140", 0)), Decimal("0.00"))
    reserve_min = Decimal("0.00")
    pertes_imputees = Decimal("0.00")
    lignes = []

    if resultat > 0:
        contraintes = calculer_contraintes_affectation(
            resultat_beneficiaire=restant,
            forme_juridique=getattr(societe, "forme_juridique", None),
            capital_social=getattr(societe, "capital_social", 0),
            reserve_legale_avant=reserve_avant,
            report_deficitaire=max(money(soldes_valides.get("1169", 0)), Decimal("0.00")),
            resultat_instance_deficitaire=max(money(soldes_valides.get("1189", 0)), Decimal("0.00")),
            report_beneficiaire=max(-money(soldes_valides.get("1161", 0)), Decimal("0.00")),
        )
        if not contraintes["forme_supportee"]:
            raise HTTPException(409,
                "Affectation bénéficiaire bloquée : la forme juridique de la société n'est pas prise en charge "
                "par le moteur de réserve légale 052. Renseignez correctement SA / SARL / SARL AU dans les paramètres "
                "ou faites valider le traitement juridique avant comptabilisation.")
        if not contraintes["capital_renseigne"]:
            raise HTTPException(409,
                "Affectation bénéficiaire bloquée : le capital social doit être renseigné pour contrôler la réserve légale.")

        reserve_min = money(contraintes["reserve_legale_minimale"])
        if money(data.reserve_legale) + Decimal("0.01") < reserve_min:
            raise HTTPException(409,
                f"Réserve légale insuffisante : minimum {reserve_min:.2f} MAD selon "
                f"{contraintes['regle']['referentiel']} (forme {contraintes['regle']['code']}).")

        # Apurement prioritaire des pertes antérieures : d'abord le report à
        # nouveau débiteur 1169, puis les résultats anciens en instance 1189.
        perte_1169_dispo = max(money(soldes_valides.get("1169", 0)), Decimal("0.00"))
        perte_1189_dispo = max(money(soldes_valides.get("1189", 0)), Decimal("0.00"))
        perte_1169 = min(restant, perte_1169_dispo)
        perte_1189 = min(restant - perte_1169, perte_1189_dispo)
        pertes_imputees = money(perte_1169 + perte_1189)
        montant_a_ventiler = money(restant - pertes_imputees)

        allocations = [
            ("1140", "Affectation résultat — réserve légale", money(data.reserve_legale)),
            ("1152", "Affectation résultat — autres réserves", money(data.autres_reserves)),
            ("1161", "Affectation résultat — report à nouveau", money(data.report_a_nouveau)),
            ("4465", "Affectation résultat — dividendes à payer", money(data.dividendes)),
        ]
        total_ventile = money(sum((m for _, _, m in allocations), Decimal("0.00")))
        if abs(total_ventile - montant_a_ventiler) > Decimal("0.01"):
            raise HTTPException(400,
                f"Après apurement automatique de {pertes_imputees:.2f} MAD de pertes antérieures, "
                f"la décision doit ventiler exactement {montant_a_ventiler:.2f} MAD "
                f"(saisie : {total_ventile:.2f} MAD).")
        if money(data.dividendes) - money(contraintes["dividendes_max_sur_resultat"]) > Decimal("0.01"):
            raise HTTPException(409,
                f"Dividendes trop élevés au regard du bénéfice distribuable contrôlé : maximum "
                f"{money(contraintes['dividendes_max_sur_resultat']):.2f} MAD sur le résultat {exercice_origine}.")

        lignes.append(models.LigneEcriture(
            compte=compte_source, libelle=f"Affectation du bénéfice {exercice_origine}",
            debit=restant, credit=0,
        ))
        if perte_1169 > Decimal("0.005"):
            lignes.append(models.LigneEcriture(
                compte="1169", libelle=f"Apurement pertes antérieures par résultat {exercice_origine}",
                debit=0, credit=perte_1169,
            ))
        if perte_1189 > Decimal("0.005"):
            lignes.append(models.LigneEcriture(
                compte="1189", libelle=f"Apurement résultat déficitaire antérieur en instance",
                debit=0, credit=perte_1189,
            ))
        for compte, libelle, montant in allocations:
            if montant > Decimal("0.005"):
                lignes.append(models.LigneEcriture(compte=compte, libelle=libelle, debit=0, credit=montant))
    else:
        if money(data.reserve_legale) + money(data.autres_reserves) + money(data.dividendes) > Decimal("0.005"):
            raise HTTPException(400, "Une perte ne peut pas être affectée à des réserves ou à des dividendes via cet assistant.")
        report = money(data.report_a_nouveau)
        if abs(report - restant) > Decimal("0.01"):
            raise HTTPException(400, f"La perte doit être reportée intégralement sur 1169 : {restant:.2f} MAD.")
        lignes = [
            models.LigneEcriture(compte="1169", libelle=f"Report de la perte {exercice_origine}", debit=restant, credit=0),
            models.LigneEcriture(compte=compte_source, libelle=f"Affectation de la perte {exercice_origine}", debit=0, credit=restant),
        ]

    d = money(sum((money(l.debit) for l in lignes), Decimal("0.00")))
    c = money(sum((money(l.credit) for l in lignes), Decimal("0.00")))
    if abs(d - c) > Decimal("0.01"):
        raise HTTPException(500, "Écriture d'affectation déséquilibrée : opération annulée.")

    ecriture = models.Ecriture(
        societe_id=societe_id, date=data.date_affectation, date_piece=data.date_decision,
        journal=models.JournalEnum.OD,
        libelle=f"Affectation du résultat {exercice_origine} — {data.reference_decision}", reference=reference,
        exercice=exercice_affectation, source="cloture", est_validee=False, lignes=lignes,
    )
    db.add(ecriture)
    db.flush()
    ecriture.est_validee = True
    ecriture.date_validation = datetime.now()
    ecriture.validee_par = current_user.get("id")
    db.flush()

    decision = models.DecisionAffectationResultat(
        societe_id=societe_id, exercice_origine=exercice_origine,
        exercice_comptabilisation=exercice_affectation,
        date_decision=data.date_decision, date_comptabilisation=data.date_affectation,
        reference_decision=data.reference_decision, organe_decision=data.organe_decision,
        forme_juridique_snapshot=getattr(societe, "forme_juridique", None),
        capital_social_snapshot=money(getattr(societe, "capital_social", 0)),
        resultat_origine=resultat, pertes_anterieures_imputees=pertes_imputees,
        reserve_legale_avant=reserve_avant, reserve_legale_minimale=reserve_min,
        reserve_legale_affectee=money(data.reserve_legale),
        autres_reserves=money(data.autres_reserves), report_a_nouveau=money(data.report_a_nouveau),
        dividendes=money(data.dividendes), compte_source=compte_source,
        ecriture_id=ecriture.id, created_by=current_user.get("id"),
    )
    db.add(decision)
    db.flush()

    # La décision de l'organe compétent est la pièce justificative prioritaire
    # de l'écriture d'affectation pour le FEC, sans modifier l'écriture validée.
    db.add(models.EcritureJustificatif(
        societe_id=societe_id, ecriture_id=ecriture.id,
        reference=data.reference_decision, date_piece=data.date_decision,
        source_type="decision_affectation", source_id=decision.id,
        prioritaire=True, motif=f"{data.organe_decision} — affectation résultat {exercice_origine}",
        created_by=current_user.get("id"),
    ))
    db.commit()
    db.refresh(ecriture)
    return {
        "message": f"Résultat {exercice_origine} affecté dans l'exercice {exercice_affectation}.",
        "ecriture_id": ecriture.id, "numero_ecriture": ecriture.numero_ecriture,
        "decision_id": decision.id, "reference_decision": decision.reference_decision,
        "montant": float(restant), "pertes_anterieures_imputees": float(pertes_imputees),
        "reserve_legale_minimale": float(reserve_min),
        "exercice_affectation": exercice_affectation, "compte_source": compte_source,
    }


@router.post("/generer-dotations")
def generer_dotations_depuis_cloture(
    exercice: int = Query(...),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Génère les dotations manquantes de l'exercice, sans quitter l'écran de clôture."""
    from routers.immobilisations import generer_dotations_annee
    if exercice_est_clos(db, current_user["societe_id"], exercice):
        raise HTTPException(423, f"Exercice {exercice} clôturé : dotations impossibles.")
    return generer_dotations_annee(exercice, current_user, db)


@router.post("/rouvrir")
def rouvrir_exercice(
    exercice: int = Query(...),
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    """Compatibilité API : COMPTA.3 rend la clôture définitive."""
    if not exercice_est_clos(db, current_user["societe_id"], exercice):
        raise HTTPException(404, f"L'exercice {exercice} n'est pas clôturé.")
    raise HTTPException(409,
        f"COMPTA.3 : l'exercice {exercice} est clôturé définitivement. "
        "Les corrections doivent être comptabilisées sur une période ouverte ultérieure.")


@router.get("/liste")
def liste_clotures(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clotures = db.query(models.ClotureExercice).filter_by(
        societe_id=current_user["societe_id"]).order_by(models.ClotureExercice.exercice.desc()).all()
    return [{
        "exercice": c.exercice,
        "date_cloture": c.date_cloture.isoformat() if c.date_cloture else None,
        "resultat_net": _resultat_cloture_effectif(db, current_user["societe_id"], c.exercice),
    } for c in clotures]
