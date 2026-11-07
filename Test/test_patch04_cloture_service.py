from decimal import Decimal
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.cloture_service import construire_ajustement, contrepasser


def _eq(lignes):
    return sum(x["debit"] for x in lignes) == sum(x["credit"] for x in lignes)


def test_cca():
    l, auto, c = construire_ajustement("cca", "1200", "6125")
    assert auto is True and _eq(l)
    assert l[0]["compte"] == "3491" and l[0]["debit"] == Decimal("1200.00")
    assert l[1]["compte"] == "6125" and l[1]["credit"] == Decimal("1200.00")


def test_fnp():
    l, auto, _ = construire_ajustement("fnp", 2500, "6131")
    assert auto is True and _eq(l)
    assert l[0]["compte"] == "6131" and l[1]["compte"] == "4417"


def test_pca_fae():
    pca, _, _ = construire_ajustement("pca", 900, "7124")
    fae, _, _ = construire_ajustement("fae", 900, "7124")
    assert _eq(pca) and _eq(fae)
    assert pca[0]["debit"] == Decimal("900.00") and pca[1]["credit"] == Decimal("900.00")
    assert fae[0]["compte"] == "3427" and fae[0]["debit"] == Decimal("900.00")


def test_provision_non_contrepassable():
    l, auto, _ = construire_ajustement("provision_risque", 3000)
    assert auto is False and _eq(l)
    assert l[0]["compte"] == "6195" and l[1]["compte"] == "1518"


def test_contrepassation():
    l, _, _ = construire_ajustement("cca", 1200, "6125")
    r = contrepasser(l)
    assert _eq(r)
    assert r[0]["credit"] == l[0]["debit"]
    assert r[1]["debit"] == l[1]["credit"]


if __name__ == "__main__":
    tests = [test_cca, test_fnp, test_pca_fae, test_provision_non_contrepassable, test_contrepassation]
    for t in tests:
        t()
    print(f"OK — {len(tests)} tests Clôture Patch 04")
