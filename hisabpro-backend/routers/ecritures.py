from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, text, func, or_
from typing import List, Optional
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from database import get_db
from auth import get_current_user, requiert_ecriture, requiert_admin
import models, schemas
from routers.cloture import exercice_est_clos
from services.reprises_provisions_service import proteger_ecriture as proteger_reprise_provision
from services.reprises_provisions_service import verifier_validation as verifier_validation_reprise
from services.exercices_service import verifier_date_ecriture
from services.auxiliaire_service import (
    rattacher_ligne_auxiliaire,
    verifier_auxiliaires_avant_validation,
)
from services.plan_comptable import assurer_plan_societe


def _verifier_comptes_plan(db: Session, societe_id: int, lignes):
    """Refuse une saisie sur un compte absent/inactif du plan de la société."""
    assurer_plan_societe(db, societe_id)
    comptes = {str(getattr(l, "compte", "") or "").strip() for l in (lignes or [])}
    actifs = {r[0] for r in db.query(models.CompteSociete.numero).filter(
        models.CompteSociete.societe_id == societe_id,
        models.CompteSociete.numero.in_(comptes),
        models.CompteSociete.actif == True,  # noqa: E712
    ).all()} if comptes else set()
    invalides = sorted(c for c in comptes if c and c not in actifs)
    if invalides:
        raise HTTPException(400,
            "Compte(s) absent(s) ou désactivé(s) dans le plan de la société : " + ", ".join(invalides))


def _verifier_non_validee(ecriture, action="modifier"):
    """Une écriture validée est définitive : toute correction passe par une
    contrepassation, jamais par une réécriture de l'original."""
    if getattr(ecriture, "est_validee", False) or (getattr(ecriture, "numero_ecriture", None) or "").strip():
        raise HTTPException(423,
            f"Écriture {getattr(ecriture, 'numero_ecriture', None) or ('#' + str(ecriture.id))} définitive : "
            f"impossible de la {action}. Utilisez une contrepassation.")


def _journal_code(value):
    """Normalise un journal SQLAlchemy/Pydantic en code court (AC, VT, OD...)."""
    return str(getattr(value, "value", value) or "")


def _verifier_perimetre_numero(ecriture, *, journal=None, exercice=None, date_comptable=None):
    """Protège le périmètre d'un numéro comptable déjà définitif.

    Depuis 07C.2, un vrai brouillon n'a aucun ``numero_ecriture`` : son journal
    et sa date restent donc corrigeables. Dès la première validation, le numéro
    devient définitif et verrouille société, journal, exercice et date comptable.
    """
    numero = (getattr(ecriture, "numero_ecriture", None) or "").strip()
    if not numero:
        return

    journal_actuel = _journal_code(getattr(ecriture, "journal", None))
    journal_cible = _journal_code(journal) if journal is not None else journal_actuel
    if journal_cible != journal_actuel:
        raise HTTPException(409,
            f"Journal verrouillé par le numéro définitif {numero}. "
            f"L'écriture appartient au journal {journal_actuel} et ne peut pas être déplacée vers {journal_cible}.")

    exercice_actuel = int(getattr(ecriture, "exercice"))
    exercice_cible = int(exercice) if exercice is not None else exercice_actuel
    if exercice_cible != exercice_actuel:
        raise HTTPException(409,
            f"Exercice verrouillé par le numéro définitif {numero}. "
            f"L'écriture appartient à l'exercice {exercice_actuel} et ne peut pas être déplacée vers {exercice_cible}.")

    date_actuelle = getattr(ecriture, "date", None)
    if date_comptable is not None and date_comptable != date_actuelle:
        raise HTTPException(409,
            f"Date comptable verrouillée par le numéro définitif {numero} "
            f"({date_actuelle} -> {date_comptable}). Une correction datée doit suivre le chemin d'annulation/contrepassation.")


def _verifier_chronologie_validation(db: Session, ecriture):
    """Refuse une première validation antidatée dans un journal.

    Le trigger PostgreSQL 07C.2 reste l'autorité sous concurrence ; ce contrôle
    applicatif sert surtout à renvoyer un message 409 lisible avant le COMMIT.
    Une écriture déjà numérotée (dévalidation exceptionnelle) conserve son rang.
    """
    if (getattr(ecriture, "numero_ecriture", None) or "").strip():
        return

    derniere_date = (
        db.query(func.max(models.Ecriture.date))
        .filter(
            models.Ecriture.societe_id == ecriture.societe_id,
            models.Ecriture.exercice == ecriture.exercice,
            models.Ecriture.journal == ecriture.journal,
            models.Ecriture.est_validee.is_(True),
            models.Ecriture.numero_ecriture.isnot(None),
            models.Ecriture.id != ecriture.id,
        )
        .scalar()
    )
    if derniere_date is not None and ecriture.date < derniere_date:
        raise HTTPException(409,
            f"Validation non chronologique : la date comptable {ecriture.date} est antérieure "
            f"à la dernière date validée {derniere_date} du journal {_journal_code(ecriture.journal)}. "
            "Corrigez la date du brouillon avant de le valider, ou validez d'abord les brouillons plus anciens : "
            "le bouton « Valider les brouillons » du Journal les traite dans l'ordre chronologique.")


def _verifier_periode_ouverte(db, societe_id, valeur, action="modifier"):
    """Contrôle l'exercice ET la sous-période correspondant à une date/année."""
    if isinstance(valeur, date):
        try:
            return verifier_date_ecriture(db, societe_id, valeur, action)
        except ValueError as exc:
            raise HTTPException(423, str(exc))
    # Compatibilité pour les appels historiques qui ne disposent que de l'année.
    if exercice_est_clos(db, societe_id, int(valeur)):
        raise HTTPException(423,
            f"Exercice {valeur} clôturé : impossible d'y {action} une écriture. "
            "Passez la correction sur une période ouverte ultérieure via une contrepassation traçable.")
    return None

router = APIRouter(prefix="/api/ecritures", tags=["ecritures"])


def _set_audit_context(db: Session, current_user: dict, action: str, motif: str | None = None):
    """Pose un contexte transactionnel lu par les triggers PostgreSQL du Patch 07A.

    ``set_config(..., true)`` limite volontairement les valeurs à la transaction
    courante : une connexion réutilisée par le pool ne conserve donc jamais
    l'identité de l'utilisateur précédent.
    """
    db.execute(text("SELECT set_config('hisabpro.audit_actor_id', :v, true)"),
               {"v": str((current_user or {}).get("id") or "")})
    db.execute(text("SELECT set_config('hisabpro.audit_societe_id', :v, true)"),
               {"v": str((current_user or {}).get("societe_id") or "")})
    db.execute(text("SELECT set_config('hisabpro.audit_actor_role', :v, true)"),
               {"v": str((current_user or {}).get("role") or "")})
    db.execute(text("SELECT set_config('hisabpro.audit_action', :v, true)"),
               {"v": str(action or "")})
    db.execute(text("SELECT set_config('hisabpro.audit_motif', :v, true)"),
               {"v": str(motif or "")})


def _audit_rows(db: Session, sql: str, params: dict):
    """Convertit proprement les lignes SQLAlchemy en objets JSON FastAPI."""
    return [dict(r) for r in db.execute(text(sql), params).mappings().all()]



def _lecture_ecritures(ecritures):
    """Signale les données historiques illisibles sans les modifier ni les omettre."""
    resultats, anomalies = [], []
    for ecriture in ecritures:
        try:
            resultats.append(schemas.EcritureOut.model_validate(ecriture))
        except ValidationError as exc:
            anomalies.append({'id': ecriture.id, 'erreurs': [
                {'champ': '.'.join(str(p) for p in erreur['loc']), 'motif': erreur['msg']}
                for erreur in exc.errors()
            ]})
    if anomalies:
        references = ', '.join('#' + str(a['id']) for a in anomalies)
        raise HTTPException(409, detail={
            'msg': f"Lecture impossible : données comptables invalides dans les écritures {references}. Contrôlez ces écritures.",
            'ecritures': anomalies,
        })
    return resultats


@router.get("", response_model=List[schemas.EcritureOut])
def lister_ecritures(
    exercice:  int            = Query(..., description="Année de l'exercice"),
    journal:   Optional[str]  = Query(None),
    date_from: Optional[date] = Query(None),
    date_to:   Optional[date] = Query(None),
    recherche: Optional[str]  = Query(None),
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=2000),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les écritures de l'exercice, avec filtres optionnels."""
    q = (
        db.query(models.Ecriture)
        .options(joinedload(models.Ecriture.lignes), joinedload(models.Ecriture.justificatifs))
        .filter(
            models.Ecriture.societe_id == current_user["societe_id"],
            models.Ecriture.exercice   == exercice,
        )
    )
    if journal:
        q = q.filter(models.Ecriture.journal == journal)
    if date_from:
        q = q.filter(models.Ecriture.date >= date_from)
    if date_to:
        q = q.filter(models.Ecriture.date <= date_to)
    if recherche:
        terme = f"%{recherche.strip()}%"
        q = q.filter(or_(
            models.Ecriture.libelle.ilike(terme),
            models.Ecriture.reference.ilike(terme),
            models.Ecriture.numero_ecriture.ilike(terme),
            models.Ecriture.justificatifs.any(models.EcritureJustificatif.reference.ilike(terme)),
        ))

    # Aucun plafond implicite : le Journal doit pouvoir représenter l'exercice
    # complet. Les consommateurs qui souhaitent paginer peuvent toujours fournir
    # explicitement ``skip``/``limit`` (limite de sécurité à 2 000 par page).
    q = q.order_by(models.Ecriture.date.desc(), models.Ecriture.id.desc()).offset(skip)
    if limit is not None:
        q = q.limit(limit)
    return _lecture_ecritures(q.all())


def _lignes_reporting(db: Session, societe_id: int, exercice: int, date_from=None, date_to=None):
    """Source unique des états comptables : uniquement les écritures définitives.

    Contrairement à ``GET /api/ecritures`` cette requête n'est jamais paginée :
    elle sert aux états réglementaires/analytiques (balance, grand livre,
    lettrage). Les filtres de dates portent toujours sur l'exercice demandé.
    """
    q = (
        db.query(models.LigneEcriture, models.Ecriture)
        .options(joinedload(models.LigneEcriture.lettrages))
        .join(models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id)
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
            models.Ecriture.numero_ecriture.isnot(None),
        )
    )
    if date_from:
        q = q.filter(models.Ecriture.date >= date_from)
    if date_to:
        q = q.filter(models.Ecriture.date <= date_to)
    return q.order_by(models.Ecriture.date, models.Ecriture.id, models.LigneEcriture.id).all()


def _valider_periode_reporting(date_from: Optional[date], date_to: Optional[date]):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "La date de début doit être antérieure ou égale à la date de fin.")


def _normaliser_auxiliaire(value) -> str:
    raw = " ".join(str(value or "").strip().casefold().split())
    return re.sub(r"[^\w]+", " ", raw, flags=re.UNICODE).strip()


def _index_tiers_reporting(db: Session, societe_id: int):
    """Construit un index historique des tiers sans dépendre de leur statut actif.

    Les états comptables doivent continuer à identifier un tiers désactivé après
    la comptabilisation d'une pièce. Un sous-compte dédié est prioritaire ; sur
    les comptes collectifs 3421/4411 on rapproche le libellé de ligne / écriture
    avec le nom de la fiche tiers.
    """
    index = {
        "3421": {"tiers": [], "par_compte": {}},
        "4411": {"tiers": [], "par_compte": {}},
    }
    rows = db.query(models.Tiers).filter(models.Tiers.societe_id == societe_id).all()
    for tiers in rows:
        type_tiers = str(getattr(tiers, "type", "") or "")
        definitions = (
            ("3421", "compte_client", {"client", "les_deux"}),
            ("4411", "compte_fournisseur", {"fournisseur", "les_deux"}),
        )
        for prefixe, champ, types_acceptes in definitions:
            if type_tiers not in types_acceptes:
                continue
            compte = str(getattr(tiers, champ, None) or prefixe).strip() or prefixe
            item = {
                "id": tiers.id,
                "nom": str(getattr(tiers, "nom", "") or "").strip() or f"Tiers #{tiers.id}",
                "nom_norm": _normaliser_auxiliaire(getattr(tiers, "nom", "")),
                "compte": compte,
            }
            index[prefixe]["tiers"].append(item)
            index[prefixe]["par_compte"].setdefault(compte, []).append(item)

    # Les noms les plus longs sont testés en premier pour éviter qu'un tiers
    # "ABC" ne capture une écriture appartenant à "ABC Industrie".
    for data in index.values():
        data["tiers"].sort(key=lambda x: len(x["nom_norm"]), reverse=True)
    return index


def _prefixe_tiers(compte: str) -> Optional[str]:
    compte = str(compte or "").strip()
    if compte.startswith("3421"):
        return "3421"
    if compte.startswith("4411"):
        return "4411"
    return None


def _resoudre_auxiliaire_reporting(ligne, ecriture, index_tiers):
    """Résout l'auxiliaire natif ; fallback prudent uniquement pour l'historique.

    Depuis le patch 053, ``tiers_id`` et les snapshots auxiliaires portés par la
    ligne sont la source de vérité. Le rapprochement par libellé n'est conservé
    que pour rendre lisibles les anciennes lignes non encore enrichies.
    """
    compte = str(getattr(ligne, "compte", "") or "").strip()
    tiers_id = getattr(ligne, "tiers_id", None)
    code_aux = str(getattr(ligne, "compte_auxiliaire_snapshot", None) or "").strip()
    lib_aux = str(getattr(ligne, "libelle_auxiliaire_snapshot", None) or "").strip()
    if tiers_id and code_aux and lib_aux:
        return {
            "cle": f"tiers:{tiers_id}",
            "tiers_id": tiers_id,
            "tiers": lib_aux,
            "compte_auxiliaire": code_aux,
            "identifie": True,
        }
    prefixe = _prefixe_tiers(compte)
    if not prefixe:
        return None

    data = index_tiers[prefixe]
    candidats_compte = data["par_compte"].get(compte, [])
    # Un sous-compte dédié et unique est le signal le plus fiable.
    if compte != prefixe and len(candidats_compte) == 1:
        t = candidats_compte[0]
        return {
            "cle": f"tiers:{t['id']}", "tiers_id": t["id"], "tiers": t["nom"],
            "compte_auxiliaire": compte, "identifie": True,
        }

    textes = [
        str(getattr(ligne, "libelle", "") or "").strip(),
        str(getattr(ecriture, "libelle", "") or "").strip(),
    ]
    textes_norm = [_normaliser_auxiliaire(x) for x in textes if x]

    correspondances = []
    for t in data["tiers"]:
        nom = t["nom_norm"]
        if not nom:
            continue
        for texte in textes_norm:
            # Le test avec espaces joue le rôle de frontière de mots et évite les
            # correspondances accidentelles à l'intérieur d'un identifiant.
            if texte == nom or f" {nom} " in f" {texte} ":
                correspondances.append(t)
                break

    if correspondances:
        longueur_max = max(len(t["nom_norm"]) for t in correspondances)
        meilleurs = {t["id"]: t for t in correspondances if len(t["nom_norm"]) == longueur_max}
        if len(meilleurs) == 1:
            t = next(iter(meilleurs.values()))
            return {
                "cle": f"tiers:{t['id']}", "tiers_id": t["id"], "tiers": t["nom"],
                "compte_auxiliaire": compte if compte != prefixe else None,
                "identifie": True,
            }

    # En dernier recours on expose le libellé comptable au lieu de fabriquer un
    # lien vers une fiche tiers. Cela rend l'anomalie visible dans la balance.
    brut = textes[0] or textes[1] or "Tiers non identifié"
    brut_norm = _normaliser_auxiliaire(brut) or f"ligne-{getattr(ligne, 'id', 'x')}"
    return {
        "cle": f"non-identifie:{compte}:{brut_norm}",
        "tiers_id": None,
        "tiers": brut,
        "compte_auxiliaire": compte if compte != prefixe else None,
        "identifie": False,
    }


def _rows_reporting_jusqua_date(db: Session, societe_id: int, exercice: int, date_to: Optional[date]):
    # Charger une seule fois tout ce qui est nécessaire pour calculer à la fois
    # le solde d'ouverture et les mouvements de la période.
    return _lignes_reporting(db, societe_id, exercice, None, date_to)


@router.get("/reporting/balance/pdf")
def reporting_balance_pdf(
    exercice: int = Query(...),
    genre: str = Query('generale', pattern='^(generale|auxiliaire|agee|resultat|comparative)$'),
    type_tiers: str = Query('client', pattern='^(client|fournisseur)$'),
    date_from: date = Query(...),
    date_to: date = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from fastapi.responses import Response
    from services.balance_pdf_service import exporter_balance_pdf
    _valider_periode_reporting(date_from, date_to)
    contenu = exporter_balance_pdf(db, current_user, exercice, genre, date_from, date_to, type_tiers)
    return Response(contenu, media_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="balance_{genre}_{type_tiers}_{date_to}.pdf"',
        'X-HisabPro-Source': 'comptabilite-serveur',
    })


@router.get("/reporting/balance")
def reporting_balance(
    exercice: int = Query(...),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Balance exhaustive avec ouverture, mouvements et solde de clôture.

    Le solde final d'une période intermédiaire tient compte des écritures
    définitives antérieures à ``date_from`` dans le même exercice ; il ne s'agit
    donc plus du simple net des mouvements visibles.
    """
    _valider_periode_reporting(date_from, date_to)
    sid = current_user["societe_id"]
    rows = _rows_reporting_jusqua_date(db, sid, exercice, date_to)
    index_tiers = _index_tiers_reporting(db, sid)

    comptes = {}
    auxiliaire = {"3421": {}, "4411": {}}
    ecritures_periode = set()
    ecritures_anterieures = set()

    def compte_item(compte):
        return comptes.setdefault(compte, {
            "compte": compte,
            "solde_initial": Decimal("0.00"),
            "debit": Decimal("0.00"),
            "credit": Decimal("0.00"),
        })

    def aux_item(prefixe, meta):
        return auxiliaire[prefixe].setdefault(meta["cle"], {
            "tiers_id": meta["tiers_id"],
            "tiers": meta["tiers"],
            "compte_auxiliaire": meta["compte_auxiliaire"],
            "identifie": meta["identifie"],
            "solde_initial": Decimal("0.00"),
            "debit": Decimal("0.00"),
            "credit": Decimal("0.00"),
        })

    for ligne, ec in rows:
        d = _montant_decimal(ligne.debit)
        c = _montant_decimal(ligne.credit)
        est_anterieur = bool(date_from and ec.date < date_from)
        if est_anterieur:
            ecritures_anterieures.add(ec.id)
        else:
            ecritures_periode.add(ec.id)

        item = compte_item(ligne.compte)
        if est_anterieur:
            item["solde_initial"] += d - c
        else:
            item["debit"] += d
            item["credit"] += c

        prefixe = _prefixe_tiers(ligne.compte)
        if prefixe:
            meta = _resoudre_auxiliaire_reporting(ligne, ec, index_tiers)
            aux = aux_item(prefixe, meta)
            if est_anterieur:
                aux["solde_initial"] += d - c
            else:
                aux["debit"] += d
                aux["credit"] += c

    comptes_out = []
    # Un libellé commun à l'écran et aux exports, sans compléter le plan lors
    # d'une lecture. Les comptes désactivés conservent leur historique.
    from services.plan_comptable import PLAN_COMPTABLE
    numeros = list(comptes)
    libelles_reference = dict(db.query(
        models.CompteCGNCReference.numero, models.CompteCGNCReference.libelle,
    ).filter(models.CompteCGNCReference.numero.in_(numeros)).all()) if numeros else {}
    libelles_societe = dict(db.query(
        models.CompteSociete.numero, models.CompteSociete.libelle,
    ).filter(models.CompteSociete.societe_id == sid,
             models.CompteSociete.numero.in_(numeros)).all()) if numeros else {}
    for x in sorted(comptes.values(), key=lambda x: x["compte"]):
        solde_final = x["solde_initial"] + x["debit"] - x["credit"]
        if x["solde_initial"] == 0 and x["debit"] == 0 and x["credit"] == 0:
            continue
        comptes_out.append({
            "compte": x["compte"],
            "libelle": libelles_societe.get(x["compte"]) or libelles_reference.get(x["compte"]) or PLAN_COMPTABLE.get(x["compte"]) or "Compte non référencé",
            "solde_initial": float(x["solde_initial"]),
            "debit": float(x["debit"]),
            "credit": float(x["credit"]),
            "solde_final": float(solde_final),
        })

    auxiliaire_out = {}
    for prefixe, groupes in auxiliaire.items():
        lignes = []
        for x in groupes.values():
            solde_final = x["solde_initial"] + x["debit"] - x["credit"]
            if x["solde_initial"] == 0 and x["debit"] == 0 and x["credit"] == 0:
                continue
            lignes.append({
                "tiers_id": x["tiers_id"],
                "tiers": x["tiers"],
                "compte_auxiliaire": x["compte_auxiliaire"],
                "identifie": x["identifie"],
                "solde_initial": float(x["solde_initial"]),
                "debit": float(x["debit"]),
                "credit": float(x["credit"]),
                "solde_final": float(solde_final),
            })
        auxiliaire_out[prefixe] = sorted(lignes, key=lambda x: (not x["identifie"], x["tiers"].casefold()))

    total_debit = sum((x["debit"] for x in comptes.values()), Decimal("0.00"))
    total_credit = sum((x["credit"] for x in comptes.values()), Decimal("0.00"))
    total_ouverture = sum((x["solde_initial"] for x in comptes.values()), Decimal("0.00"))
    total_final = sum((x["solde_initial"] + x["debit"] - x["credit"] for x in comptes.values()), Decimal("0.00"))

    return {
        "exercice": exercice,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "nb_ecritures": len(ecritures_periode),
        "nb_ecritures_anterieures": len(ecritures_anterieures),
        "comptes": comptes_out,
        "auxiliaire": auxiliaire_out,
        "controle": {
            "mouvement_debit": float(total_debit),
            "mouvement_credit": float(total_credit),
            "ecart_mouvements": float(total_debit - total_credit),
            "ecart_ouverture": float(total_ouverture),
            "ecart_final": float(total_final),
        },
    }


@router.get("/reporting/grand-livre")
def reporting_grand_livre(
    exercice: int = Query(...),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Grand livre exhaustif avec solde d'ouverture et solde cumulé."""
    _valider_periode_reporting(date_from, date_to)
    sid = current_user["societe_id"]
    rows = _rows_reporting_jusqua_date(db, sid, exercice, date_to)
    index_tiers = _index_tiers_reporting(db, sid)

    soldes_ouverture = {}
    mouvements_periode = []
    ecritures_ids = set()

    for ligne, ec in rows:
        d = _montant_decimal(ligne.debit)
        c = _montant_decimal(ligne.credit)
        if date_from and ec.date < date_from:
            soldes_ouverture[ligne.compte] = soldes_ouverture.get(ligne.compte, Decimal("0.00")) + d - c
        else:
            mouvements_periode.append((ligne, ec, d, c))
            ecritures_ids.add(ec.id)

    comptes = {}
    for ligne, ec, d, c in mouvements_periode:
        if ligne.compte not in comptes:
            ouverture = soldes_ouverture.get(ligne.compte, Decimal("0.00"))
            comptes[ligne.compte] = {
                "compte": ligne.compte,
                "solde_initial": ouverture,
                "total_debit": Decimal("0.00"),
                "total_credit": Decimal("0.00"),
                "solde_courant": ouverture,
                "mouvements": [],
            }
        item = comptes[ligne.compte]
        item["total_debit"] += d
        item["total_credit"] += c
        item["solde_courant"] += d - c

        meta = _resoudre_auxiliaire_reporting(ligne, ec, index_tiers)
        item["mouvements"].append({
            "ecriture_id": ec.id,
            "ligne_id": ligne.id,
            "numero_ecriture": ec.numero_ecriture,
            "date": ec.date.isoformat(),
            "journal": _journal_code(ec.journal),
            "reference": ec.reference,
            "libelle": ec.libelle,
            "ligne_libelle": ligne.libelle,
            "debit": float(d),
            "credit": float(c),
            "solde_cumule": float(item["solde_courant"]),
            "code_lettrage": ligne.code_lettrage,
            "date_lettrage": ligne.date_lettrage.isoformat() if ligne.date_lettrage else None,
            "tiers_id": meta["tiers_id"] if meta else None,
            "tiers": meta["tiers"] if meta else None,
            "tiers_identifie": meta["identifie"] if meta else None,
        })

    comptes_out = []
    for x in sorted(comptes.values(), key=lambda x: x["compte"]):
        comptes_out.append({
            "compte": x["compte"],
            "solde_initial": float(x["solde_initial"]),
            "total_debit": float(x["total_debit"]),
            "total_credit": float(x["total_credit"]),
            "solde": float(x["solde_courant"]),
            "solde_final": float(x["solde_courant"]),
            "mouvements": x["mouvements"],
        })

    return {
        "exercice": exercice,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "nb_ecritures": len(ecritures_ids),
        "comptes": comptes_out,
    }


MONTANT_QUANTUM = Decimal("0.01")


def _montant_decimal(value) -> Decimal:
    """Convertit un montant entrant en Decimal monétaire à 2 décimales.

    Conversion via str() pour ne jamais importer l'imprécision binaire d'un float
    dans le grand livre.
    """
    try:
        if isinstance(value, bool):
            raise ValueError("Un booléen n'est pas un montant")
        montant = Decimal(str(value or 0))
        if not montant.is_finite():
            raise ValueError("Un montant doit être fini")
        arrondi = montant.quantize(MONTANT_QUANTUM, rounding=ROUND_HALF_UP)
        # Les colonnes débit/crédit sont NUMERIC(18,2). Contrôler après
        # l'arrondi existant, qui peut lui-même franchir la capacité SQL.
        if abs(arrondi) >= Decimal("10000000000000000"):
            raise HTTPException(422, "Montant comptable trop élevé pour être enregistré.")
        return arrondi
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(422, f"Montant comptable invalide : {value!r}")


def _verifier_equilibre(lignes):
    """Contrôle strict de la partie double en arithmétique décimale.

    - au moins deux lignes ;
    - aucune valeur négative ;
    - une ligne est débit OU crédit, jamais les deux ;
    - aucune ligne à zéro ;
    - égalité exacte à 2 décimales entre débit et crédit.
    """
    if not lignes or len(lignes) < 2:
        raise HTTPException(400, "Une écriture doit contenir au moins deux lignes (partie double)")

    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")

    for index, ligne in enumerate(lignes, start=1):
        debit = _montant_decimal(getattr(ligne, "debit", 0))
        credit = _montant_decimal(getattr(ligne, "credit", 0))

        if debit < 0 or credit < 0:
            raise HTTPException(400, f"Ligne {index} : débit et crédit ne peuvent pas être négatifs.")
        if debit > 0 and credit > 0:
            raise HTTPException(400, f"Ligne {index} : renseignez le débit OU le crédit, pas les deux.")
        if debit == 0 and credit == 0:
            raise HTTPException(400, f"Ligne {index} : un montant au débit ou au crédit est obligatoire.")

        total_debit += debit
        total_credit += credit

    if total_debit != total_credit:
        ecart = total_debit - total_credit
        raise HTTPException(
            400,
            f"Écriture déséquilibrée : total débits {total_debit:,.2f} ≠ total crédits {total_credit:,.2f} "
            f"(écart {ecart:+,.2f}). Une écriture doit respecter la partie double."
        )
    if total_debit <= 0:
        raise HTTPException(400, "Une écriture ne peut pas avoir des montants tous nuls")


@router.post("", response_model=schemas.EcritureOut, status_code=201)
def creer_ecriture(
    data: schemas.EcritureCreate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Crée une nouvelle écriture comptable."""
    exercice_cible = _verifier_periode_ouverte(db, current_user["societe_id"], data.date, "créer")
    _verifier_equilibre(data.lignes)
    _verifier_comptes_plan(db, current_user["societe_id"], data.lignes)
    _set_audit_context(db, current_user, "creation_manuelle")
    from datetime import datetime as _dt
    valider = bool(getattr(data, "est_validee", False))
    # COMPTA.3 : même lorsqu'on demande « valider dès la création », l'écriture
    # est d'abord insérée comme brouillon afin que ses lignes soient constituées,
    # puis elle devient définitive dans la même transaction. Cela permet au garde-
    # fou DB d'interdire toute modification de lignes après numérotation.
    ecriture = models.Ecriture(
        societe_id=current_user["societe_id"],
        est_validee=False,
        date_validation=None,
        validee_par=None,
        date=data.date,
        date_piece=getattr(data, "date_piece", None) or data.date,
        journal=data.journal,
        libelle=data.libelle.strip(),
        reference=(data.reference or "").strip() or None,
        exercice=exercice_cible.annee,
        source="manuel",
    )
    db.add(ecriture)
    db.flush()

    for l in data.lignes:
        ligne = models.LigneEcriture(
            ecriture_id=ecriture.id,
            compte=l.compte,
            libelle=l.libelle,
            debit=_montant_decimal(l.debit),
            credit=_montant_decimal(l.credit),
        )
        rattacher_ligne_auxiliaire(
            db, current_user["societe_id"], ligne,
            tiers_id=getattr(l, "tiers_id", None),
        )
        db.add(ligne)
    db.flush()

    if valider:
        verifier_auxiliaires_avant_validation(ecriture.lignes)
        _verifier_chronologie_validation(db, ecriture)
        ecriture.est_validee = True
        ecriture.date_validation = _dt.now()
        ecriture.validee_par = current_user["id"]
        db.flush()

    db.commit()
    db.refresh(ecriture)
    return ecriture


# ── Piste d'audit comptable (Patch 07A) ─────────────────────────────────────

@router.get("/audit/journal")
def journal_audit(
    exercice: int = Query(...),
    limit: int = Query(200, ge=1, le=1000),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Journal append-only des événements portant sur les écritures de l'exercice.

    On ne renvoie ici que les événements de niveau ``ecritures`` pour garder
    l'écran synthétique. Le détail d'une écriture inclut également les lignes.
    """
    return _audit_rows(db, """
        SELECT id, societe_id, ecriture_id, table_cible, ligne_id, action,
               acteur_id, acteur_nom, acteur_email, acteur_role, motif,
               ancien, nouveau, transaction_id, created_at
          FROM audit_ecritures
         WHERE societe_id = :sid
           AND table_cible = 'ecritures'
           AND COALESCE((nouveau->>'exercice')::int, (ancien->>'exercice')::int) = :exercice
         ORDER BY id DESC
         LIMIT :limit
    """, {"sid": current_user["societe_id"], "exercice": exercice, "limit": limit})


@router.get("/{ecriture_id}/audit")
def audit_ecriture(
    ecriture_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne la chronologie complète d'une écriture, lignes comprises."""
    # L'écriture peut avoir été supprimée : le contrôle tenant repose donc sur
    # la copie ``societe_id`` conservée dans l'audit, pas sur une FK vivante.
    return _audit_rows(db, """
        SELECT id, societe_id, ecriture_id, table_cible, ligne_id, action,
               acteur_id, acteur_nom, acteur_email, acteur_role, motif,
               ancien, nouveau, transaction_id, created_at
          FROM audit_ecritures
         WHERE societe_id = :sid AND ecriture_id = :eid
         ORDER BY id ASC
    """, {"sid": current_user["societe_id"], "eid": ecriture_id})


class JustificatifEcritureIn(BaseModel):
    reference: str = Field(..., min_length=1, max_length=100)
    date_piece: Optional[date] = None
    motif: Optional[str] = Field(None, max_length=500)


class AuxiliaireHistoriqueIn(BaseModel):
    tiers_id: int = Field(..., gt=0)
    motif: Optional[str] = Field(None, max_length=500)


@router.get("/par-piece", response_model=List[schemas.EcritureOut])
def rechercher_par_piece(
    reference: str = Query(..., min_length=1, max_length=100),
    date_piece: Optional[date] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrouve une écriture à partir de la référence/date du justificatif.

    Avis n°24 §2.4.b : la recherche tient compte de la référence d'origine et
    des compléments documentaires ajoutés sans réécriture de l'écriture.
    """
    ref = reference.strip()
    q = (
        db.query(models.Ecriture)
        .options(joinedload(models.Ecriture.lignes), joinedload(models.Ecriture.justificatifs))
        .filter(models.Ecriture.societe_id == current_user["societe_id"])
        .filter(or_(
            models.Ecriture.reference == ref,
            models.Ecriture.justificatifs.any(models.EcritureJustificatif.reference == ref),
        ))
    )
    resultats = q.order_by(models.Ecriture.date.desc(), models.Ecriture.id.desc()).all()
    if date_piece is not None:
        resultats = [e for e in resultats if e.date_piece_fec == date_piece]
    return _lecture_ecritures(resultats)


@router.post("/{ecriture_id}/lignes/{ligne_id}/auxiliaire-complement", status_code=201)
def ajouter_auxiliaire_historique(
    ecriture_id: int,
    ligne_id: int,
    data: AuxiliaireHistoriqueIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Documente l'auxiliaire d'une ancienne ligne 3421/4411 sans la réécrire.

    Le complément est append-only. Une éventuelle correction ultérieure se fait
    par un nouveau complément ; le FEC retient le dernier complément complet.
    """
    societe_id = current_user["societe_id"]
    ecriture = db.query(models.Ecriture).filter_by(
        id=ecriture_id, societe_id=societe_id
    ).first()
    if not ecriture:
        raise HTTPException(404, "Écriture introuvable")

    ligne = db.query(models.LigneEcriture).filter_by(
        id=ligne_id, ecriture_id=ecriture.id
    ).first()
    if not ligne:
        raise HTTPException(404, "Ligne comptable introuvable dans cette écriture")

    compte = str(ligne.compte or "").strip()
    if compte.startswith("3421"):
        nature = "client"
        roles_valides = {"client", "les_deux"}
        attr_code = "code_aux_client"
        prefixe = "C"
    elif compte.startswith("4411"):
        nature = "fournisseur"
        roles_valides = {"fournisseur", "les_deux"}
        attr_code = "code_aux_fournisseur"
        prefixe = "F"
    else:
        raise HTTPException(422, "Le complément auxiliaire historique est réservé aux comptes collectifs 3421/4411.")

    tiers = db.query(models.Tiers).filter_by(
        id=data.tiers_id, societe_id=societe_id
    ).first()
    if not tiers:
        raise HTTPException(404, "Tiers introuvable")
    role = str(getattr(getattr(tiers, "type", None), "value", getattr(tiers, "type", "")) or "")
    if role not in roles_valides:
        raise HTTPException(422, f"Le tiers sélectionné n'est pas compatible avec un auxiliaire {nature}.")

    code_aux = (getattr(tiers, attr_code, None) or "").strip()
    if not code_aux:
        code_aux = f"{prefixe}{tiers.id:08d}"
        setattr(tiers, attr_code, code_aux)
        db.flush()

    complement = models.LigneAuxiliaireComplement(
        societe_id=societe_id,
        ligne_ecriture_id=ligne.id,
        tiers_id=tiers.id,
        nature_auxiliaire=nature,
        compte_auxiliaire_snapshot=code_aux,
        libelle_auxiliaire_snapshot=(tiers.nom or "").strip(),
        source_type="manuel_fec",
        source_id=tiers.id,
        motif=(data.motif or "").strip() or "Complément auxiliaire FEC historique saisi manuellement.",
        created_by=current_user.get("id"),
    )
    if not complement.libelle_auxiliaire_snapshot:
        raise HTTPException(422, "Le tiers sélectionné doit avoir un nom.")
    db.add(complement)
    db.commit()
    db.refresh(complement)
    return {
        "id": complement.id,
        "ligne_ecriture_id": ligne.id,
        "tiers_id": tiers.id,
        "nature_auxiliaire": nature,
        "compte_auxiliaire": code_aux,
        "libelle_auxiliaire": complement.libelle_auxiliaire_snapshot,
        "message": "Auxiliaire historique ajouté sans modifier l'écriture définitive.",
    }


@router.get("/{ecriture_id}/justificatifs")
def lister_justificatifs_ecriture(
    ecriture_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ecriture = (
        db.query(models.Ecriture)
        .options(joinedload(models.Ecriture.justificatifs))
        .filter_by(id=ecriture_id, societe_id=current_user["societe_id"])
        .first()
    )
    if not ecriture:
        raise HTTPException(404, "Écriture introuvable")
    return {
        "ecriture_id": ecriture.id,
        "reference_origine": ecriture.reference,
        "date_piece_origine": ecriture.date_piece or ecriture.date,
        "reference_fec": ecriture.reference_fec,
        "date_piece_fec": ecriture.date_piece_fec,
        "complements": [
            {
                "id": j.id,
                "reference": j.reference,
                "date_piece": j.date_piece,
                "source_type": j.source_type,
                "source_id": j.source_id,
                "fichier_nom": j.fichier_nom,
                "prioritaire": j.prioritaire,
                "motif": j.motif,
                "created_by": j.created_by,
                "created_at": j.created_at,
            }
            for j in (ecriture.justificatifs or [])
        ],
    }


@router.post("/{ecriture_id}/justificatifs", status_code=201)
def ajouter_justificatif_ecriture(
    ecriture_id: int,
    data: JustificatifEcritureIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Ajoute une référence documentaire sans modifier l'écriture comptable.

    Sur une écriture définitive, cette table append-only est précisément ce qui
    permet de compléter la piste d'audit sans casser l'irréversibilité COMPTA.3.
    """
    ecriture = db.query(models.Ecriture).filter_by(
        id=ecriture_id, societe_id=current_user["societe_id"]
    ).first()
    if not ecriture:
        raise HTTPException(404, "Écriture introuvable")
    reference = (data.reference or "").strip()
    if not reference:
        raise HTTPException(422, "La référence du justificatif ne peut pas être vide.")
    piece = models.EcritureJustificatif(
        societe_id=current_user["societe_id"],
        ecriture_id=ecriture.id,
        reference=reference,
        date_piece=data.date_piece or ecriture.date_piece or ecriture.date,
        source_type="manuel",
        prioritaire=True,
        motif=(data.motif or "").strip() or None,
        created_by=current_user.get("id"),
    )
    db.add(piece)
    db.commit()
    db.refresh(piece)
    return {
        "id": piece.id,
        "reference": piece.reference,
        "date_piece": piece.date_piece,
        "prioritaire": piece.prioritaire,
        "message": "Référence justificative ajoutée sans modifier l'écriture définitive.",
    }


@router.get("/{ecriture_id}", response_model=schemas.EcritureOut)
def obtenir_ecriture(
    ecriture_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ecriture = (
        db.query(models.Ecriture)
        .options(joinedload(models.Ecriture.lignes), joinedload(models.Ecriture.justificatifs))
        .filter_by(id=ecriture_id, societe_id=current_user["societe_id"])
        .first()
    )
    if not ecriture:
        raise HTTPException(status_code=404, detail="Écriture introuvable")
    return _lecture_ecritures([ecriture])[0]


@router.patch("/{ecriture_id}", response_model=schemas.EcritureOut)
def modifier_ecriture(
    ecriture_id: int,
    data: schemas.EcritureUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Modifie une écriture existante (remplace les lignes)."""
    ecriture = db.query(models.Ecriture).filter_by(
        id=ecriture_id, societe_id=current_user["societe_id"]
    ).populate_existing().with_for_update().first()
    if not ecriture:
        raise HTTPException(404, "Écriture introuvable")
    from services.ras_reglement_service import proteger_ecriture_capture
    proteger_ecriture_capture(db,current_user['societe_id'],ecriture_id)
    proteger_reprise_provision(db,current_user['societe_id'],ecriture_id)

    _verifier_non_validee(ecriture, "modifier")
    _verifier_periode_ouverte(db, current_user["societe_id"], ecriture.date, "modifier")
    _set_audit_context(db, current_user, "modification")

    # La date arrive en chaîne ("2026-07-15") : on la convertit avant tout usage,
    # sinon le contrôle de période et l'enregistrement échouent.
    nouvelle_date = None
    if data.date is not None:
        from datetime import date as _date, datetime as _dt
        if isinstance(data.date, str):
            try:
                nouvelle_date = _dt.strptime(data.date[:10], "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(422, "Date invalide : format attendu AAAA-MM-JJ.")
        elif isinstance(data.date, _date):
            nouvelle_date = data.date
        if nouvelle_date is not None:
            exercice_cible = _verifier_periode_ouverte(db, current_user["societe_id"], nouvelle_date,
                                      "déplacer une écriture")

    # Date du justificatif : distincte de la date de comptabilisation.
    nouvelle_date_piece = None
    if getattr(data, "date_piece", None) is not None:
        from datetime import date as _date, datetime as _dt
        if isinstance(data.date_piece, str):
            try:
                nouvelle_date_piece = _dt.strptime(data.date_piece[:10], "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(422, "Date de pièce invalide : format attendu AAAA-MM-JJ.")
        elif isinstance(data.date_piece, _date):
            nouvelle_date_piece = data.date_piece

    # 07C.3 : ``CL`` est un journal système exclusivement alimenté par le
    # moteur de clôture. Même un brouillon manuel ne peut pas y être déplacé.
    if data.journal is not None and _journal_code(data.journal).upper() == "CL":
        raise HTTPException(403,
            "Le journal CL est réservé aux écritures de clôture générées par HisabPro.")

    # 07C.2 : un brouillon sans numéro peut encore changer de journal/date.
    # Une écriture ayant déjà reçu son numéro définitif conserve en revanche
    # journal, exercice et date comptable pour préserver sa chronologie.
    if data.journal is not None:
        _verifier_perimetre_numero(ecriture, journal=data.journal)
    exercice_nouveau = None
    if nouvelle_date is not None:
        exercice_nouveau = exercice_cible.annee
        _verifier_perimetre_numero(
            ecriture, exercice=exercice_nouveau, date_comptable=nouvelle_date
        )

    # Mettre à jour les champs de l'écriture.
    if data.journal is not None:
        ecriture.journal = data.journal
    if nouvelle_date is not None:
        ecriture.date = nouvelle_date
        if not (getattr(ecriture, "numero_ecriture", None) or "").strip():
            ecriture.exercice = exercice_nouveau
    if nouvelle_date_piece is not None:
        ecriture.date_piece = nouvelle_date_piece
    elif nouvelle_date is not None and getattr(ecriture, "date_piece", None) is None:
        ecriture.date_piece = nouvelle_date
    if data.libelle   is not None: ecriture.libelle    = data.libelle.strip()
    if data.reference is not None: ecriture.reference  = data.reference.strip() or None

    # Remplacer les lignes si fournies
    if data.lignes is not None:
        _verifier_equilibre(data.lignes)
        _verifier_comptes_plan(db, current_user["societe_id"], data.lignes)
        # Supprimer les anciennes lignes
        for l in ecriture.lignes:
            db.delete(l)
        db.flush()
        # Créer les nouvelles
        for l in data.lignes:
            ligne = models.LigneEcriture(
                ecriture_id=ecriture.id,
                compte=l.compte,
                libelle=l.libelle or '',
                debit=_montant_decimal(l.debit),
                credit=_montant_decimal(l.credit),
            )
            rattacher_ligne_auxiliaire(
                db, current_user["societe_id"], ligne,
                tiers_id=getattr(l, "tiers_id", None),
            )
            db.add(ligne)

    db.commit()
    db.refresh(ecriture)
    return ecriture


def _liberer_document_source(db: Session, societe_id: int, ecriture):
    """Remet à « non comptabilisé » le document à l'origine d'une écriture supprimée.

    Le lien natif du règlement prime sur la référence documentaire. Une
    référence libre ne doit jamais libérer un document d'une autre origine.
    """
    source = getattr(ecriture, "source", None)
    if source not in {"facture", "avoir", "reglement"}:
        return
    ref = (ecriture.reference or "").strip()
    if source == "reglement":
        base = db.query(models.Reglement).filter_by(societe_id=societe_id)
        if base.filter_by(ecriture_annulation_id=ecriture.id).first():
            raise HTTPException(409,
                "Cette écriture porte l'annulation d'un règlement : sa suppression ferait disparaître la correction comptable.")
        if ecriture.contrepassation_de_id:
            return
        lies = base.filter_by(ecriture_id=ecriture.id).order_by(models.Reglement.id).all()
        if len(lies) > 1:
            raise HTTPException(409,
                "Plusieurs règlements sont liés à cette écriture : suppression bloquée pour préserver leurs sources.")
        if lies:
            reglement = lies[0]
            if reglement.statut == "annule":
                raise HTTPException(409, "L'écriture d'origine d'un règlement annulé doit être conservée.")
            # Mise à jour conditionnelle : si une opération concurrente a
            # changé le lien, elle ne peut pas être écrasée par une lecture
            # antérieure. Le Journal détient déjà le verrou de la pièce.
            n = base.filter_by(id=reglement.id, ecriture_id=ecriture.id).update(
                {"est_comptabilisee": False, "ecriture_id": None}, synchronize_session=False)
            if n != 1:
                raise HTTPException(409, "Le lien du règlement a changé. Réessayez après la fin de l'opération.")
            return
        if not ref:
            return
        correspondance = (models.Reglement.numero == ref) | (models.Reglement.reference == ref)
        if ref.startswith("REG-"):
            try:
                correspondance = correspondance | (models.Reglement.id == int(ref[4:]))
            except ValueError:
                pass
        candidats = base.filter(
            models.Reglement.ecriture_id.is_(None),
            models.Reglement.est_comptabilisee.is_(True),
            models.Reglement.date == ecriture.date,
            correspondance,
        ).order_by(models.Reglement.id).all()
        if len(candidats) > 1:
            raise HTTPException(409,
                "Plusieurs règlements historiques correspondent à cette référence : suppression automatique ambiguë.")
        if candidats:
            montant = Decimal(str(candidats[0].montant or 0))
            debit = sum((Decimal(str(l.debit or 0)) for l in ecriture.lignes), Decimal(0))
            credit = sum((Decimal(str(l.credit or 0)) for l in ecriture.lignes), Decimal(0))
            if (not montant.is_finite() or not debit.is_finite() or not credit.is_finite()
                    or montant <= 0 or debit != montant or credit != montant):
                raise HTTPException(409,
                    "Les montants ne recoupent pas le règlement historique : suppression automatique bloquée.")
            n = base.filter_by(id=candidats[0].id, ecriture_id=None,
                est_comptabilisee=True, date=ecriture.date).filter(
                    models.Reglement.statut != "annule").update(
                        {"est_comptabilisee": False}, synchronize_session=False)
            if n != 1:
                raise HTTPException(409, "L'état du règlement historique a changé ou il est annulé : suppression bloquée.")
        return
    if source == "facture":
        reference_source = ecriture.reference
        tiers = {l.tiers_id for l in ecriture.lignes if l.tiers_id is not None}
        if (db.get_bind().dialect.name == "postgresql" and
                db.execute(text("SELECT to_regclass('public.audit_ecritures') IS NOT NULL")).scalar()):
            creations = db.execute(text("""SELECT nouveau,transaction_id FROM audit_ecritures
                WHERE societe_id=:s AND ecriture_id=:e AND table_cible='ecritures'
                  AND ancien IS NULL AND nouveau IS NOT NULL AND action<>'baseline_initiale'
                ORDER BY id"""), {'s': societe_id, 'e': ecriture.id}).mappings().all()
            if len(creations) > 1:
                raise HTTPException(409, "La trace de création de la pièce est ambiguë : vérification nécessaire.")
            if creations:
                creation = creations[0]
                origine = creation['nouveau']
                if (origine.get('source') != "facture" or origine.get('id') != ecriture.id
                        or origine.get('societe_id') != societe_id
                        or origine.get('date') != ecriture.date.isoformat()):
                    raise HTTPException(409, "L'origine ou la date de la pièce diffère de sa création : vérification nécessaire.")
                tiers_creation = {int(v) for v in db.execute(text("""SELECT DISTINCT nouveau->>'tiers_id'
                    FROM audit_ecritures WHERE societe_id=:s AND ecriture_id=:e
                      AND table_cible='lignes_ecriture' AND action='ligne_ajoutee'
                      AND transaction_id=:t AND nouveau->>'tiers_id' IS NOT NULL"""),
                    {'s': societe_id, 'e': ecriture.id, 't': creation['transaction_id']}).scalars()}
                if tiers != tiers_creation:
                    raise HTTPException(409, "Les auxiliaires de la pièce diffèrent de sa création : vérification nécessaire.")
                reference_source = origine.get('reference')
        if not (reference_source or '').strip():
            raise HTTPException(409, "La facture source ne peut pas être identifiée : vérifiez la référence de cette pièce.")
        factures = db.query(models.Facture).filter(
            models.Facture.societe_id == societe_id,
            models.Facture.date == ecriture.date,
            or_(models.Facture.numero == reference_source,
                (models.Facture.type == "achat") & (models.Facture.reference == reference_source)),
        ).order_by(models.Facture.id).all()
        if tiers:
            factures = [f for f in factures if f.tiers_id in tiers] if len(tiers) == 1 else []
        if len(factures) != 1:
            raise HTTPException(409,
                "La facture source est absente ou ambiguë : vérifiez la référence, la date et le tiers de cette pièce.")
        factures[0].est_comptabilisee = False
        # Une RAS historique peut être portée par une OD distincte, toujours
        # présente. Supprimer le brouillon de facture ne l'annule pas.
        return

    if not ref:
        return

    # ── Avoir ──
    Avoir = getattr(models, "Avoir", None)
    if source == "avoir" and Avoir is not None:
        avoir = db.query(Avoir).filter_by(societe_id=societe_id, numero=ref).first()
        if avoir is not None:
            avoir.est_comptabilisee = False
            return



@router.delete("/{ecriture_id}", status_code=204)
def supprimer_ecriture(
    ecriture_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    ecriture = db.query(models.Ecriture).filter_by(
        id=ecriture_id, societe_id=current_user["societe_id"]
    ).populate_existing().with_for_update().first()
    if not ecriture:
        raise HTTPException(status_code=404, detail="Écriture introuvable")
    from services.ras_reglement_service import proteger_ecriture_capture
    proteger_ecriture_capture(db,current_user['societe_id'],ecriture_id)
    proteger_reprise_provision(db,current_user['societe_id'],ecriture_id)
    _verifier_non_validee(ecriture, "supprimer")
    ajustement = db.query(models.AjustementInventaire.id).filter(
        models.AjustementInventaire.societe_id == current_user["societe_id"],
        or_(models.AjustementInventaire.ecriture_id == ecriture_id,
            models.AjustementInventaire.contrepassation_id == ecriture_id),
    ).first()
    if ajustement:
        raise HTTPException(409,
            "Cette pièce est liée à un ajustement d'inventaire. Supprimez l'ajustement "
            "depuis Clôture pour conserver la cohérence avec sa contrepassation.")
    if (getattr(ecriture, "numero_ecriture", None) or "").strip():
        raise HTTPException(409,
            f"Suppression interdite : l'écriture possède déjà le numéro définitif {ecriture.numero_ecriture}. "
            "Utilisez une écriture d'annulation/contrepassation pour conserver la continuité de la séquence.")
    _verifier_periode_ouverte(db, current_user["societe_id"], ecriture.date, "supprimer")
    _set_audit_context(db, current_user, "suppression_brouillon")

    # Le document source redevient « non comptabilisé » : sans cela il resterait
    # marqué comme tel alors que son écriture n'existe plus, et il serait
    # impossible de la régénérer depuis son module.
    _liberer_document_source(db, current_user["societe_id"], ecriture)

    db.delete(ecriture)
    db.commit()


@router.get("/stats/kpi")
def kpi_dashboard(
    exercice: int = Query(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calcule les KPIs du dashboard pour l'exercice donné."""
    lignes = (
        db.query(models.LigneEcriture)
        .join(models.Ecriture)
        .filter(
            models.Ecriture.societe_id == current_user["societe_id"],
            models.Ecriture.exercice   == exercice,
        )
        .all()
    )

    ca = charges = tva_collect = tva_recup = 0

    for l in lignes:
        if l.compte.startswith("7") and l.credit > 0:
            ca += l.credit
        if l.compte.startswith("6") and l.debit > 0:
            charges += l.debit
        if l.compte.startswith("4455") and l.credit > 0:
            tva_collect += l.credit
        if l.compte.startswith("3455") and l.debit > 0:
            tva_recup += l.debit

    nb_ecritures = db.query(models.Ecriture).filter_by(
        societe_id=current_user["societe_id"], exercice=exercice
    ).count()

    nb_attente = db.query(models.Facture).filter_by(
        societe_id=current_user["societe_id"],
        statut=models.StatutFactureEnum.en_attente,
        exercice=exercice,
    ).count()

    return schemas.KPIDashboard(
        chiffre_affaires=ca,
        charges=charges,
        resultat_net=ca - charges,
        tva_due=max(0, tva_collect - tva_recup),
        nb_ecritures=nb_ecritures,
        nb_factures_attente=nb_attente,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION DES ÉCRITURES
#
# Une écriture saisie reste en « brouillon » : librement corrigeable. La validation
# la rend définitive — plus aucune modification ni suppression n'est possible.
# C'est le principe d'intangibilité du chemin de révision comptable.
# ═══════════════════════════════════════════════════════════════════════════════

class ValiderLotIn(BaseModel):
    ids: List[int]


@router.post("/{ecriture_id}/valider")
def valider_ecriture(
    ecriture_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Rend une écriture définitive."""
    from datetime import datetime as _dt
    ecriture = db.query(models.Ecriture).filter_by(
        id=ecriture_id, societe_id=current_user["societe_id"]
    ).populate_existing().with_for_update().first()
    if not ecriture:
        raise HTTPException(404, "Écriture introuvable")
    if ecriture.est_validee:
        raise HTTPException(400, "Cette écriture est déjà validée.")

    _verifier_periode_ouverte(db, current_user["societe_id"], ecriture.date, "valider")
    verifier_validation_reprise(db, current_user['societe_id'], ecriture_id)
    _set_audit_context(db, current_user, "validation")

    # On ne valide jamais une écriture déséquilibrée : elle deviendrait
    # définitive avec une anomalie impossible à corriger.
    total_d = sum((_montant_decimal(l.debit) for l in ecriture.lignes), Decimal("0.00"))
    total_c = sum((_montant_decimal(l.credit) for l in ecriture.lignes), Decimal("0.00"))
    if total_d != total_c:
        raise HTTPException(400,
            f"Écriture déséquilibrée (débit {total_d:.2f} / crédit {total_c:.2f}) : "
            "corrigez-la avant de la valider.")
    if not ecriture.lignes:
        raise HTTPException(400, "Écriture sans ligne : rien à valider.")
    verifier_auxiliaires_avant_validation(ecriture.lignes)

    _verifier_chronologie_validation(db, ecriture)
    ecriture.est_validee = True
    ecriture.date_validation = _dt.now()
    ecriture.validee_par = current_user["id"]
    db.commit()
    db.refresh(ecriture)  # récupère le numero_ecriture attribué par le trigger 07C.2
    return {
        "message": f"Écriture {ecriture.numero_ecriture or ('#' + str(ecriture.id))} validée.",
        "id": ecriture.id,
        "numero_ecriture": ecriture.numero_ecriture,
        "date_validation": ecriture.date_validation,
    }


@router.post("/valider-lot")
def valider_lot(
    data: ValiderLotIn,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Valide plusieurs écritures d'un coup, en signalant celles qui posent problème."""
    from datetime import datetime as _dt
    societe_id = current_user["societe_id"]
    _set_audit_context(db, current_user, "validation_lot")
    validees, refusees = [], []
    numeros = {}

    # Charge d'abord les écritures et les traite par journal/date/id : un lot
    # sélectionné dans un ordre arbitraire ne doit jamais produire une séquence
    # contraire à la chronologie comptable.
    demandees = {int(eid) for eid in data.ids}
    trouvees = (
        db.query(models.Ecriture)
        .filter(models.Ecriture.societe_id == societe_id, models.Ecriture.id.in_(demandees))
        .order_by(models.Ecriture.id)
        .populate_existing().with_for_update()
        .all()
    ) if demandees else []
    par_id = {e.id: e for e in trouvees}
    for eid in data.ids:
        if int(eid) not in par_id:
            refusees.append({"id": int(eid), "motif": "introuvable"})

    a_traiter = sorted(
        par_id.values(),
        key=lambda e: (_journal_code(e.journal), e.date, e.id),
    )

    for e in a_traiter:
        eid = e.id
        if e.est_validee:
            refusees.append({"id": eid, "motif": "déjà validée"}); continue
        try:
            verifier_date_ecriture(db, societe_id, e.date, "valider")
            verifier_validation_reprise(db, societe_id, eid)
            _verifier_chronologie_validation(db, e)
        except (ValueError, HTTPException) as exc:
            motif = exc.detail if isinstance(exc, HTTPException) else str(exc)
            refusees.append({"id": eid, "motif": motif}); continue
        d = sum((_montant_decimal(l.debit) for l in e.lignes), Decimal("0.00"))
        c = sum((_montant_decimal(l.credit) for l in e.lignes), Decimal("0.00"))
        if d != c:
            refusees.append({"id": eid, "motif": f"déséquilibrée ({d - c:+.2f})"}); continue
        if not e.lignes:
            refusees.append({"id": eid, "motif": "sans ligne"}); continue
        try:
            verifier_auxiliaires_avant_validation(e.lignes)
        except HTTPException as exc:
            refusees.append({"id": eid, "motif": exc.detail}); continue

        e.est_validee = True
        e.date_validation = _dt.now()
        e.validee_par = current_user["id"]
        db.flush()
        db.refresh(e)  # récupère le numéro donné par PostgreSQL avant l'élément suivant
        validees.append(eid)
        numeros[str(eid)] = e.numero_ecriture

    db.commit()
    return {
        "nb_validees": len(validees), "nb_refusees": len(refusees),
        "validees": validees, "refusees": refusees, "numeros": numeros,
    }


class ContrepasserIn(BaseModel):
    date_correction: Optional[date] = None
    motif: Optional[str] = Field(None, max_length=500)


def _choisir_date_contrepassation(db: Session, societe_id: int, ecriture, date_demandee: Optional[date] = None):
    """Choisit une date de correction sans alourdir la saisie utilisateur.

    Si une date est fournie, elle doit être ouverte et ne peut pas précéder
    l'écriture originale. Sinon HisabPro prend la première date disponible d'une
    période ouverte à partir de la date originale.
    """
    if date_demandee is not None:
        if date_demandee < ecriture.date:
            raise HTTPException(409, "La contrepassation ne peut pas être datée avant l'écriture originale.")
        _verifier_periode_ouverte(db, societe_id, date_demandee, "contrepasser")
        return date_demandee

    periode = (
        db.query(models.PeriodeComptable, models.ExerciceComptable)
        .join(models.ExerciceComptable, models.PeriodeComptable.exercice_id == models.ExerciceComptable.id)
        .filter(
            models.ExerciceComptable.societe_id == societe_id,
            models.ExerciceComptable.statut != "cloture",
            models.PeriodeComptable.statut == "ouverte",
            models.PeriodeComptable.date_fin >= ecriture.date,
        )
        .order_by(models.PeriodeComptable.date_debut.asc())
        .first()
    )
    if not periode:
        raise HTTPException(409,
            "Aucune période comptable ouverte n'est disponible pour la contrepassation. Ouvrez une période de travail.")

    p, _ex = periode
    return max(ecriture.date, p.date_debut)


@router.post("/{ecriture_id}/contrepasser")
def contrepasser_ecriture(
    ecriture_id: int,
    data: ContrepasserIn | None = None,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Crée une écriture compensatoire définitive, sans toucher à l'original."""
    from datetime import datetime as _dt
    original = db.query(models.Ecriture).filter_by(
        id=ecriture_id, societe_id=current_user["societe_id"]
    ).populate_existing().with_for_update().first()
    if not original:
        raise HTTPException(404, "Écriture introuvable")
    from services.ras_reglement_service import proteger_ecriture_capture
    proteger_ecriture_capture(db,current_user['societe_id'],ecriture_id)
    proteger_reprise_provision(db,current_user['societe_id'],ecriture_id)
    if not original.est_validee or not (original.numero_ecriture or "").strip():
        raise HTTPException(409, "Seule une écriture définitive peut être contrepassée.")

    existante = db.query(models.Ecriture).filter_by(
        societe_id=current_user["societe_id"], contrepassation_de_id=original.id
    ).first()
    if existante:
        return {
            "message": f"L'écriture {original.numero_ecriture} est déjà contrepassée par {existante.numero_ecriture or ('#' + str(existante.id))}.",
            "id": existante.id,
            "numero_ecriture": existante.numero_ecriture,
            "date": existante.date,
            "deja_existante": True,
        }

    payload = data or ContrepasserIn()
    motif = (payload.motif or "Correction d'une écriture validée").strip()
    date_correction = _choisir_date_contrepassation(
        db, current_user["societe_id"], original, payload.date_correction
    )
    exercice_cible = _verifier_periode_ouverte(db, current_user["societe_id"], date_correction, "contrepasser")
    _set_audit_context(db, current_user, "contrepassation", motif)

    correction = models.Ecriture(
        societe_id=current_user["societe_id"],
        date=date_correction,
        date_piece=date_correction,
        journal=original.journal,
        libelle=f"Contrepassation {original.numero_ecriture} — {original.libelle}"[:300],
        reference=f"ANN-{original.numero_ecriture}"[:100],
        exercice=exercice_cible.annee,
        source="correction",
        est_validee=False,
        contrepassation_de_id=original.id,
        motif_correction=motif,
    )
    db.add(correction)
    db.flush()

    for ligne in original.lignes:
        db.add(models.LigneEcriture(
            ecriture_id=correction.id,
            compte=ligne.compte,
            libelle=(ligne.libelle or original.libelle),
            debit=_montant_decimal(ligne.credit),
            credit=_montant_decimal(ligne.debit),
            tiers_id=getattr(ligne, "tiers_id", None),
            nature_auxiliaire=getattr(ligne, "nature_auxiliaire", None),
            compte_auxiliaire_snapshot=getattr(ligne, "compte_auxiliaire_snapshot", None),
            libelle_auxiliaire_snapshot=getattr(ligne, "libelle_auxiliaire_snapshot", None),
        ))
    db.flush()

    _verifier_chronologie_validation(db, correction)
    correction.est_validee = True
    correction.date_validation = _dt.now()
    correction.validee_par = current_user["id"]
    db.commit()
    db.refresh(correction)

    return {
        "message": f"Contrepassation {correction.numero_ecriture} créée pour {original.numero_ecriture}.",
        "id": correction.id,
        "numero_ecriture": correction.numero_ecriture,
        "date": correction.date,
        "deja_existante": False,
    }


# Route historique conservée uniquement pour renvoyer un message explicite aux
# anciens clients front : COMPTA.3 interdit désormais toute dévalidation.
class DevaliderIn(BaseModel):
    motif: Optional[str] = Field(None, max_length=500)


@router.post("/{ecriture_id}/devalider")
def devalider_ecriture(
    ecriture_id: int,
    data: DevaliderIn | None = None,
    current_user = Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    raise HTTPException(409,
        "COMPTA.3 : une écriture validée est définitive et ne peut plus être dévalidée. Utilisez la contrepassation.")


@router.get("/a-valider/compteur")
def compteur_a_valider(
    exercice: int = Query(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Nombre et montant des écritures en attente de validation."""
    q = db.query(models.Ecriture).filter_by(
        societe_id=current_user["societe_id"], exercice=exercice, est_validee=False)
    ecritures = q.all()
    total = sum(sum(l.debit or 0 for l in e.lignes) for e in ecritures)
    return {
        "nb_a_valider": len(ecritures),
        "montant_total": round(total, 2),
        "plus_ancienne": min((e.date for e in ecritures), default=None),
    }
