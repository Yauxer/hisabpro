"""
Router Lettrage — lettrage comptable des comptes tiers.

COMPTA-FINAL : la source de vérité est la ligne comptable définitive et le
lettrage est conservé dans ``lettrages_comptables`` afin de ne jamais modifier
une écriture validée.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
import re
from database import get_db
from auth import get_current_user, requiert_ecriture
import models
from services.tva_service import ventilation_facture, total_ventilation

router = APIRouter(prefix="/api/lettrage", tags=["lettrage"])


class LettrageComptableIn(BaseModel):
    ligne_ids: List[int]
    code: Optional[str] = None
    # Lettrage partiel (959) : sélection non équilibrée explicitement voulue,
    # complétée plus tard en ajoutant des lignes au même code.
    partiel: bool = False


def _normaliser_tiers(value: Optional[str]) -> str:
    return " ".join((value or "").strip().casefold().split())


def _compte_lettrable(compte: str) -> bool:
    return bool(compte) and compte[:4] in {"3421", "4411"}


def _cle_tiers_ligne(ligne) -> str:
    """Clé stable d'auxiliaire pour le lettrage.

    Patch 053 : ``tiers_id``/le code auxiliaire figé sont prioritaires. Le
    libellé libre n'est conservé qu'en repli pour les historiques antérieurs à
    la migration, afin de ne pas casser leur consultation.
    """
    compte = (ligne.compte or "").strip()
    if compte not in {"3421", "4411"}:
        return f"compte:{compte}"
    tiers_id = getattr(ligne, "tiers_id", None)
    if tiers_id:
        return f"tiers_id:{int(tiers_id)}"
    code_aux = _normaliser_tiers(getattr(ligne, "compte_auxiliaire_snapshot", None))
    if code_aux:
        return f"aux:{code_aux}"
    # Repli legacy uniquement : les nouvelles validations 3421/4411 sans tiers
    # natif sont bloquées par le service auxiliaire et le trigger PostgreSQL.
    tiers = _normaliser_tiers(ligne.libelle)
    return f"tiers:{tiers}" if tiers else ""


def _verifier_compte_demande(compte: str):
    if not _compte_lettrable(compte):
        raise HTTPException(400, "Seuls les comptes clients 3421 et fournisseurs 4411 sont lettrables")


def _exercice_est_cloture(db: Session, societe_id: int, exercice: int) -> bool:
    ex = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=int(exercice)
    ).first()
    if ex and ex.statut == "cloture":
        return True
    return db.query(models.ClotureExercice.id).filter_by(
        societe_id=societe_id, exercice=int(exercice)
    ).first() is not None


def _verifier_exercice_modifiable(db: Session, societe_id: int, exercice: int):
    if _exercice_est_cloture(db, societe_id, exercice):
        raise HTTPException(
            423,
            f"Exercice {exercice} clôturé : le lettrage est en lecture seule.",
        )


def _verrouiller_generation_codes(db: Session, societe_id: int):
    """Sérialise la génération AAA/AAB/... par société sous PostgreSQL.

    Sans ce verrou deux utilisateurs pourraient lire le même prochain code et
    créer deux groupes distincts portant la même lettre.
    """
    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:namespace, :sid)"),
            {"namespace": 49049, "sid": int(societe_id)},
        )


def _code_depuis_set(codes: set[str]) -> str:
    import itertools
    import string

    lettres = string.ascii_uppercase
    for taille in range(3, 5):
        for chars in itertools.product(lettres, repeat=taille):
            code = "".join(chars)
            if code not in codes:
                return code
    raise HTTPException(409, "Espace de codes de lettrage épuisé")


def _codes_comptables_utilises(db: Session, societe_id: int) -> set[str]:
    # Les codes historiques désactivés restent réservés : on ne recycle jamais
    # un code déjà présent dans l'audit de lettrage.
    return {
        x[0]
        for x in db.query(models.LettrageComptable.code)
        .filter(models.LettrageComptable.societe_id == societe_id)
        .distinct()
        .all()
        if x[0]
    }


def _codes_partiels(lignes) -> set[str]:
    """Un code est partiel tant que ses lignes actives ne s'équilibrent pas."""
    soldes = {}
    for ligne in lignes:
        code = ligne.code_lettrage
        if code:
            soldes[code] = soldes.get(code, Decimal(0)) + Decimal(str(ligne.debit or 0)) - Decimal(str(ligne.credit or 0))
    return {c for c, solde in soldes.items() if solde != 0}


def _lignes_code_actif(db: Session, societe_id: int, code: str):
    return (
        db.query(models.LigneEcriture, models.Ecriture)
        .options(joinedload(models.LigneEcriture.lettrages))
        .join(models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id)
        .join(models.LettrageComptable, models.LettrageComptable.ligne_ecriture_id == models.LigneEcriture.id)
        .filter(models.LettrageComptable.societe_id == societe_id, models.LettrageComptable.code == code,
                models.LettrageComptable.actif.is_(True), models.Ecriture.societe_id == societe_id)
        .all()
    )


def _ligne_comptable_out(ligne, ec, partiels=frozenset()):
    return {
        "ligne_id": ligne.id,
        "ecriture_id": ec.id,
        "numero_ecriture": ec.numero_ecriture,
        "date": ec.date.isoformat(),
        "journal": str(getattr(ec.journal, "value", ec.journal)),
        "reference": ec.reference,
        "libelle": ec.libelle,
        "ligne_libelle": ligne.libelle,
        "tiers": (getattr(ligne, "libelle_auxiliaire_snapshot", None) or ligne.libelle or "").strip() or None,
        "tiers_id": getattr(ligne, "tiers_id", None),
        "compte_auxiliaire": getattr(ligne, "compte_auxiliaire_snapshot", None),
        "compte": ligne.compte,
        "debit": float(ligne.debit or 0),
        "credit": float(ligne.credit or 0),
        "code_lettrage": ligne.code_lettrage,
        "date_lettrage": ligne.date_lettrage.isoformat() if ligne.date_lettrage else None,
        "lettrage_partiel": bool(ligne.code_lettrage and ligne.code_lettrage in partiels),
    }


@router.get("/comptable")
def lister_lignes_comptables(
    exercice: int = Query(...),
    compte: str = Query(..., min_length=3, max_length=10),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toutes les lignes définitives d'un compte tiers, sans pagination Journal."""
    _verifier_compte_demande(compte)
    rows = (
        db.query(models.LigneEcriture, models.Ecriture)
        .options(joinedload(models.LigneEcriture.lettrages))
        .join(models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id)
        .filter(
            models.Ecriture.societe_id == current_user["societe_id"],
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
            models.Ecriture.numero_ecriture.isnot(None),
            models.LigneEcriture.compte.like(f"{compte}%"),
        )
        .order_by(models.Ecriture.date, models.Ecriture.id, models.LigneEcriture.id)
        .all()
    )
    partiels = _codes_partiels([l for l, _ in rows])
    return [_ligne_comptable_out(l, e, partiels) for l, e in rows]


def _charger_lignes_a_lettrer(db: Session, societe_id: int, ids: List[int], existantes=(), partiel=False):
    ids_uniques = sorted(set(int(x) for x in ids))
    if len(ids_uniques) + len(existantes) < 2 or not ids_uniques:
        raise HTTPException(400, "Sélectionnez au moins deux lignes à lettrer")

    rows = (
        db.query(models.LigneEcriture, models.Ecriture)
        .options(joinedload(models.LigneEcriture.lettrages))
        .join(models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id)
        .filter(
            models.LigneEcriture.id.in_(ids_uniques),
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.est_validee.is_(True),
            models.Ecriture.numero_ecriture.isnot(None),
        )
        .all()
    )
    if len(rows) != len(ids_uniques):
        raise HTTPException(404, "Une ou plusieurs lignes comptables sont introuvables ou non définitives")
    if any(l.code_lettrage for l, _ in rows):
        raise HTTPException(409, "Une ou plusieurs lignes sont déjà lettrées")
    nouvelles = rows
    rows = list(existantes) + list(rows)

    comptes = {(l.compte or "").strip() for l, _ in rows}
    if len(comptes) != 1 or not _compte_lettrable(next(iter(comptes), "")):
        raise HTTPException(400, "Le lettrage doit porter sur un même compte tiers 3421/4411")

    exercices = {int(e.exercice) for _, e in rows}
    if len(exercices) != 1:
        raise HTTPException(400, "Le lettrage manuel doit porter sur un même exercice")
    exercice = next(iter(exercices))
    _verifier_exercice_modifiable(db, societe_id, exercice)

    cles_tiers = {_cle_tiers_ligne(l) for l, _ in rows}
    if "" in cles_tiers:
        raise HTTPException(
            400,
            "Tiers non identifié : renseignez le tiers sur les lignes du compte collectif avant lettrage.",
        )
    if len(cles_tiers) != 1:
        raise HTTPException(
            400,
            "Le lettrage doit concerner un seul client/fournisseur (même sous-compte ou même tiers).",
        )

    debit = sum(Decimal(str(l.debit or 0)) for l, _ in rows)
    credit = sum(Decimal(str(l.credit or 0)) for l, _ in rows)
    if debit != credit and not partiel:
        raise HTTPException(400, f"Sélection non équilibrée : débit {debit:.2f} / crédit {credit:.2f}. "
                                 "Cochez « lettrage partiel » pour un règlement partiel.")
    if partiel and (debit == 0 or credit == 0):
        raise HTTPException(400, "Un lettrage partiel associe au moins un débit et un crédit du même tiers.")
    return nouvelles, debit != credit


@router.post("/comptable/lettrer")
def lettrer_lignes_comptables(
    data: LettrageComptableIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    _verrouiller_generation_codes(db, sid)
    codes = _codes_comptables_utilises(db, sid)
    code = (data.code or _code_depuis_set(codes)).strip().upper()
    if not re.fullmatch(r"[A-Z]{3,10}", code):
        raise HTTPException(400, "Le code de lettrage doit contenir de 3 à 10 lettres.")
    existantes = []
    if code in codes:
        # Seul un lettrage partiel actif peut être complété ; un code soldé ou
        # délettré n'est jamais réutilisé.
        existantes = _lignes_code_actif(db, sid, code)
        if not existantes or code not in _codes_partiels([l for l, _ in existantes]):
            raise HTTPException(409, f"Le code {code} a déjà été utilisé")
    rows, reste_partiel = _charger_lignes_a_lettrer(db, sid, data.ligne_ids, existantes, data.partiel)

    maintenant = datetime.utcnow()
    for ligne, _ in rows:
        db.add(
            models.LettrageComptable(
                societe_id=sid,
                ligne_ecriture_id=ligne.id,
                code=code,
                date_lettrage=maintenant,
                created_by=current_user.get("id"),
                actif=True,
                partiel=reste_partiel,
            )
        )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if reste_partiel:
            raise HTTPException(409, "Lettrage partiel refusé par la base : appliquer la migration 130.") from exc
        raise
    return {"code": code, "nb": len(rows), "ligne_ids": [l.id for l, _ in rows], "partiel": reste_partiel}


@router.post("/comptable/delettrer/{code}")
def delettrer_lignes_comptables(
    code: str,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    rows = (
        db.query(models.LettrageComptable)
        .options(
            joinedload(models.LettrageComptable.ligne).joinedload(models.LigneEcriture.ecriture)
        )
        .filter_by(societe_id=sid, code=code.upper(), actif=True)
        .all()
    )
    if not rows:
        raise HTTPException(404, "Code de lettrage actif introuvable")

    exercices = {
        int(row.ligne.ecriture.exercice)
        for row in rows
        if row.ligne is not None and row.ligne.ecriture is not None
    }
    if not exercices:
        raise HTTPException(409, "Impossible d'identifier l'exercice du lettrage")
    for exercice in exercices:
        _verifier_exercice_modifiable(db, sid, exercice)

    maintenant = datetime.utcnow()
    for row in rows:
        row.actif = False
        row.date_delettrage = maintenant
        row.delettre_par = current_user.get("id")
    db.commit()
    return {"ok": True, "code": code.upper(), "nb": len(rows)}


@router.post("/comptable/auto")
def lettrage_comptable_auto(
    exercice: int = Query(...),
    compte: str = Query(..., min_length=3, max_length=10),
    tiers: Optional[str] = Query(None),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    _verifier_compte_demande(compte)
    _verifier_exercice_modifiable(db, sid, exercice)

    rows = (
        db.query(models.LigneEcriture, models.Ecriture)
        .options(joinedload(models.LigneEcriture.lettrages))
        .join(models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id)
        .filter(
            models.Ecriture.societe_id == sid,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
            models.Ecriture.numero_ecriture.isnot(None),
            models.LigneEcriture.compte.like(f"{compte}%"),
        )
        .order_by(models.Ecriture.date, models.Ecriture.id, models.LigneEcriture.id)
        .all()
    )
    rows = [(l, e) for l, e in rows if not l.code_lettrage]

    tiers_filtre = _normaliser_tiers(tiers)
    if tiers_filtre:
        rows = [
            (l, e)
            for l, e in rows
            if _normaliser_tiers(getattr(l, "libelle_auxiliaire_snapshot", None)) == tiers_filtre
            or (not getattr(l, "libelle_auxiliaire_snapshot", None) and _normaliser_tiers(l.libelle) == tiers_filtre)
        ]

    # Les nouvelles lignes collectives portent un auxiliaire natif. Les rares
    # historiques legacy restent consultables via le repli de _cle_tiers_ligne.
    groupes = {}
    for ligne, ec in rows:
        cle_tiers = _cle_tiers_ligne(ligne)
        if not cle_tiers:
            continue
        groupes.setdefault(((ligne.compte or "").strip(), cle_tiers), []).append((ligne, ec))

    _verrouiller_generation_codes(db, sid)
    codes = _codes_comptables_utilises(db, sid)
    maintenant = datetime.utcnow()
    resultats = []

    for _, items in groupes.items():
        debits = [(l, e) for l, e in items if Decimal(str(l.debit or 0)) > 0]
        credits = [(l, e) for l, e in items if Decimal(str(l.credit or 0)) > 0]
        credits_utilises = set()

        for ligne_debit, ecriture_debit in debits:
            montant = Decimal(str(ligne_debit.debit or 0)).quantize(Decimal("0.01"))
            candidats = [
                (ligne_credit, ecriture_credit)
                for ligne_credit, ecriture_credit in credits
                if ligne_credit.id not in credits_utilises
                and Decimal(str(ligne_credit.credit or 0)).quantize(Decimal("0.01")) == montant
            ]
            if not candidats:
                continue

            # En cas de montants identiques répétés, la date la plus proche est
            # le choix le moins ambigu ; l'utilisateur peut toujours délettrer.
            ligne_credit, _ = min(
                candidats,
                key=lambda x: abs((x[1].date - ecriture_debit.date).days),
            )
            code = _code_depuis_set(codes)
            codes.add(code)
            credits_utilises.add(ligne_credit.id)

            for ligne in (ligne_debit, ligne_credit):
                db.add(
                    models.LettrageComptable(
                        societe_id=sid,
                        ligne_ecriture_id=ligne.id,
                        code=code,
                        date_lettrage=maintenant,
                        created_by=current_user.get("id"),
                        actif=True,
                    )
                )
            resultats.append(
                {"code": code, "ligne_ids": [ligne_debit.id, ligne_credit.id], "montant": float(montant)}
            )

    db.commit()
    return {"nb": len(resultats), "lettrages": resultats}


def _prochain_code(db: Session, societe_id: int) -> str:
    """Génère un nouveau code d'au moins trois lettres ; historique inchangé."""
    # Récupérer tous les codes utilisés
    codes_f = db.query(models.Facture.code_lettrage).filter(
        models.Facture.societe_id == societe_id,
        models.Facture.code_lettrage.isnot(None)
    ).all()
    codes_r = db.query(models.Reglement.code_lettrage).filter(
        models.Reglement.societe_id == societe_id,
        models.Reglement.code_lettrage.isnot(None)
    ).all()
    codes = set(c[0] for c in codes_f + codes_r if c[0])

    # Générer séquence A..Z, AA..AZ, BA..BZ...
    import string
    lettres = string.ascii_uppercase
    # Simple séquence
    for l in lettres:
        if l not in codes:
            return l
    for l1 in lettres:
        for l2 in lettres:
            code = l1 + l2
            if code not in codes:
                return code
    return "ZZ"


# ── Lister factures et règlements d'un tiers ─────────────────────────────────
@router.get("/tiers/{tiers}")
def lister_tiers(
    tiers:    str,
    exercice: int           = Query(...),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    factures = db.query(models.Facture).options(
        joinedload(models.Facture.lignes)
    ).filter_by(
        societe_id=current_user["societe_id"],
        tiers=tiers,
    ).filter(
        models.Facture.exercice == exercice,
        models.Facture.statut != "annulee",
    ).order_by(models.Facture.date.desc()).all()

    reglements = db.query(models.Reglement).filter_by(
        societe_id=current_user["societe_id"],
        tiers=tiers,
    ).filter(
        func.extract('year', models.Reglement.date) == exercice
    ).order_by(models.Reglement.date.desc()).all()

    def total_ttc(f):
        return float(total_ventilation(ventilation_facture(f))["ttc"])

    return {
        "factures": [{
            "id":            f.id,
            "numero":        f.numero,
            "date":          str(f.date),
            "type":          f.type.value,
            "total_ttc":     total_ttc(f),
            "statut":        f.statut.value,
            "code_lettrage": f.code_lettrage,
        } for f in factures],
        "reglements": [{
            "id":            r.id,
            "date":          str(r.date),
            "montant":       r.montant,
            "mode":          r.mode,
            "reference":     r.reference,
            "facture_id":    r.facture_id,
            "code_lettrage": r.code_lettrage,
        } for r in reglements],
    }


# ── Lister tous les tiers avec factures ouvertes ─────────────────────────────
@router.get("/tiers")
def lister_tous_tiers(
    exercice: int = Query(...),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    rows = db.query(
        models.Facture.tiers,
        models.Facture.type,
        func.count(models.Facture.id).label("nb_factures"),
    ).filter(
        models.Facture.societe_id == current_user["societe_id"],
        models.Facture.exercice   == exercice,
        models.Facture.statut     != "annulee",
    ).group_by(models.Facture.tiers, models.Facture.type).all()

    return [{"tiers": r.tiers, "type": r.type.value, "nb_factures": r.nb_factures} for r in rows]


# ── Anciennes routes documentaires désactivées ────────────────────────────────
# Depuis COMPTA-FINAL, le lettrage a une seule source de vérité :
# ``lettrages_comptables``. Les anciennes routes qui écrivaient uniquement sur
# Facture/Reglement créeraient sinon un état différent du Grand Livre et du FEC.
def _route_legacy_desactivee():
    raise HTTPException(
        410,
        "Ancienne API désactivée : utilisez le lettrage comptable /api/lettrage/comptable.",
    )


@router.post("/lettrer")
def lettrer_legacy(
    facture_id: int,
    reglement_id: int,
    code: Optional[str] = None,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    _route_legacy_desactivee()


@router.post("/delettrer")
def delettrer_legacy(
    code: str,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    _route_legacy_desactivee()


@router.post("/auto/{tiers}")
def lettrage_auto_legacy(
    tiers: str,
    exercice: int = Query(...),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    _route_legacy_desactivee()


# Les anciennes routes de rapprochement hébergées historiquement dans ce router
# sont également coupées : le rapprochement 048 vit exclusivement sous
# /api/rapprochement et lie une ligne de relevé à une ligne comptable définitive.
@router.post("/rapprocher")
def rapprocher_legacy(
    ligne_id: int,
    reglement_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    # On conserve le contrôle tenant de l'ancienne route pendant la période de
    # compatibilité, puis on renvoie explicitement vers la nouvelle API.
    reglement = db.query(models.Reglement).filter_by(
        id=reglement_id, societe_id=current_user["societe_id"]
    ).first()
    if not reglement:
        raise HTTPException(404, "Règlement introuvable")
    raise HTTPException(410, "Ancienne API désactivée : utilisez /api/rapprochement.")


@router.post("/derap")
def derap_legacy(
    ligne_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    raise HTTPException(410, "Ancienne API désactivée : utilisez /api/rapprochement.")
