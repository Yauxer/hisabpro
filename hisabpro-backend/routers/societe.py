from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
import math
from typing import Optional, List
from database import get_db
from auth import get_current_user, requiert_ecriture
import models
from services.facturation_numero_service import prochain_numero_preview, prefixe_facture
from services.identifiants_maroc_service import normaliser_ice, normaliser_if, normaliser_tp
from services.exercices_service import ensure_exercice, verifier_chevauchement
from services.premiers_exercices_service import periodes_a_preparer
from services.logo_societe_service import normaliser_logo

router = APIRouter(prefix="/api/societe", tags=["societe"])

MODULES_DISPONIBLES = ["facturation", "comptabilite", "paie_grh"]


# ── Schemas ───────────────────────────────────────────────────────────────────

class SocieteUpdate(BaseModel):
    raison_sociale:     Optional[str] = Field(None, min_length=1, max_length=200)
    identifiant_fiscal: Optional[str] = None
    ice:                Optional[str] = None
    rc:                 Optional[str] = None
    patente:            Optional[str] = None
    cnss_numero:        Optional[str] = None
    adresse:            Optional[str] = None
    ville:              Optional[str] = None
    pays:               Optional[str] = None
    telephone:          Optional[str] = None
    fax:                Optional[str] = None
    email:              Optional[str] = None
    site_web:           Optional[str] = None
    banque:             Optional[str] = None
    agence:             Optional[str] = None
    rib:                Optional[str] = None
    exercice_debut:     Optional[int] = None

    @field_validator("exercice_debut")
    @classmethod
    def exercice_debut_valide(cls, v):
        if v is not None and not 1900 <= v <= 2200:
            raise ValueError("L’année de début doit être comprise entre 1900 et 2200.")
        return v
    periodicite_tva:    Optional[str] = None
    forme_juridique:    Optional[str] = None
    capital_social:     Optional[float] = None
    prefixe_facture:    Optional[str] = None
    prefixe_devis:      Optional[str] = None
    prefixe_bc:         Optional[str] = None
    prefixe_bl:         Optional[str] = None
    prefixe_avoir:      Optional[str] = None
    stock_declencheur_vente: Optional[str] = None
    stock_declencheur_achat: Optional[str] = None
    devise:             Optional[str] = None
    regime_fiscal:      Optional[str] = None
    regime_tva:         Optional[str] = None
    secteur:            Optional[str] = None
    format_libelle_vente:  Optional[str] = None
    format_libelle_achat:  Optional[str] = None
    format_libelle_avoir:  Optional[str] = None
    format_libelle_banque: Optional[str] = None
    logo_url:           Optional[str] = None

    @field_validator("logo_url")
    @classmethod
    def logo_valide(cls, value):
        return normaliser_logo(value)

    @field_validator("raison_sociale", mode="before")
    @classmethod
    def raison_sociale_requise(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("capital_social", mode="before")
    @classmethod
    def capital_valide(cls, v):
        if v is None:
            return v
        try:
            valide = not isinstance(v, bool) and math.isfinite(float(v)) and float(v) >= 0
        except (TypeError, ValueError, OverflowError):
            valide = False
        if not valide:
            # Un float NaN dans l'erreur Pydantic est lui-même impossible à
            # sérialiser en JSON. Réponse métier explicite avant toute mutation.
            raise HTTPException(400, "Le capital social doit être un montant fini et positif ou nul.")
        return v

    @field_validator("ice")
    @classmethod
    def ice_valide(cls, v):
        return normaliser_ice(v)

    @field_validator("identifiant_fiscal")
    @classmethod
    def if_valide(cls, v):
        return normaliser_if(v)

    @field_validator("patente")
    @classmethod
    def patente_valide(cls, v):
        return normaliser_tp(v)

    @field_validator("stock_declencheur_vente")
    @classmethod
    def stock_vente_valide(cls, v):
        if v is not None and v not in {"facture", "bl"}:
            raise ValueError("Le déclencheur de stock vente doit être 'facture' ou 'bl'.")
        return v

    @field_validator("stock_declencheur_achat")
    @classmethod
    def stock_achat_valide(cls, v):
        if v is not None and v not in {"facture", "br"}:
            raise ValueError("Le déclencheur de stock achat doit être 'facture' ou 'br'.")
        return v


class SocieteOut(BaseModel):
    id:                 int
    raison_sociale:     str
    identifiant_fiscal: Optional[str]
    ice:                Optional[str]
    rc:                 Optional[str]
    patente:            Optional[str]
    cnss_numero:        Optional[str]
    adresse:            Optional[str]
    ville:              Optional[str]
    pays:               Optional[str]
    telephone:          Optional[str]
    fax:                Optional[str]
    email:              Optional[str]
    site_web:           Optional[str]
    banque:             Optional[str]
    agence:             Optional[str]
    rib:                Optional[str]
    exercice_debut:     Optional[int]
    periodicite_tva:    Optional[str]
    forme_juridique:    Optional[str] = None
    capital_social:     Optional[float] = None
    prefixe_facture:    Optional[str] = "FA"
    prefixe_devis:      Optional[str] = "DV"
    prefixe_bc:         Optional[str] = "BC"
    prefixe_bl:         Optional[str] = "BL"
    prefixe_avoir:      Optional[str] = "AV"
    stock_declencheur_vente: Optional[str] = "facture"
    stock_declencheur_achat: Optional[str] = "facture"
    devise:             Optional[str] = "MAD"
    regime_fiscal:      Optional[str] = "is"
    regime_tva:         Optional[str] = "encaissement"
    secteur:            Optional[str] = None
    format_libelle_vente:  Optional[str] = "Facture {numero} {tiers}"
    format_libelle_achat:  Optional[str] = "Facture d'achat {numero} {tiers}"
    format_libelle_avoir:  Optional[str] = "Avoir {numero} {tiers}"
    format_libelle_banque: Optional[str] = "Règlement {tiers} {ref}"
    logo_url:           Optional[str]
    modules:            List[str] = []

    class Config:
        from_attributes = True


class ModuleToggle(BaseModel):
    module: str
    actif:  bool


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_modules_actifs(societe_id: int, db: Session) -> List[str]:
    """Retourne la liste des codes de modules actifs pour une société."""
    modules = db.query(models.ModuleActif).filter_by(
        societe_id=societe_id, actif=True
    ).all()
    return [m.module for m in modules]


def module_est_actif(societe_id: int, module: str, db: Session) -> bool:
    """Vérifie si un module est actif pour une société."""
    m = db.query(models.ModuleActif).filter_by(
        societe_id=societe_id, module=module, actif=True
    ).first()
    return m is not None


def activer_modules_defaut(societe_id: int, db: Session):
    """Active tous les modules par défaut pour une nouvelle société."""
    for module in MODULES_DISPONIBLES:
        existant = db.query(models.ModuleActif).filter_by(
            societe_id=societe_id, module=module
        ).first()
        if not existant:
            db.add(models.ModuleActif(societe_id=societe_id, module=module, actif=True))
    db.commit()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/moi", response_model=SocieteOut)
def get_ma_societe(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne les infos de la société de l'utilisateur connecté."""
    societe = db.query(models.Societe).filter_by(
        id=current_user["societe_id"]
    ).first()
    if not societe:
        raise HTTPException(status_code=404, detail="Société introuvable")

    modules = get_modules_actifs(societe.id, db)
    return {**societe.__dict__, "modules": modules}


@router.patch("/moi", response_model=SocieteOut)
def modifier_ma_societe(
    data: SocieteUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Met à jour les infos de la société (admin uniquement)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    if not societe:
        raise HTTPException(status_code=404, detail="Société introuvable")

    # Le paramètre « Début d’exercice » représente le premier exercice
    # accessible, pas une nouvelle borne à appliquer aux périodes existantes.
    # Lorsqu'il est avancé dans le passé, créer les exercices manquants sans
    # déplacer ni supprimer les écritures / périodes déjà enregistrées.
    debut_demande = data.exercice_debut
    if debut_demande is not None:
        debut_demande = int(debut_demande)
        plus_ancien = db.query(models.ExerciceComptable).filter_by(
            societe_id=societe.id
        ).order_by(models.ExerciceComptable.date_debut.asc()).first()
        try:
            periodes = periodes_a_preparer(debut_demande, plus_ancien)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        for annee, debut, fin in periodes:
            chevauche = verifier_chevauchement(db, societe.id, debut, fin)
            if chevauche:
                raise HTTPException(
                    409,
                    f"Impossible de créer {annee} : chevauchement avec l’exercice "
                    f"{chevauche.annee} ({chevauche.date_debut}–{chevauche.date_fin})."
                )
            try:
                ensure_exercice(db, societe.id, annee, debut, fin)
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from exc

    for k, v in data.model_dump(exclude_none=True).items():
        setattr(societe, k, v)

    db.commit()
    db.refresh(societe)
    modules = get_modules_actifs(societe.id, db)
    return {**societe.__dict__, "modules": modules}


@router.get("/modules")
def get_modules(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne l'état de tous les modules pour la société."""
    tous = db.query(models.ModuleActif).filter_by(
        societe_id=current_user["societe_id"]
    ).all()

    # Une lecture ne doit jamais écrire en base. Les sociétés créées par les
    # parcours normaux ont déjà leurs lignes de modules ; pour une ancienne
    # base incomplète on expose simplement les valeurs par défaut en mémoire.
    if not tous:
        return {m: {"actif": True, "date_activation": None} for m in MODULES_DISPONIBLES}

    return {
        m.module: {
            "actif": m.actif,
            "date_activation": m.date_activation,
        }
        for m in tous
    }


@router.patch("/modules")
def toggle_module(
    data: ModuleToggle,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Active ou désactive un module (admin uniquement)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    if data.module not in MODULES_DISPONIBLES:
        raise HTTPException(
            status_code=400,
            detail=f"Module inconnu. Disponibles : {MODULES_DISPONIBLES}"
        )

    module = db.query(models.ModuleActif).filter_by(
        societe_id=current_user["societe_id"],
        module=data.module
    ).first()

    if module:
        module.actif = data.actif
    else:
        module = models.ModuleActif(
            societe_id=current_user["societe_id"],
            module=data.module,
            actif=data.actif,
        )
        db.add(module)

    db.commit()
    return {"module": data.module, "actif": data.actif, "message": "Module mis à jour"}


# ── Numérotation automatique des documents ────────────────────────────────────
@router.get("/prochain-numero")
def prochain_numero(
    type_doc: str,
    exercice: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne le prochain numéro séquentiel pour un type de document donné.
    Format : {PREFIXE}-{EXERCICE}-{SEQ:03d}. La séquence repart à 1 à chaque exercice.
    Le numéro proposé reste modifiable par l'utilisateur ; l'unicité est
    contrôlée à l'enregistrement."""
    societe_id = current_user["societe_id"]
    societe = db.query(models.Societe).filter_by(id=societe_id).first()

    config = {
        "facture": (getattr(societe, "prefixe_facture", None) or "FA", models.Facture,      models.Facture.numero),
        "devis":   (getattr(societe, "prefixe_devis",   None) or "DV", models.Devis,        models.Devis.numero),
        "bc":      (getattr(societe, "prefixe_bc",      None) or "BC", models.BonCommande,  models.BonCommande.numero),
        "bl":      (getattr(societe, "prefixe_bl",      None) or "BL", models.BonLivraison, models.BonLivraison.numero),
        "proforma": ("PF",                                              models.Facture,      models.Facture.numero),
        "br":      ("BR",                                               models.BonLivraison, models.BonLivraison.numero),
        "avoir":   (getattr(societe, "prefixe_avoir",   None) or "AV", models.Avoir,        models.Avoir.numero),
    }
    if type_doc not in config:
        raise HTTPException(400, f"Type de document inconnu : {type_doc}")

    prefixe, modele, col_numero = config[type_doc]

    # FACT.4 : pour les factures/proformas, l'aperçu lit le compteur atomique
    # PostgreSQL mais ne réserve rien. La réservation se fait à la validation.
    if type_doc in {"facture", "proforma"}:
        vrai_prefixe = prefixe_facture(societe, type_doc == "proforma")
        numero, prochain = prochain_numero_preview(
            db, societe_id, exercice, type_doc, vrai_prefixe
        )
        return {
            "numero": numero, "prefixe": vrai_prefixe,
            "sequence": prochain, "exercice": exercice,
            "est_prevision": True,
        }

    # Les autres documents conservent temporairement leur logique historique.
    # Cherche le plus grand numéro séquentiel existant pour ce préfixe + exercice.
    # On parcourt les numéros du pattern {prefixe}-{exercice}-* et on extrait la séquence.
    numeros = db.query(col_numero).filter(
        modele.societe_id == societe_id,
        col_numero.like(f"{prefixe}-{exercice}-%"),
    ).all()

    max_seq = 0
    for (num,) in numeros:
        try:
            seq = int(num.rsplit("-", 1)[1])
            if seq > max_seq:
                max_seq = seq
        except (ValueError, IndexError):
            continue  # numéro saisi manuellement hors format — ignoré

    prochain = max_seq + 1
    return {
        "numero": f"{prefixe}-{exercice}-{prochain:03d}",
        "prefixe": prefixe,
        "sequence": prochain,
        "exercice": exercice,
    }
