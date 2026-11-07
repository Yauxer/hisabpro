from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import math
from services.parametres_paie_service import sortie_taux_cotisation
from database import get_db
from auth import get_current_user, requiert_ecriture
import models

router = APIRouter(prefix="/api/parametres", tags=["parametres"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class BaremeIROut(BaseModel):
    id:          int
    annee:       int
    tranche_min: float
    tranche_max: Optional[float]
    taux:        float
    deduction:   float

    class Config:
        from_attributes = True


class TauxCotisationOut(BaseModel):
    id:       int
    annee:    int
    code:     str
    libelle:  Optional[str]
    taux_sal: Optional[float]
    taux_pat: Optional[float]
    plafond:  Optional[float]
    anomalies: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TauxCotisationUpdate(BaseModel):
    taux_sal: Optional[float] = None
    taux_pat: Optional[float] = None
    plafond:  Optional[float] = None

    @field_validator('taux_sal', 'taux_pat', 'plafond', mode='before')
    @classmethod
    def verifier_nombre(cls, valeur, info):
        if valeur is None:
            return None
        if isinstance(valeur, bool):
            raise ValueError('Un booléen ne peut pas être un paramètre de cotisation')
        try:
            nombre = float(valeur)
        except (TypeError, ValueError, OverflowError):
            raise ValueError('Le paramètre doit être un nombre fini') from None
        if not math.isfinite(nombre):
            raise ValueError('Le paramètre doit être un nombre fini')
        if info.field_name == 'plafond':
            if nombre <= 0:
                raise ValueError('Le plafond doit être strictement positif')
        elif not 0 <= nombre <= 1:
            raise ValueError('Le taux doit être un ratio compris entre 0 et 1')
        return valeur


class DeductionIROut(BaseModel):
    id:               int
    annee:            int
    code:             str
    libelle:          Optional[str]
    montant_an:       float
    max_beneficiaires: Optional[int]

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/bareme-ir/{annee}", response_model=List[BaremeIROut])
def get_bareme_ir(
    annee: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Retourne le barème IR pour une année donnée."""
    bareme = db.query(models.BaremeIR).filter_by(annee=annee).order_by(models.BaremeIR.tranche_min).all()
    if not bareme:
        raise HTTPException(status_code=404, detail=f"Aucun barème IR trouvé pour {annee}")
    return bareme


@router.get("/taux-cotisations/{annee}", response_model=List[TauxCotisationOut])
def get_taux_cotisations(
    annee: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Retourne les taux CNSS/AMO pour une année donnée."""
    taux = db.query(models.TauxCotisation).filter_by(annee=annee).all()
    if not taux:
        raise HTTPException(status_code=404, detail=f"Aucun taux trouvé pour {annee}")
    return [sortie_taux_cotisation(t) for t in taux]


@router.get("/deductions-ir/{annee}", response_model=List[DeductionIROut])
def get_deductions_ir(
    annee: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Retourne les déductions IR pour une année donnée."""
    return db.query(models.DeductionIR).filter_by(annee=annee).all()


@router.patch("/taux-cotisations/{taux_id}", response_model=TauxCotisationOut)
def modifier_taux(
    taux_id: int,
    data: TauxCotisationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(requiert_ecriture),
):
    """Modifie un taux de cotisation (admin uniquement)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    taux = db.query(models.TauxCotisation).filter_by(id=taux_id).first()
    if not taux:
        raise HTTPException(status_code=404, detail="Taux introuvable")

    if data.taux_sal is not None: taux.taux_sal = data.taux_sal
    if data.taux_pat is not None: taux.taux_pat = data.taux_pat
    if data.plafond  is not None: taux.plafond  = data.plafond

    db.commit()
    db.refresh(taux)
    return sortie_taux_cotisation(taux)


@router.get("/annees-disponibles")
def annees_disponibles(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Retourne les années pour lesquelles on a des paramètres fiscaux."""
    annees = db.query(models.BaremeIR.annee).distinct().order_by(models.BaremeIR.annee).all()
    return [a[0] for a in annees]


# ── Calcul IR depuis la DB ────────────────────────────────────────────────────

def calculer_ir_db(
    salaire_brut_annuel: float,
    situation: str,
    nb_enfants: int,
    annee: int,
    db: Session,
) -> float:
    """Calcule l'IR annuel depuis le barème en base de données."""

    # Frais professionnels — CGI art. 59-I-A :
    # 35 % si le revenu brut annuel imposable n'excède pas 78 000 MAD ;
    # 25 % au-delà, avec un plafond annuel de 35 000 MAD.
    taux_fp = 0.35 if salaire_brut_annuel <= 78000 else 0.25
    abattement_fp = min(salaire_brut_annuel * taux_fp, 35000)

    # Cotisations déductibles
    taux = {t.code: t for t in db.query(models.TauxCotisation).filter_by(annee=annee).all()}

    plafond_cnss = taux.get("cnss_retraite", None)
    plafond_an   = plafond_cnss.plafond if plafond_cnss else 72000
    base_cnss    = min(salaire_brut_annuel, plafond_an)

    deduct_retraite = base_cnss * (taux["cnss_retraite"].taux_sal if "cnss_retraite" in taux else 0.0448)
    deduct_amo      = salaire_brut_annuel * (taux["amo"].taux_sal if "amo" in taux else 0.0226)

    revenu_net = salaire_brut_annuel - abattement_fp - deduct_retraite - deduct_amo

    # Barème IR
    bareme = db.query(models.BaremeIR).filter_by(annee=annee).order_by(models.BaremeIR.tranche_min).all()
    ir = 0.0
    for tranche in bareme:
        if revenu_net < tranche.tranche_min:
            break
        if tranche.tranche_max is None or revenu_net <= tranche.tranche_max:
            ir = revenu_net * tranche.taux - tranche.deduction
            break
        ir = revenu_net * tranche.taux - tranche.deduction

    # Déductions familiales
    deductions = {d.code: d for d in db.query(models.DeductionIR).filter_by(annee=annee).all()}

    # Réduction pour charges de famille : le plafond légal porte sur le NOMBRE
    # TOTAL de personnes à charge, et non 6 enfants + 1 conjoint.
    conjoint_charge = 1 if situation == "marie" and "conjoint" in deductions else 0
    enfants_charge = max(0, int(nb_enfants or 0))
    nb_personnes_charge = min(6, conjoint_charge + enfants_charge)

    if nb_personnes_charge:
        # Les jeux de données 2025/2026 utilisent le même montant par personne
        # pour conjoint et enfant. On lit la valeur en base afin de conserver le
        # moteur paramétrable par exercice.
        ref = deductions.get("enfant") or deductions.get("conjoint")
        if ref:
            ir -= nb_personnes_charge * ref.montant_an

    return max(0.0, ir)


def calculer_cotisations_db(employe: models.Employe, annee: int, db: Session) -> dict:
    """Calcule toutes les cotisations depuis la DB pour un exercice donné."""
    taux_list = db.query(models.TauxCotisation).filter_by(annee=annee).all()
    taux = {t.code: t for t in taux_list}

    plafond_mensuel = (taux["cnss_retraite"].plafond / 12) if "cnss_retraite" in taux else 6000
    base_cnss       = min(employe.salaire_brut, plafond_mensuel)
    base_plein      = employe.salaire_brut

    # Salarial
    cnss_ret_sal = base_cnss  * (taux["cnss_retraite"].taux_sal if "cnss_retraite" in taux else 0.0448)
    amo_sal      = base_plein * (taux["amo"].taux_sal            if "amo"           in taux else 0.0226)
    total_sal    = cnss_ret_sal + amo_sal

    # IR mensuel
    ir_annuel = calculer_ir_db(employe.salaire_brut * 12, employe.situation_familiale, employe.nb_enfants, annee, db)
    ir_mensuel = ir_annuel / 12

    salaire_net = employe.salaire_brut - total_sal - ir_mensuel

    # Patronal
    cnss_ret_pat = base_cnss  * (taux["cnss_retraite"].taux_pat  if "cnss_retraite" in taux else 0.0798)
    prest_fam    = base_cnss  * (taux["cnss_prest_fam"].taux_pat if "cnss_prest_fam" in taux else 0.0692)
    amo_pat      = base_plein * (taux["amo"].taux_pat             if "amo"           in taux else 0.0226)
    accidents    = base_plein * (taux["accidents"].taux_pat       if "accidents"     in taux else 0.0100)
    formation    = base_plein * (taux["formation_prof"].taux_pat  if "formation_prof" in taux else 0.0160)
    total_pat    = cnss_ret_pat + prest_fam + amo_pat + accidents + formation

    return {
        "salaire_brut":        employe.salaire_brut,
        "cnss_retraite_sal":   cnss_ret_sal,
        "amo_sal":             amo_sal,
        "total_retenues_sal":  total_sal,
        "ir":                  ir_mensuel,
        "salaire_net":         salaire_net,
        "cnss_retraite_pat":   cnss_ret_pat,
        "prestations_fam":     prest_fam,
        "amo_pat":             amo_pat,
        "accidents":           accidents,
        "formation":           formation,
        "total_charges_pat":   total_pat,
        "cout_employeur":      employe.salaire_brut + total_pat,
    }
