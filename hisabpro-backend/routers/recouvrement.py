from datetime import date
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session, joinedload

from database import get_db
from auth import get_current_user, requiert_ecriture
import models
from services.recouvrement_service import construire_situation

router = APIRouter(prefix="/api/recouvrement", tags=["recouvrement"])


def _montant_promis_valide(value):
    if value is not None:
        if isinstance(value, bool):
            raise ValueError("Le montant promis doit être un montant, pas un booléen")
        try:
            montant = float(value)
        except (ValueError, TypeError, OverflowError):
            raise ValueError("Le montant promis doit être numérique")
        if not math.isfinite(montant) or montant <= 0:
            raise ValueError("Le montant promis doit être fini et strictement positif")
    return value


class RelanceCreate(BaseModel):
    facture_id: int
    niveau: int = 1
    date_relance: date = Field(default_factory=date.today)
    canal: str = "email"
    commentaire: Optional[str] = None
    date_promesse_reglement: Optional[date] = None
    montant_promis: Optional[float] = None
    prochaine_relance: Optional[date] = None

    @field_validator("niveau")
    @classmethod
    def niveau_valide(cls, value):
        if value not in (1, 2, 3):
            raise ValueError("Le niveau de relance doit être 1, 2 ou 3")
        return value

    @field_validator("canal")
    @classmethod
    def canal_valide(cls, value):
        if value not in {"email", "telephone", "courrier", "whatsapp", "autre"}:
            raise ValueError("Canal de relance invalide")
        return value

    @field_validator("montant_promis", mode="before")
    @classmethod
    def montant_valide(cls, value):
        return _montant_promis_valide(value)


class RelanceUpdate(BaseModel):
    niveau: Optional[int] = None
    canal: Optional[str] = None
    commentaire: Optional[str] = None
    date_promesse_reglement: Optional[date] = None
    montant_promis: Optional[float] = None
    prochaine_relance: Optional[date] = None
    statut: Optional[str] = None

    @field_validator("montant_promis", mode="before")
    @classmethod
    def montant_valide(cls, value):
        return _montant_promis_valide(value)

    @field_validator("niveau")
    @classmethod
    def niveau_valide(cls, value):
        if value is not None and value not in (1, 2, 3):
            raise ValueError("Le niveau de relance doit être 1, 2 ou 3")
        return value

    @field_validator("canal")
    @classmethod
    def canal_valide(cls, value):
        if value is not None and value not in {"email", "telephone", "courrier", "whatsapp", "autre"}:
            raise ValueError("Canal de relance invalide")
        return value

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, value):
        if value is not None and value not in {"effectuee", "annulee"}:
            raise ValueError("Statut de relance invalide")
        return value


@router.get("/situation")
def situation_recouvrement(
    exercice: int = Query(...),
    date_reference: Optional[date] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return construire_situation(
        db,
        current_user["societe_id"],
        exercice,
        date_reference=date_reference,
    )


@router.get("/relances")
def lister_relances(
    facture_id: Optional[int] = Query(None),
    exercice: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(models.RelanceRecouvrement).options(
        joinedload(models.RelanceRecouvrement.facture)
    ).join(
        models.Facture, models.Facture.id == models.RelanceRecouvrement.facture_id
    ).filter(models.RelanceRecouvrement.societe_id == current_user["societe_id"])
    if facture_id is not None:
        q = q.filter(models.RelanceRecouvrement.facture_id == facture_id)
    if exercice is not None:
        q = q.filter(models.Facture.exercice == exercice)
    rows = q.order_by(
        models.RelanceRecouvrement.date_relance.desc(),
        models.RelanceRecouvrement.id.desc(),
    ).all()
    return [_relance_out(r, r.facture) for r in rows]


@router.post("/relances", status_code=201)
def creer_relance(
    data: RelanceCreate,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    facture = db.query(models.Facture).filter_by(
        id=data.facture_id,
        societe_id=current_user["societe_id"],
    ).first()
    if not facture:
        raise HTTPException(404, "Facture introuvable")
    if getattr(facture.type, "value", facture.type) != "vente":
        raise HTTPException(422, "Les relances de recouvrement sont réservées aux factures clients")
    if not facture.est_validee or facture.est_proforma:
        raise HTTPException(409, "Seule une facture client validée peut faire l'objet d'une relance")

    situation = construire_situation(db, current_user["societe_id"], facture.exercice)
    ligne = next((x for x in situation["factures"] if x["id"] == facture.id), None)
    if ligne and ligne['reste_du'] is None:
        raise HTTPException(409, ligne.get('ras_anomalie') or 'Solde indéterminable : relance non enregistrée')
    if not ligne or ligne["reste_du"] <= 0.01:
        raise HTTPException(409, "Cette facture est déjà soldée : aucune relance n'est nécessaire")
    if data.montant_promis is not None and data.montant_promis > ligne["reste_du"] + 0.01:
        raise HTTPException(422, "Le montant promis ne peut pas dépasser le reste à payer")
    if data.date_promesse_reglement and data.date_promesse_reglement < data.date_relance:
        raise HTTPException(422, "La date de promesse ne peut pas précéder la relance")
    if data.prochaine_relance and data.prochaine_relance <= data.date_relance:
        raise HTTPException(422, "La prochaine relance doit être postérieure à la relance courante")

    row = models.RelanceRecouvrement(
        societe_id=current_user["societe_id"],
        facture_id=facture.id,
        niveau=data.niveau,
        date_relance=data.date_relance,
        canal=data.canal,
        commentaire=data.commentaire,
        date_promesse_reglement=data.date_promesse_reglement,
        montant_promis=data.montant_promis,
        prochaine_relance=data.prochaine_relance,
        created_by=current_user.get("id"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _relance_out(row)


@router.patch("/relances/{relance_id}")
def modifier_relance(
    relance_id: int,
    data: RelanceUpdate,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    row = db.query(models.RelanceRecouvrement).filter_by(
        id=relance_id,
        societe_id=current_user["societe_id"],
    ).first()
    if not row:
        raise HTTPException(404, "Relance introuvable")

    values = data.model_dump(exclude_unset=True)
    niveau = values.get("niveau", row.niveau)
    canal = values.get("canal", row.canal)
    statut = values.get("statut", row.statut)
    commentaire = values.get("commentaire", row.commentaire)
    date_promesse = values.get("date_promesse_reglement", row.date_promesse_reglement)
    montant_promis = values.get("montant_promis", row.montant_promis)
    prochaine = values.get("prochaine_relance", row.prochaine_relance)

    if niveau not in (1, 2, 3):
        raise HTTPException(422, "Le niveau de relance doit être 1, 2 ou 3")
    if canal not in {"email", "telephone", "courrier", "whatsapp", "autre"}:
        raise HTTPException(422, "Canal de relance invalide")
    if statut not in {"effectuee", "annulee"}:
        raise HTTPException(422, "Statut de relance invalide")
    if montant_promis is not None and (not math.isfinite(float(montant_promis)) or float(montant_promis) <= 0):
        raise HTTPException(422, "Le montant promis doit être fini et strictement positif")
    if date_promesse and date_promesse < row.date_relance:
        raise HTTPException(422, "La date de promesse ne peut pas précéder la relance")
    if prochaine and prochaine <= row.date_relance:
        raise HTTPException(422, "La prochaine relance doit être postérieure à la relance courante")

    # La promesse conserve le contexte du contact historique. Un paiement
    # ultérieur ne doit pas empêcher l'annulation du suivi ou une correction
    # de commentaire ; seule une nouvelle promesse se compare au solde actuel.
    if "montant_promis" in values and montant_promis is not None:
        facture = db.query(models.Facture).filter_by(
            id=row.facture_id, societe_id=current_user["societe_id"]
        ).first()
        if facture:
            situation = construire_situation(db, current_user["societe_id"], facture.exercice)
            ligne = next((x for x in situation["factures"] if x["id"] == facture.id), None)
            if not ligne:
                raise HTTPException(409, "Cette facture est déjà soldée")
            if ligne['reste_du'] is None:
                raise HTTPException(409, ligne.get('ras_anomalie') or 'Solde indéterminable : promesse non enregistrée')
            if float(montant_promis) > ligne["reste_du"] + 0.01:
                raise HTTPException(422, "Le montant promis ne peut pas dépasser le reste à payer")

    row.niveau = niveau
    row.canal = canal
    row.statut = statut
    row.commentaire = commentaire
    row.date_promesse_reglement = date_promesse
    row.montant_promis = montant_promis
    row.prochaine_relance = prochaine
    db.commit()
    db.refresh(row)
    return _relance_out(row)


def _relance_out(row, facture=None):
    facture = facture or getattr(row, "facture", None)
    return {
        "id": row.id,
        "facture_id": row.facture_id,
        "facture_numero": getattr(facture, "numero", None),
        "tiers": getattr(facture, "tiers", None),
        "niveau": row.niveau,
        "date_relance": row.date_relance,
        "canal": row.canal,
        "commentaire": row.commentaire,
        "date_promesse_reglement": row.date_promesse_reglement,
        "montant_promis": float(row.montant_promis) if row.montant_promis is not None else None,
        "prochaine_relance": row.prochaine_relance,
        "statut": row.statut,
        "created_by": row.created_by,
        "created_at": row.created_at,
    }
