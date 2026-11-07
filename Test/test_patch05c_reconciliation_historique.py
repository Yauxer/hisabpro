# -*- coding: utf-8 -*-
from decimal import Decimal
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.immobilisations_reconciliation_service import (  # noqa: E402
    comptes_recommandes,
    suggerer_categorie,
    construire_lignes_reclassement,
)


def test_suggestion_serveur():
    cat, forte = suggerer_categorie("Serveur Dell", "Véhicule")
    assert cat == "Matériel informatique"
    assert forte is True
    assert comptes_recommandes(cat)["compte_immo"] == "2355"


def test_voiture():
    cat, _ = suggerer_categorie("Voiture commerciale", "Véhicule")
    c = comptes_recommandes(cat)
    assert c == {"compte_immo": "2340", "compte_amort": "2834", "compte_dotation": "61934"}


def test_reclassement_ne_cree_aucun_montant_manquant():
    item = {
        "acquisition": {"comptes_detectes": {"2340": 10000.00}},
        "amortissement": {
            "comptes_detectes": {"2834": 677.78},
            "dotations_exercice_detectees": {"61934": 677.78},
        },
    }
    cible = comptes_recommandes("Matériel informatique")
    lignes = construire_lignes_reclassement(item, cible, 2026)
    debit = sum((Decimal(str(x[1])) for x in lignes), Decimal("0"))
    credit = sum((Decimal(str(x[2])) for x in lignes), Decimal("0"))
    assert debit == credit
    assert debit == Decimal("11355.56")  # 10 000 + 677,78 + 677,78 transférés
    assert all(Decimal(str(d)) >= 0 and Decimal(str(c)) >= 0 for _, d, c, _ in lignes)


def test_orpheline_sans_acquisition_ne_fabrique_pas_brut():
    item = {
        "acquisition": {"comptes_detectes": {}},
        "amortissement": {
            "comptes_detectes": {"2834": 2000.00},
            "dotations_exercice_detectees": {"6193": 2000.00},
        },
    }
    lignes = construire_lignes_reclassement(item, comptes_recommandes("Matériel informatique"), 2026)
    # Aucun débit 2355 n'est créé : seuls les amortissements/dotations existants sont reclassés.
    assert not any(compte == "2355" for compte, *_ in lignes)
    assert any(compte == "28355" for compte, *_ in lignes)
    assert any(compte == "61935" for compte, *_ in lignes)


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
    print(f"OK — {len(tests)} tests Patch 05C réconciliation historique")
