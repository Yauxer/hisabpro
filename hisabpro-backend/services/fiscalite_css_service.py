# -*- coding: utf-8 -*-
"""Contribution sociale de solidarité sur les bénéfices — Patch 08.6.

Référentiel : CGI 2026, articles 267 à 273, tels que prorogés pour 2026,
2027 et 2028 par la LF 2026. Les mêmes seuils/taux étaient applicables sur
2023-2025.

Pour une société, la contribution d'une année est assise sur le bénéfice net
fiscal du dernier exercice clos. Elle reste distincte de la liquidation IS.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0.00")
MILLION = Decimal("1000000.00")


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _add_months(d: date, months: int) -> date:
    idx = (d.month - 1) + months
    year = d.year + idx // 12
    month = idx % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def taux_css(benefice) -> Decimal:
    b = money(benefice)
    if b < MILLION:
        return Decimal("0.000")
    if b < Decimal("5000000"):
        return Decimal("1.500")
    if b < Decimal("10000000"):
        return Decimal("2.500")
    if b < Decimal("40000000"):
        return Decimal("3.500")
    return Decimal("5.000")


def calculer_css(
    *,
    annee: int,
    benefice_reference=None,
    exercice_reference: int | None = None,
    date_fin_reference: date | None = None,
    reference_forcee=None,
    exoneration_permanente: bool = False,
) -> dict:
    """Calcule la CSS due au titre de ``annee``.

    ``benefice_reference`` correspond au bénéfice net fiscal du dernier exercice
    clos. ``reference_forcee`` est réservé à la reprise d'un dossier lorsque la
    liquidation historique n'est pas disponible dans HisabPro.
    """
    if annee < 2023 or annee > 2028:
        return {
            "applicable": False,
            "disponible": True,
            "annee": annee,
            "exercice_reference": exercice_reference or annee - 1,
            "base": ZERO,
            "taux": Decimal("0.000"),
            "montant_du": ZERO,
            "source": "hors_periode",
            "libelle_source": "Contribution non paramétrée hors période 2023-2028",
            "date_echeance": None,
            "exoneree_permanente": bool(exoneration_permanente),
        }

    if reference_forcee is not None:
        base = money(reference_forcee)
        if base < ZERO:
            raise ValueError("Le bénéfice de référence CSS forcé ne peut pas être négatif.")
        source = "manuel"
        libelle = "Bénéfice net fiscal de référence saisi manuellement et justifié"
    elif benefice_reference is None:
        return {
            "applicable": True,
            "disponible": False,
            "annee": annee,
            "exercice_reference": exercice_reference or annee - 1,
            "base": ZERO,
            "taux": Decimal("0.000"),
            "montant_du": ZERO,
            "source": "indisponible",
            "libelle_source": f"Liquidation fiscale {exercice_reference or annee - 1} non confirmée",
            "date_echeance": _add_months(date_fin_reference, 3) if date_fin_reference else None,
            "exoneree_permanente": bool(exoneration_permanente),
        }
    else:
        base = money(benefice_reference)
        source = "liquidation_n_1"
        libelle = f"Bénéfice net fiscal confirmé de l'exercice {exercice_reference or annee - 1}"

    taux = taux_css(base)
    montant = money(base * taux / Decimal("100"))
    if exoneration_permanente:
        montant = ZERO

    return {
        "applicable": True,
        "disponible": True,
        "annee": annee,
        "exercice_reference": exercice_reference or annee - 1,
        "base": base,
        "taux": taux,
        "montant_du": montant,
        "source": source,
        "libelle_source": libelle,
        "date_echeance": _add_months(date_fin_reference, 3) if date_fin_reference else None,
        "exoneree_permanente": bool(exoneration_permanente),
        "sous_seuil": base < MILLION,
    }
