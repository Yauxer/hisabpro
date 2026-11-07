# -*- coding: utf-8 -*-
"""
Gestion des utilisateurs d'une société (réservée aux administrateurs).

Rôles :
  admin     — tout, y compris la gestion des utilisateurs et les paramètres société
  comptable — toutes les opérations métier (saisie, factures, clôture, immobilisations)
  lecture   — consultation seule, aucune modification
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, requiert_admin, hash_password
import models, schemas
from services.utilisateurs_acces_service import (
    verrouiller_administration, verifier_retrait_administrateur,
    verifier_admin_apres_verrou, societes_admin_secondaires,
)

router = APIRouter(prefix="/api/utilisateurs", tags=["utilisateurs"])

ROLES_VALIDES = ("admin", "comptable", "lecture", "personnel")
LIBELLES_ROLES = {
    "admin": "Administrateur",
    "comptable": "Comptable",
    "lecture": "Consultation seule",
    "personnel": "Personnel seul",
}


class UtilisateurCreate(BaseModel):
    nom: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    mot_de_passe: str
    role: str = "comptable"

    @field_validator("nom", mode="before")
    @classmethod
    def nom_requis(cls, v):
        return v.strip() if isinstance(v, str) else v


class UtilisateurUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = None
    actif: Optional[bool] = None
    mot_de_passe: Optional[str] = None

    @field_validator("nom", mode="before")
    @classmethod
    def nom_requis(cls, v):
        return v.strip() if isinstance(v, str) else v


def _sortie(u: models.Utilisateur, liaison=None, societe_id=None):
    role = liaison.role if liaison else u.role
    return {
        "id": u.id,
        "nom": u.nom,
        "email": u.email,
        "role": role,
        "role_libelle": LIBELLES_ROLES.get(role, role),
        "actif": bool(u.actif and (liaison.actif if liaison else True)),
        "actif_compte": bool(u.actif),
        "actif_acces": bool(liaison.actif if liaison else u.actif),
        "societe_id": societe_id if societe_id is not None else u.societe_id,
        "acces_invite": liaison is not None,
    }


def _acces_utilisateur(db, user_id, societe_id):
    user = db.query(models.Utilisateur).filter_by(id=user_id).populate_existing().first()
    if user and user.societe_id == societe_id:
        return user, None
    liaison = db.query(models.UtilisateurSociete).filter_by(
        utilisateur_id=user_id, societe_id=societe_id,
    ).populate_existing().first() if user else None
    if not liaison:
        raise HTTPException(404, "Utilisateur introuvable")
    return user, liaison


@router.get("")
def lister(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les utilisateurs de la société. Accessible à tous (annuaire),
    mais seuls les admins peuvent créer ou modifier."""
    users = db.query(models.Utilisateur).filter_by(
        societe_id=current_user["societe_id"]
    ).order_by(models.Utilisateur.nom).all()
    invites = db.query(models.Utilisateur, models.UtilisateurSociete).join(
        models.UtilisateurSociete,
        models.UtilisateurSociete.utilisateur_id == models.Utilisateur.id,
    ).filter(
        models.UtilisateurSociete.societe_id == current_user["societe_id"],
        models.Utilisateur.societe_id != current_user["societe_id"],
    ).all()
    resultats = [_sortie(u) for u in users] + [
        _sortie(u, liaison, current_user["societe_id"]) for u, liaison in invites
    ]
    return sorted(resultats, key=lambda row: (row["nom"].casefold(), row["id"]))


@router.get("/roles")
def lister_roles(current_user=Depends(get_current_user)):
    """Rôles disponibles, pour alimenter les listes déroulantes."""
    return [
        {"code": "admin", "libelle": LIBELLES_ROLES["admin"],
         "description": "Accès complet, gestion des utilisateurs et des paramètres."},
        {"code": "comptable", "libelle": LIBELLES_ROLES["comptable"],
         "description": "Saisie et gestion comptable et commerciale, clôture d'exercice."},
        {"code": "lecture", "libelle": LIBELLES_ROLES["lecture"],
         "description": "Consultation et export uniquement, aucune modification possible."},
        {"code": "personnel", "libelle": LIBELLES_ROLES["personnel"],
         "description": "Personnel uniquement, sous habilitations explicites ; aucun accès comptable ou commercial."},
    ]


@router.post("", status_code=201)
def creer(
    data: UtilisateurCreate,
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    if data.role not in ROLES_VALIDES:
        raise HTTPException(400, f"Rôle invalide. Valeurs acceptées : {', '.join(ROLES_VALIDES)}.")
    if data.role == 'personnel':
        from services.personnel_profil_service import verifier_installation
        verifier_installation(db)
    if len(data.mot_de_passe) < 8:
        raise HTTPException(400, "Le mot de passe doit contenir au moins 8 caractères.")
    if db.query(models.Utilisateur).filter_by(email=data.email).first():
        raise HTTPException(400, "Cette adresse e-mail est déjà utilisée.")

    user = models.Utilisateur(
        societe_id=current_user["societe_id"],
        nom=data.nom,
        email=data.email,
        hashed_password=hash_password(data.mot_de_passe),
        role=data.role,
        actif=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _sortie(user)


@router.patch("/{user_id}")
def modifier(
    user_id: int,
    data: UtilisateurUpdate,
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    user, liaison = _acces_utilisateur(db, user_id, societe_id)
    secondaires = societes_admin_secondaires(db, user) if liaison is None and data.actif is False else []
    verrouiller_administration(db, [societe_id, *secondaires])
    verifier_admin_apres_verrou(db, current_user["id"], societe_id)
    user, liaison = _acces_utilisateur(db, user_id, societe_id)
    acces = liaison if liaison is not None else user
    if liaison is not None and (data.nom is not None or data.mot_de_passe is not None):
        raise HTTPException(403, "Un administrateur de cette société peut modifier les accès de l'invité, pas son compte personnel.")

    if data.role is not None and data.role not in ROLES_VALIDES:
        raise HTTPException(400, f"Rôle invalide. Valeurs acceptées : {', '.join(ROLES_VALIDES)}.")
    if data.role == 'personnel':
        from services.personnel_profil_service import verifier_installation
        verifier_installation(db)
    if data.actif is False and user.id == current_user["id"]:
        raise HTTPException(400, "Vous ne pouvez pas désactiver votre propre accès.")
    verifier_retrait_administrateur(
        db, societe_id, user.id, acces.role, bool(acces.actif and user.actif),
        data.role if data.role is not None else acces.role,
        bool(user.actif and (data.actif if data.actif is not None else acces.actif)),
    )
    for secondaire in secondaires:
        try:
            verifier_retrait_administrateur(db, secondaire, user.id, "admin", bool(user.actif), "admin", False)
        except HTTPException as exc:
            raise HTTPException(400, f"Ce compte est le dernier administrateur actif de la société {secondaire}. Transférez ses droits avant de le désactiver.") from exc

    if data.role is not None:
        acces.role = data.role

    if data.nom is not None:
        user.nom = data.nom

    if data.actif is not None:
        acces.actif = data.actif

    if data.mot_de_passe:
        if len(data.mot_de_passe) < 8:
            raise HTTPException(400, "Le mot de passe doit contenir au moins 8 caractères.")
        user.hashed_password = hash_password(data.mot_de_passe)

    db.commit()
    db.refresh(user)
    return _sortie(user, liaison, societe_id)


@router.delete("/{user_id}", status_code=204)
def supprimer(
    user_id: int,
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    verrouiller_administration(db, societe_id)
    verifier_admin_apres_verrou(db, current_user["id"], societe_id)
    user, liaison = _acces_utilisateur(db, user_id, societe_id)
    if user.id == current_user["id"]:
        raise HTTPException(400, "Vous ne pouvez pas supprimer votre propre compte.")
    acces = liaison if liaison is not None else user
    verifier_retrait_administrateur(db, societe_id, user.id, acces.role,
                                   bool(acces.actif and user.actif), acces.role, False)
    if liaison is None and db.query(models.UtilisateurSociete).filter_by(utilisateur_id=user.id).first():
        raise HTTPException(409, "Ce compte possède des accès à d'autres sociétés. Désactivez-le plutôt que de supprimer ses accès partagés.")
    if liaison is None:
        from services.personnel_acces_service import verifier_suppression_compte
        verifier_suppression_compte(db, user.id)
    db.delete(acces)
    db.commit()
