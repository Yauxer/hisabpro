from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth import get_current_user, requiert_ecriture
import models, schemas

router = APIRouter(prefix="/api/banques", tags=["banques"])


@router.get("", response_model=List[schemas.CompteBancaireOut])
def lister_comptes(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    return db.query(models.CompteBancaire).filter_by(
        societe_id=current_user["societe_id"], actif=True
    ).order_by(models.CompteBancaire.banque).all()


@router.post("", response_model=schemas.CompteBancaireOut, status_code=201)
def creer_compte(
    data: schemas.CompteBancaireCreate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    compte = models.CompteBancaire(
        societe_id=current_user["societe_id"],
        **data.model_dump()
    )
    db.add(compte)
    db.commit()
    db.refresh(compte)
    return compte


@router.patch("/{compte_id}", response_model=schemas.CompteBancaireOut)
def modifier_compte(
    compte_id: int,
    data: schemas.CompteBancaireUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    compte = db.query(models.CompteBancaire).filter_by(
        id=compte_id, societe_id=current_user["societe_id"]
    ).first()
    if not compte:
        raise HTTPException(404, "Compte bancaire introuvable")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(compte, k, v)
    db.commit()
    db.refresh(compte)
    return compte


@router.delete("/{compte_id}", status_code=204)
def supprimer_compte(
    compte_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    compte = db.query(models.CompteBancaire).filter_by(
        id=compte_id, societe_id=current_user["societe_id"]
    ).first()
    if not compte:
        raise HTTPException(404, "Compte bancaire introuvable")
    compte.actif = False
    db.commit()
