from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date
from database import get_db
from auth import hash_password, verify_password, create_access_token, get_current_user, valider_mot_de_passe
import models, schemas
from services.identifiants_maroc_service import normaliser_ice, normaliser_if
from services.plan_comptable import assurer_plan_societe
from services.exercices_service import ensure_exercice

router = APIRouter(prefix="/api/auth", tags=["auth"])

MODULES_DEFAUT = ["facturation", "comptabilite", "paie_grh"]


class ChangementMotDePasse(BaseModel):
    mot_de_passe_actuel: str = Field(..., max_length=4096)
    nouveau_mot_de_passe: str = Field(..., max_length=4096)


@router.post("/mot-de-passe", status_code=204)
def changer_mot_de_passe(data: ChangementMotDePasse,
                        current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Le compte personnel est partagé entre sociétés : ni un identifiant de
    # tiers ni les droits d'un administrateur invité ne déterminent sa cible.
    user = db.query(models.Utilisateur).filter_by(id=current_user["id"], actif=True).populate_existing().with_for_update().first()
    if not user:
        raise HTTPException(401, "Compte indisponible.")
    if not verify_password(data.mot_de_passe_actuel, user.hashed_password):
        raise HTTPException(400, "Le mot de passe actuel est incorrect.")
    valider_mot_de_passe(data.nouveau_mot_de_passe)
    if verify_password(data.nouveau_mot_de_passe, user.hashed_password):
        raise HTTPException(400, "Choisissez un mot de passe différent du mot de passe actuel.")
    user.hashed_password = hash_password(data.nouveau_mot_de_passe)
    db.commit()


class RegisterRequest(BaseModel):
    # Utilisateur
    nom:      str = Field(..., min_length=1, max_length=100)
    email:    str = Field(..., min_length=1, max_length=100)
    password: str
    # Société
    raison_sociale:      str = Field(..., min_length=1, max_length=200)
    identifiant_fiscal:  Optional[str] = None
    ice:                 Optional[str] = None
    ville:               Optional[str] = None
    telephone:           Optional[str] = None

    @field_validator("nom", "email", "raison_sociale", mode="before")
    @classmethod
    def texte_requis(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("ice")
    @classmethod
    def ice_valide(cls, v):
        return normaliser_ice(v)

    @field_validator("identifiant_fiscal")
    @classmethod
    def if_valide(cls, v):
        return normaliser_if(v)


@router.post("/register", response_model=schemas.Token)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Crée une nouvelle société et son administrateur."""
    if db.query(models.Utilisateur).filter_by(email=data.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # Politique de mot de passe minimale
    if len(data.password or "") < 8:
        raise HTTPException(status_code=400,
            detail="Le mot de passe doit contenir au moins 8 caractères")
    if data.password.lower() in ("password", "12345678", "azertyui", "motdepasse"):
        raise HTTPException(status_code=400, detail="Mot de passe trop courant")

    # Crée la société
    societe = models.Societe(
        raison_sociale=data.raison_sociale,
        exercice_debut=date.today().year,
        identifiant_fiscal=data.identifiant_fiscal,
        ice=data.ice,
        ville=data.ville,
        telephone=data.telephone,
    )
    db.add(societe)
    db.flush()

    # Crée l'utilisateur admin
    user = models.Utilisateur(
        societe_id=societe.id,
        nom=data.nom,
        email=data.email,
        hashed_password=hash_password(data.password),
        role="admin",
    )
    db.add(user)
    db.flush()

    # Active tous les modules par défaut
    for module in MODULES_DEFAUT:
        db.add(models.ModuleActif(
            societe_id=societe.id,
            module=module,
            actif=True,
        ))

    # Même préparation que /societes/nouvelle : l'inscription doit fournir
    # immédiatement un plan et un exercice utilisables, dans cette transaction.
    assurer_plan_societe(db, societe.id)
    ensure_exercice(db, societe.id, date.today().year)
    db.commit()
    db.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "societe_id": societe.id,
        "role": user.role,
    }, password_hash=user.hashed_password)
    return {"access_token": token, "role": user.role}


@router.post("/login", response_model=schemas.Token)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Connexion avec email + mot de passe."""
    user = db.query(models.Utilisateur).filter_by(email=data.email, actif=True).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = create_access_token({
        "sub": str(user.id),
        "societe_id": user.societe_id,
        "role": user.role,
    }, password_hash=user.hashed_password)
    return {"access_token": token, "role": user.role}


@router.get("/me", response_model=schemas.UtilisateurOut)
def me(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Retourne les infos de l'utilisateur connecté."""
    user = db.query(models.Utilisateur).filter_by(id=current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {**user.__dict__, "societe_id": current_user["societe_id"], "role": current_user["role"]}
