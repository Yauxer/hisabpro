from decimal import Decimal
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND / "services"))

import fiscalite_cm_service as service


def test_base_cm_ne_retient_que_les_familles_de_article_144():
    r = service.calculer_base_cm({
        "7111": 100000,      # CA
        "71243": 50000,      # services
        "7188": 1000,        # autre exploitation
        "7161": 2000,        # subvention exploitation
        "7321": 3000,        # produit financier
        "7331": 4000,        # gain change
        "7381": 5000,        # intérêts
        "7561": 6000,        # subvention non courante
        "75861": 7000,       # don reçu
        "71321": 999999,     # variation stocks — exclue
        "7143": 999999,      # immobilisation produite — exclue
        "7195": 999999,      # reprise exploitation — exclue
        "7392": 999999,      # reprise financière — exclue
        "7513": 999999,      # cession immobilisation — exclue
        "7577": 999999,      # reprise subvention investissement — exclue
    })
    assert r["base_comptable_brute"] == Decimal("178000.00")


def test_cm_droit_commun_applique_025_et_minimum_3000():
    r = service.calculer_cotisation_minimale(
        produits_par_compte={"7111": 500000},
        is_theorique=0,
    )
    assert r["cm_calculee"] == Decimal("1250.00")
    assert r["minimum_3000"] == Decimal("3000.00")
    assert r["cm_exigible"] == Decimal("3000.00")
    assert r["impot_du_avant_acomptes"] == Decimal("3000.00")
    assert r["nature_impot_du"] == "CM"


def test_cm_proportionnelle_depasse_minimum():
    r = service.calculer_cotisation_minimale(
        produits_par_compte={"7111": 2000000},
        is_theorique=1000,
    )
    assert r["cm_calculee"] == Decimal("5000.00")
    assert r["cm_exigible"] == Decimal("5000.00")
    assert r["nature_impot_du"] == "CM"


def test_cm_mixte_taux_015_et_025():
    r = service.calculer_cotisation_minimale(
        produits_par_compte={"7111": 1000000},
        is_theorique=100,
        base_taux_reduit_015=400000,
    )
    assert r["base_taux_reduit_015"] == Decimal("400000.00")
    assert r["base_taux_standard_025"] == Decimal("600000.00")
    assert r["cm_part_reduite"] == Decimal("600.00")
    assert r["cm_part_standard"] == Decimal("1500.00")
    assert r["cm_calculee"] == Decimal("2100.00")
    assert r["cm_exigible"] == Decimal("3000.00")


def test_base_exclue_reduit_assiette_avant_ventilation():
    r = service.calculer_cotisation_minimale(
        produits_par_compte={"7111": 2000000},
        is_theorique=0,
        base_exclue=500000,
        base_taux_reduit_015=500000,
    )
    assert r["base_apres_exclusion"] == Decimal("1500000.00")
    assert r["base_taux_standard_025"] == Decimal("1000000.00")
    assert r["cm_calculee"] == Decimal("3250.00")


def test_exoneration_totale_met_cm_a_zero_sans_annuler_is():
    r = service.calculer_cotisation_minimale(
        produits_par_compte={"7111": 10000000},
        is_theorique=25000,
        exoneration_totale=True,
    )
    assert r["cm_exigible"] == Decimal("0.00")
    assert r["impot_du_avant_acomptes"] == Decimal("25000.00")
    assert r["nature_impot_du"] == "IS"


def test_neutralisation_minimum_conserve_cm_proportionnelle():
    r = service.calculer_cotisation_minimale(
        produits_par_compte={"7111": 500000},
        is_theorique=0,
        minimum_3000_exonere=True,
    )
    assert r["minimum_3000"] == Decimal("0.00")
    assert r["cm_exigible"] == Decimal("1250.00")


def test_is_superieur_a_cm_reste_impot_du():
    r = service.calculer_cotisation_minimale(
        produits_par_compte={"7111": 2000000},
        is_theorique=100000,
    )
    assert r["cm_exigible"] == Decimal("5000.00")
    assert r["impot_du_avant_acomptes"] == Decimal("100000.00")
    assert r["nature_impot_du"] == "IS"


def test_ajustements_cm_incoherents_sont_refuses():
    with pytest.raises(ValueError):
        service.calculer_cotisation_minimale(
            produits_par_compte={"7111": 1000}, is_theorique=0, base_exclue=1001
        )
    with pytest.raises(ValueError):
        service.calculer_cotisation_minimale(
            produits_par_compte={"7111": 1000}, is_theorique=0, base_taux_reduit_015=1001
        )


def test_sql_023_et_ui_exposent_cm_avec_justifications():
    sql = (BACKEND / "023_cotisation_minimale.sql").read_text(encoding="utf-8")
    router = (BACKEND / "routers" / "fiscalite.py").read_text(encoding="utf-8")
    page = (ROOT / "src" / "pages" / "FiscaliteIS.jsx").read_text(encoding="utf-8")
    assert "cm_base_taux_reduit_015" in sql
    assert "cm_exoneration_totale" in sql
    assert "ck_fiscal_cm_taux_reduit_justifie" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_parametres_exercice TO hisabpro" in sql
    assert "calculer_cotisation_minimale" in router
    assert '"cotisation_minimale": cotisation_minimale' in router
    assert "Cotisation minimale" in page
    assert "Impôt dû avant acomptes" in page
    assert "Base éligible au taux réduit 0,15 %" in page
