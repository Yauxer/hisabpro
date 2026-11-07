from decimal import Decimal
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.livre_inventaire_service import calculer_cpc, calculer_bilan, empreinte_snapshot


def test_cpc_simple():
    soldes = {
        "7111": Decimal("-120000.00"),
        "6111": Decimal("40000.00"),
        "6134": Decimal("10000.00"),
        "61935": Decimal("1000.00"),
    }
    cpc = calculer_cpc(soldes)
    assert cpc["total_produits_exploitation"] == Decimal("120000.00")
    assert cpc["total_charges_exploitation"] == Decimal("51000.00")
    assert cpc["resultat_net"] == Decimal("69000.00")


def test_bilan_equilibre_simple():
    soldes = {
        "1111": Decimal("-100000.00"),
        "5141": Decimal("100000.00"),
    }
    b = calculer_bilan(soldes, Decimal("0.00"))
    assert b["total_actif"] == Decimal("100000.00")
    assert b["total_passif"] == Decimal("100000.00")
    assert b["equilibre"] is True


def test_hash_stable():
    a = {"b": 2, "a": {"x": 1}}
    b = {"a": {"x": 1}, "b": 2}
    assert empreinte_snapshot(a) == empreinte_snapshot(b)


if __name__ == "__main__":
    test_cpc_simple(); test_bilan_equilibre_simple(); test_hash_stable()
    print("OK — 3 tests Livre d'inventaire Patch 05")
