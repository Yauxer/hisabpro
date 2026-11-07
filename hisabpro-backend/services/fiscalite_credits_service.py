# -*- coding: utf-8 -*-
"""Retenues et crédits imputables sur l'IS — Patch 08.6."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0.00")
TYPES_CREDIT_IS = {
    "pprf": "Retenue à la source sur produits de placements à revenu fixe (PPRF)",
    "retenue_tiers": "Retenue à la source sur rémunérations allouées à des tiers",
    "autre": "Autre crédit / retenue imputable documenté",
}
ORDRE = ("pprf", "retenue_tiers", "autre")


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def construire_credits_is(credits) -> dict:
    """Agrège les crédits et calcule le reliquat disponible à la liquidation.

    Un crédit peut avoir déjà été utilisé sur des acomptes. Cette fraction est
    conservée pour la traçabilité mais n'est évidemment pas imputée une seconde
    fois lors de la liquidation annuelle.
    """
    lignes = []
    par_type = {k: ZERO for k in TYPES_CREDIT_IS}
    deja_acomptes = ZERO
    disponible = ZERO

    for c in credits or []:
        typ = getattr(c, "type", None) if not isinstance(c, dict) else c.get("type")
        if typ not in TYPES_CREDIT_IS:
            raise ValueError(f"Type de crédit IS inconnu : {typ}")
        montant = money(getattr(c, "montant", 0) if not isinstance(c, dict) else c.get("montant"))
        impute = money(
            getattr(c, "montant_deja_impute_acomptes", 0)
            if not isinstance(c, dict) else c.get("montant_deja_impute_acomptes")
        )
        if montant <= ZERO:
            raise ValueError("Le montant d'un crédit IS doit être positif.")
        if impute < ZERO or impute > montant:
            raise ValueError("La fraction déjà imputée sur acomptes doit être comprise entre 0 et le montant du crédit.")
        solde = money(montant - impute)
        par_type[typ] = money(par_type[typ] + solde)
        deja_acomptes = money(deja_acomptes + impute)
        disponible = money(disponible + solde)
        if isinstance(c, dict):
            ligne = dict(c)
        else:
            ligne = {
                "id": getattr(c, "id", None),
                "type": typ,
                "montant": montant,
                "montant_deja_impute_acomptes": impute,
                "date_retenue": getattr(c, "date_retenue", None),
                "reference": getattr(c, "reference", None),
                "commentaire": getattr(c, "commentaire", None),
            }
        ligne.update({
            "libelle_type": TYPES_CREDIT_IS[typ],
            "montant": montant,
            "montant_deja_impute_acomptes": impute,
            "solde_liquidation": solde,
        })
        lignes.append(ligne)

    return {
        "types": TYPES_CREDIT_IS,
        "lignes": lignes,
        "par_type": par_type,
        "total_montant": money(sum((money(l["montant"]) for l in lignes), ZERO)),
        "total_deja_impute_acomptes": deja_acomptes,
        "total_disponible_liquidation": disponible,
    }
