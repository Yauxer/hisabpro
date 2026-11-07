# -*- coding: utf-8 -*-
"""Plan comptable propre à chaque société — Patch 055."""
from typing import Optional
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user, requiert_admin
from database import get_db
import models
from services.plan_comptable import assurer_plan_societe
from services.utilisateurs_acces_service import verrouiller_administration, verifier_admin_apres_verrou

router = APIRouter(prefix="/api/plan-comptable", tags=["plan-comptable"])

_NUM_RE = re.compile(r"^[0-9]{4,10}$")


class CompteCreate(BaseModel):
    numero: str = Field(..., min_length=5, max_length=10)
    libelle: str = Field(..., min_length=2, max_length=300)
    type_compte: Optional[str] = Field(None, max_length=10)

    @field_validator("libelle", mode="before")
    @classmethod
    def libelle_requis(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("numero")
    @classmethod
    def numero_valide(cls, v):
        v = str(v or "").strip()
        if not _NUM_RE.fullmatch(v):
            raise ValueError("Le numéro doit contenir uniquement 5 à 10 chiffres.")
        return v


class CompteUpdate(BaseModel):
    libelle: Optional[str] = Field(None, min_length=2, max_length=300)
    actif: Optional[bool] = None

    @field_validator("libelle", mode="before")
    @classmethod
    def libelle_requis(cls, v):
        return v.strip() if isinstance(v, str) else v


def _usage(db: Session, sid: int, numero: str) -> int:
    return int(db.query(func.count(models.LigneEcriture.id)).join(
        models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id
    ).filter(
        models.Ecriture.societe_id == sid,
        models.LigneEcriture.compte == numero,
    ).scalar() or 0)


def _out(db: Session, sid: int, c: models.CompteSociete, usages=None):
    return {
        "id": c.id,
        "numero": c.numero,
        "compte": c.numero,
        "libelle": c.libelle,
        "classe": c.classe,
        "type": c.type_compte,
        "type_compte": c.type_compte,
        "origine": c.origine,
        "actif": bool(c.actif),
        "nb_ecritures": (_usage(db, sid, c.numero) if usages is None else int(usages.get(c.numero, 0))),
    }


@router.get("")
def lister_plan(
    inclure_inactifs: bool = Query(True),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    # La migration et la création de société préparent le plan. La consultation
    # reste un SELECT, même si une ancienne société n'a pas encore de comptes.
    q = db.query(models.CompteSociete).filter(models.CompteSociete.societe_id == sid)
    if not inclure_inactifs:
        q = q.filter(models.CompteSociete.actif == True)  # noqa: E712
    rows = q.order_by(models.CompteSociete.numero.asc()).all()

    # Un seul GROUP BY pour la page d'administration au lieu d'une requête
    # COUNT par compte (~900). L'autocomplétion n'a pas besoin des usages.
    usages = {}
    if inclure_inactifs and rows:
        usages = dict(db.query(
            models.LigneEcriture.compte, func.count(models.LigneEcriture.id)
        ).join(
            models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id
        ).filter(
            models.Ecriture.societe_id == sid
        ).group_by(models.LigneEcriture.compte).all())
    return [_out(db, sid, c, usages=usages) for c in rows]


@router.post("/initialiser")
def initialiser_plan(
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    """Ajoute les références CGNC absentes, sans remplacer les comptes existants."""
    sid = current_user["societe_id"]
    verrouiller_administration(db, sid)
    verifier_admin_apres_verrou(db, current_user["id"], sid)
    assurer_plan_societe(db, sid)
    db.commit()
    nombre = db.query(models.CompteSociete).filter_by(societe_id=sid).count()
    return {"nb_comptes": nombre, "message": "Plan comptable complété."}


@router.post("", status_code=201)
def creer_compte(
    data: CompteCreate,
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    assurer_plan_societe(db, sid)
    numero = data.numero.strip()
    if db.query(models.CompteSociete).filter_by(societe_id=sid, numero=numero).first():
        raise HTTPException(409, f"Le compte {numero} existe déjà dans le plan de cette société.")

    # Une extension personnalisée doit rester rattachée à une racine existante
    # afin de préserver la structure CGNC et les états qui travaillent par préfixe.
    parents = db.query(models.CompteSociete).filter(
        models.CompteSociete.societe_id == sid,
        models.CompteSociete.actif == True,  # noqa: E712
    ).all()
    parent = max((c for c in parents if numero.startswith(c.numero) and len(c.numero) < len(numero)),
                 key=lambda c: len(c.numero), default=None)
    if parent is None:
        raise HTTPException(422,
            "Un compte personnalisé doit être une subdivision d'un compte actif existant du plan CGNC/société.")

    c = models.CompteSociete(
        societe_id=sid,
        numero=numero,
        libelle=data.libelle.strip(),
        classe=int(numero[0]),
        type_compte=(data.type_compte or parent.type_compte),
        origine="personnalise",
        actif=True,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _out(db, sid, c)


@router.patch("/{numero}")
def modifier_compte(
    numero: str,
    data: CompteUpdate,
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    assurer_plan_societe(db, sid)
    c = db.query(models.CompteSociete).filter_by(societe_id=sid, numero=numero).first()
    if not c:
        raise HTTPException(404, "Compte introuvable dans le plan de cette société.")
    if data.libelle is not None:
        c.libelle = data.libelle.strip()
    if data.actif is not None:
        c.actif = bool(data.actif)
    db.commit()
    db.refresh(c)
    return _out(db, sid, c)


@router.delete("/{numero}", status_code=204)
def supprimer_compte(
    numero: str,
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    c = db.query(models.CompteSociete).filter_by(societe_id=sid, numero=numero).first()
    if not c:
        raise HTTPException(404, "Compte introuvable.")
    if c.origine != "personnalise":
        raise HTTPException(409, "Un compte du référentiel CGNC ne peut pas être supprimé ; désactivez-le si nécessaire.")
    if _usage(db, sid, numero):
        raise HTTPException(409, "Ce compte a déjà été mouvementé. Il peut être désactivé mais pas supprimé.")
    db.delete(c)
    db.commit()
    return None
