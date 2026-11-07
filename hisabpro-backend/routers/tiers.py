from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional, List
import re
from database import get_db
from auth import get_current_user, requiert_ecriture
import models
from services.identifiants_maroc_service import normaliser_ice, normaliser_if

router = APIRouter(prefix="/api/tiers", tags=["tiers"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class TiersCreate(BaseModel):
    type:               str  # client | fournisseur | les_deux
    nom:                str
    ice:                Optional[str] = None
    identifiant_fiscal: Optional[str] = None
    rc:                 Optional[str] = None
    adresse:            Optional[str] = None
    ville:              Optional[str] = None
    telephone:          Optional[str] = None
    email:              Optional[str] = None
    categorie_fiscale:    Optional[str] = "professionnel"
    compte_client:      Optional[str] = "3421"
    compte_fournisseur: Optional[str] = "4411"
    assujetti_tva:      Optional[bool] = True
    taux_ras:           Optional[float] = None
    delai_paiement:     Optional[int] = 60
    plafond_credit:     Optional[float] = 0.0

    @field_validator("nom")
    @classmethod
    def nom_obligatoire(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Le nom / la raison sociale est obligatoire")
        return v

    @field_validator("type")
    @classmethod
    def type_valide(cls, v):
        if v is None:
            return v
        if v not in {"client", "fournisseur", "les_deux"}:
            raise ValueError("Type de tiers invalide")
        return v

    @field_validator("ice")
    @classmethod
    def ice_valide(cls, v):
        return normaliser_ice(v)

    @field_validator("identifiant_fiscal")
    @classmethod
    def if_valide(cls, v):
        return normaliser_if(v)

    @field_validator("categorie_fiscale")
    @classmethod
    def categorie_fiscale_valide(cls, v):
        if v in (None, ""):
            return "indetermine"
        if v not in {"professionnel", "autoentrepreneur", "particulier", "indetermine"}:
            raise ValueError("Catégorie fiscale de tiers invalide")
        return v

    @field_validator("email")
    @classmethod
    def email_valide(cls, v):
        if v in (None, ""):
            return None
        v = v.strip()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", v):
            raise ValueError("Adresse email invalide")
        return v

    @field_validator("delai_paiement")
    @classmethod
    def delai_valide(cls, v):
        if v is not None and v < 0:
            raise ValueError("Le délai de paiement ne peut pas être négatif")
        return v

    @field_validator("plafond_credit")
    @classmethod
    def plafond_valide(cls, v):
        if v is not None and v < 0:
            raise ValueError("Le plafond de crédit ne peut pas être négatif")
        return v

    @field_validator("taux_ras")
    @classmethod
    def ras_valide(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError("Le taux RAS doit être compris entre 0 et 100 %")
        return v


class TiersUpdate(TiersCreate):
    type: Optional[str] = None
    nom:  Optional[str] = None


class TiersOut(BaseModel):
    id:                 int
    type:               str
    nom:                str
    code_aux_client:      Optional[str] = None
    code_aux_fournisseur: Optional[str] = None
    ice:                Optional[str]
    identifiant_fiscal: Optional[str]
    rc:                 Optional[str]
    adresse:            Optional[str]
    ville:              Optional[str]
    telephone:          Optional[str]
    email:              Optional[str]
    categorie_fiscale:    str
    compte_client:      Optional[str]
    compte_fournisseur: Optional[str]
    assujetti_tva:      bool
    taux_ras:           Optional[float]
    delai_paiement:     Optional[int]
    plafond_credit:     Optional[float]
    actif:              bool

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[TiersOut])
def lister_tiers(
    type:      Optional[str] = Query(None),  # client | fournisseur | les_deux
    recherche: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 200,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(models.Tiers).filter_by(
        societe_id=current_user["societe_id"], actif=True
    )
    if type:
        q = q.filter(
            (models.Tiers.type == type) | (models.Tiers.type == "les_deux")
        )
    if recherche:
        q = q.filter(
            models.Tiers.nom.ilike(f"%{recherche}%") |
            models.Tiers.ice.ilike(f"%{recherche}%") |
            models.Tiers.ville.ilike(f"%{recherche}%") |
            models.Tiers.code_aux_client.ilike(f"%{recherche}%") |
            models.Tiers.code_aux_fournisseur.ilike(f"%{recherche}%")
        )
    return q.order_by(models.Tiers.nom).offset(skip).limit(limit).all()


@router.post("", response_model=TiersOut, status_code=201)
def creer_tiers(
    data: TiersCreate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    tiers = models.Tiers(
        societe_id=current_user["societe_id"],
        **data.model_dump()
    )
    db.add(tiers)
    db.flush()
    # COMPTA-AUX : codes auxiliaires stables et non saisis manuellement.
    if tiers.type in {"client", "les_deux"} and not tiers.code_aux_client:
        tiers.code_aux_client = f"C{tiers.id:08d}"
    if tiers.type in {"fournisseur", "les_deux"} and not tiers.code_aux_fournisseur:
        tiers.code_aux_fournisseur = f"F{tiers.id:08d}"
    db.commit()
    db.refresh(tiers)
    return tiers


@router.get("/{tiers_id}", response_model=TiersOut)
def obtenir_tiers(
    tiers_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tiers = db.query(models.Tiers).filter_by(
        id=tiers_id, societe_id=current_user["societe_id"]
    ).first()
    if not tiers:
        raise HTTPException(status_code=404, detail="Tiers introuvable")
    return tiers


@router.put("/{tiers_id}", response_model=TiersOut)
def modifier_tiers(
    tiers_id: int,
    data: TiersUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    tiers = db.query(models.Tiers).filter_by(
        id=tiers_id, societe_id=current_user["societe_id"]
    ).first()
    if not tiers:
        raise HTTPException(status_code=404, detail="Tiers introuvable")

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(tiers, k, v)

    # Si le tiers change de rôle, on lui attribue le code auxiliaire manquant
    # sans jamais recycler/modifier un code déjà utilisé.
    if tiers.type in {"client", "les_deux"} and not tiers.code_aux_client:
        tiers.code_aux_client = f"C{tiers.id:08d}"
    if tiers.type in {"fournisseur", "les_deux"} and not tiers.code_aux_fournisseur:
        tiers.code_aux_fournisseur = f"F{tiers.id:08d}"

    db.commit()
    db.refresh(tiers)
    return tiers


@router.delete("/{tiers_id}", status_code=204)
def supprimer_tiers(
    tiers_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    tiers = db.query(models.Tiers).filter_by(
        id=tiers_id, societe_id=current_user["societe_id"]
    ).first()
    if not tiers:
        raise HTTPException(status_code=404, detail="Tiers introuvable")
    tiers.actif = False
    db.commit()
