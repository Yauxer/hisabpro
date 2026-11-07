# -*- coding: utf-8 -*-
"""Tests autonomes Patch 05B — Livre d'inventaire v2."""
from decimal import Decimal
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.livre_inventaire_service import (  # noqa: E402
    CURRENT_LIVRE_VERSION,
    calculer_bilan,
    calculer_rapprochement_immobilisations,
)


def test_version_archive_v2():
    assert CURRENT_LIVRE_VERSION == 2


def test_tresorerie_sans_compensation():
    soldes = {
        "5141": Decimal("2038.00"),
        "5144": Decimal("-13200.00"),
    }
    bilan = calculer_bilan(soldes, Decimal("0"))
    banque_actif = next(x for x in bilan["tresorerie_actif"] if x["label"].startswith("Banques"))
    reclass_passif = next(x for x in bilan["tresorerie_passif"] if "à reclasser" in x["label"])
    assert banque_actif["net"] == Decimal("2038.00")
    assert reclass_passif["montant"] == Decimal("13200.00")


def test_immobilisations_ecart_detecte_compte_par_compte():
    lignes = [
        {"compte_immo": "2340", "compte_amort": "2834", "valeur_brute": 50000, "amortissements_cumules": 12205.56},
        {"compte_immo": "2350", "compte_amort": "2835", "valeur_brute": 120000, "amortissements_cumules": 10866.67},
        {"compte_immo": "2355", "compte_amort": "28355", "valeur_brute": 1000, "amortissements_cumules": 67.78},
    ]
    soldes = {
        "2340": Decimal("20000.00"),
        "2350": Decimal("120000.00"),
        "2355": Decimal("1000.00"),
        "2834": Decimal("-13677.78"),
        "2835": Decimal("-24000.00"),
        "28355": Decimal("-67.78"),
    }
    r = calculer_rapprochement_immobilisations(lignes, soldes)
    assert r["brut_module"] == 171000.0
    assert r["brut_comptable"] == 141000.0
    assert r["ecart_brut"] == 30000.0
    assert r["rapproche"] is False
    assert any(x["compte"] == "2340" and x["ecart"] == 30000.0 for x in r["details_comptes"])


def test_immobilisations_rapprochees():
    lignes = [
        {"compte_immo": "2355", "compte_amort": "28355", "valeur_brute": 1000, "amortissements_cumules": 67.78},
    ]
    soldes = {"2355": Decimal("1000.00"), "28355": Decimal("-67.78")}
    r = calculer_rapprochement_immobilisations(lignes, soldes)
    assert r["rapproche"] is True
    assert r["ecart_brut"] == 0.0
    assert r["ecart_amortissements"] == 0.0
    assert r["ecart_vnc"] == 0.0


if __name__ == "__main__":
    tests = [
        test_version_archive_v2,
        test_tresorerie_sans_compensation,
        test_immobilisations_ecart_detecte_compte_par_compte,
        test_immobilisations_rapprochees,
    ]
    for test in tests:
        test()
    print("OK — 4 tests Patch 05B cohérence Livre d'inventaire")
