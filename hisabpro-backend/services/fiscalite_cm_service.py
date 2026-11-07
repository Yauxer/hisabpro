# -*- coding: utf-8 -*-
"""Cotisation minimale (CM) — Patch 08.4.

Référentiel principal : CGI 2026, article 144.
Le moteur calcule la base CM à partir des comptes de produits éligibles puis
applique :
- 0,25 % au droit commun ;
- 0,15 % à la fraction d'opérations éligibles au taux réduit ;
- minimum de perception de 3 000 MAD pour l'IS, sauf exception justifiée ;
- exonération totale éventuelle, historisée et justifiée.

La ventilation au taux réduit et les exclusions particulières ne sont jamais
inférées à partir d'un simple secteur : elles doivent être confirmées dans les
paramètres fiscaux de l'exercice.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0.00")
TAUX_CM_STANDARD = Decimal("0.25")
TAUX_CM_REDUIT = Decimal("0.15")
MINIMUM_CM_IS = Decimal("3000.00")

# Article 144-I-B : CA + autres produits d'exploitation, produits financiers,
# subventions et dons. Les familles ci-dessous correspondent au CGNC utilisé
# par HisabPro. Les variations de stocks, immobilisations produites, reprises,
# cessions d'immobilisations et transferts de charges restent hors base.
FAMILLES_CM = (
    ("chiffre_affaires", "Chiffre d'affaires", ("711", "712")),
    ("autres_produits_exploitation", "Autres produits d'exploitation", ("718",)),
    ("subventions_exploitation", "Subventions d'exploitation", ("716",)),
    ("produits_financiers", "Produits financiers", ("732", "733", "738")),
    ("subventions_dons_non_courants", "Subventions et dons non courants", ("756", "7586")),
)

PRODUITS_TAUX_REDUIT_015 = (
    "produits pétroliers",
    "gaz",
    "beurre",
    "huile",
    "sucre",
    "farine",
    "eau",
    "électricité",
    "médicaments",
)


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _somme_prefixes(produits_par_compte: dict, prefixes: tuple[str, ...]) -> Decimal:
    total = ZERO
    for compte, montant in (produits_par_compte or {}).items():
        code = str(compte or "").strip()
        if any(code.startswith(prefixe) for prefixe in prefixes):
            total += money(montant)
    return money(total)


def calculer_base_cm(produits_par_compte: dict) -> dict:
    """Reconstruit la base brute CM depuis les comptes de produits validés."""
    details = []
    total = ZERO
    for code, libelle, prefixes in FAMILLES_CM:
        montant = _somme_prefixes(produits_par_compte, prefixes)
        details.append({"code": code, "libelle": libelle, "montant": montant, "prefixes": list(prefixes)})
        total += montant
    # Une contre-écriture peut rendre ponctuellement une famille négative ; la
    # base totale ne doit toutefois jamais devenir négative.
    return {"base_comptable_brute": money(max(ZERO, total)), "details": details}


def calculer_cotisation_minimale(
    *,
    produits_par_compte: dict,
    is_theorique,
    base_exclue=0,
    base_taux_reduit_015=0,
    exoneration_totale=False,
    minimum_3000_exonere=False,
) -> dict:
    base = calculer_base_cm(produits_par_compte)
    brute = money(base["base_comptable_brute"])
    exclue = money(base_exclue)
    reduite = money(base_taux_reduit_015)
    is_calcule = money(is_theorique)

    if exclue < 0 or reduite < 0:
        raise ValueError("Les ajustements de base CM doivent être positifs.")
    if exclue > brute:
        raise ValueError("La base exclue de la CM ne peut pas dépasser la base comptable brute.")

    base_apres_exclusion = money(brute - exclue)
    if reduite > base_apres_exclusion:
        raise ValueError("La base soumise au taux CM de 0,15% ne peut pas dépasser la base CM après exclusions.")

    base_standard = money(base_apres_exclusion - reduite)
    cm_standard = money(base_standard * TAUX_CM_STANDARD / Decimal("100"))
    cm_reduite = money(reduite * TAUX_CM_REDUIT / Decimal("100"))
    cm_calculee = money(cm_standard + cm_reduite)

    minimum = ZERO if minimum_3000_exonere else MINIMUM_CM_IS
    if exoneration_totale:
        cm_exigible = ZERO
        motif_calcul = "exoneration_totale"
    else:
        cm_exigible = money(max(cm_calculee, minimum))
        motif_calcul = "minimum_3000" if minimum > ZERO and cm_calculee < minimum else "calcul_proportionnel"

    impot_du = money(max(is_calcule, cm_exigible))
    nature = "IS" if is_calcule >= cm_exigible else "CM"

    return {
        **base,
        "base_exclue": exclue,
        "base_apres_exclusion": base_apres_exclusion,
        "base_taux_reduit_015": reduite,
        "base_taux_standard_025": base_standard,
        "taux_standard": TAUX_CM_STANDARD,
        "taux_reduit": TAUX_CM_REDUIT,
        "cm_part_standard": cm_standard,
        "cm_part_reduite": cm_reduite,
        "cm_calculee": cm_calculee,
        "minimum_3000": money(minimum),
        "exoneration_totale": bool(exoneration_totale),
        "minimum_3000_exonere": bool(minimum_3000_exonere),
        "cm_exigible": cm_exigible,
        "motif_calcul": motif_calcul,
        "is_theorique": is_calcule,
        "impot_du_avant_acomptes": impot_du,
        "nature_impot_du": nature,
        "produits_taux_reduit_015": list(PRODUITS_TAUX_REDUIT_015),
    }
