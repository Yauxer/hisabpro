from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session, joinedload

from database import get_db
from auth import get_current_user, requiert_ecriture
import models
from routers.cloture import exercice_est_clos
from routers.factures import _calc_totaux, _situation_paiement_facture
from services.echeancier_service import (
    echeances_persistantes_ou_defaut,
    repartition_fifo,
    remplacer_echeancier_db, supprimer_echeancier_db,
    montant_echeance_fini,
)

router = APIRouter(prefix="/api/factures", tags=["echeanciers"])


class EcheanceIn(BaseModel):
    date_echeance: date
    montant: float
    libelle: Optional[str] = None

    @field_validator("montant", mode="before")
    @classmethod
    def valider_montant(cls, valeur):
        return montant_echeance_fini(valeur)


class EcheancierIn(BaseModel):
    echeances: List[EcheanceIn]


def _facture(db: Session, societe_id: int, facture_id: int, verrouiller: bool = False):
    # PostgreSQL n'autorise pas FOR UPDATE sur les côtés nullable produits par
    # certains joinedload(). On verrouille donc la facture seule en écriture ;
    # ses lignes/échéances seront chargées ensuite par la session si nécessaire.
    if verrouiller:
        row = db.query(models.Facture).filter_by(
            id=facture_id, societe_id=societe_id
        ).with_for_update().first()
    else:
        row = db.query(models.Facture).options(
            joinedload(models.Facture.lignes),
            joinedload(models.Facture.echeances),
        ).filter_by(id=facture_id, societe_id=societe_id).first()
    if not row:
        raise HTTPException(404, "Facture introuvable")
    if row.est_proforma:
        raise HTTPException(409, "Une proforma ne porte pas d'échéancier de règlement définitif.")
    return row


def _sortie(db: Session, societe_id: int, facture, date_reference: Optional[date] = None):
    total_ht, _, total_ttc, _, _ = _calc_totaux(facture)
    situation = _situation_paiement_facture(db, societe_id, facture)
    rows = echeances_persistantes_ou_defaut(facture, total_ttc)
    calc = repartition_fifo(rows, situation["total_effectif"], date_reference=date_reference)
    return {
        "facture_id": facture.id,
        "numero": facture.numero,
        "tiers": facture.tiers,
        "total_ttc": round(float(total_ttc), 2),
        "total_ht": round(float(total_ht), 2),
        "total_impute": round(float(situation["total_effectif"]), 2),
        "reste_du": round(float(situation["solde_restant"]), 2),
        "personnalise": bool(getattr(facture, "echeances", None)),
        **calc,
    }


@router.get("/{facture_id}/echeancier")
def lire_echeancier(
    facture_id: int,
    date_reference: Optional[date] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    facture = _facture(db, current_user["societe_id"], facture_id)
    return _sortie(db, current_user["societe_id"], facture, date_reference)


@router.put("/{facture_id}/echeancier")
def modifier_echeancier(
    facture_id: int,
    data: EcheancierIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    facture = _facture(db, societe_id, facture_id, verrouiller=True)
    if exercice_est_clos(db, societe_id, facture.exercice):
        raise HTTPException(423, f"Exercice {facture.exercice} clôturé : échéancier non modifiable.")

    situation = _situation_paiement_facture(db, societe_id, facture)
    if facture.est_validee and situation["total_effectif"] > 0.01:
        raise HTTPException(
            409,
            "L'échéancier d'une facture ayant déjà reçu un règlement, un acompte, un avoir ou une RAS est figé."
        )

    _, _, total_ttc, _, _ = _calc_totaux(facture)
    try:
        if not data.echeances:
            supprimer_echeancier_db(db, societe_id, facture)
        else:
            remplacer_echeancier_db(db, societe_id, facture, data.echeances, total_ttc)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    db.commit()
    db.refresh(facture)
    return _sortie(db, societe_id, facture)
