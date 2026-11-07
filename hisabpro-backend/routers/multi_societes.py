from fastapi import APIRouter, Depends, HTTPException
from datetime import date
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from database import get_db
from auth import get_current_user, create_access_token, requiert_ecriture
import models
from services.identifiants_maroc_service import normaliser_ice, normaliser_if
from services.exercices_service import ensure_exercice
from services.plan_comptable import assurer_plan_societe
from services.utilisateurs_acces_service import (
    verrouiller_administration, verifier_retrait_administrateur,
    verifier_admin_apres_verrou,
)

router = APIRouter(prefix="/api/societes", tags=["multi-societes"])
from routers.societes_liees import router as societes_liees_router
router.include_router(societes_liees_router)

MODULES_DEFAUT = ["facturation", "comptabilite", "paie_grh"]


# ── Schemas ───────────────────────────────────────────────────────────────────

class SocieteCreate(BaseModel):
    raison_sociale: str = Field(..., min_length=2, max_length=200)
    ice:            Optional[str] = None
    identifiant_fiscal: Optional[str] = None
    rc:             Optional[str] = None
    ville:          Optional[str] = None
    pays:           Optional[str] = "Maroc"
    telephone:      Optional[str] = None
    email:          Optional[str] = None

    @field_validator("raison_sociale")
    @classmethod
    def raison_sociale_valide(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("La raison sociale doit contenir au moins deux caractères.")
        return v

    @field_validator("ice")
    @classmethod
    def ice_valide(cls, v):
        return normaliser_ice(v)

    @field_validator("identifiant_fiscal")
    @classmethod
    def if_valide(cls, v):
        return normaliser_if(v)


class SocieteOut(BaseModel):
    id:             int
    raison_sociale: str
    ice:            Optional[str]
    ville:          Optional[str]
    pays:           Optional[str]
    role:           str  # rôle de l'utilisateur dans cette société

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_societes_utilisateur(user_id: int, db: Session):
    """Retourne toutes les sociétés accessibles par un utilisateur."""
    user = db.query(models.Utilisateur).filter_by(id=user_id).first()
    if not user:
        return []

    societes = []
    ids_vus = set()

    # Société principale (toujours incluse)
    societe = db.query(models.Societe).filter_by(id=user.societe_id).first()
    if societe:
        societes.append({"societe": societe, "role": user.role})
        ids_vus.add(societe.id)

    # Autres sociétés via table liaison
    try:
        liaisons = db.query(models.UtilisateurSociete).filter_by(
            utilisateur_id=user_id, actif=True
        ).all()
        for liaison in liaisons:
            if liaison.societe_id not in ids_vus:
                s = db.query(models.Societe).filter_by(id=liaison.societe_id).first()
                if s:
                    societes.append({"societe": s, "role": liaison.role})
                    ids_vus.add(s.id)
    except Exception:
        pass  # Table pas encore créée

    return societes


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/mes-societes", response_model=List[SocieteOut])
def mes_societes(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste toutes les sociétés accessibles par l'utilisateur connecté."""
    societes = get_societes_utilisateur(current_user["id"], db)
    return [
        {**s["societe"].__dict__, "role": s["role"]}
        for s in societes
    ]


@router.post("/switcher/{societe_id}")
def switcher_societe(
    societe_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change la société active — retourne un nouveau token."""
    user_id = current_user["id"]

    # Vérifie que l'utilisateur a accès à cette société
    societes = get_societes_utilisateur(user_id, db)
    societe_trouvee = next(
        (s for s in societes if s["societe"].id == societe_id), None
    )
    if not societe_trouvee:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé à cette société"
        )

    societe  = societe_trouvee["societe"]
    role     = societe_trouvee["role"]

    # Génère un nouveau token avec le bon societe_id
    utilisateur = db.query(models.Utilisateur).filter_by(id=user_id).first()
    nouveau_token = create_access_token({
        "sub":        str(user_id),
        "societe_id": societe_id,
        "role":       role,
    }, password_hash=utilisateur.hashed_password)

    return {
        "access_token": nouveau_token,
        "token_type":   "bearer",
        "role":         role,
        "societe": {
            "id":             societe.id,
            "raison_sociale": societe.raison_sociale,
            "ville":          societe.ville,
        }
    }


@router.post("/nouvelle", status_code=201)
def creer_societe(
    data: SocieteCreate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Crée une société isolée et prépare ses modules, son plan et son exercice."""
    # Crée la société
    societe = models.Societe(
        raison_sociale=data.raison_sociale,
        exercice_debut=date.today().year,
        ice=data.ice,
        identifiant_fiscal=data.identifiant_fiscal,
        rc=data.rc,
        ville=data.ville,
        pays=data.pays or "Maroc",
        telephone=data.telephone,
        email=data.email,
    )
    db.add(societe)
    db.flush()

    # Active les modules par défaut
    for module in MODULES_DEFAUT:
        db.add(models.ModuleActif(
            societe_id=societe.id,
            module=module,
            actif=True,
        ))

    # Liaison utilisateur ↔ nouvelle société
    liaison = models.UtilisateurSociete(
        utilisateur_id=current_user["id"],
        societe_id=societe.id,
        role="admin",
        actif=True,
    )
    db.add(liaison)

    # L'initialisation est atomique avec la création : la nouvelle société
    # possède immédiatement un plan CGNC et un premier exercice utilisable.
    # Un échec annule société, modules et liaison au lieu de laisser une fiche
    # orpheline ou inaccessible.
    assurer_plan_societe(db, societe.id)
    ensure_exercice(db, societe.id, date.today().year)
    db.commit()
    db.refresh(societe)

    return {
        "id":             societe.id,
        "raison_sociale": societe.raison_sociale,
        "message":        "Société créée avec succès"
    }


@router.post("/{societe_id}/inviter")
def inviter_utilisateur(
    societe_id: int,
    email: str,
    role: str = "comptable",
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Donne accès à un utilisateur existant sur une société."""
    if role not in {"admin", "comptable", "lecture", "personnel"}:
        raise HTTPException(status_code=400, detail="Rôle invalide")
    # Vérifie que l'invitant est admin de cette société
    societes = get_societes_utilisateur(current_user["id"], db)
    societe_trouvee = next(
        (s for s in societes if s["societe"].id == societe_id), None
    )
    if not societe_trouvee or societe_trouvee["role"] != "admin":
        raise HTTPException(status_code=403, detail="Droits admin requis")
    verrouiller_administration(db, societe_id)
    verifier_admin_apres_verrou(db, current_user["id"], societe_id)

    # Trouve l'utilisateur cible
    if role == 'personnel':
        from services.personnel_profil_service import verifier_installation
        verifier_installation(db)
    user_cible = db.query(models.Utilisateur).filter_by(email=email).first()
    if not user_cible:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if not user_cible.actif:
        raise HTTPException(409, "Ce compte est désactivé. Son administrateur principal doit le réactiver avant l'attribution d'un accès.")
    if user_cible.societe_id == societe_id:
        # Une liaison secondaire sur la société principale est ignorée par
        # l'authentification ; la créer donnerait une illusion de changement.
        raise HTTPException(409, "Cet utilisateur appartient déjà à cette société. Modifiez son rôle dans la gestion des utilisateurs.")

    # Crée ou met à jour la liaison
    existant = db.query(models.UtilisateurSociete).filter_by(
        utilisateur_id=user_cible.id,
        societe_id=societe_id,
    ).first()

    if existant:
        verifier_retrait_administrateur(
            db, societe_id, user_cible.id, existant.role,
            bool(existant.actif and user_cible.actif), role, bool(user_cible.actif),
        )
        existant.role  = role
        existant.actif = True
    else:
        db.add(models.UtilisateurSociete(
            utilisateur_id=user_cible.id,
            societe_id=societe_id,
            role=role,
            actif=True,
        ))

    db.commit()
    return {"message": f"{email} a accès à la société {societe_id} en tant que {role}"}
