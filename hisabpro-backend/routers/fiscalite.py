# -*- coding: utf-8 -*-
"""Résultat fiscal et IS — Patch 08.1 à 08.6."""
from datetime import date as date_cls
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session, joinedload

from database import get_db
from auth import get_current_user, requiert_ecriture
import models
from services.fiscalite_is_service import CATEGORIES_IS, calculer_is, money
from services.fiscalite_retraitements_service import CATEGORIES_RETRAITEMENT, analyser_retraitements
from services.fiscalite_deficits_service import (
    construire_situation_deficits,
    montant_amortissements_comptabilises,
    ventiler_deficit_genere,
)
from services.fiscalite_cm_service import calculer_cotisation_minimale
from services.fiscalite_acomptes_service import (
    construire_acomptes,
    calculer_liquidation,
    determiner_reference_acomptes,
    construire_snapshot_liquidation,
)
from services.fiscalite_css_service import calculer_css
from services.fiscalite_credits_service import TYPES_CREDIT_IS, construire_credits_is
from services.exercice_verrou_service import verrouiller_mutation_fiscale, verrouiller_deficits_fiscaux

router = APIRouter(prefix="/api/fiscalite", tags=["fiscalite"])


class ParametresISIn(BaseModel):
    categorie_is: str = "droit_commun"
    justification_regime: Optional[str] = None
    maintien_taux_35_transition: bool = False
    deficit_reportable_disponible: Decimal = Field(default=Decimal("0.00"), ge=0)
    taux_is_force: Optional[Decimal] = Field(default=None, ge=0, le=100)
    justification_taux_force: Optional[str] = None
    # Cotisation minimale — Patch 08.4
    cm_base_exclue: Decimal = Field(default=Decimal("0.00"), ge=0)
    cm_justification_base_exclue: Optional[str] = None
    cm_base_taux_reduit_015: Decimal = Field(default=Decimal("0.00"), ge=0)
    cm_justification_taux_reduit: Optional[str] = None
    cm_exoneration_totale: bool = False
    cm_justification_exoneration: Optional[str] = None
    cm_minimum_3000_exonere: bool = False
    cm_justification_minimum_exonere: Optional[str] = None
    # Acomptes provisionnels — Patch 08.5
    acomptes_reference_forcee: Optional[Decimal] = Field(default=None, ge=0)
    acomptes_justification_reference_forcee: Optional[str] = None
    # Contribution sociale de solidarité — Patch 08.6
    css_benefice_reference_forcee: Optional[Decimal] = Field(default=None, ge=0)
    css_justification_reference_forcee: Optional[str] = None
    css_exoneration_permanente: bool = False
    css_justification_exoneration: Optional[str] = None

    @model_validator(mode="after")
    def valider(self):
        if self.categorie_is not in CATEGORIES_IS:
            raise ValueError("Catégorie IS inconnue")
        if self.categorie_is != "droit_commun" and not (self.justification_regime or "").strip():
            raise ValueError("Une justification est obligatoire pour un régime IS particulier.")
        if self.taux_is_force is not None and not (self.justification_taux_force or "").strip():
            raise ValueError("Une justification est obligatoire lorsqu'un taux IS est forcé.")
        if money(self.cm_base_exclue) > 0 and not (self.cm_justification_base_exclue or "").strip():
            raise ValueError("Une justification est obligatoire pour exclure une partie de la base de cotisation minimale.")
        if money(self.cm_base_taux_reduit_015) > 0 and not (self.cm_justification_taux_reduit or "").strip():
            raise ValueError("Une justification est obligatoire pour appliquer le taux CM réduit de 0,15%.")
        if self.cm_exoneration_totale and not (self.cm_justification_exoneration or "").strip():
            raise ValueError("Une justification est obligatoire pour l'exonération totale de cotisation minimale.")
        if self.cm_minimum_3000_exonere and not (self.cm_justification_minimum_exonere or "").strip():
            raise ValueError("Une justification est obligatoire pour neutraliser le minimum de 3 000 MAD.")
        if self.acomptes_reference_forcee is not None and not (self.acomptes_justification_reference_forcee or "").strip():
            raise ValueError("Une justification est obligatoire lorsqu'une référence annuelle d'acomptes est forcée.")
        if self.css_benefice_reference_forcee is not None and not (self.css_justification_reference_forcee or "").strip():
            raise ValueError("Une justification est obligatoire lorsqu'un bénéfice de référence CSS est forcé.")
        if self.css_exoneration_permanente and not (self.css_justification_exoneration or "").strip():
            raise ValueError("Une justification est obligatoire pour l'exonération permanente de CSS.")
        return self


class RetraitementIn(BaseModel):
    type: str
    categorie: str = "autre"
    libelle: str = Field(min_length=2, max_length=250)
    montant: Decimal = Field(gt=0)
    compte_source: Optional[str] = Field(default=None, max_length=120)
    reference: Optional[str] = Field(default=None, max_length=120)
    commentaire: Optional[str] = None

    @model_validator(mode="after")
    def valider_type(self):
        if self.type not in ("reintegration", "deduction"):
            raise ValueError("type doit être 'reintegration' ou 'deduction'")
        if self.categorie not in CATEGORIES_RETRAITEMENT:
            raise ValueError("Catégorie de retraitement fiscal inconnue")
        return self


class DeficitFiscalIn(BaseModel):
    exercice_origine: int = Field(ge=1900, le=2200)
    montant_ordinaire: Decimal = Field(default=Decimal("0.00"), ge=0)
    montant_amortissements: Decimal = Field(default=Decimal("0.00"), ge=0)
    commentaire: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def valider_total(self):
        if money(self.montant_ordinaire) + money(self.montant_amortissements) <= 0:
            raise ValueError("Le déficit fiscal doit avoir un montant positif.")
        return self


class AcompteISIn(BaseModel):
    montant_verse: Decimal = Field(default=Decimal("0.00"), ge=0)
    date_versement: Optional[date_cls] = None
    reference_paiement: Optional[str] = Field(default=None, max_length=120)
    dispense: bool = False
    reference_dispense: Optional[str] = Field(default=None, max_length=200)
    commentaire: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def valider_acompte(self):
        montant = money(self.montant_verse)
        if montant <= 0 and not self.dispense:
            raise ValueError("Renseignez un paiement positif ou marquez l'acompte comme dispensé.")
        if montant > 0 and self.date_versement is None:
            raise ValueError("La date de versement est obligatoire pour un acompte payé.")
        if self.dispense and montant > 0:
            raise ValueError("Un acompte ne peut pas être à la fois payé et marqué comme dispensé.")
        if self.dispense and not (self.reference_dispense or "").strip():
            raise ValueError("La référence de la déclaration de dispense est obligatoire.")
        return self


class CreditISIn(BaseModel):
    type: str
    montant: Decimal = Field(gt=0)
    montant_deja_impute_acomptes: Decimal = Field(default=Decimal("0.00"), ge=0)
    date_retenue: Optional[date_cls] = None
    reference: str = Field(min_length=2, max_length=160)
    commentaire: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def valider_credit(self):
        if self.type not in TYPES_CREDIT_IS:
            raise ValueError("Type de crédit IS inconnu.")
        if money(self.montant_deja_impute_acomptes) > money(self.montant):
            raise ValueError("Le montant déjà imputé sur acomptes ne peut pas dépasser le crédit.")
        if self.type == "autre" and not (self.commentaire or "").strip():
            raise ValueError("Une justification est obligatoire pour un autre crédit / retenue IS.")
        return self


class CSSPaiementIn(BaseModel):
    montant_verse: Decimal = Field(gt=0)
    date_versement: date_cls
    reference_paiement: str = Field(min_length=2, max_length=160)
    commentaire: Optional[str] = Field(default=None, max_length=1000)


def _parametres_dict(p):
    if not p:
        return {
            "categorie_is": "droit_commun",
            "justification_regime": None,
            "maintien_taux_35_transition": False,
            "deficit_reportable_disponible": Decimal("0.00"),
            "taux_is_force": None,
            "justification_taux_force": None,
            "cm_base_exclue": Decimal("0.00"),
            "cm_justification_base_exclue": None,
            "cm_base_taux_reduit_015": Decimal("0.00"),
            "cm_justification_taux_reduit": None,
            "cm_exoneration_totale": False,
            "cm_justification_exoneration": None,
            "cm_minimum_3000_exonere": False,
            "cm_justification_minimum_exonere": None,
            "acomptes_reference_forcee": None,
            "acomptes_justification_reference_forcee": None,
            "css_benefice_reference_forcee": None,
            "css_justification_reference_forcee": None,
            "css_exoneration_permanente": False,
            "css_justification_exoneration": None,
        }
    return {
        "categorie_is": p.categorie_is,
        "justification_regime": p.justification_regime,
        "maintien_taux_35_transition": bool(p.maintien_taux_35_transition),
        "deficit_reportable_disponible": money(p.deficit_reportable_disponible),
        "taux_is_force": p.taux_is_force,
        "justification_taux_force": p.justification_taux_force,
        "cm_base_exclue": money(getattr(p, "cm_base_exclue", 0)),
        "cm_justification_base_exclue": getattr(p, "cm_justification_base_exclue", None),
        "cm_base_taux_reduit_015": money(getattr(p, "cm_base_taux_reduit_015", 0)),
        "cm_justification_taux_reduit": getattr(p, "cm_justification_taux_reduit", None),
        "cm_exoneration_totale": bool(getattr(p, "cm_exoneration_totale", False)),
        "cm_justification_exoneration": getattr(p, "cm_justification_exoneration", None),
        "cm_minimum_3000_exonere": bool(getattr(p, "cm_minimum_3000_exonere", False)),
        "cm_justification_minimum_exonere": getattr(p, "cm_justification_minimum_exonere", None),
        "acomptes_reference_forcee": getattr(p, "acomptes_reference_forcee", None),
        "acomptes_justification_reference_forcee": getattr(p, "acomptes_justification_reference_forcee", None),
        "css_benefice_reference_forcee": getattr(p, "css_benefice_reference_forcee", None),
        "css_justification_reference_forcee": getattr(p, "css_justification_reference_forcee", None),
        "css_exoneration_permanente": bool(getattr(p, "css_exoneration_permanente", False)),
        "css_justification_exoneration": getattr(p, "css_justification_exoneration", None),
    }


def _charger_ecritures_fiscales(db: Session, societe_id: int, exercice: int):
    """Charge les écritures de l'exercice en excluant les écritures techniques de clôture.

    Les clôtures historiques 01→07C.2 pouvaient être en OD ; la référence
    CLOTURE-N est donc exclue en plus du journal/source CL.
    """
    return (
        db.query(models.Ecriture)
        .options(joinedload(models.Ecriture.lignes))
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
        )
        .all()
    )


def _est_cloture_technique(ecriture) -> bool:
    ref = (ecriture.reference or "").upper()
    journal = getattr(ecriture.journal, "value", ecriture.journal)
    return ecriture.source == "cloture" or journal == "CL" or ref.startswith("CLOTURE-")


def _source_comptable(db: Session, societe_id: int, exercice: int):
    ecritures = _charger_ecritures_fiscales(db, societe_id, exercice)
    validees = [e for e in ecritures if e.est_validee and not _est_cloture_technique(e)]
    brouillons = [e for e in ecritures if not e.est_validee and not _est_cloture_technique(e)]

    produits = Decimal("0.00")
    charges_hors_is = Decimal("0.00")
    is_comptabilise = Decimal("0.00")
    impot_courant_comptabilise = Decimal("0.00")
    impots_resultat_par_compte = {}
    charges_par_compte = {}
    produits_par_compte = {}
    charges_sans_reference = Decimal("0.00")
    charges_sans_reference_par_compte = {}

    for e in validees:
        ecriture_sans_reference = not (e.reference or "").strip()
        for l in e.lignes:
            compte = (l.compte or "").strip()
            debit = money(l.debit)
            credit = money(l.credit)
            if compte.startswith("7"):
                mouvement = money(credit - debit)
                produits += mouvement
                produits_par_compte[compte] = money(produits_par_compte.get(compte, Decimal("0.00")) + mouvement)
            elif compte.startswith("67"):
                mouvement = money(debit - credit)
                is_comptabilise += mouvement
                impots_resultat_par_compte[compte] = money(
                    impots_resultat_par_compte.get(compte, Decimal("0.00")) + mouvement
                )
                if compte.startswith(("6701", "6705")):
                    impot_courant_comptabilise += mouvement
            elif compte.startswith("6"):
                mouvement = money(debit - credit)
                charges_hors_is += mouvement
                charges_par_compte[compte] = money(charges_par_compte.get(compte, Decimal("0.00")) + mouvement)
                if ecriture_sans_reference:
                    charges_sans_reference += mouvement
                    charges_sans_reference_par_compte[compte] = money(
                        charges_sans_reference_par_compte.get(compte, Decimal("0.00")) + mouvement
                    )

    resultat_avant_is = money(produits - charges_hors_is)
    return {
        "resultat_comptable_avant_is": resultat_avant_is,
        "produits_comptables": money(produits),
        "charges_hors_is": money(charges_hors_is),
        "is_deja_comptabilise": money(is_comptabilise),
        "impot_courant_comptabilise": money(impot_courant_comptabilise),
        "nb_ecritures_validees": len(validees),
        "nb_brouillons_exclus": len(brouillons),
        "_charges_par_compte": charges_par_compte,
        "_produits_par_compte": produits_par_compte,
        "_charges_sans_reference": money(max(Decimal("0.00"), charges_sans_reference)),
        "_charges_sans_reference_par_compte": charges_sans_reference_par_compte,
        "_impots_resultat_par_compte": impots_resultat_par_compte,
    }


def _etat_comptabilisation_is(source: dict, liquidation: dict):
    """Compare l'impôt courant calculé avec les comptes 6701/6705.

    Les comptes 6708 (rappels/dégrèvements) restent dans la charge d'impôt du
    CPC, mais ne remplacent jamais la comptabilisation de l'impôt courant de
    l'exercice.
    """
    attendu = money((liquidation or {}).get("impot_du_avant_acomptes"))
    nature = (liquidation or {}).get("nature_impot_du") or "IS"
    compte_attendu = "6705" if nature == "CM" else "6701"
    par_compte = source.get("_impots_resultat_par_compte") or {}
    montant_compte_attendu = money(par_compte.get(compte_attendu))
    courant_total = money(source.get("impot_courant_comptabilise"))
    autre_compte = "6701" if compte_attendu == "6705" else "6705"
    montant_autre = money(par_compte.get(autre_compte))
    absente = courant_total == Decimal("0.00")
    coherente = (
        montant_compte_attendu == attendu
        and montant_autre == Decimal("0.00")
        and courant_total == attendu
    )
    return {
        "attendu": attendu,
        "nature_impot": nature,
        "compte_charge_attendu": compte_attendu,
        "montant_compte_attendu": montant_compte_attendu,
        "montant_autre_compte_courant": montant_autre,
        "comptabilise": courant_total,
        "absente": absente,
        "coherente": coherente,
    }


def _serialiser_retraitement(r):
    return {
        "id": r.id,
        "niveau": "manuel",
        "type": r.type,
        "type_suggere": r.type,
        "categorie": r.categorie,
        "libelle": r.libelle,
        "montant": money(r.montant),
        "montant_detecte": money(r.montant),
        "compte_source": r.compte_source,
        "reference": r.reference,
        "commentaire": r.commentaire,
        "automatique": False,
        "impacte_calcul": True,
    }


def _serialiser_deficit(d):
    return {
        "id": d.id,
        "exercice_origine": d.exercice_origine,
        "montant_ordinaire": money(d.montant_ordinaire),
        "montant_amortissements": money(d.montant_amortissements),
        "montant_total": money(money(d.montant_ordinaire) + money(d.montant_amortissements)),
        "source": d.source,
        "commentaire": d.commentaire,
    }


def _charger_deficits(db: Session, societe_id: int):
    deficits = db.query(models.FiscalDeficit).filter_by(societe_id=societe_id).order_by(
        models.FiscalDeficit.exercice_origine.asc(), models.FiscalDeficit.id.asc()
    ).all()
    imputations = db.query(models.FiscalDeficitImputation).filter_by(societe_id=societe_id).order_by(
        models.FiscalDeficitImputation.exercice_cible.asc(), models.FiscalDeficitImputation.id.asc()
    ).all()
    return deficits, imputations


def _reintegrations_amortissements(manuels, automatiques) -> Decimal:
    categories = {"amortissements_non_deductibles", "amortissement_vehicule"}
    total = Decimal("0.00")
    for r in manuels:
        if r.type == "reintegration" and r.categorie in categories:
            total += money(r.montant)
    for r in automatiques:
        if r.get("type") == "reintegration" and r.get("categorie") in categories:
            total += money(r.get("montant"))
    return money(total)


def _serialiser_liquidation(l):
    if not l:
        return None
    return {
        "id": l.id,
        "exercice": l.exercice,
        "benefice_fiscal_imposable": money(l.benefice_fiscal_imposable),
        "is_theorique": money(l.is_theorique),
        "cm_exigible": money(l.cm_exigible),
        "impot_du": money(l.impot_du),
        "nature_impot": l.nature_impot,
        "acomptes_imputables": money(l.acomptes_imputables),
        "credits_is_imputables": money(getattr(l, "credits_is_imputables", 0)),
        "solde_a_payer": money(l.solde_a_payer),
        "excedent_acomptes": money(l.excedent_acomptes),
        "excedent_credits_is": money(getattr(l, "excedent_credits_is", 0)),
        "excedent_total": money(getattr(l, "excedent_total", getattr(l, "excedent_acomptes", 0))),
        "detail": getattr(l, "snapshot_detail", None),
        "date_confirmation": l.date_confirmation,
        "confirmee_par": l.confirmee_par,
    }


def _serialiser_acompte(a):
    return {
        "numero": a.numero,
        "montant_verse": money(a.montant_verse),
        "date_versement": a.date_versement,
        "reference_paiement": a.reference_paiement,
        "dispense": bool(a.dispense),
        "reference_dispense": a.reference_dispense,
        "commentaire": a.commentaire,
    }


def _serialiser_credit_is(c):
    return {
        "id": c.id,
        "type": c.type,
        "montant": money(c.montant),
        "montant_deja_impute_acomptes": money(c.montant_deja_impute_acomptes),
        "date_retenue": c.date_retenue,
        "reference": c.reference,
        "commentaire": c.commentaire,
    }


def _serialiser_css_paiement(p):
    if not p:
        return None
    return {
        "id": p.id,
        "annee": p.annee,
        "montant_verse": money(p.montant_verse),
        "date_versement": p.date_versement,
        "reference_paiement": p.reference_paiement,
        "commentaire": p.commentaire,
    }


def _date_fin_exercice(db: Session, societe_id: int, exercice: int):
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=exercice).first()
    return ex.date_fin if ex else date_cls(exercice, 12, 31)


def _date_debut_exercice(db: Session, societe_id: int, exercice: int):
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=exercice).first()
    return ex.date_debut if ex else date_cls(exercice, 1, 1)


def _exercice_reference_existe(db: Session, societe_id: int, exercice: int) -> bool:
    """Indique s'il existe un exercice comptable antérieur au courant.

    On s'appuie d'abord sur les dates pour rester compatible avec les exercices
    décalés, puis sur l'année comme repli pour les anciennes données.
    """
    courant = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=exercice
    ).first()
    q = db.query(models.ExerciceComptable.id).filter(
        models.ExerciceComptable.societe_id == societe_id
    )
    if courant and courant.date_debut:
        return q.filter(models.ExerciceComptable.date_fin < courant.date_debut).first() is not None
    return q.filter(models.ExerciceComptable.annee < exercice).first() is not None


def _verifier_liquidation_non_confirmee(db: Session, societe_id: int, exercice: int):
    verrouiller_mutation_fiscale(db, societe_id, exercice)
    if db.query(models.FiscalLiquidationIS).filter_by(societe_id=societe_id, exercice=exercice).first():
        raise HTTPException(409, "La liquidation fiscale de cet exercice est confirmée et immuable.")


def _verifier_calcul_is_modifiable(db: Session, societe_id: int, exercice: int):
    """Fige, après clôture, ce qui détermine la charge d'impôt courant de N.

    Les éléments de règlement (acomptes, retenues/crédits) et les références
    documentaires qui n'altèrent pas l'impôt courant peuvent encore être
    complétés jusqu'à la confirmation de liquidation.
    """
    _verifier_liquidation_non_confirmee(db, societe_id, exercice)
    ex = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=exercice
    ).first()
    if ex and ex.statut == "cloture":
        raise HTTPException(409,
            "Exercice clôturé : les éléments qui déterminent l'impôt courant sont figés. "
            "Toute correction doit suivre une procédure comptable/fiscale auditée.")


_PARAMETRES_IMPACTANT_IMPOT_COURANT = (
    "categorie_is",
    "justification_regime",
    "maintien_taux_35_transition",
    "deficit_reportable_disponible",
    "taux_is_force",
    "justification_taux_force",
    "cm_base_exclue",
    "cm_justification_base_exclue",
    "cm_base_taux_reduit_015",
    "cm_justification_taux_reduit",
    "cm_exoneration_totale",
    "cm_justification_exoneration",
    "cm_minimum_3000_exonere",
    "cm_justification_minimum_exonere",
)


def _normaliser_parametre_comparable(v):
    if isinstance(v, Decimal):
        return money(v)
    if isinstance(v, str):
        return v.strip()
    return v


def _verifier_parametres_is_modifiables(db: Session, societe_id: int, exercice: int, data):
    """Autorise après clôture uniquement les paramètres de liquidation/référence.

    Le PUT transporte tout le formulaire. On compare donc les champs qui
    influencent réellement l'IS/CM à leurs valeurs déjà enregistrées : une
    référence annuelle d'acomptes ou une référence CSS peut encore être
    documentée après clôture, sans permettre de recalculer rétroactivement la
    charge 6701/6705 déjà arrêtée.
    """
    _verifier_liquidation_non_confirmee(db, societe_id, exercice)
    ex = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=exercice
    ).first()
    if not ex or ex.statut != "cloture":
        return

    p = db.query(models.FiscalParametreExercice).filter_by(
        societe_id=societe_id, exercice=exercice
    ).first()
    avant = _parametres_dict(p)
    apres = data.model_dump()
    modifies = [
        champ for champ in _PARAMETRES_IMPACTANT_IMPOT_COURANT
        if _normaliser_parametre_comparable(avant.get(champ))
        != _normaliser_parametre_comparable(apres.get(champ))
    ]
    if modifies:
        raise HTTPException(409,
            "Exercice clôturé : les paramètres qui déterminent l'IS/CM sont figés. "
            "Les paramètres de liquidation (référence d'acomptes/CSS) restent complétables "
            "jusqu'à confirmation de la liquidation.")


@router.get("/is/{exercice}")
def situation_is(
    exercice: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if exercice < 2023:
        raise HTTPException(400, "Le moteur fiscal IS actuel couvre les exercices 2023 et suivants.")

    societe_id = current_user["societe_id"]
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    if not societe:
        raise HTTPException(404, "Société introuvable")

    p = db.query(models.FiscalParametreExercice).filter_by(
        societe_id=societe_id, exercice=exercice
    ).first()
    params = _parametres_dict(p)

    manuels = db.query(models.FiscalRetraitement).filter_by(
        societe_id=societe_id, exercice=exercice
    ).order_by(models.FiscalRetraitement.id.asc()).all()

    source = _source_comptable(db, societe_id, exercice)
    vehicules = db.query(models.Immobilisation).filter(
        models.Immobilisation.societe_id == societe_id,
        models.Immobilisation.vehicule_tourisme.is_(True),
        models.Immobilisation.valeur_brute > Decimal("400000.00"),
    ).all()
    analyse = analyser_retraitements(
        charges_par_compte=source["_charges_par_compte"],
        produits_par_compte=source["_produits_par_compte"],
        charges_sans_reference=source["_charges_sans_reference"],
        charges_sans_reference_par_compte=source["_charges_sans_reference_par_compte"],
        vehicules_tourisme_superieurs_plafond=[
            {"id": i.id, "designation": i.designation, "valeur_brute": money(i.valeur_brute)} for i in vehicules
        ],
    )
    auto = analyse["automatiques"]

    reintegrations = sum((money(r.montant) for r in manuels if r.type == "reintegration"), Decimal("0.00"))
    deductions = sum((money(r.montant) for r in manuels if r.type == "deduction"), Decimal("0.00"))
    reintegrations += analyse["total_automatique_reintegrations"]
    deductions += analyse["total_automatique_deductions"]

    # Premier passage sans déficits antérieurs : il fixe la base fiscale avant
    # imputation et, en cas de perte, le déficit généré par l'exercice.
    try:
        calcul_avant_deficits = calculer_is(
            exercice=exercice,
            resultat_comptable_avant_is=source["resultat_comptable_avant_is"],
            reintegrations=reintegrations,
            deductions=deductions,
            deficit_reportable_disponible=Decimal("0.00"),
            categorie_is=params["categorie_is"],
            maintien_taux_35_transition=params["maintien_taux_35_transition"],
            taux_force=params["taux_is_force"],
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    deficits_db, imputations_db = _charger_deficits(db, societe_id)
    situation_deficits = construire_situation_deficits(
        deficits=deficits_db,
        imputations=imputations_db,
        exercice_cible=exercice,
        base_avant_deficit=max(Decimal("0.00"), money(calcul_avant_deficits["resultat_fiscal_avant_deficit"])),
    )

    # Calcul final : l'imputation proposée est déterministe et respecte les
    # millésimes. Les imputations confirmées sont historisées séparément ;
    # si la base fiscale change, l'UI demande de reconfirmer la proposition.
    calcul = calculer_is(
        exercice=exercice,
        resultat_comptable_avant_is=source["resultat_comptable_avant_is"],
        reintegrations=reintegrations,
        deductions=deductions,
        deficit_reportable_disponible=situation_deficits["disponible_total"],
        categorie_is=params["categorie_is"],
        maintien_taux_35_transition=params["maintien_taux_35_transition"],
        taux_force=params["taux_is_force"],
    )

    try:
        cotisation_minimale = calculer_cotisation_minimale(
            produits_par_compte=source["_produits_par_compte"],
            is_theorique=calcul["is_theorique"],
            base_exclue=params["cm_base_exclue"],
            base_taux_reduit_015=params["cm_base_taux_reduit_015"],
            exoneration_totale=params["cm_exoneration_totale"],
            minimum_3000_exonere=params["cm_minimum_3000_exonere"],
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    # Patch 08.5 — acomptes provisionnels et liquidation.
    liquidation_precedente_db = db.query(models.FiscalLiquidationIS).filter_by(
        societe_id=societe_id, exercice=exercice - 1
    ).first()
    liquidation_courante_db = db.query(models.FiscalLiquidationIS).filter_by(
        societe_id=societe_id, exercice=exercice
    ).first()
    liquidation_precedente = _serialiser_liquidation(liquidation_precedente_db)
    try:
        reference_acomptes = determiner_reference_acomptes(
            exercice=exercice,
            liquidation_precedente=liquidation_precedente,
            categorie_is=params["categorie_is"],
            maintien_taux_35_transition=params["maintien_taux_35_transition"],
            taux_force=params["taux_is_force"],
            reference_forcee=params.get("acomptes_reference_forcee"),
            exercice_reference_existe=_exercice_reference_existe(db, societe_id, exercice),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    acomptes_db = db.query(models.FiscalAcompteIS).filter_by(
        societe_id=societe_id, exercice=exercice
    ).order_by(models.FiscalAcompteIS.numero.asc()).all()

    # Patch 08.6 — les retenues déjà imputées sur acomptes doivent compter dans
    # la couverture de ces acomptes, tout en étant exclues du reliquat disponible
    # à la liquidation annuelle (pas de double imputation).
    credits_db = db.query(models.FiscalCreditIS).filter_by(
        societe_id=societe_id, exercice=exercice
    ).order_by(models.FiscalCreditIS.type.asc(), models.FiscalCreditIS.id.asc()).all()
    try:
        credits_is = construire_credits_is(credits_db)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    excedent_precedent = money(liquidation_precedente.get("excedent_acomptes")) if liquidation_precedente else Decimal("0.00")
    situation_acomptes = construire_acomptes(
        date_debut=_date_debut_exercice(db, societe_id, exercice),
        reference=reference_acomptes,
        paiements=[_serialiser_acompte(a) for a in acomptes_db],
        excedent_precedent=excedent_precedent,
        credits_ras_deja_imputes=credits_is["total_deja_impute_acomptes"],
    )

    liquidation_detail = calculer_liquidation(
        impot_du_avant_acomptes=cotisation_minimale["impot_du_avant_acomptes"],
        situation_acomptes=situation_acomptes,
        credits_is=credits_is,
    )
    comptabilisation_is = _etat_comptabilisation_is(source, {
        "impot_du_avant_acomptes": cotisation_minimale["impot_du_avant_acomptes"],
        "nature_impot_du": cotisation_minimale["nature_impot_du"],
    })

    # CSS de l'année : assise sur le bénéfice net fiscal du dernier exercice clos.
    try:
        css = calculer_css(
            annee=exercice,
            benefice_reference=(liquidation_precedente or {}).get("benefice_fiscal_imposable") if liquidation_precedente else None,
            exercice_reference=exercice - 1,
            date_fin_reference=_date_fin_exercice(db, societe_id, exercice - 1),
            reference_forcee=params.get("css_benefice_reference_forcee"),
            exoneration_permanente=params.get("css_exoneration_permanente", False),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    css_paiement_db = db.query(models.FiscalCSSPaiement).filter_by(
        societe_id=societe_id, annee=exercice
    ).first()
    css_paiement = _serialiser_css_paiement(css_paiement_db)
    css_verse = money((css_paiement or {}).get("montant_verse"))
    css_reste = money(max(Decimal("0.00"), money(css.get("montant_du")) - css_verse))
    css_excedent = money(max(Decimal("0.00"), css_verse - money(css.get("montant_du"))))
    if not css.get("applicable"):
        css_statut = "hors_periode"
    elif not css.get("disponible"):
        css_statut = "reference_manquante"
    elif money(css.get("montant_du")) == 0:
        css_statut = "non_due"
    elif css_reste == 0:
        css_statut = "solde"
    elif css_paiement and css_verse > 0:
        css_statut = "partiel"
    elif css.get("date_echeance") and date_cls.today() > css["date_echeance"]:
        css_statut = "en_retard"
    else:
        css_statut = "a_payer"
    css.update({
        "paiement": css_paiement,
        "montant_verse": css_verse,
        "reste_a_payer": css_reste,
        "excedent_verse": css_excedent,
        "statut": css_statut,
    })

    amortissements_comptabilises = montant_amortissements_comptabilises(source["_charges_par_compte"])
    amortissements_reintegres = _reintegrations_amortissements(manuels, auto)
    amortissements_deductibles = money(max(Decimal("0.00"), amortissements_comptabilises - amortissements_reintegres))
    deficit_genere = ventiler_deficit_genere(calcul["deficit_fiscal_genere"], amortissements_deductibles)

    # Enrichit les lots DB avec leurs soldes/états calculés.
    lots_par_id = {l["id"]: l for l in situation_deficits["lots"]}
    inventaire_deficits = []
    for d in deficits_db:
        ligne = _serialiser_deficit(d)
        ligne.update(lots_par_id.get(d.id, {}))
        inventaire_deficits.append(ligne)

    alertes = []
    if source["nb_brouillons_exclus"]:
        alertes.append(
            f"{source['nb_brouillons_exclus']} brouillon(s) exclu(s) : le calcul fiscal repose uniquement sur les écritures validées."
        )
    if exercice > 2026:
        alertes.append(
            f"Exercice {exercice} : estimation basée sur les taux cibles actuellement prévus par le CGI 2026. "
            f"À confirmer avec le CGI / la Loi de Finances {exercice} dès publication."
        )
    if params["categorie_is"] != "droit_commun":
        alertes.append("Régime IS particulier appliqué : la justification enregistrée doit être conservée avec le dossier fiscal.")
    if params["taux_is_force"] is not None:
        alertes.append("Un taux IS dérogatoire est forcé manuellement : vérifiez sa justification juridique.")
    if (societe.regime_fiscal or "is") != "is":
        alertes.append(f"Le régime fiscal société est '{societe.regime_fiscal}' et non 'is'. Vérifiez l'applicabilité de ce calcul.")
    if money(params.get("deficit_reportable_disponible")) > 0:
        alertes.append(
            "Ancien solde de déficit non millésimé détecté dans les paramètres 08.1 : il n'est plus imputé automatiquement. "
            "Ventilez-le par exercice d'origine dans le tableau des déficits fiscaux afin de contrôler son délai de report."
        )
    if situation_deficits["ordinaire_expire"] > 0:
        alertes.append(
            f"{money(situation_deficits['ordinaire_expire'])} MAD de déficit ordinaire sont expirés pour l'exercice {exercice} "
            "au regard de la limite des quatre exercices de l'article 12 du CGI."
        )
    if situation_deficits["total_confirme"] > 0 and not situation_deficits["confirmation_a_jour"]:
        alertes.append(
            "L'imputation de déficits enregistrée pour cet exercice ne correspond plus à la proposition calculée. "
            "Reconfirmez l'imputation après vérification du résultat fiscal."
        )
    if params["cm_exoneration_totale"]:
        alertes.append("Cotisation minimale exonérée pour cet exercice : conservez la justification juridique enregistrée.")
    if money(params["cm_base_exclue"]) > 0:
        alertes.append("Une partie de la base CM est exclue manuellement : vérifiez la justification et les pièces du dossier fiscal.")
    if money(params["cm_base_taux_reduit_015"]) > 0:
        alertes.append("Une fraction de la base CM est soumise au taux réduit de 0,15% : vérifiez l'éligibilité des opérations concernées.")
    if params["cm_minimum_3000_exonere"]:
        alertes.append("Le minimum de perception de 3 000 MAD est neutralisé manuellement : vérifiez la justification juridique.")
    if not reference_acomptes["disponible"] and not reference_acomptes.get("non_applicable"):
        alertes.append(
            f"Acomptes {exercice} : aucune liquidation fiscale {exercice - 1} confirmée n'est disponible. "
            "Confirmez N-1 ou renseignez une référence annuelle justifiée pour calculer les quatre acomptes."
        )
    if params.get("acomptes_reference_forcee") is not None:
        alertes.append("La base annuelle des acomptes est forcée manuellement : conservez la justification avec le dossier fiscal.")
    acomptes_en_retard = [a for a in situation_acomptes["acomptes"] if a["statut"] == "en_retard"]
    if acomptes_en_retard:
        nums = ", ".join(str(a["numero"]) for a in acomptes_en_retard)
        alertes.append(f"Acompte(s) provisionnel(s) potentiellement en retard : {nums}. Vérifiez les paiements et éventuelles dispenses déclarées.")
    if credits_is["total_disponible_liquidation"] > 0:
        alertes.append(
            f"{money(credits_is['total_disponible_liquidation'])} MAD de retenues/crédits IS restent disponibles à la liquidation. "
            "HisabPro les impute avant les acomptes dans l'ordre PPRF, retenues sur rémunérations à des tiers, puis autres crédits documentés."
        )
    if params.get("css_benefice_reference_forcee") is not None:
        alertes.append("CSS : le bénéfice net fiscal de référence est forcé manuellement. Conservez la justification avec le dossier fiscal.")
    if params.get("css_exoneration_permanente"):
        alertes.append("CSS : exonération permanente déclarée. Vérifiez que la société relève bien d'une exonération permanente d'IS et conservez la justification.")
    if css.get("applicable") and not css.get("disponible"):
        alertes.append(
            f"CSS {exercice} : liquidation fiscale {exercice - 1} indisponible. "
            "Confirmez l'exercice précédent ou saisissez un bénéfice net fiscal de référence justifié."
        )
    if css.get("statut") == "en_retard":
        alertes.append(f"CSS {exercice} potentiellement en retard : échéance {css.get('date_echeance')}. Vérifiez la déclaration et le paiement SIMPL-IS.")
    if not comptabilisation_is["coherente"]:
        if comptabilisation_is["absente"] and money(comptabilisation_is["attendu"]) > 0:
            alertes.append(
                f"Impôt sur les résultats non encore comptabilisé : {money(comptabilisation_is['attendu'])} MAD "
                f"attendus au compte {comptabilisation_is['compte_charge_attendu']}. La clôture HisabPro le comptabilisera automatiquement."
            )
        elif not comptabilisation_is["absente"]:
            alertes.append(
                "La comptabilisation de l'impôt courant ne correspond pas au calcul fiscal actuel. "
                "La clôture sera bloquée jusqu'au rapprochement des comptes 6701/6705."
            )
    snapshot = _serialiser_liquidation(liquidation_courante_db)
    if snapshot and not reference_acomptes.get("disponible") and not reference_acomptes.get("non_applicable"):
        alertes.append(
            "Cette liquidation a été confirmée avec une référence d'acomptes indisponible. "
            "Elle provient d'un état antérieur au contrôle de cohérence Patch 092 et doit être corrigée avant utilisation comme référence fiscale."
        )
    if snapshot and (
        money(snapshot["impot_du"]) != money(cotisation_minimale["impot_du_avant_acomptes"])
        or money(snapshot["acomptes_imputables"]) != money(liquidation_detail["acomptes_et_credit_imputables"])
        or money(snapshot.get("credits_is_imputables")) != money(liquidation_detail["credits_is_disponibles_liquidation"])
    ):
        alertes.append(
            "La liquidation confirmée diffère du calcul live actuel. La photographie confirmée reste immuable ; "
            "une correction éventuelle devra passer par la procédure administrative auditée."
        )

    return {
        "exercice": exercice,
        "societe": {
            "raison_sociale": societe.raison_sociale,
            "identifiant_fiscal": societe.identifiant_fiscal,
            "ice": societe.ice,
            "regime_fiscal": societe.regime_fiscal,
        },
        "categories_is": CATEGORIES_IS,
        "categories_retraitement": CATEGORIES_RETRAITEMENT,
        "parametres": params,
        "source_comptable": {k: v for k, v in source.items() if not k.startswith("_")},
        "retraitements": [_serialiser_retraitement(r) for r in manuels] + auto,
        "retraitements_a_confirmer": analyse["a_confirmer"],
        "checklist_fiscale": analyse["checklist"],
        "synthese_retraitements": {
            "nb_automatiques": len(auto),
            "nb_a_confirmer": analyse["nb_a_confirmer"],
            "nb_manuels": len(manuels),
            "total_automatique_reintegrations": analyse["total_automatique_reintegrations"],
            "total_automatique_deductions": analyse["total_automatique_deductions"],
        },
        "deficits": {
            "inventaire": inventaire_deficits,
            "disponible_ordinaire": situation_deficits["disponible_ordinaire"],
            "disponible_amortissements": situation_deficits["disponible_amortissements"],
            "disponible_total": situation_deficits["disponible_total"],
            "ordinaire_expire": situation_deficits["ordinaire_expire"],
            "proposition": situation_deficits["proposition"],
            "total_propose": situation_deficits["total_propose"],
            "total_confirme": situation_deficits["total_confirme"],
            "confirmation_a_jour": situation_deficits["confirmation_a_jour"],
            "legacy_non_millesime": money(params.get("deficit_reportable_disponible")),
            "amortissements_comptabilises": amortissements_comptabilises,
            "amortissements_reintegres": amortissements_reintegres,
            "amortissements_deductibles": amortissements_deductibles,
            "deficit_genere_propose": deficit_genere,
        },
        "calcul": calcul,
        "cotisation_minimale": cotisation_minimale,
        "acomptes": situation_acomptes,
        "credits_is": credits_is,
        "contribution_solidarite": css,
        "comptabilisation_is": comptabilisation_is,
        "liquidation": {
            "is_theorique": money(calcul["is_theorique"]),
            "cm_exigible": money(cotisation_minimale["cm_exigible"]),
            "impot_du_avant_acomptes": money(cotisation_minimale["impot_du_avant_acomptes"]),
            "nature_impot_du": cotisation_minimale["nature_impot_du"],
            **liquidation_detail,
            "confirmee": snapshot is not None,
            "snapshot": snapshot,
        },
        "alertes": alertes,
        "source_legale": {
            "resultat_fiscal": "CGI 2026 — articles 8 à 12",
            "charges_deductibles": "CGI 2026 — article 10",
            "charges_non_deductibles": "CGI 2026 — article 11",
            "produits_participation": "CGI 2026 — article 6-I-C-1°",
            "deficit_reportable": "CGI 2026 — article 12",
            "taux_is": "CGI — article 19 et article 247-XXXVII-A (transition 2023-2026)",
            "cotisation_minimale": "CGI 2026 — article 144",
            "acomptes_liquidation": "CGI 2026 — article 170 ; article 247-XXXVII-B pour la transition 2023-2026",
            "credits_retenues_is": "CGI / doctrine DGI — imputation des retenues PPRF et rémunérations allouées à des tiers sur l'IS",
            "contribution_solidarite": "CGI 2026 — articles 267 à 273 ; LF 2026 — prorogation 2026-2028",
        },
    }


@router.put("/is/{exercice}/parametres")
def enregistrer_parametres_is(
    exercice: int,
    data: ParametresISIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    _verifier_parametres_is_modifiables(db, societe_id, exercice, data)
    # Refuse d'enregistrer une ventilation CM impossible par rapport à la
    # base comptable actuellement détectée. Cela évite un paramétrage qui
    # ferait échouer le calcul au prochain chargement.
    source = _source_comptable(db, societe_id, exercice)
    try:
        calculer_cotisation_minimale(
            produits_par_compte=source["_produits_par_compte"],
            is_theorique=Decimal("0.00"),
            base_exclue=data.cm_base_exclue,
            base_taux_reduit_015=data.cm_base_taux_reduit_015,
            exoneration_totale=data.cm_exoneration_totale,
            minimum_3000_exonere=data.cm_minimum_3000_exonere,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    p = db.query(models.FiscalParametreExercice).filter_by(
        societe_id=societe_id, exercice=exercice
    ).first()
    if not p:
        p = models.FiscalParametreExercice(societe_id=societe_id, exercice=exercice)
        db.add(p)
    for k, v in data.model_dump().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return _parametres_dict(p)


@router.post("/is/{exercice}/retraitements")
def ajouter_retraitement(
    exercice: int,
    data: RetraitementIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    _verifier_calcul_is_modifiable(db, current_user["societe_id"], exercice)
    r = models.FiscalRetraitement(
        societe_id=current_user["societe_id"], exercice=exercice, **data.model_dump()
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _serialiser_retraitement(r)


@router.patch("/is/retraitements/{retraitement_id}")
def modifier_retraitement(
    retraitement_id: int,
    data: RetraitementIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    r = db.query(models.FiscalRetraitement).filter_by(
        id=retraitement_id, societe_id=current_user["societe_id"]
    ).first()
    if not r:
        raise HTTPException(404, "Retraitement fiscal introuvable")
    _verifier_calcul_is_modifiable(db, current_user["societe_id"], r.exercice)
    for k, v in data.model_dump().items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return _serialiser_retraitement(r)


@router.delete("/is/retraitements/{retraitement_id}", status_code=204)
def supprimer_retraitement(
    retraitement_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    r = db.query(models.FiscalRetraitement).filter_by(
        id=retraitement_id, societe_id=current_user["societe_id"]
    ).first()
    if not r:
        raise HTTPException(404, "Retraitement fiscal introuvable")
    _verifier_calcul_is_modifiable(db, current_user["societe_id"], r.exercice)
    db.delete(r)
    db.commit()
    return None


# ── Acomptes provisionnels & liquidation — Patch 08.5 ───────────────────────

@router.put("/is/{exercice}/acomptes/{numero}")
def enregistrer_acompte_is(
    exercice: int,
    numero: int,
    data: AcompteISIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    if numero not in (1, 2, 3, 4):
        raise HTTPException(400, "Le numéro d'acompte doit être compris entre 1 et 4.")
    societe_id = current_user["societe_id"]
    _verifier_liquidation_non_confirmee(db, societe_id, exercice)
    a = db.query(models.FiscalAcompteIS).filter_by(
        societe_id=societe_id, exercice=exercice, numero=numero
    ).first()
    if not a:
        a = models.FiscalAcompteIS(societe_id=societe_id, exercice=exercice, numero=numero)
        db.add(a)
    for k, v in data.model_dump().items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return _serialiser_acompte(a)


@router.delete("/is/{exercice}/acomptes/{numero}", status_code=204)
def supprimer_acompte_is(
    exercice: int,
    numero: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    _verifier_liquidation_non_confirmee(db, societe_id, exercice)
    a = db.query(models.FiscalAcompteIS).filter_by(
        societe_id=societe_id, exercice=exercice, numero=numero
    ).first()
    if not a:
        raise HTTPException(404, "Acompte fiscal introuvable")
    db.delete(a)
    db.commit()
    return None


@router.post("/is/{exercice}/liquidation/confirmer")
def confirmer_liquidation_is(
    exercice: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    _verifier_liquidation_non_confirmee(db, societe_id, exercice)
    if exercice > 2026:
        raise HTTPException(409, f"Le référentiel fiscal {exercice} n'est pas encore figé dans HisabPro : liquidation définitive bloquée.")
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=exercice).first()
    if not ex or ex.statut != "cloture":
        raise HTTPException(409, "Clôturez d'abord l'exercice comptable avant de confirmer sa liquidation fiscale.")

    situation = situation_is(exercice, current_user=current_user, db=db)

    compta_is = situation.get("comptabilisation_is") or {}
    if not compta_is.get("coherente", False):
        raise HTTPException(409,
            f"Liquidation bloquée : l'impôt courant attendu ({money(compta_is.get('attendu'))} MAD, "
            f"compte {compta_is.get('compte_charge_attendu') or '6701/6705'}) n'est pas comptabilisé de manière cohérente. "
            "La clôture comptable doit d'abord constater l'impôt sur les résultats.")

    # Patch 092 — une liquidation annuelle ne peut pas être figée si la base des
    # acomptes reste indéterminée. Le seul cas sans référence autorisé est le
    # véritable premier exercice, explicitement marqué « non_applicable ».
    reference_acomptes = (situation.get("acomptes") or {}).get("reference") or {}
    if not reference_acomptes.get("disponible") and not reference_acomptes.get("non_applicable"):
        raise HTTPException(
            409,
            f"Référence des acomptes {exercice} indisponible : confirmez la liquidation fiscale "
            f"{exercice - 1} ou renseignez une référence annuelle justifiée avant de confirmer la liquidation IS.",
        )

    if situation["source_comptable"]["nb_brouillons_exclus"] > 0:
        raise HTTPException(409, "Des brouillons comptables subsistent : liquidation fiscale définitive impossible.")
    deficits = situation["deficits"]
    if money(deficits.get("total_propose")) > 0 and not deficits.get("confirmation_a_jour"):
        raise HTTPException(409, "Confirmez d'abord l'imputation des déficits fiscaux proposée pour cet exercice.")

    liq = situation["liquidation"]
    c = situation["calcul"]
    snapshot_detail = construire_snapshot_liquidation(situation)
    obj = models.FiscalLiquidationIS(
        societe_id=societe_id,
        exercice=exercice,
        benefice_fiscal_imposable=money(c["benefice_fiscal_imposable"]),
        is_theorique=money(liq["is_theorique"]),
        cm_exigible=money(liq["cm_exigible"]),
        impot_du=money(liq["impot_du_avant_acomptes"]),
        nature_impot=liq["nature_impot_du"],
        acomptes_imputables=money(liq["acomptes_et_credit_imputables"]),
        credits_is_imputables=money(liq["credits_is_disponibles_liquidation"]),
        solde_a_payer=money(liq["solde_a_payer"]),
        excedent_acomptes=money(liq["excedent_acomptes"]),
        excedent_credits_is=money(liq["excedent_credits_is"]),
        excedent_total=money(liq["excedent_total"]),
        snapshot_detail=snapshot_detail,
        confirmee_par=current_user.get("id"),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _serialiser_liquidation(obj)


# ── Retenues/crédits IS & CSS — Patch 08.6 ─────────────────────────────────

@router.post("/is/{exercice}/credits")
def ajouter_credit_is(
    exercice: int,
    data: CreditISIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    _verifier_liquidation_non_confirmee(db, societe_id, exercice)
    obj = models.FiscalCreditIS(
        societe_id=societe_id, exercice=exercice, **data.model_dump()
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _serialiser_credit_is(obj)


@router.delete("/is/{exercice}/credits/{credit_id}", status_code=204)
def supprimer_credit_is(
    exercice: int,
    credit_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    _verifier_liquidation_non_confirmee(db, societe_id, exercice)
    obj = db.query(models.FiscalCreditIS).filter_by(
        id=credit_id, societe_id=societe_id, exercice=exercice
    ).first()
    if not obj:
        raise HTTPException(404, "Crédit / retenue IS introuvable")
    db.delete(obj)
    db.commit()
    return None


@router.put("/is/{annee}/css/paiement")
def enregistrer_paiement_css(
    annee: int,
    data: CSSPaiementIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    if annee < 2023 or annee > 2028:
        raise HTTPException(400, "La CSS actuellement paramétrée couvre les années 2023 à 2028.")
    societe_id = current_user["societe_id"]
    situation = situation_is(annee, current_user=current_user, db=db)
    css = situation["contribution_solidarite"]
    if not css.get("disponible"):
        raise HTTPException(409, "La base CSS est indisponible : renseignez d'abord la liquidation de référence ou une reprise justifiée.")
    if money(css.get("montant_du")) <= 0:
        raise HTTPException(409, "Aucune contribution sociale de solidarité n'est actuellement due pour cette année.")
    obj = db.query(models.FiscalCSSPaiement).filter_by(societe_id=societe_id, annee=annee).first()
    if not obj:
        obj = models.FiscalCSSPaiement(societe_id=societe_id, annee=annee)
        db.add(obj)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return _serialiser_css_paiement(obj)


@router.delete("/is/{annee}/css/paiement", status_code=204)
def supprimer_paiement_css(
    annee: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    obj = db.query(models.FiscalCSSPaiement).filter_by(
        societe_id=current_user["societe_id"], annee=annee
    ).first()
    if not obj:
        raise HTTPException(404, "Paiement CSS introuvable")
    db.delete(obj)
    db.commit()
    return None


# ── Déficits fiscaux par millésime — Patch 08.3 ──────────────────────────────

@router.post("/deficits")
def ajouter_deficit_fiscal(
    data: DeficitFiscalIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    verrouiller_deficits_fiscaux(db, societe_id, ecriture=True)
    existe = db.query(models.FiscalDeficit).filter_by(
        societe_id=societe_id, exercice_origine=data.exercice_origine
    ).first()
    if existe:
        raise HTTPException(409, f"Un déficit fiscal est déjà enregistré pour {data.exercice_origine}.")
    d = models.FiscalDeficit(
        societe_id=societe_id,
        exercice_origine=data.exercice_origine,
        montant_ordinaire=money(data.montant_ordinaire),
        montant_amortissements=money(data.montant_amortissements),
        source="manuel",
        commentaire=data.commentaire,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return _serialiser_deficit(d)


@router.patch("/deficits/{deficit_id}")
def modifier_deficit_fiscal(
    deficit_id: int,
    data: DeficitFiscalIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    verrouiller_deficits_fiscaux(db, societe_id, ecriture=True)
    d = db.query(models.FiscalDeficit).filter_by(id=deficit_id, societe_id=societe_id).first()
    if not d:
        raise HTTPException(404, "Déficit fiscal introuvable")
    if db.query(models.FiscalDeficitImputation).filter_by(deficit_id=d.id, societe_id=societe_id).first():
        raise HTTPException(409, "Ce déficit a déjà été imputé : son millésime et ses montants ne peuvent plus être modifiés.")
    doublon = db.query(models.FiscalDeficit).filter(
        models.FiscalDeficit.societe_id == societe_id,
        models.FiscalDeficit.exercice_origine == data.exercice_origine,
        models.FiscalDeficit.id != d.id,
    ).first()
    if doublon:
        raise HTTPException(409, f"Un déficit fiscal est déjà enregistré pour {data.exercice_origine}.")
    d.exercice_origine = data.exercice_origine
    d.montant_ordinaire = money(data.montant_ordinaire)
    d.montant_amortissements = money(data.montant_amortissements)
    d.commentaire = data.commentaire
    db.commit()
    db.refresh(d)
    return _serialiser_deficit(d)


@router.delete("/deficits/{deficit_id}", status_code=204)
def supprimer_deficit_fiscal(
    deficit_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    verrouiller_deficits_fiscaux(db, societe_id, ecriture=True)
    d = db.query(models.FiscalDeficit).filter_by(id=deficit_id, societe_id=societe_id).first()
    if not d:
        raise HTTPException(404, "Déficit fiscal introuvable")
    if db.query(models.FiscalDeficitImputation).filter_by(deficit_id=d.id, societe_id=societe_id).first():
        raise HTTPException(409, "Ce déficit a déjà été utilisé : supprimez d'abord ses imputations si une correction est nécessaire.")
    db.delete(d)
    db.commit()
    return None


@router.post("/is/{exercice}/deficits/enregistrer-genere")
def enregistrer_deficit_genere(
    exercice: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    verrouiller_deficits_fiscaux(db, current_user["societe_id"], ecriture=True)
    _verifier_calcul_is_modifiable(db, current_user["societe_id"], exercice)
    situation = situation_is(exercice, current_user=current_user, db=db)
    genere = situation["deficits"]["deficit_genere_propose"]
    if money(genere["montant_total"]) <= 0:
        raise HTTPException(400, "L'exercice ne génère actuellement aucun déficit fiscal à enregistrer.")

    societe_id = current_user["societe_id"]
    d = db.query(models.FiscalDeficit).filter_by(societe_id=societe_id, exercice_origine=exercice).first()
    if d:
        if d.source != "calcul":
            raise HTTPException(409, "Un déficit saisi manuellement existe déjà pour cet exercice. Vérifiez-le avant tout remplacement.")
        if db.query(models.FiscalDeficitImputation).filter_by(deficit_id=d.id, societe_id=societe_id).first():
            raise HTTPException(409, "Le déficit de cet exercice a déjà été utilisé et ne peut plus être recalculé automatiquement.")
    else:
        d = models.FiscalDeficit(societe_id=societe_id, exercice_origine=exercice, source="calcul")
        db.add(d)

    d.montant_ordinaire = money(genere["part_ordinaire"])
    d.montant_amortissements = money(genere["part_amortissements"])
    d.commentaire = "Déficit généré automatiquement depuis le résultat fiscal HisabPro."
    db.commit()
    db.refresh(d)
    return _serialiser_deficit(d)


@router.post("/is/{exercice}/deficits/confirmer-imputation")
def confirmer_imputation_deficits(
    exercice: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Enregistre exactement la proposition HisabPro calculée pour l'exercice."""
    societe_id = current_user["societe_id"]
    verrouiller_deficits_fiscaux(db, societe_id, ecriture=True)
    _verifier_calcul_is_modifiable(db, societe_id, exercice)
    situation = situation_is(exercice, current_user=current_user, db=db)
    proposition = situation["deficits"]["proposition"]

    # Remplacement atomique de l'imputation de l'exercice : permet de reconfirmer
    # proprement si le résultat fiscal a changé avant liquidation définitive.
    db.query(models.FiscalDeficitImputation).filter_by(
        societe_id=societe_id, exercice_cible=exercice
    ).delete(synchronize_session=False)

    groupes = {}
    for p in proposition:
        g = groupes.setdefault(p["deficit_id"], {"ordinaire": Decimal("0.00"), "amortissements": Decimal("0.00")})
        g[p["nature"]] += money(p["montant"])

    for deficit_id, g in groupes.items():
        db.add(models.FiscalDeficitImputation(
            societe_id=societe_id,
            deficit_id=deficit_id,
            exercice_cible=exercice,
            montant_ordinaire=money(g["ordinaire"]),
            montant_amortissements=money(g["amortissements"]),
        ))
    db.commit()
    return {
        "exercice": exercice,
        "nb_lots": len(groupes),
        "montant_confirme": money(sum((money(p["montant"]) for p in proposition), Decimal("0.00"))),
    }


@router.delete("/is/{exercice}/deficits/imputation", status_code=204)
def annuler_imputation_deficits(
    exercice: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    verrouiller_deficits_fiscaux(db, current_user["societe_id"], ecriture=True)
    _verifier_calcul_is_modifiable(db, current_user["societe_id"], exercice)
    db.query(models.FiscalDeficitImputation).filter_by(
        societe_id=current_user["societe_id"], exercice_cible=exercice
    ).delete(synchronize_session=False)
    db.commit()
    return None
