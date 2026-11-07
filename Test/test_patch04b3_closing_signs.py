from decimal import Decimal
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.cloture_service import construire_ligne_soldage


def test_solde_debiteur():
    l = construire_ligne_soldage("6111", Decimal("34100.00"))
    assert l["debit"] == Decimal("0.00")
    assert l["credit"] == Decimal("34100.00")


def test_solde_crediteur_atypique_charge():
    # Cas réellement rencontré : CCA sur 6134 sans charge initiale dans le jeu de test.
    l = construire_ligne_soldage("6134", Decimal("-1200.00"))
    assert l["debit"] == Decimal("1200.00")
    assert l["credit"] == Decimal("0.00")


def test_solde_crediteur_produit():
    l = construire_ligne_soldage("7124", Decimal("-1000.00"))
    assert l["debit"] == Decimal("1000.00")
    assert l["credit"] == Decimal("0.00")


def test_jamais_de_montant_negatif():
    for s in (Decimal("1200"), Decimal("-1200"), Decimal("0")):
        l = construire_ligne_soldage("6134", s)
        if l:
            assert l["debit"] >= 0 and l["credit"] >= 0
            assert (l["debit"] == 0) != (l["credit"] == 0)


if __name__ == "__main__":
    tests = [test_solde_debiteur, test_solde_crediteur_atypique_charge,
             test_solde_crediteur_produit, test_jamais_de_montant_negatif]
    for t in tests:
        t()
    print(f"OK — {len(tests)} tests Patch 04B.3 soldage de clôture")
