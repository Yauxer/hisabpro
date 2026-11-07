from datetime import date
from decimal import Decimal
from types import SimpleNamespace
import os
import pytest
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
from services import etic_service as etic


def test_absence_date_ne_declenche_pas_echeance_60_jours():
    f = SimpleNamespace(date=date(2026, 1, 1), delai_paiement=60, echeances=[])
    assert etic._echeances_documentees_etic(f, Decimal("120")) == []


def test_date_enregistree_est_conservee():
    f = SimpleNamespace(date_echeance=date(2027, 2, 1), echeances=[])
    assert etic._echeances_documentees_etic(f, Decimal("120"))[0]["date_echeance"] == f.date_echeance


@pytest.mark.parametrize("montants", [[60, 59], [0, 120], [-10, 130]])
def test_echeancier_incoherent_non_qualifie(montants):
    f = SimpleNamespace(date_echeance=date(2026, 2, 1), echeances=[
        SimpleNamespace(ordre=i, date_echeance=date(2026 + i, 6, 1), montant=m)
        for i, m in enumerate(montants)
    ])
    assert etic._echeances_documentees_etic(f, Decimal("120")) == []


def test_echeancier_documente_conserve_les_tranches():
    f = SimpleNamespace(echeances=[
        SimpleNamespace(ordre=1, date_echeance=date(2026, 6, 1), montant=60),
        SimpleNamespace(ordre=2, date_echeance=date(2028, 6, 1), montant=60),
    ])
    rows = etic._echeances_documentees_etic(f, Decimal("120"))
    assert etic._classer_echeances_ouvertes(
        etic.repartition_fifo(rows, 30, date(2026, 12, 31))["echeances"], date(2026, 12, 31)
    ) == {"echues": Decimal("30"), "moins_un_an": Decimal("0"), "plus_un_an": Decimal("60")}


@pytest.mark.parametrize("qualifie", [0, 80])
def test_source_recoupe_solde_mais_dates_manquantes_bloquent_confirmation(monkeypatch, qualifie):
    monkeypatch.setattr(etic, "_ventilation_factures_par_compte", lambda *a: {
        "3421": {"echues": Decimal(qualifie), "moins_un_an": Decimal(0),
                 "plus_un_an": Decimal(0), "total_source": Decimal(120)}
    })
    lignes = [{"compte": "3421", "montant": 120}]
    etic._ajouter_echeances_auto(object(), 3, 2026, lignes, "vente")
    row = lignes[0]
    assert "echeance_auto" not in row
    assert row["echeance_auto_ecart"] == 0
    assert row["echeance_auto_non_qualifie"] == 120 - qualifie
    if qualifie:
        assert row["echeance_auto_reliquat"] == 40
        assert row["echeance_auto_partiel"]["echues"] == 80
    assert etic._erreurs_ventilation_b6_b7("B6", {"lignes": lignes}, {"autres_analyses_neant": True})
