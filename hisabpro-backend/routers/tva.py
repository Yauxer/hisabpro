# -*- coding: utf-8 -*-
"""TVA marocaine — déclaration calculée depuis les faits générateurs.

Patch 02B :
- ventes encaissement / débit ;
- paiements partiels ;
- avoirs avec régularisation par delta cumulatif ;
- acomptes clients taxables à l'encaissement ;
- acomptes fournisseurs déductibles seulement une fois rattachés à une facture ;
- déductibilité explicite par facture + prorata annuel ;
- crédit de TVA d'ouverture et report période par période.

Ce moteur prépare une situation fiscale contrôlable. Il ne constitue pas encore
une télédéclaration DGI ni un mécanisme de gel/validation d'une déclaration déposée.
"""
from calendar import monthrange
import math
from datetime import date, timedelta
import json
from types import SimpleNamespace
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload

from auth import get_current_user, requiert_ecriture
from database import get_db
import models
from services.tva_regles_service import est_sans_tva
from services.compta_mapping_service import part_immobilisations_par_taux
from services.tva_service import (
    D, ZERO, acompte_ttc_ventilation, ajouter_ventilation, allouer_paiement,
    appliquer_credit_periode, appliquer_pourcentage, date_paiement_effective, date_encaissement_acompte, delta_ventilation,
    finaliser_bloc, money, pct, soustraire_ventilation, taux_key,
    total_ventilation, ventilation_avoir, ventilation_facture,
)

router = APIRouter(prefix="/api/tva", tags=["tva"])
from routers.ras_tva_registre import router as registre_ras_tva
router.include_router(registre_ras_tva)
from routers.ras_rapprochements import router as rapprochements_ras_tva
router.include_router(rapprochements_ras_tva)


from services.ras_tva_simulation_service import SimulationRasTvaIn, simuler


@router.post('/ras/simulation')
def simuler_ras_tva(data: SimulationRasTvaIn, current_user=Depends(get_current_user)):
    return simuler(data)


class TVAParametresIn(BaseModel):
    credit_ouverture: float = 0.0
    prorata_deduction_pct: float = 100.0

    @field_validator("credit_ouverture", "prorata_deduction_pct", mode="before")
    @classmethod
    def parametre_numerique(cls, v):
        if isinstance(v, bool):
            raise ValueError("Un paramètre TVA ne peut pas être un booléen")
        return v

    @field_validator("credit_ouverture")
    @classmethod
    def credit_non_negatif(cls, v):
        if not math.isfinite(v) or v < 0:
            raise ValueError("Le crédit TVA d'ouverture doit être fini et non négatif")
        return v

    @field_validator("prorata_deduction_pct")
    @classmethod
    def prorata_valide(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Le prorata de déduction doit être compris entre 0 et 100")
        return v


def _bornes(exercice: int, mois: Optional[int], trimestre: Optional[int]):
    if not date.min.year <= exercice <= date.max.year:
        raise HTTPException(400, "Année hors du calendrier pris en charge (1 à 9999)")
    if mois is not None and trimestre is not None:
        raise HTTPException(400, "Choisir soit un mois, soit un trimestre")
    if mois is not None:
        if mois < 1 or mois > 12:
            raise HTTPException(400, "Mois invalide")
        return date(exercice, mois, 1), date(exercice, mois, monthrange(exercice, mois)[1]), "mensuelle"
    if trimestre is not None:
        if trimestre < 1 or trimestre > 4:
            raise HTTPException(400, "Trimestre invalide")
        m1 = 1 + (trimestre - 1) * 3
        m3 = m1 + 2
        return date(exercice, m1, 1), date(exercice, m3, monthrange(exercice, m3)[1]), "trimestrielle"
    return date(exercice, 1, 1), date(exercice, 12, 31), "annuelle"


def _enum_value(value):
    return getattr(value, "value", value)


def _get_parametres(db: Session, societe_id: int, exercice: int):
    p = db.query(models.TVAParametreExercice).filter_by(
        societe_id=societe_id, exercice=exercice
    ).first()
    return p


def _regime_facture(facture, societe):
    return (getattr(facture, "regime_tva", None) or getattr(societe, "regime_tva", None) or "encaissement").lower()


def _avoirs_cutoff(db, societe_id, facture_id, cutoff):
    if cutoff is None:
        return []
    return db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter(
        models.Avoir.societe_id == societe_id,
        models.Avoir.facture_id == facture_id,
        models.Avoir.date <= cutoff,
        models.Avoir.statut != models.StatutAvoirEnum.annule,
    ).order_by(models.Avoir.date.asc(), models.Avoir.id.asc()).all()


def _ventilation_nette_cutoff(db, societe_id, facture, cutoff):
    if cutoff is None or facture.date > cutoff:
        return {}
    net = ventilation_facture(facture)
    for avoir in _avoirs_cutoff(db, societe_id, facture.id, cutoff):
        net = soustraire_ventilation(net, ventilation_avoir(avoir))
    return net


def _total_reglements_cutoff(db, societe_id, facture_id, cutoff, alertes):
    if cutoff is None:
        return ZERO
    total = ZERO
    regs = db.query(models.Reglement).filter_by(
        societe_id=societe_id, facture_id=facture_id
    ).order_by(models.Reglement.date.asc(), models.Reglement.id.asc()).all()
    for r in regs:
        if str(_enum_value(getattr(r, "statut", "")) or "").lower() == "annule":
            # Un paiement immédiat annulé reste encaissé jusqu'à sa date d'annulation :
            # la TVA déjà due n'est pas réécrite, la période d'annulation la régularise.
            # Chèques/effets : annulables seulement avant encaissement, donc sans TVA.
            mode = str(getattr(r, "mode", "") or "").lower()
            if mode in {"cheque", "effet"} or r.date is None or r.date > cutoff:
                continue
            annulation = getattr(r, "date_annulation_effective", None)
            if annulation is None and getattr(r, "ecriture_annulation_id", None):
                annulation = db.query(models.Ecriture.date).filter_by(
                    id=r.ecriture_annulation_id, societe_id=societe_id).scalar()
            if annulation is None:
                alertes.add(f"Règlement {r.numero or r.id} annulé : date d'annulation inconnue ; TVA des périodes antérieures à qualifier.")
                continue
            if annulation > cutoff:
                total += max(D(getattr(r, "montant", 0)), ZERO)
            continue
        if str(_enum_value(getattr(r, "statut", "")) or "").lower() == "rejete":
            # Impayé après encaissement : la TVA reste due jusqu'à la date du rejet.
            enc, rejet = getattr(r, "date_encaissement", None), getattr(r, "date_rejet_effective", None)
            if enc and rejet and enc <= cutoff < rejet:
                total += max(D(getattr(r, "montant", 0)), ZERO)
            continue
        eff = date_paiement_effective(r)
        if eff is None:
            mode = str(getattr(r, "mode", "") or "").lower()
            statut = str(_enum_value(getattr(r, "statut", "")) or "").lower()
            if mode in {"cheque", "effet"} and statut not in {"rejete", "annule", "portefeuille", "encaissement", "a_payer"}:
                alertes.add(f"Règlement {r.numero or r.id} : date d'encaissement fiscal absente ; ignoré en TVA.")
            continue
        if eff <= cutoff:
            total += max(D(getattr(r, "montant", 0)), ZERO)
    # Compensation du crédit d'un avoir avec une autre facture du même tiers.
    # Une simple date d'imputation historique n'est pas une preuve d'acceptation.
    utilisations = db.query(models.UtilisationAvoir).join(
        models.Avoir, models.Avoir.id == models.UtilisationAvoir.avoir_id,
    ).filter(
        models.UtilisationAvoir.societe_id == societe_id,
        models.UtilisationAvoir.facture_id == facture_id,
        models.UtilisationAvoir.type_utilisation == "imputation",
        models.UtilisationAvoir.date_utilisation <= cutoff,
        models.Avoir.societe_id == societe_id,
        models.Avoir.statut != models.StatutAvoirEnum.annule,
    ).all()
    for u in utilisations:
        signature = u.date_acceptation_compensation
        if signature is None:
            alertes.add(f"Imputation d'avoir {u.id} : accord de compensation non confirmé ; date de signature et justificatif à qualifier pour la TVA.")
            continue
        if u.statut == "annulee":
            annulation = u.date_annulation_effective
            if annulation is None:
                alertes.add(f"Compensation {u.id} : date effective d'annulation absente ; TVA à qualifier.")
                continue
            if annulation <= cutoff:
                continue
        if signature <= cutoff:
            total += max(D(u.montant), ZERO)
    return money(total)


def _imputations_acomptes_facture(db, societe_id, facture_id, type_acompte, cutoff):
    """Chaque affectation réelle ; le pointeur unique n'est qu'un secours legacy."""
    rows = db.query(models.ImputationAcompte, models.Acompte).join(
        models.Acompte, models.Acompte.id == models.ImputationAcompte.acompte_id,
    ).filter(
        models.ImputationAcompte.societe_id == societe_id,
        models.ImputationAcompte.facture_id == facture_id,
        models.ImputationAcompte.statut == "active",
        models.ImputationAcompte.date_imputation <= cutoff,
        models.Acompte.societe_id == societe_id,
        models.Acompte.type == type_acompte,
        models.Acompte.statut != "annule",
    ).all()
    for imputation, acompte in rows:
        yield acompte, imputation.montant, imputation.date_imputation
    legacy = db.query(models.Acompte).filter(
        models.Acompte.societe_id == societe_id,
        models.Acompte.facture_id == facture_id,
        models.Acompte.type == type_acompte,
        models.Acompte.statut == "impute",
        ~models.Acompte.imputations.any(models.ImputationAcompte.societe_id == societe_id),
    ).all()
    for acompte in legacy:
        date_imp = acompte.date_imputation
        if date_imp is None or date_imp <= cutoff:
            yield acompte, acompte.montant, date_imp


def _total_acomptes_fournisseur_cutoff(db, societe_id, facture, cutoff, alertes=None):
    """Acompte fournisseur utilisable comme paiement uniquement avec facture justificative."""
    if cutoff is None or facture.date > cutoff:
        return ZERO
    total = ZERO
    for a, montant_impute, date_imp in _imputations_acomptes_facture(db, societe_id, facture.id, "fournisseur", cutoff):
        effective = date_encaissement_acompte(a)
        if effective is None:
            if alertes is not None and getattr(a, "statut_paiement", "encaisse") not in {"en_attente", "rejete"}:
                alertes.add(f"Acompte fournisseur {a.numero or a.id} : date de paiement effective absente ; déduction TVA à qualifier depuis les pièces.")
            continue
        # La déduction ne peut être antérieure à la facture justificative.
        naissance = max(effective, facture.date, date_imp or facture.date)
        if naissance <= cutoff:
            total += max(D(montant_impute), ZERO)
    return money(total)


def _total_acomptes_clients_taxables_cutoff(db, societe_id, facture, cutoff):
    """Part affectée déjà taxée comme acompte, sans la compter aussi sur la facture."""
    if cutoff is None or facture.date > cutoff:
        return ZERO
    total = ZERO
    for a, montant_impute, _ in _imputations_acomptes_facture(db, societe_id, facture.id, "client", cutoff):
        if not getattr(a, "tva_applicable", True):
            continue
        effective = date_encaissement_acompte(a)
        if effective is not None and effective <= cutoff:
            total += max(D(montant_impute), ZERO)
    return money(total)


def _situation_facture_cutoff(db, societe, facture, cutoff, prorata_global, alertes):
    """Situation TVA CUMULÉE d'une facture à une date de coupure."""
    societe_id = societe.id
    net = _ventilation_nette_cutoff(db, societe_id, facture, cutoff)
    if not net:
        return {}

    ftype = str(_enum_value(facture.type))
    if ftype == "vente":
        regime = _regime_facture(facture, societe)
        if regime in {"exonere", "hors_champ"}:
            return {}
        if regime == "debit":
            # Le delta cumulatif évite aussi un doublon lorsqu'un chèque remis
            # avant facturation n'est encaissé et affecté qu'après le débit.
            acompte_avant = _total_acomptes_clients_taxables_cutoff(db, societe_id, facture, cutoff)
            total_net = total_ventilation(net)["ttc"]
            restant_debit = max(total_net - acompte_avant, ZERO)
            return allouer_paiement(net, restant_debit)

        paye = _total_reglements_cutoff(db, societe_id, facture.id, cutoff, alertes)
        return allouer_paiement(net, paye)

    # Achat : paiement + acomptes fournisseurs rattachés à la facture.
    paye = _total_reglements_cutoff(db, societe_id, facture.id, cutoff, alertes)
    paye += _total_acomptes_fournisseur_cutoff(db, societe_id, facture, cutoff, alertes)
    situation = allouer_paiement(net, paye)

    nature = (getattr(facture, "nature_tva_achat", None) or "charge").lower()
    deductible = ZERO if nature == "non_deductible" else pct(getattr(facture, "tva_deductible_pct", 100))
    situation = appliquer_pourcentage(situation, deductible)
    situation = appliquer_pourcentage(situation, prorata_global)
    return situation


def _part_immo_situation(db, societe_id, facture, situation, cutoff):
    """Lot 979 : part « immobilisations » d'une situation TVA cumulée d'achat à une date."""
    if not situation:
        return {}
    parts = part_immobilisations_par_taux(db, societe_id, facture, _avoirs_cutoff(db, societe_id, facture.id, cutoff))
    out = {}
    for taux, vals in situation.items():
        f = parts.get(D(taux), ZERO)
        if f:
            out[taux] = {"base": money(D(vals.get("base")) * f), "tva": money(D(vals.get("tva")) * f)}
    return out


def _situation_acomptes_clients_cutoff(db, societe_id, cutoff, alertes=None):
    """TVA cumulée sur avances/acomptes clients encaissés, indépendamment de la facture finale."""
    out = {}
    if cutoff is None:
        return out
    acomptes = db.query(models.Acompte).filter(
        models.Acompte.societe_id == societe_id,
        models.Acompte.type == "client",
        models.Acompte.date <= cutoff,
        models.Acompte.statut != "annule",
        models.Acompte.tva_applicable == True,  # noqa: E712
    ).all()
    for a in acomptes:
        if est_sans_tva(getattr(a, "qualification_tva", "taxable")):
            continue
        effective = date_encaissement_acompte(a)
        if effective is None:
            if alertes is not None and getattr(a, "statut_paiement", "encaisse") not in {"en_attente", "rejete"}:
                alertes.add(f"Acompte {a.numero or a.id} : date d'encaissement effective absente ; TVA à qualifier depuis les pièces.")
            continue
        if effective > cutoff:
            continue
        ajouter_ventilation(out, acompte_ttc_ventilation(a.montant, a.taux_tva))
    # convertir dict sérialisable -> dict Decimal pour delta
    return {
        D(t): {"base": vals["base"], "tva": vals["tva"], "ttc": D(vals["base"]) + D(vals["tva"])}
        for t, vals in out.items()
    }


def _calculer_brut(db, societe, debut, fin, prorata_global, inclure_details=True):
    """Calcule collectée/récupérable de la période, avant crédit antérieur."""
    societe_id = societe.id
    avant = debut - timedelta(days=1) if debut > date.min else None
    alertes = set()
    collectee_taux = {}
    recup_taux = {}
    recup_charges_taux = {}
    recup_immo_taux = {}
    details_ventes = []
    details_achats = []

    factures = db.query(models.Facture).options(joinedload(models.Facture.lignes)).filter(
        models.Facture.societe_id == societe_id,
        models.Facture.est_proforma == False,  # noqa: E712
        models.Facture.statut != models.StatutFactureEnum.annulee,
        models.Facture.date <= fin,
    ).order_by(models.Facture.date, models.Facture.id).all()  # ordre stable (impression, restauration)

    for facture in factures:
        sit_fin = _situation_facture_cutoff(db, societe, facture, fin, prorata_global, alertes)
        sit_avant = _situation_facture_cutoff(db, societe, facture, avant, prorata_global, alertes)
        delta = delta_ventilation(sit_fin, sit_avant)
        if not delta:
            continue

        ftype = str(_enum_value(facture.type))
        if ftype == "vente":
            ajouter_ventilation(collectee_taux, delta)
            if inclure_details:
                details_ventes.append({
                    "facture_id": facture.id, "facture_numero": facture.numero,
                    "tiers": facture.tiers, "date_facture": facture.date.isoformat(),
                    "regime": _regime_facture(facture, societe), "origine": "facture_reglements_avoirs",
                    "ventilation": {taux_key(t): {"base": float(v["base"]), "tva": float(v["tva"])} for t, v in delta.items()},
                })
        else:
            ajouter_ventilation(recup_taux, delta)
            nature = (getattr(facture, "nature_tva_achat", None) or "charge").lower()
            if nature == "immobilisation":
                ajouter_ventilation(recup_immo_taux, delta)
            else:
                # Lot 979 : dans une facture ordinaire, la part des lignes portant un
                # compte d'immobilisation est déclarée en TVA sur immobilisations.
                # Chaque situation cumulée est ventilée avec la part immobilisée à
                # sa propre date (avoirs déduits), puis on fait la différence.
                immo_part = delta_ventilation(_part_immo_situation(db, societe_id, facture, sit_fin, fin),
                                              _part_immo_situation(db, societe_id, facture, sit_avant, avant))
                charges_part = {}
                for taux, vals in delta.items():
                    i = immo_part.get(taux, {"base": ZERO, "tva": ZERO})
                    charges_part[taux] = {"base": D(vals.get("base")) - D(i["base"]), "tva": D(vals.get("tva")) - D(i["tva"])}
                ajouter_ventilation(recup_immo_taux, immo_part)
                ajouter_ventilation(recup_charges_taux, charges_part)
            if inclure_details:
                details_achats.append({
                    "facture_id": facture.id, "facture_numero": facture.numero,
                    "tiers": facture.tiers, "date_facture": facture.date.isoformat(),
                    "origine": "facture_reglements_avoirs", "nature_tva_achat": nature,
                    "tva_deductible_pct": float(getattr(facture, "tva_deductible_pct", 100) or 0),
                    "prorata_pct": float(prorata_global),
                    "ventilation": {taux_key(t): {"base": float(v["base"]), "tva": float(v["tva"])} for t, v in delta.items()},
                })

    # Immobilisations saisies directement dans le registre (hors facture fournisseur).
    # L'historique antérieur au Patch 03 n'est pas repris automatiquement : seules
    # les lignes tva_suivie_directement=True entrent dans le calcul.
    immos = db.query(models.Immobilisation).filter(
        models.Immobilisation.societe_id == societe_id,
        models.Immobilisation.tva_suivie_directement == True,  # noqa: E712
        models.Immobilisation.date_acquisition <= fin,
    ).order_by(models.Immobilisation.date_acquisition, models.Immobilisation.id).all()

    for immo in immos:
        taux = D(getattr(immo, "taux_tva", 0))
        prix_ht = D(getattr(immo, "prix_acquisition_ht", 0))
        ded_pct = pct(getattr(immo, "tva_recuperable_pct", 100))
        date_paiement = getattr(immo, "date_paiement", None)

        qualification_acquisition = getattr(immo, "qualification_tva", "taxable")
        if not est_sans_tva(qualification_acquisition) and taux > ZERO and ded_pct > ZERO:
            if date_paiement and debut <= date_paiement <= fin:
                coef = (ded_pct / D(100)) * (prorata_global / D(100))
                base_ded = money(prix_ht * coef)
                tva_ded = money(prix_ht * taux / D(100) * coef)
                vent = {taux: {"base": base_ded, "tva": tva_ded, "ttc": money(base_ded + tva_ded)}}
                ajouter_ventilation(recup_taux, vent)
                ajouter_ventilation(recup_immo_taux, vent)
                if inclure_details:
                    details_achats.append({
                        "facture_id": None, "facture_numero": None,
                        "tiers": getattr(immo, "fournisseur", None),
                        "date_facture": immo.date_acquisition.isoformat(),
                        "origine": "immobilisation_directe", "nature_tva_achat": "immobilisation",
                        "immobilisation_id": immo.id, "designation": immo.designation,
                        "date_paiement": date_paiement.isoformat(),
                        "tva_deductible_pct": float(ded_pct), "prorata_pct": float(prorata_global),
                        "ventilation": {taux_key(taux): {"base": float(base_ded), "tva": float(tva_ded)}},
                    })
            elif immo.date_acquisition <= fin and not date_paiement and inclure_details:
                alertes.add(
                    f"Immobilisation {immo.id} ({immo.designation}) : acquisition non payée ; "
                    "TVA sur immobilisation non déduite."
                )

        # Cession d'immobilisation : régime des débits -> date de cession ;
        # régime encaissement -> date d'encaissement effectif.
        if getattr(immo, "type_sortie", None) == "cession" and getattr(immo, "date_sortie", None):
            prix_cession = D(getattr(immo, "prix_cession_ht", 0))
            taux_cession = D(getattr(immo, "taux_tva_cession", 0))
            regime_cession = (getattr(immo, "regime_tva_cession", None) or getattr(societe, "regime_tva", None) or "encaissement").lower()
            date_fiscale = immo.date_sortie if regime_cession == "debit" else getattr(immo, "date_encaissement_cession", None)
            qualification_cession = getattr(immo, "qualification_tva_cession", "taxable")
            if not est_sans_tva(qualification_cession) and prix_cession > ZERO and taux_cession > ZERO:
                if date_fiscale and debut <= date_fiscale <= fin:
                    tva_c = money(prix_cession * taux_cession / D(100))
                    vent_c = {taux_cession: {"base": money(prix_cession), "tva": tva_c, "ttc": money(prix_cession + tva_c)}}
                    ajouter_ventilation(collectee_taux, vent_c)
                    if inclure_details:
                        details_ventes.append({
                            "facture_id": None, "facture_numero": None, "tiers": None,
                            "origine": "cession_immobilisation", "immobilisation_id": immo.id,
                            "designation": immo.designation, "date_cession": immo.date_sortie.isoformat(),
                            "date_fiscale": date_fiscale.isoformat(), "regime": regime_cession,
                            "ventilation": {taux_key(taux_cession): {"base": float(money(prix_cession)), "tva": float(tva_c)}},
                        })
                elif immo.date_sortie <= fin and regime_cession == "encaissement" and not date_fiscale:
                    alertes.add(
                        f"Cession immobilisation {immo.id} ({immo.designation}) : encaissement non renseigné ; "
                        "TVA collectée non exigible dans le moteur."
                    )

    # Acomptes clients : le fait générateur est l'encaissement, même avant facture.
    acompte_fin = _situation_acomptes_clients_cutoff(db, societe_id, fin, alertes)
    acompte_avant = _situation_acomptes_clients_cutoff(db, societe_id, avant, alertes)
    delta_acomptes = delta_ventilation(acompte_fin, acompte_avant)
    if delta_acomptes:
        ajouter_ventilation(collectee_taux, delta_acomptes)
        if inclure_details:
            details_ventes.append({
                "facture_id": None, "facture_numero": None, "tiers": None,
                "origine": "acomptes_clients", "regime": "encaissement",
                "ventilation": {taux_key(t): {"base": float(v["base"]), "tva": float(v["tva"])} for t, v in delta_acomptes.items()},
            })

    return {
        "collectee": finaliser_bloc(collectee_taux),
        "recuperable": finaliser_bloc(recup_taux),
        "recuperable_charges": finaliser_bloc(recup_charges_taux),
        "recuperable_immobilisations": finaliser_bloc(recup_immo_taux),
        "details_ventes": details_ventes,
        "details_achats": details_achats,
        "alertes": alertes,
    }


def _periodes_precedentes(exercice, debut_cible, periodicite):
    periodes = []
    if periodicite == "mensuelle":
        for mois in range(1, debut_cible.month):
            periodes.append((date(exercice, mois, 1), date(exercice, mois, monthrange(exercice, mois)[1])))
    elif periodicite == "trimestrielle":
        m1_cible = ((debut_cible.month - 1) // 3) * 3 + 1
        for m1 in range(1, m1_cible, 3):
            m3 = m1 + 2
            periodes.append((date(exercice, m1, 1), date(exercice, m3, monthrange(exercice, m3)[1])))
    return periodes


ALERTE_DEPOTS_INDISPONIBLES = ("Dépôts TVA non consultables : appliquer la migration 129 "
                               "(déclarations déposées) ; montants recalculés uniquement.")


_COLONNES_DEPOT = ("id, societe_id, exercice, periodicite, date_debut, date_fin, collectee, recuperable, "
                   "credit_anterieur, tva_due, credit_tva, date_depot, reference_depot, motif_rectification, "
                   "remplace_id, statut, created_at")


def _depots_disponibles(db):
    """Table créée par la seule migration 129 (comme 125) : absente ou illisible, le calcul
    reste disponible et le gel est signalé indisponible."""
    if "depots_tva_129" not in db.info:
        db.info["depots_tva_129"] = bool(db.scalar(text(
            "SELECT CASE WHEN to_regclass('public.declarations_tva_deposees') IS NULL THEN FALSE "
            "ELSE has_table_privilege('public.declarations_tva_deposees', 'SELECT') END")))
    return db.info["depots_tva_129"]


def _declaration_deposee(db, societe_id, debut, fin):
    if not _depots_disponibles(db):
        return None
    row = db.execute(text(
        f"SELECT {_COLONNES_DEPOT} FROM public.declarations_tva_deposees "
        "WHERE societe_id=:s AND date_debut=:d AND date_fin=:f AND statut='active'"
    ), {"s": societe_id, "d": debut, "f": fin}).mappings().first()
    return SimpleNamespace(**row) if row else None


def _credit_anterieur(db, societe, exercice, debut, periodicite, credit_ouverture, prorata):
    credit = money(credit_ouverture)
    for p_debut, p_fin in _periodes_precedentes(exercice, debut, periodicite):
        deposee = _declaration_deposee(db, societe.id, p_debut, p_fin)
        if deposee is not None:
            # Le crédit reporté est celui réellement déclaré, pas un recalcul.
            credit = money(deposee.credit_tva)
            continue
        brut = _calculer_brut(db, societe, p_debut, p_fin, prorata, inclure_details=False)
        collectee = D(brut["collectee"]["total"])
        recup = D(brut["recuperable"]["total"])
        credit = appliquer_credit_periode(credit, collectee, recup)["credit_fin"]
    return credit


@router.get("/parametres/{exercice}")
def lire_parametres_tva(
    exercice: Annotated[int, Path(ge=1, le=9999)],
    current_user=Depends(get_current_user),
    db: Session=Depends(get_db),
):
    p = _get_parametres(db, current_user["societe_id"], exercice)
    return {
        "exercice": exercice,
        "credit_ouverture": float(p.credit_ouverture) if p else 0.0,
        "prorata_deduction_pct": float(p.prorata_deduction_pct) if p else 100.0,
    }


@router.put("/parametres/{exercice}")
def enregistrer_parametres_tva(
    exercice: Annotated[int, Path(ge=1, le=9999)],
    data: TVAParametresIn,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    from routers.cloture import exercice_est_clos
    # Garder le statut stable jusqu'au commit, y compris si une clôture
    # concurrente attend déjà la même ligne d'exercice. Le verrou partagé
    # bloque un changement de statut, tout en restant compatible avec le
    # contrôle SQL096 d'un autre rédacteur des paramètres TVA.
    exercice_comptable = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=exercice).with_for_update(read=True).first()
    if (exercice_comptable is not None and exercice_comptable.statut == 'cloture') or exercice_est_clos(db, societe_id, exercice):
        raise HTTPException(409, "Exercice clôturé : les paramètres TVA sont verrouillés.")
    # Les lecteurs du statut partagent le verrou : deux premières saisies
    # peuvent donc arriver ensemble. L'UPSERT conserve l'unicité sans500 et
    # RETURNING restitue les valeurs de cette opération, avant un autre rédacteur.
    stmt = insert(models.TVAParametreExercice).values(
        societe_id=societe_id, exercice=exercice,
        credit_ouverture=money(data.credit_ouverture),
        prorata_deduction_pct=D(data.prorata_deduction_pct))
    p = db.execute(stmt.on_conflict_do_update(
        index_elements=['societe_id', 'exercice'],
        set_={'credit_ouverture': stmt.excluded.credit_ouverture,
              'prorata_deduction_pct': stmt.excluded.prorata_deduction_pct,
              'updated_at': func.now()},
    ).returning(models.TVAParametreExercice.credit_ouverture,
                models.TVAParametreExercice.prorata_deduction_pct)).one()
    db.commit()
    return {
        "message": "Paramètres TVA enregistrés",
        "exercice": exercice,
        "credit_ouverture": float(p.credit_ouverture),
        "prorata_deduction_pct": float(p.prorata_deduction_pct),
    }


def _calculer_declaration(db, societe, exercice, mois, trimestre):
    societe_id = societe.id
    debut, fin, periodicite = _bornes(exercice, mois, trimestre)
    from services.ras_tva_reglement_service import verifier_declaration_automatique
    verifier_declaration_automatique(db, societe_id, fin)
    params = _get_parametres(db, societe_id, exercice)
    credit_ouverture = D(params.credit_ouverture if params else 0)
    prorata = pct(params.prorata_deduction_pct if params else 100)

    brut = _calculer_brut(db, societe, debut, fin, prorata, inclure_details=True)
    collectee = D(brut["collectee"]["total"])
    recuperable = D(brut["recuperable"]["total"])

    if periodicite == "annuelle":
        credit_anterieur = credit_ouverture
    else:
        credit_anterieur = _credit_anterieur(
            db, societe, exercice, debut, periodicite, credit_ouverture, prorata
        )

    solde_periode = appliquer_credit_periode(credit_anterieur, collectee, recuperable)
    tva_due = solde_periode["tva_due"]
    credit_fin = solde_periode["credit_fin"]

    alertes = set(brut["alertes"])
    periodicite_societe = (getattr(societe, "periodicite_tva", None) or "mensuelle").lower()
    if periodicite != "annuelle" and periodicite != periodicite_societe:
        alertes.add(
            f"La société est paramétrée en TVA {periodicite_societe}; cette vue {periodicite} est une simulation de contrôle."
        )
    if prorata < D(100):
        alertes.add(f"Prorata de déduction appliqué : {prorata}% (paramètre exercice {exercice}).")

    # Cas non automatisables sans qualification métier explicite.
    nb_non_ded = db.query(models.Facture).filter(
        models.Facture.societe_id == societe_id,
        models.Facture.type == models.TypeFactureEnum.achat,
        models.Facture.date >= debut, models.Facture.date <= fin,
        models.Facture.nature_tva_achat == "non_deductible",
    ).count()
    if nb_non_ded:
        alertes.add(f"{nb_non_ded} facture(s) d'achat marquée(s) TVA non déductible sur la période.")

    return {
        "periode": {"type": periodicite, "date_debut": debut.isoformat(), "date_fin": fin.isoformat()},
        "regime_tva": (getattr(societe, "regime_tva", None) or "encaissement").lower(),
        "parametres": {
            "credit_ouverture": float(money(credit_ouverture)),
            "prorata_deduction_pct": float(prorata),
        },
        "collectee": brut["collectee"],
        "recuperable": brut["recuperable"],
        "recuperable_charges": brut["recuperable_charges"],
        "recuperable_immobilisations": brut["recuperable_immobilisations"],
        "credit_tva_anterieur": float(money(credit_anterieur)),
        "tva_due_avant_credit": float(max(money(collectee - recuperable), ZERO)),
        "tva_due": float(tva_due),
        "credit_tva": float(credit_fin),
        "details_ventes": brut["details_ventes"],
        "details_achats": brut["details_achats"],
        "alertes": sorted(alertes),
        "limitations": [
            "retenue_tva_article_117",
            "controle_automatique_exclusions_article_106",
            "regularisations_immobilisations_article_104",
        ],
        "statut_conformite": "moteur_02b_a_controler_avant_depot",
    }


@router.get("/declaration")
def declaration_tva(
    exercice: int = Query(..., ge=1, le=9999),
    mois: Optional[int] = Query(None),
    trimestre: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
    db: Session=Depends(get_db),
):
    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    if not societe:
        raise HTTPException(404, "Société introuvable")
    resultat = _calculer_declaration(db, societe, exercice, mois, trimestre)
    debut = date.fromisoformat(resultat["periode"]["date_debut"])
    fin = date.fromisoformat(resultat["periode"]["date_fin"])
    deposee = _declaration_deposee(db, societe.id, debut, fin)
    if not _depots_disponibles(db):
        resultat["alertes"] = sorted(set(resultat["alertes"]) | {ALERTE_DEPOTS_INDISPONIBLES})
    resultat["declaration_deposee"] = _fmt_deposee(deposee) if deposee else None
    resultat["ecarts_depot"] = _ecarts_depot(resultat, deposee) if deposee else None
    if resultat["ecarts_depot"]:
        resultat["alertes"] = sorted(set(resultat["alertes"]) | {
            f"Déclaration déposée le {deposee.date_depot.strftime('%d/%m/%Y')} (réf. {deposee.reference_depot}) : "
            "le recalcul actuel diffère des montants déposés. Les montants déposés restent figés ; "
            "régularisation ou déclaration rectificative à qualifier."})
    return resultat


# ── Déclarations déposées (959) ──────────────────────────────────────────────

_CHAMPS_DEPOT = ("collectee", "recuperable", "credit_anterieur", "tva_due", "credit_tva")


def _montants_declaration(resultat):
    return {
        "collectee": money(D(resultat["collectee"]["total"])),
        "recuperable": money(D(resultat["recuperable"]["total"])),
        "credit_anterieur": money(D(resultat["credit_tva_anterieur"])),
        "tva_due": money(D(resultat["tva_due"])),
        "credit_tva": money(D(resultat["credit_tva"])),
    }


def _fmt_deposee(d):
    return {
        "id": d.id, "periodicite": d.periodicite,
        "date_debut": d.date_debut.isoformat(), "date_fin": d.date_fin.isoformat(),
        **{k: float(getattr(d, k)) for k in _CHAMPS_DEPOT},
        "date_depot": d.date_depot.isoformat(), "reference_depot": d.reference_depot,
        "motif_rectification": d.motif_rectification, "remplace_id": d.remplace_id,
        "statut": d.statut, "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def _ecarts_depot(resultat, deposee):
    actuel = _montants_declaration(resultat)
    ecarts = {k: float(actuel[k] - money(getattr(deposee, k))) for k in _CHAMPS_DEPOT
              if actuel[k] != money(getattr(deposee, k))}
    return ecarts or None


class DeclarationDeposeeIn(BaseModel):
    exercice: int
    mois: Optional[int] = None
    trimestre: Optional[int] = None
    date_depot: date
    reference_depot: str
    remplace_id: Optional[int] = None
    motif_rectification: Optional[str] = None


@router.get("/declarations-deposees")
def lister_declarations_deposees(
    exercice: int = Query(..., ge=1, le=9999),
    current_user=Depends(get_current_user),
    db: Session=Depends(get_db),
):
    if not _depots_disponibles(db):
        raise HTTPException(503, ALERTE_DEPOTS_INDISPONIBLES)
    rows = db.execute(text(
        f"SELECT {_COLONNES_DEPOT} FROM public.declarations_tva_deposees "
        "WHERE societe_id=:s AND exercice=:e ORDER BY date_debut, id"
    ), {"s": current_user["societe_id"], "e": exercice}).mappings().all()
    return [_fmt_deposee(SimpleNamespace(**r)) for r in rows]


@router.post("/declarations-deposees", status_code=201)
def enregistrer_declaration_deposee(
    data: DeclarationDeposeeIn,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    """Fige la déclaration telle que calculée à cet instant, avec la référence du dépôt."""
    societe_id = current_user["societe_id"]
    societe = db.query(models.Societe).filter_by(id=societe_id).with_for_update().first()
    if not societe:
        raise HTTPException(404, "Société introuvable")
    if not _depots_disponibles(db):
        raise HTTPException(503, ALERTE_DEPOTS_INDISPONIBLES)
    if not data.mois and not data.trimestre:
        raise HTTPException(422, "Seule une période mensuelle ou trimestrielle peut être déposée.")
    reference = (data.reference_depot or "").strip()
    if not reference or len(reference) > 100:
        raise HTTPException(422, "Renseignez la référence du dépôt (100 caractères maximum).")
    resultat = _calculer_declaration(db, societe, data.exercice, data.mois, data.trimestre)
    debut = date.fromisoformat(resultat["periode"]["date_debut"])
    fin = date.fromisoformat(resultat["periode"]["date_fin"])
    periodicite = resultat["periode"]["type"]
    if periodicite != (getattr(societe, "periodicite_tva", None) or "mensuelle").lower():
        raise HTTPException(422, "La période déposée doit suivre la périodicité TVA de la société.")
    if data.date_depot <= fin or data.date_depot > date.today():
        raise HTTPException(422, "La date de dépôt doit suivre la fin de la période et ne peut pas être future.")
    active = _declaration_deposee(db, societe_id, debut, fin)
    motif = (data.motif_rectification or "").strip() or None
    if active is not None:
        if data.remplace_id != active.id:
            raise HTTPException(409, "Cette période est déjà déposée : une rectificative doit désigner la déclaration remplacée.")
        if not motif:
            raise HTTPException(422, "Une déclaration rectificative exige un motif.")
        if data.date_depot < active.date_depot:
            raise HTTPException(422, "La rectificative ne peut précéder le dépôt qu'elle remplace.")
        db.execute(text("UPDATE public.declarations_tva_deposees SET statut='remplacee' "
                        "WHERE id=:i AND societe_id=:s AND statut='active'"), {"i": active.id, "s": societe_id})
    elif data.remplace_id is not None:
        raise HTTPException(404, "Déclaration remplacée introuvable pour cette période.")
    montants = _montants_declaration(resultat)
    from fastapi.encoders import jsonable_encoder
    snapshot = jsonable_encoder({k: v for k, v in resultat.items() if k not in ("declaration_deposee", "ecarts_depot")})
    row = db.execute(text(
        "INSERT INTO public.declarations_tva_deposees(societe_id, exercice, periodicite, date_debut, date_fin, "
        "collectee, recuperable, credit_anterieur, tva_due, credit_tva, snapshot, date_depot, reference_depot, "
        "motif_rectification, remplace_id, statut, deposee_par) VALUES (:s, :e, :p, :d, :f, :collectee, :recuperable, "
        ":credit_anterieur, :tva_due, :credit_tva, CAST(:snap AS json), :dd, :ref, :motif, :remplace, 'active', :u) "
        f"RETURNING {_COLONNES_DEPOT}"
    ), {"s": societe_id, "e": data.exercice, "p": periodicite, "d": debut, "f": fin, **montants,
        "snap": json.dumps(snapshot, ensure_ascii=False), "dd": data.date_depot, "ref": reference, "motif": motif,
        "remplace": active.id if active else None, "u": current_user.get("id")}).mappings().one()
    db.commit()
    return _fmt_deposee(SimpleNamespace(**row))
