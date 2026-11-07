# -*- coding: utf-8 -*-
"""Règles de calcul des immobilisations HisabPro.

Le module est volontairement indépendant de FastAPI/SQLAlchemy pour pouvoir être
recetté sans base de données :
- ventilation du coût d'acquisition et de la TVA ;
- prorata temporis linéaire sur convention 30/360 à partir de la mise en service ;
- dégressif marocain par mois à partir du premier jour du mois d'acquisition ;
- arrêt du plan à la date de sortie ;
- calcul de la VNC et de la plus/moins-value comptable.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

CENT = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def D(value) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def money(value) -> Decimal:
    return D(value).quantize(CENT, rounding=ROUND_HALF_UP)


def pct(value, default=100) -> Decimal:
    raw = D(default if value is None else value)
    return max(ZERO, min(raw, HUNDRED))


def coefficient_degressif(duree: int) -> Decimal:
    """Coefficients prévus par le CGI marocain : 3-4 ans 1,5 ; 5-6 ans 2 ; >6 ans 3."""
    if duree < 3:
        raise ValueError("Le dégressif requiert une durée d'au moins 3 ans")
    if duree <= 4:
        return Decimal("1.5")
    if duree <= 6:
        return Decimal("2")
    return Decimal("3")


def ventilation_acquisition(prix_ht, taux_tva=20, tva_recuperable_pct=100) -> dict:
    """Ventile une acquisition.

    La TVA non récupérable augmente le coût d'entrée comptable du bien. La TVA
    récupérable reste isolée en 34551. Le crédit fournisseur porte sur le TTC.
    """
    prix_ht = money(prix_ht)
    taux = max(D(taux_tva), ZERO)
    ded_pct = pct(tva_recuperable_pct)
    if prix_ht < ZERO:
        raise ValueError("Le prix HT ne peut pas être négatif")
    if taux > HUNDRED:
        raise ValueError("Le taux de TVA doit être compris entre 0 et 100")

    tva_totale = money(prix_ht * taux / HUNDRED)
    tva_recuperable = money(tva_totale * ded_pct / HUNDRED)
    tva_non_recuperable = money(tva_totale - tva_recuperable)
    cout_entree = money(prix_ht + tva_non_recuperable)
    ttc = money(prix_ht + tva_totale)
    return {
        "prix_ht": prix_ht,
        "tva_totale": tva_totale,
        "tva_recuperable": tva_recuperable,
        "tva_non_recuperable": tva_non_recuperable,
        "cout_entree": cout_entree,
        "ttc": ttc,
    }


def _add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:  # 29 février
        return d.replace(month=2, day=28, year=d.year + years)


def _days_30_360_inclusive(start: date, end: date) -> int:
    """Nombre de jours selon une convention 30/360, bornes inclusives.

    Cette convention permet d'obtenir notamment 180/360 pour une mise en service
    au 01/07 et une clôture au 31/12.
    """
    if end < start:
        return 0
    d1 = min(start.day, 30)
    d2 = min(end.day, 30)
    days = 360 * (end.year - start.year) + 30 * (end.month - start.month) + (d2 - d1) + 1
    # Sur une année complète 01/01 -> 31/12, la formule inclusive donne 360.
    return max(0, min(days, 360 * max(1, end.year - start.year + 1)))


def _months_inclusive(start: date, end: date) -> int:
    if end < start:
        return 0
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def _first_day_month(d: date) -> date:
    return d.replace(day=1)


def _last_day_month(d: date) -> date:
    return d.replace(day=monthrange(d.year, d.month)[1])


def _plan_lineaire(
    valeur_brute: Decimal,
    valeur_residuelle: Decimal,
    duree: int,
    debut: date,
    date_sortie: Optional[date] = None,
) -> list[dict]:
    base = max(money(valeur_brute - valeur_residuelle), ZERO)
    if base <= ZERO:
        return []
    fin_normale = _add_years(debut, duree) - timedelta(days=1)
    fin_plan = min(fin_normale, date_sortie) if date_sortie else fin_normale
    if fin_plan < debut:
        return []

    annuite = base / D(duree)
    cumul = ZERO
    tableau = []
    for annee in range(debut.year, fin_plan.year + 1):
        p_debut = max(debut, date(annee, 1, 1))
        p_fin = min(fin_plan, date(annee, 12, 31))
        if p_fin < p_debut:
            continue
        jours = _days_30_360_inclusive(p_debut, p_fin)
        prorata = min(D(jours) / D(360), ONE)
        dotation = money(annuite * prorata)

        # Sur le dernier exercice de la durée normale, absorber les centimes de
        # prorata/arrondi afin que le plan atteigne exactement la base amortissable.
        if p_fin == fin_normale:
            dotation = money(base - cumul)
        elif cumul + dotation > base:
            dotation = money(base - cumul)

        cumul = money(cumul + max(dotation, ZERO))
        vnc = money(valeur_brute - cumul)
        tableau.append({
            "annee": annee,
            "debut_periode": p_debut,
            "fin_periode": p_fin,
            "base_debut": money(valeur_brute - (cumul - dotation)),
            "prorata": (D(jours) / D(360)).quantize(Decimal("0.000001")),
            "dotation": dotation,
            "cumul": cumul,
            "valeur_nette": max(vnc, valeur_residuelle) if not date_sortie else vnc,
            "taux_effectif": (dotation / valeur_brute * HUNDRED).quantize(Decimal("0.01")) if valeur_brute else ZERO,
        })
    return tableau


def _plan_degressif(
    valeur_brute: Decimal,
    valeur_residuelle: Decimal,
    duree: int,
    date_acquisition: date,
    coeff: Optional[Decimal] = None,
    date_sortie: Optional[date] = None,
) -> list[dict]:
    if duree < 3:
        raise ValueError("Le dégressif requiert une durée d'au moins 3 ans")
    base_amort = max(money(valeur_brute - valeur_residuelle), ZERO)
    if base_amort <= ZERO:
        return []

    debut = _first_day_month(date_acquisition)
    # La durée dégressive est appréciée en mois entiers.
    fin_normale = _last_day_month(_add_years(debut, duree) - timedelta(days=1))
    fin_plan = min(fin_normale, date_sortie) if date_sortie else fin_normale
    if fin_plan < debut:
        return []

    coeff = D(coeff) if coeff else coefficient_degressif(duree)
    taux_deg = (ONE / D(duree)) * coeff
    cumul = ZERO
    tableau = []

    for annee in range(debut.year, fin_plan.year + 1):
        p_debut = max(debut, date(annee, 1, 1))
        p_fin = min(fin_plan, date(annee, 12, 31))
        if p_fin < p_debut:
            continue

        # Le dégressif marocain raisonne par mois entiers : le mois d'acquisition
        # est compté à partir de son premier jour.
        mois_periode = _months_inclusive(_first_day_month(p_debut), _first_day_month(p_fin))
        fraction = D(mois_periode) / D(12)
        vnc_debut = money(valeur_brute - cumul)
        restant_amort = max(money(vnc_debut - valeur_residuelle), ZERO)
        mois_restants = _months_inclusive(_first_day_month(p_debut), _first_day_month(fin_normale))

        dot_deg = money(restant_amort * taux_deg * fraction)
        dot_lin = money(restant_amort * D(mois_periode) / D(max(mois_restants, 1)))
        dotation = max(dot_deg, dot_lin)
        if cumul + dotation > base_amort:
            dotation = money(base_amort - cumul)
        if p_fin == fin_normale:
            dotation = money(base_amort - cumul)

        cumul = money(cumul + max(dotation, ZERO))
        vnc = money(valeur_brute - cumul)
        tableau.append({
            "annee": annee,
            "debut_periode": p_debut,
            "fin_periode": p_fin,
            "base_debut": vnc_debut,
            "prorata": fraction.quantize(Decimal("0.000001")),
            "dotation": dotation,
            "cumul": cumul,
            "valeur_nette": max(vnc, valeur_residuelle) if not date_sortie else vnc,
            "taux_effectif": (dotation / valeur_brute * HUNDRED).quantize(Decimal("0.01")) if valeur_brute else ZERO,
            "coefficient": coeff,
        })
    return tableau


def calculer_tableau_amortissement(immo, date_sortie_override: Optional[date] = None) -> list[dict]:
    if not bool(getattr(immo, "amortissable", True)):
        return []
    duree = getattr(immo, "duree_amort", None)
    if not duree or int(duree) <= 0:
        return []

    valeur_brute = money(getattr(immo, "valeur_brute", 0))
    residuelle = money(getattr(immo, "valeur_residuelle", 0))
    if residuelle < ZERO or residuelle > valeur_brute:
        raise ValueError("La valeur résiduelle doit être comprise entre 0 et la valeur brute")

    date_acq = getattr(immo, "date_acquisition")
    date_service = getattr(immo, "date_mise_en_service", None) or date_acq
    date_sortie = date_sortie_override if date_sortie_override is not None else getattr(immo, "date_sortie", None)
    methode = (getattr(immo, "methode", None) or "lineaire").lower()

    if methode == "lineaire":
        return _plan_lineaire(valeur_brute, residuelle, int(duree), date_service, date_sortie)
    if methode == "degressif":
        return _plan_degressif(
            valeur_brute, residuelle, int(duree), date_acq,
            getattr(immo, "taux_degressif", None), date_sortie,
        )
    raise ValueError(f"Méthode d'amortissement inconnue : {methode}")


def situation_a_date(immo, date_reference: date) -> dict:
    """Retourne cumul et VNC théoriques à une date donnée."""
    sortie = getattr(immo, "date_sortie", None)
    cutoff = min(date_reference, sortie) if sortie else date_reference
    tableau = calculer_tableau_amortissement(immo, date_sortie_override=cutoff)
    if not tableau:
        valeur = money(getattr(immo, "valeur_brute", 0))
        return {"cumul": ZERO, "vnc": valeur}
    last = tableau[-1]
    return {"cumul": money(last["cumul"]), "vnc": money(last["valeur_nette"])}



def dotation_sur_periode(immo, date_debut: date, date_fin: date) -> dict:
    """Dotation théorique comprise entre deux dates comptables incluses.

    Indépendante de l'année civile : elle sert aux exercices décalés en prenant
    la différence de cumul théorique entre l'ouverture et la clôture réelles.
    """
    if date_fin < date_debut:
        return {"dotation": ZERO, "cumul_ouverture": ZERO, "cumul_fin": ZERO}
    cumul_ouverture = money(situation_a_date(immo, date_debut - timedelta(days=1))["cumul"])
    cumul_fin = money(situation_a_date(immo, date_fin)["cumul"])
    return {
        "dotation": money(max(cumul_fin - cumul_ouverture, ZERO)),
        "cumul_ouverture": cumul_ouverture,
        "cumul_fin": cumul_fin,
    }

def resultat_cession(immo, date_cession: date, prix_cession_ht) -> dict:
    situation = situation_a_date(immo, date_cession)
    prix = money(prix_cession_ht)
    resultat = money(prix - situation["vnc"])
    return {
        "cumul_amortissement": situation["cumul"],
        "vnc": situation["vnc"],
        "prix_cession_ht": prix,
        "resultat_cession": resultat,
        "nature_resultat": "plus_value" if resultat > ZERO else "moins_value" if resultat < ZERO else "neutre",
    }
