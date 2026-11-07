# -*- coding: utf-8 -*-
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
Q4 = Decimal("0.0001")


def money(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(CENT, rounding=ROUND_HALF_UP)


def qty(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(Q4, rounding=ROUND_HALF_UP)


def construire_lignes_rapprochement(cibles: dict, soldes: dict):
    """Construit l'ajustement du stock 31xx vers la valeur physique cible."""
    lignes = []
    for compte_stock, info in sorted(cibles.items()):
        variations = set(info.get("variations") or [])
        if len(variations) != 1:
            raise ValueError(
                f"Le compte de stock {compte_stock} est associé à plusieurs comptes de variation."
            )
        cible = money(info.get("valeur", 0))
        actuel = money(soldes.get(compte_stock, 0))
        ecart = money(cible - actuel)
        if abs(ecart) <= CENT:
            continue
        compte_variation = next(iter(variations))
        if ecart > 0:
            lignes.extend([
                {"compte": compte_stock, "libelle": "Stock final", "debit": ecart, "credit": Decimal("0.00")},
                {"compte": compte_variation, "libelle": "Variation de stock", "debit": Decimal("0.00"), "credit": ecart},
            ])
        else:
            montant = -ecart
            lignes.extend([
                {"compte": compte_variation, "libelle": "Variation de stock", "debit": montant, "credit": Decimal("0.00")},
                {"compte": compte_stock, "libelle": "Stock final", "debit": Decimal("0.00"), "credit": montant},
            ])
    return lignes
