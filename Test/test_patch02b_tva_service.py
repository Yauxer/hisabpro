from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.tva_service import (
    D, acompte_ttc_ventilation, appliquer_credit_periode,
    appliquer_pourcentage, soustraire_ventilation,
    total_ventilation, ventilation_avoir, ventilation_facture,
)


def ns(**kwargs):
    return SimpleNamespace(**kwargs)


def facture_simple():
    return ns(
        lignes=[ns(quantite=1, prix_unitaire=1000, tva=20, remise=0, remise2=0, rabais=0)],
        frais_transport_ht=0, frais_transport_tva=20,
        frais_emballage_ht=0, frais_emballage_tva=20,
        remise_globale=0, ristourne=0, escompte=0,
    )


def test_acompte_ttc_20():
    v = acompte_ttc_ventilation(1200, 20)[D(20)]
    assert v["base"] == Decimal("1000.00")
    assert v["tva"] == Decimal("200.00")
    assert v["ttc"] == Decimal("1200.00")


def test_avoir_diminue_facture():
    f = facture_simple()
    av = ns(lignes=[ns(quantite=1, prix_unitaire=300, tva=20, remise=0, remise2=0, rabais=0)])
    net = soustraire_ventilation(ventilation_facture(f), ventilation_avoir(av))
    total = total_ventilation(net)
    assert total["base"] == Decimal("700.00")
    assert total["tva"] == Decimal("140.00")
    assert total["ttc"] == Decimal("840.00")


def test_prorata_80_pourcent():
    v = ventilation_facture(facture_simple())
    v80 = appliquer_pourcentage(v, 80)
    total = total_ventilation(v80)
    assert total["base"] == Decimal("800.00")
    assert total["tva"] == Decimal("160.00")


def test_credit_anterieur_absorbe_tva_due():
    r = appliquer_credit_periode(150, 200, 100)
    assert r["tva_due"] == Decimal("0.00")
    assert r["credit_fin"] == Decimal("50.00")


def test_credit_genere_sur_periode():
    r = appliquer_credit_periode(0, 100, 260)
    assert r["tva_due"] == Decimal("0.00")
    assert r["credit_fin"] == Decimal("160.00")


if __name__ == "__main__":
    tests = [
        test_acompte_ttc_20,
        test_avoir_diminue_facture,
        test_prorata_80_pourcent,
        test_credit_anterieur_absorbe_tva_due,
        test_credit_genere_sur_periode,
    ]
    for test in tests:
        test()
    print(f"OK — {len(tests)} tests TVA Patch 02B")
