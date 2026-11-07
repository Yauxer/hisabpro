# -*- coding: utf-8 -*-
"""
Acomptes / avances — HisabPro.

Cycle : réception (client) ou versement (fournisseur) d'un acompte avant facturation,
comptabilisation (5141|5161 ↔ 4421 client, 3411 ↔ 5141|5161 fournisseur),
puis imputation sur une facture (4421 → 3421 ou 4411 → 3411) qui réduit son reste à payer.
"""
from datetime import datetime as dt, date as date_cls
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from schemas import _nombre_fini
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from auth import get_current_user, requiert_ecriture
import models
from services.compta_mapping_service import (
    trouver_tiers, compte_tiers, compte_tiers_facture, compte_tresorerie,
)
from services.tva_regles_service import qualification_valide, valider_tva
from services.commercial_numero_service import reserver_numero_commercial
from services.auxiliaire_service import rattacher_tiers_aux_lignes

router = APIRouter(prefix="/api/acomptes", tags=["acomptes"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class AcompteCreate(BaseModel):
    type:      str = "client"
    tiers:     str
    tiers_id:  Optional[int] = None
    date:      str
    montant:   float
    tva_applicable: bool = True
    taux_tva:  float = 20.0
    qualification_tva: str = "taxable"
    mode:      Literal["virement", "cheque", "especes", "effet", "carte", "prelevement", "autre"] = "virement"
    banque:    Optional[str] = None
    compte_bancaire_id: Optional[int] = None
    reference: Optional[str] = None
    date_echeance: Optional[date_cls] = None
    notes:     Optional[str] = None
    comptabiliser: bool = True

    @field_validator("montant", "taux_tva", mode="before")
    @classmethod
    def valider_nombre_fini(cls, valeur):
        return _nombre_fini(valeur)


class ImputationAcompteOut(BaseModel):
    id: int
    facture_id: int
    facture_numero: Optional[str] = None
    date_imputation: date_cls
    montant: float
    est_comptabilisee: bool = False
    statut: str = "active"
    date_annulation: Optional[dt] = None
    ecriture_id: Optional[int] = None
    ecriture_annulation_id: Optional[int] = None


class AcompteOut(BaseModel):
    id:                 int
    numero:             str
    type:               str
    tiers:              str
    tiers_id:           Optional[int] = None
    date:               date_cls
    exercice:           int
    montant:            float
    montant_impute:     float = 0.0
    montant_disponible: float = 0.0
    nb_factures_imputees: int = 0
    imputations:        List[ImputationAcompteOut] = []
    tva_applicable:     bool
    taux_tva:           float
    qualification_tva:  str = "taxable"
    mode:               str
    banque:             Optional[str] = None
    compte_bancaire_id: Optional[int] = None
    reference:          Optional[str]
    date_echeance:      Optional[date_cls] = None
    statut_paiement:    str = "encaisse"
    date_encaissement:  Optional[date_cls] = None
    statut:             str
    facture_id:         Optional[int]
    date_imputation:    Optional[date_cls] = None
    facture_numero:     Optional[str] = None
    est_comptabilisee:  bool
    est_imputee_compta: bool
    notes:              Optional[str]
    date_annulation:    Optional[dt] = None
    ecriture_annulation_id: Optional[int] = None

    class Config:
        from_attributes = True


class ImputerIn(BaseModel):
    facture_id: int
    montant: Optional[float] = None
    date_imputation: Optional[date_cls] = None
    comptabiliser: bool = True

    @field_validator("montant", mode="before")
    @classmethod
    def valider_montant_fini(cls, valeur):
        return None if valeur is None else _nombre_fini(valeur)


class StatutPaiementIn(BaseModel):
    statut: Literal["encaisse", "rejete"]
    date_operation: Optional[date_cls] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt(acompte, db):
    rows = db.query(models.ImputationAcompte).filter_by(
        societe_id=acompte.societe_id, acompte_id=acompte.id
    ).order_by(models.ImputationAcompte.date_imputation, models.ImputationAcompte.id).all()
    actives = [x for x in rows if getattr(x, "statut", "active") == "active"]
    total_impute = round(sum(float(x.montant or 0) for x in actives), 2)
    imputations = []
    for x in rows:
        numero = db.query(models.Facture.numero).filter_by(id=x.facture_id, societe_id=acompte.societe_id).scalar()
        imputations.append({
            "id": x.id, "facture_id": x.facture_id, "facture_numero": numero,
            "date_imputation": x.date_imputation, "montant": float(x.montant or 0),
            "est_comptabilisee": bool(x.est_comptabilisee),
            "statut": getattr(x, "statut", "active") or "active",
            "date_annulation": getattr(x, "date_annulation", None),
            "ecriture_id": getattr(x, "ecriture_id", None),
            "ecriture_annulation_id": getattr(x, "ecriture_annulation_id", None),
        })
    factures_uniques = {x.facture_id for x in actives}
    facture_numero = None
    if len(factures_uniques) == 1:
        fid = next(iter(factures_uniques))
        facture_numero = db.query(models.Facture.numero).filter_by(id=fid, societe_id=acompte.societe_id).scalar()
    return {
        **{c: getattr(acompte, c, None) for c in [
            "id", "numero", "type", "tiers", "tiers_id", "date", "exercice", "montant", "tva_applicable", "taux_tva", "qualification_tva", "mode",
            "banque", "compte_bancaire_id", "reference", "date_echeance", "statut_paiement", "date_encaissement", "statut", "facture_id", "date_imputation", "est_comptabilisee",
            "est_imputee_compta", "notes", "date_annulation", "ecriture_annulation_id"]},
        "facture_numero": facture_numero,
        "montant_impute": total_impute,
        "montant_disponible": round(max(float(acompte.montant or 0) - total_impute, 0.0), 2),
        "nb_factures_imputees": len(factures_uniques),
        "imputations": imputations,
    }


def _verifier_module_compta(db, societe_id):
    module = db.query(models.ModuleActif).filter_by(
        societe_id=societe_id, module="comptabilite", actif=True
    ).first()
    return module is not None


def _verifier_periode(db, societe_id, annee, quoi="cette opération"):
    """Refuse toute écriture sur un exercice clôturé."""
    from routers.cloture import exercice_est_clos
    if exercice_est_clos(db, societe_id, annee):
        raise HTTPException(423,
            f"Exercice {annee} clôturé définitivement : {quoi} est impossible. "
            "La correction doit être comptabilisée sur une période ouverte ultérieure.")


def _verifier_date_operation(db, societe_id, jour, quoi="cette opération"):
    try:
        from services.exercices_service import verifier_date_ecriture
        return verifier_date_ecriture(db, societe_id, jour, action="enregistrer")
    except ValueError as exc:
        msg = str(exc)
        status = 423 if "clôtur" in msg.lower() or "fermé" in msg.lower() else 409
        raise HTTPException(status, f"{quoi} : {msg}") from exc


def _compte_tresorerie_acompte(db, societe_id, acompte):
    compte_id = getattr(acompte, "compte_bancaire_id", None)
    if compte_id:
        cb = db.query(models.CompteBancaire).filter_by(
            id=compte_id, societe_id=societe_id, actif=True
        ).first()
        if not cb:
            raise HTTPException(422, "Le compte bancaire sélectionné est introuvable ou inactif.")
        return cb.compte_comptable or "5141"
    return compte_tresorerie(
        db, societe_id, mode=acompte.mode, banque=getattr(acompte, "banque", None)
    )


def _recalculer_statut_acompte(db, acompte):
    actives = db.query(models.ImputationAcompte).filter_by(
        societe_id=acompte.societe_id, acompte_id=acompte.id, statut="active"
    ).all()
    total = sum(float(x.montant or 0) for x in actives)
    if acompte.statut == "annule":
        return
    if total <= 0.01:
        acompte.statut = "disponible"
        acompte.facture_id = None
        acompte.date_imputation = None
        acompte.est_imputee_compta = False
        return
    acompte.statut = "impute" if total >= float(acompte.montant or 0) - 0.01 else "partiellement_impute"
    facture_ids = {x.facture_id for x in actives}
    acompte.facture_id = next(iter(facture_ids)) if len(facture_ids) == 1 else None
    acompte.date_imputation = max(x.date_imputation for x in actives)
    acompte.est_imputee_compta = all(bool(x.est_comptabilisee) for x in actives)


def _ecriture_reception(db, societe_id, acompte):
    """Écriture de réception (client) / versement (fournisseur) de l'acompte."""
    treso = _compte_tresorerie_acompte(db, societe_id, acompte)
    journal = "CA" if acompte.mode == "especes" else "BQ"
    if acompte.type == "client":
        libelle = f"Acompte client reçu — {acompte.numero} {acompte.tiers}"
        lignes = [
            models.LigneEcriture(compte=treso,  libelle="Trésorerie", debit=acompte.montant, credit=0),
            models.LigneEcriture(compte="4421", libelle=f"{acompte.tiers} — avances et acomptes reçus", debit=0, credit=acompte.montant),
        ]
    else:
        libelle = f"Acompte fournisseur versé — {acompte.numero} {acompte.tiers}"
        lignes = [
            models.LigneEcriture(compte="3411", libelle=f"{acompte.tiers} — avances et acomptes versés", debit=acompte.montant, credit=0),
            models.LigneEcriture(compte=treso,  libelle="Trésorerie", debit=0, credit=acompte.montant),
        ]
    rattacher_tiers_aux_lignes(
        db, societe_id, lignes,
        tiers_id=getattr(acompte, "tiers_id", None),
        nature="client" if acompte.type == "client" else "fournisseur",
    )
    date_ec = getattr(acompte, "date_encaissement", None) or acompte.date
    exercice = _verifier_date_operation(db, societe_id, date_ec, "Comptabilisation de cet acompte")
    ecriture = models.Ecriture(
        societe_id=societe_id, journal=journal, date=date_ec, date_piece=date_ec,
        libelle=libelle, reference=acompte.numero, exercice=exercice.annee,
        source="acompte", lignes=lignes,
    )
    db.add(ecriture)
    db.flush()
    acompte.est_comptabilisee = True
    return ecriture


def _ecriture_imputation(db, societe_id, acompte, facture, montant, date_imputation=None):
    """Écriture d'imputation : solde le compte d'attente vers le compte tiers."""
    compte_facture = compte_tiers_facture(db, societe_id, facture)
    if acompte.type == "client":
        libelle = f"Imputation acompte {acompte.numero} sur {facture.numero}"
        lignes = [
            models.LigneEcriture(compte="4421", libelle=f"{acompte.tiers} — avances et acomptes reçus", debit=montant, credit=0),
            models.LigneEcriture(compte=compte_facture, libelle=acompte.tiers, debit=0, credit=montant),
        ]
    else:
        libelle = f"Imputation acompte {acompte.numero} sur {facture.numero}"
        lignes = [
            models.LigneEcriture(compte=compte_facture, libelle=acompte.tiers, debit=montant, credit=0),
            models.LigneEcriture(compte="3411", libelle=f"{acompte.tiers} — avances et acomptes versés", debit=0, credit=montant),
        ]
    rattacher_tiers_aux_lignes(
        db, societe_id, lignes,
        tiers_id=getattr(acompte, "tiers_id", None) or getattr(facture, "tiers_id", None),
        nature="client" if acompte.type == "client" else "fournisseur",
    )
    date_ec = date_imputation or dt.now().date()
    exercice = _verifier_date_operation(db, societe_id, date_ec, "Imputation de cet acompte")
    ecriture = models.Ecriture(
        societe_id=societe_id, journal="OD", date=date_ec, date_piece=date_ec,
        libelle=libelle, reference=acompte.numero, exercice=exercice.annee,
        source="acompte", lignes=lignes,
    )
    db.add(ecriture)
    db.flush()
    return ecriture


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[AcompteOut])
def lister_acomptes(
    exercice:   int = Query(...),
    type:       Optional[str] = Query(None),
    statut:     Optional[str] = Query(None),
    tiers:      Optional[str] = Query(None),
    facture_id: Optional[int] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    q = db.query(models.Acompte).filter_by(societe_id=current_user["societe_id"]) \
        .filter(models.Acompte.exercice == exercice)
    if type:       q = q.filter(models.Acompte.type == type)
    if statut:     q = q.filter(models.Acompte.statut == statut)
    if tiers:      q = q.filter(models.Acompte.tiers == tiers)
    if facture_id:
        ids = db.query(models.ImputationAcompte.acompte_id).filter_by(
            societe_id=current_user["societe_id"], facture_id=facture_id
        )
        q = q.filter(models.Acompte.id.in_(ids))
    return [_fmt(a, db) for a in q.order_by(models.Acompte.date.desc()).all()]


@router.post("", response_model=AcompteOut, status_code=201)
def creer_acompte(
    data: AcompteCreate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    if data.montant <= 0:
        raise HTTPException(400, "Le montant de l'acompte doit être positif")
    if data.type not in ("client", "fournisseur"):
        raise HTTPException(400, "Type invalide (client ou fournisseur)")
    try:
        date_ac = date_cls.fromisoformat(data.date)
    except ValueError:
        raise HTTPException(400, "Date invalide, format attendu AAAA-MM-JJ")

    # Compatibilité avec les anciens clients API qui n'envoyaient que
    # ``tva_applicable``. Un 0 % n'est jamais conservé comme « taxable ».
    try:
        qualification = qualification_valide(data.qualification_tva)
        if not data.tva_applicable and qualification == "taxable":
            qualification = "exonere_sans_deduction"
        taux = 0.0 if qualification != "taxable" else data.taux_tva
        taux = valider_tva(date_ac, taux, qualification)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    tva_applicable = qualification == "taxable"

    est_vente = data.type == "client"
    tiers_obj = trouver_tiers(
        db, societe_id, tiers_id=data.tiers_id, nom=data.tiers, est_vente=est_vente
    )
    if data.tiers_id and not tiers_obj:
        raise HTTPException(422, "Le tiers sélectionné est introuvable ou incompatible avec le type d'acompte.")
    tiers_nom = tiers_obj.nom if tiers_obj else data.tiers.strip()
    compte_tiers_snapshot = compte_tiers(
        db, societe_id, est_vente=est_vente,
        tiers_id=(tiers_obj.id if tiers_obj else None), nom=tiers_nom,
    )

    exercice_obj = _verifier_date_operation(db, societe_id, date_ac, "Création de l'acompte")
    exercice = exercice_obj.annee
    if data.mode == "effet" and not data.date_echeance:
        raise HTTPException(422, "La date d'échéance est obligatoire pour un effet de commerce.")
    if data.date_echeance and data.date_echeance < date_ac:
        raise HTTPException(422, "La date d'échéance ne peut pas précéder la date de l'acompte.")

    banque_nom = (data.banque or "").strip() or None
    compte_bancaire_id = data.compte_bancaire_id
    if compte_bancaire_id:
        cb = db.query(models.CompteBancaire).filter_by(
            id=compte_bancaire_id, societe_id=societe_id, actif=True
        ).first()
        if not cb:
            raise HTTPException(422, "Le compte bancaire sélectionné est introuvable ou inactif.")
        banque_nom = cb.banque

    # Un chèque/effet n'est pas considéré comme encaissé tant que l'utilisateur
    # ne confirme pas son encaissement. Cela évite de rendre l'acompte disponible
    # et de mouvementer la banque trop tôt.
    en_attente = data.mode in {"cheque", "effet"}
    statut_paiement = "en_attente" if en_attente else "encaisse"
    date_encaissement = None if en_attente else date_ac

    # FACT-C / F-010 — réservation atomique PostgreSQL, scindée par société/exercice.
    # Elle remplace définitivement l’ancien schéma COUNT()+1, vulnérable aux créations concurrentes.
    numero = reserver_numero_commercial(db, societe_id, exercice, "acompte", "AC")

    acompte = models.Acompte(
        societe_id=societe_id, numero=numero, type=data.type, tiers=tiers_nom,
        tiers_id=(tiers_obj.id if tiers_obj else None), compte_tiers_snapshot=compte_tiers_snapshot,
        date=date_ac, exercice=exercice, montant=data.montant,
        tva_applicable=tva_applicable, taux_tva=taux, qualification_tva=qualification, mode=data.mode,
        banque=banque_nom, compte_bancaire_id=compte_bancaire_id, reference=data.reference,
        date_echeance=data.date_echeance, statut_paiement=statut_paiement,
        date_encaissement=date_encaissement, notes=data.notes,
    )
    db.add(acompte)
    db.flush()

    if data.comptabiliser and statut_paiement == "encaisse":
        if not _verifier_module_compta(db, societe_id):
            raise HTTPException(400, "Module Comptabilité inactif : impossible de comptabiliser l'acompte")
        _ecriture_reception(db, societe_id, acompte)

    db.commit()
    db.refresh(acompte)
    return _fmt(acompte, db)


@router.post("/{acompte_id}/comptabiliser")
def comptabiliser_acompte(
    acompte_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    acompte = db.query(models.Acompte).filter_by(
        id=acompte_id, societe_id=societe_id
    ).with_for_update().first()
    if not acompte:
        raise HTTPException(404, "Acompte introuvable")
    if acompte.statut == "annule":
        raise HTTPException(400, "Acompte annulé : comptabilisation impossible")
    if acompte.est_comptabilisee:
        raise HTTPException(400, "Acompte déjà comptabilisé")
    if getattr(acompte, "statut_paiement", "encaisse") != "encaisse":
        raise HTTPException(409, "Confirmez d'abord l'encaissement/paiement de cet acompte.")
    if not _verifier_module_compta(db, societe_id):
        raise HTTPException(400, "Module Comptabilité inactif")
    _ecriture_reception(db, societe_id, acompte)
    db.commit()
    return {"message": f"Acompte {acompte.numero} comptabilisé"}


@router.post("/{acompte_id}/imputer")
def imputer_acompte(
    acompte_id: int,
    data: ImputerIn,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Impute tout ou partie d'un acompte sur une facture (FACT.8)."""
    societe_id = current_user["societe_id"]
    # Verrouille l'acompte pendant le calcul du disponible : deux imputations
    # concurrentes ne peuvent pas consommer le même reliquat.
    acompte = db.query(models.Acompte).filter_by(
        id=acompte_id, societe_id=societe_id
    ).with_for_update().first()
    if not acompte:
        raise HTTPException(404, "Acompte introuvable")
    if acompte.statut == "annule":
        raise HTTPException(409, "Acompte annulé : imputation impossible")
    if getattr(acompte, "statut_paiement", "encaisse") != "encaisse":
        raise HTTPException(409, "Cet acompte n'est pas encore encaissé/payé : imputation impossible.")

    deja_impute = float(db.query(func.coalesce(func.sum(models.ImputationAcompte.montant), 0)).filter_by(
        societe_id=societe_id, acompte_id=acompte.id, statut="active"
    ).scalar() or 0)
    disponible = max(float(acompte.montant or 0) - deja_impute, 0.0)
    if disponible <= 0.01:
        raise HTTPException(409, "Cet acompte est déjà entièrement imputé")

    facture = db.query(models.Facture).filter_by(
        id=data.facture_id, societe_id=societe_id
    ).with_for_update().first()
    if not facture:
        raise HTTPException(404, "Facture introuvable")
    if not facture.est_validee or facture.est_proforma:
        raise HTTPException(409, "Seule une facture définitive validée peut recevoir un acompte")
    type_attendu = "vente" if acompte.type == "client" else "achat"
    if getattr(facture.type, "value", facture.type) != type_attendu:
        raise HTTPException(400, f"Un acompte {acompte.type} ne peut être imputé que sur une facture de {type_attendu}")
    meme_tiers = (
        bool(getattr(acompte, "tiers_id", None) and getattr(facture, "tiers_id", None)
             and acompte.tiers_id == facture.tiers_id)
        or (not getattr(acompte, "tiers_id", None) and facture.tiers == acompte.tiers)
    )
    if not meme_tiers:
        raise HTTPException(400, f"Tiers différents : acompte de « {acompte.tiers} », facture de « {facture.tiers} »")

    from routers.factures import _situation_paiement_facture
    situation = _situation_paiement_facture(db, societe_id, facture)
    if situation["est_solde"]:
        raise HTTPException(409, "Cette facture est déjà soldée")
    montant = min(disponible, situation["solde_restant"]) if data.montant is None else float(data.montant or 0)
    if montant <= 0:
        raise HTTPException(422, "Le montant à imputer doit être strictement positif")
    if montant > disponible + 0.01:
        raise HTTPException(409, f"Imputation impossible : seulement {disponible:.2f} MAD restent disponibles sur l'acompte")
    if montant > situation["solde_restant"] + 0.01:
        raise HTTPException(409, f"Imputation impossible : reste à payer de la facture {situation['solde_restant']:.2f} MAD")

    date_imp = data.date_imputation or dt.now().date()
    _verifier_date_operation(db, societe_id, date_imp, "Imputation de cet acompte")
    if date_imp < acompte.date:
        raise HTTPException(422, "La date d'imputation ne peut pas précéder la date de l'acompte")
    if date_imp < facture.date:
        raise HTTPException(422, "La date d'imputation ne peut pas précéder la date de facture")

    row = models.ImputationAcompte(
        societe_id=societe_id, acompte_id=acompte.id, facture_id=facture.id,
        date_imputation=date_imp, montant=round(montant, 2), est_comptabilisee=False,
    )
    db.add(row)
    db.flush()
    if data.comptabiliser:
        if not _verifier_module_compta(db, societe_id):
            raise HTTPException(400, "Module Comptabilité inactif : impossible de comptabiliser l'imputation")
        ecriture = _ecriture_imputation(db, societe_id, acompte, facture, montant, date_imp)
        row.est_comptabilisee = True
        row.ecriture_id = ecriture.id

    _recalculer_statut_acompte(db, acompte)
    total_apres = deja_impute + montant
    db.commit()
    return {
        "message": f"{montant:.2f} MAD de l'acompte {acompte.numero} imputés sur {facture.numero}",
        "montant_impute": round(total_apres, 2),
        "montant_disponible": round(max(float(acompte.montant or 0) - total_apres, 0.0), 2),
        "statut": acompte.statut,
    }


@router.get("/{acompte_id}/factures-imputables")
def factures_imputables(
    acompte_id: int,
    current_user=Depends(get_current_user),
    db: Session=Depends(get_db),
):
    """Factures ouvertes du même tiers, tous exercices confondus.

    FACT-G supprime la dépendance au seul exercice affiché dans l'interface :
    un acompte de N peut parfaitement être imputé en N+1 sur une période ouverte.
    """
    societe_id = current_user["societe_id"]
    acompte = db.query(models.Acompte).filter_by(id=acompte_id, societe_id=societe_id).first()
    if not acompte:
        raise HTTPException(404, "Acompte introuvable")
    type_attendu = "vente" if acompte.type == "client" else "achat"
    q = db.query(models.Facture).filter(
        models.Facture.societe_id == societe_id,
        models.Facture.est_validee == True,  # noqa: E712
        models.Facture.est_proforma == False,  # noqa: E712
    ).order_by(models.Facture.date.desc(), models.Facture.id.desc())
    out = []
    from routers.factures import _situation_paiement_facture
    for facture in q.all():
        if getattr(facture.type, "value", facture.type) != type_attendu:
            continue
        meme_tiers = bool(
            acompte.tiers_id and getattr(facture, "tiers_id", None) and acompte.tiers_id == facture.tiers_id
        ) or (not acompte.tiers_id and facture.tiers == acompte.tiers)
        if not meme_tiers:
            continue
        situation = _situation_paiement_facture(db, societe_id, facture)
        if situation["solde_restant"] <= 0.01:
            continue
        out.append({
            "id": facture.id, "numero": facture.numero, "date": facture.date,
            "exercice": facture.exercice, "total_ttc": situation["total_ttc"],
            "solde_restant": situation["solde_restant"],
        })
    return out


@router.post("/{acompte_id}/statut-paiement")
def changer_statut_paiement(
    acompte_id: int,
    data: StatutPaiementIn,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    """Confirme l'encaissement/paiement d'un chèque/effet ou son rejet."""
    societe_id = current_user["societe_id"]
    acompte = db.query(models.Acompte).filter_by(
        id=acompte_id, societe_id=societe_id
    ).with_for_update().first()
    if not acompte:
        raise HTTPException(404, "Acompte introuvable")
    if acompte.statut == "annule":
        raise HTTPException(409, "Acompte annulé.")
    if acompte.mode not in {"cheque", "effet"}:
        raise HTTPException(409, "Ce suivi d'encaissement est réservé aux chèques et effets.")
    if acompte.statut_paiement == data.statut:
        return {"message": "Statut déjà appliqué"}

    jour = data.date_operation or date_cls.today()
    exercice = _verifier_date_operation(db, societe_id, jour, "Mise à jour du paiement de l'acompte")
    if data.statut == "rejete":
        nb_imp = db.query(models.ImputationAcompte).filter_by(
            societe_id=societe_id, acompte_id=acompte.id, statut="active"
        ).count()
        if nb_imp:
            raise HTTPException(409, "Cet acompte a déjà été imputé : annulez d'abord ses imputations.")
        # Compatibilité legacy : si une écriture avait déjà été créée, on la
        # contrepassse au lieu de la supprimer.
        if acompte.est_comptabilisee:
            original = db.query(models.Ecriture).filter(
                models.Ecriture.societe_id == societe_id,
                models.Ecriture.source == "acompte",
                models.Ecriture.reference == acompte.numero,
            ).order_by(models.Ecriture.id.asc()).first()
            if original:
                _ = original.lignes
                db.add(models.Ecriture(
                    societe_id=societe_id, journal=original.journal, date=jour, date_piece=jour,
                    libelle=f"Rejet acompte {acompte.numero} — {acompte.tiers}",
                    reference=f"REJET-{acompte.numero}"[:100], exercice=exercice.annee, source="acompte",
                    lignes=[models.LigneEcriture(
                        compte=l.compte, libelle=f"Rejet {l.libelle or acompte.numero}",
                        debit=l.credit, credit=l.debit,
                        tiers_id=getattr(l, "tiers_id", None),
                        nature_auxiliaire=getattr(l, "nature_auxiliaire", None),
                        compte_auxiliaire_snapshot=getattr(l, "compte_auxiliaire_snapshot", None),
                        libelle_auxiliaire_snapshot=getattr(l, "libelle_auxiliaire_snapshot", None),
                    ) for l in original.lignes],
                ))
        acompte.statut_paiement = "rejete"
        acompte.date_encaissement = None
        # L'écriture éventuelle vient d'être contrepassée : l'acompte n'est plus
        # comptabilisé dans son état courant. Une ré-acceptation future générera
        # une nouvelle écriture d'encaissement/paiement au lieu de réutiliser
        # silencieusement l'ancienne.
        acompte.est_comptabilisee = False
        db.commit()
        return {"message": "Acompte marqué rejeté"}

    # Encaissement / paiement effectif.
    acompte.statut_paiement = "encaisse"
    acompte.date_encaissement = jour
    if not acompte.est_comptabilisee:
        if not _verifier_module_compta(db, societe_id):
            raise HTTPException(400, "Module Comptabilité inactif : impossible de comptabiliser l'encaissement.")
        _ecriture_reception(db, societe_id, acompte)
    db.commit()
    return {"message": "Encaissement/paiement confirmé"}


@router.post("/{acompte_id}/imputations/{imputation_id}/annuler")
def annuler_imputation_acompte(
    acompte_id: int,
    imputation_id: int,
    date_annulation: Optional[date_cls] = Query(None),
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    """Annule une mauvaise imputation sans supprimer son historique."""
    societe_id = current_user["societe_id"]
    acompte = db.query(models.Acompte).filter_by(
        id=acompte_id, societe_id=societe_id
    ).with_for_update().first()
    if not acompte:
        raise HTTPException(404, "Acompte introuvable")
    row = db.query(models.ImputationAcompte).filter_by(
        id=imputation_id, acompte_id=acompte.id, societe_id=societe_id
    ).with_for_update().first()
    if not row:
        raise HTTPException(404, "Imputation introuvable")
    if getattr(row, "statut", "active") == "annulee":
        return {"message": "Imputation déjà annulée", "ecriture_annulation_id": row.ecriture_annulation_id}

    jour = date_annulation or date_cls.today()
    exercice = _verifier_date_operation(db, societe_id, jour, "Annulation de l'imputation")
    ecriture_annulation = None
    if row.est_comptabilisee:
        original = None
        if getattr(row, "ecriture_id", None):
            original = db.query(models.Ecriture).filter_by(
                id=row.ecriture_id, societe_id=societe_id
            ).first()
        if original is None:
            facture = db.query(models.Facture).filter_by(id=row.facture_id, societe_id=societe_id).first()
            original = db.query(models.Ecriture).filter(
                models.Ecriture.societe_id == societe_id,
                models.Ecriture.source == "acompte",
                models.Ecriture.reference == acompte.numero,
                models.Ecriture.libelle.ilike(f"%{getattr(facture, 'numero', '')}%"),
            ).order_by(models.Ecriture.id.asc()).first()
        if not original:
            raise HTTPException(409, "Écriture d'imputation d'origine introuvable : annulation bloquée.")
        _ = original.lignes
        ecriture_annulation = models.Ecriture(
            societe_id=societe_id, journal="OD", date=jour, date_piece=jour,
            libelle=f"Annulation imputation acompte {acompte.numero}",
            reference=f"ANN-IMP-{row.id}-{acompte.numero}"[:100], exercice=exercice.annee, source="acompte",
            lignes=[models.LigneEcriture(
                compte=l.compte, libelle=f"Annulation {l.libelle or acompte.numero}",
                debit=l.credit, credit=l.debit,
                tiers_id=getattr(l, "tiers_id", None),
                nature_auxiliaire=getattr(l, "nature_auxiliaire", None),
                compte_auxiliaire_snapshot=getattr(l, "compte_auxiliaire_snapshot", None),
                libelle_auxiliaire_snapshot=getattr(l, "libelle_auxiliaire_snapshot", None),
            ) for l in original.lignes],
        )
        db.add(ecriture_annulation)
        db.flush()

    row.statut = "annulee"
    row.date_annulation = dt.now()
    row.annulee_par = current_user.get("id")
    row.ecriture_annulation_id = ecriture_annulation.id if ecriture_annulation else None
    _recalculer_statut_acompte(db, acompte)
    db.commit()
    return {"message": "Imputation annulée", "ecriture_annulation_id": row.ecriture_annulation_id}


@router.patch("/{acompte_id}")
def modifier_acompte(
    acompte_id: int,
    data: dict,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Annulation ou modification des notes. Un acompte imputé ne peut plus être annulé."""
    acompte = db.query(models.Acompte).filter_by(
        id=acompte_id, societe_id=current_user["societe_id"]).first()
    if not acompte:
        raise HTTPException(404, "Acompte introuvable")

    if data.get("statut") == "annule":
        raise HTTPException(409,
            "Utilisez l'action dédiée « Annuler l'acompte » afin que la contrepassation et la piste d'audit soient automatiques.")
    if "notes" in data:
        acompte.notes = data["notes"]
    db.commit()
    return {"message": "Acompte mis à jour"}


@router.post("/{acompte_id}/annuler")
def annuler_acompte(
    acompte_id: int,
    date_annulation: Optional[date_cls] = Query(None),
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Annule un acompte non imputé, sans effacer son historique.

    Si l'encaissement/versement avait déjà été comptabilisé, HisabPro crée la
    contrepassation automatiquement sur la date ouverte choisie. Une avance déjà
    imputée sur une facture reste bloquée : son annulation nécessite d'abord un
    traitement correctif des imputations concernées.
    """
    societe_id = current_user["societe_id"]
    acompte = db.query(models.Acompte).filter_by(
        id=acompte_id, societe_id=societe_id
    ).with_for_update().first()
    if not acompte:
        raise HTTPException(404, "Acompte introuvable")
    if acompte.statut == "annule":
        return {"message": "Acompte déjà annulé", "ecriture_annulation_id": acompte.ecriture_annulation_id}

    if db.query(models.ImputationAcompte).filter_by(
        societe_id=societe_id, acompte_id=acompte.id, statut="active"
    ).count() > 0:
        raise HTTPException(409,
            "Acompte déjà imputé, même partiellement : annulez/corrigez d'abord ses imputations sur facture.")

    jour = date_annulation or dt.now().date()
    try:
        from services.exercices_service import verifier_date_ecriture
        exercice_annulation = verifier_date_ecriture(db, societe_id, jour, action="enregistrer")
    except ValueError as exc:
        msg = str(exc)
        status = 423 if "clôtur" in msg.lower() or "fermé" in msg.lower() else 409
        raise HTTPException(status, msg) from exc

    ecriture_annulation = None
    if acompte.est_comptabilisee:
        original = db.query(models.Ecriture).filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.source == "acompte",
            models.Ecriture.reference == acompte.numero,
        ).order_by(models.Ecriture.id.asc()).first()
        if not original:
            raise HTTPException(409,
                "Écriture comptable d'origine de l'acompte introuvable : annulation bloquée.")
        _ = original.lignes
        ecriture_annulation = models.Ecriture(
            societe_id=societe_id,
            journal=original.journal,
            date=jour,
            date_piece=jour,
            libelle=f"Annulation acompte {acompte.numero} — {acompte.tiers}",
            reference=f"ANN-{acompte.numero}"[:100],
            exercice=exercice_annulation.annee,
            source="acompte",
            lignes=[
                models.LigneEcriture(
                    compte=l.compte,
                    libelle=f"Annulation {l.libelle or acompte.numero}",
                    debit=l.credit,
                    credit=l.debit,
                    tiers_id=getattr(l, "tiers_id", None),
                    nature_auxiliaire=getattr(l, "nature_auxiliaire", None),
                    compte_auxiliaire_snapshot=getattr(l, "compte_auxiliaire_snapshot", None),
                    libelle_auxiliaire_snapshot=getattr(l, "libelle_auxiliaire_snapshot", None),
                ) for l in original.lignes
            ],
        )
        db.add(ecriture_annulation)
        db.flush()

    acompte.statut = "annule"
    acompte.date_annulation = dt.now()
    acompte.annule_par = current_user.get("id")
    acompte.ecriture_annulation_id = ecriture_annulation.id if ecriture_annulation else None
    db.commit()
    return {
        "message": "Acompte annulé",
        "ecriture_annulation_id": acompte.ecriture_annulation_id,
    }


@router.delete("/{acompte_id}", status_code=204)
def supprimer_acompte(
    acompte_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    acompte = db.query(models.Acompte).filter_by(
        id=acompte_id, societe_id=current_user["societe_id"]).first()
    if not acompte:
        raise HTTPException(404, "Acompte introuvable")
    raise HTTPException(409,
        "Un acompte numéroté ne se supprime pas afin de préserver la séquence documentaire. "
        "Utilisez l'action « Annuler l'acompte ».")
