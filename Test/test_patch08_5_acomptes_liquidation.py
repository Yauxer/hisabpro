from datetime import date
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND / "services"))

import fiscalite_acomptes_service as service


def test_echeances_exercice_calendaire():
    assert service.echeances_acomptes(date(2026, 1, 1)) == [
        date(2026, 3, 31), date(2026, 6, 30), date(2026, 9, 30), date(2026, 12, 31)
    ]


def test_reference_transition_2026_recalcule_taux_courant_sur_benefice_n1():
    r = service.determiner_reference_acomptes(
        exercice=2026,
        liquidation_precedente={"benefice_fiscal_imposable": 500000, "impot_du": 87500},
        categorie_is="droit_commun",
    )
    assert r["source"] == "transition_2023_2026"
    assert r["taux_reference"] == Decimal("20.000")
    assert r["montant_annuel"] == Decimal("100000.00")


def test_reference_apres_transition_reprend_impot_confirme_n1():
    r = service.determiner_reference_acomptes(
        exercice=2027,
        liquidation_precedente={"benefice_fiscal_imposable": 500000, "impot_du": 120000},
        categorie_is="droit_commun",
    )
    assert r["source"] == "liquidation_n_1"
    assert r["montant_annuel"] == Decimal("120000.00")
    assert r["provisoire"] is True


def test_reference_manuelle_prime_et_doit_etre_non_negative():
    r = service.determiner_reference_acomptes(
        exercice=2026, liquidation_precedente=None, categorie_is="droit_commun", reference_forcee=40000
    )
    assert r["source"] == "manuel"
    assert r["montant_annuel"] == Decimal("40000.00")


def test_quatre_acomptes_font_25_pourcent_chacun():
    ref = {"disponible": True, "montant_annuel": Decimal("40000"), "source": "manuel"}
    r = service.construire_acomptes(date_debut=date(2026,1,1), reference=ref, date_reference=date(2026,1,1))
    assert [x["montant_du"] for x in r["acomptes"]] == [Decimal("10000.00")] * 4
    assert r["total_du"] == Decimal("40000.00")


def test_excedent_n1_s_impute_dabord_sur_les_acomptes():
    ref = {"disponible": True, "montant_annuel": Decimal("40000"), "source": "manuel"}
    r = service.construire_acomptes(
        date_debut=date(2026,1,1), reference=ref, excedent_precedent=15000, date_reference=date(2026,1,1)
    )
    assert r["acomptes"][0]["credit_n_1_impute"] == Decimal("10000.00")
    assert r["acomptes"][0]["montant_net_a_verser"] == Decimal("0.00")
    assert r["acomptes"][1]["credit_n_1_impute"] == Decimal("5000.00")
    assert r["acomptes"][1]["montant_net_a_verser"] == Decimal("5000.00")
    assert r["credit_n_1_restant_apres_acomptes"] == Decimal("0.00")


def test_statut_retard_et_dispense():
    ref = {"disponible": True, "montant_annuel": Decimal("40000"), "source": "manuel"}
    r = service.construire_acomptes(
        date_debut=date(2026,1,1), reference=ref,
        paiements=[{"numero": 2, "dispense": True, "reference_dispense": "DECL-1"}],
        date_reference=date(2026,7,1),
    )
    assert r["acomptes"][0]["statut"] == "en_retard"
    assert r["acomptes"][1]["statut"] == "dispense"
    assert r["acomptes"][2]["statut"] == "a_venir"


def test_liquidation_calcule_solde_a_payer():
    situation = {"total_verse": Decimal("30000"), "credit_n_1_impute": Decimal("5000")}
    r = service.calculer_liquidation(impot_du_avant_acomptes=50000, situation_acomptes=situation)
    assert r["acomptes_et_credit_imputables"] == Decimal("35000.00")
    assert r["solde_a_payer"] == Decimal("15000.00")
    assert r["excedent_acomptes"] == Decimal("0.00")


def test_liquidation_calcule_excedent_reportable():
    situation = {"total_verse": Decimal("50000"), "credit_n_1_impute": Decimal("10000")}
    r = service.calculer_liquidation(impot_du_avant_acomptes=40000, situation_acomptes=situation)
    assert r["solde_a_payer"] == Decimal("0.00")
    assert r["excedent_acomptes"] == Decimal("20000.00")
    assert r["nature_solde"] == "excedent"


def test_sql_router_et_ui_exposent_patch_08_5():
    sql = (BACKEND / "024_acomptes_liquidation_is.sql").read_text(encoding="utf-8")
    router = (BACKEND / "routers" / "fiscalite.py").read_text(encoding="utf-8")
    api = (ROOT / "src" / "services" / "api.js").read_text(encoding="utf-8")
    page = (ROOT / "src" / "pages" / "FiscaliteIS.jsx").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS fiscal_liquidations_is" in sql
    assert "CREATE TABLE IF NOT EXISTS fiscal_acomptes_is" in sql
    assert "trg_hisabpro_fiscal_liquidation_immutable" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_acomptes_is TO hisabpro" in sql
    assert "determiner_reference_acomptes" in router
    assert "liquidation/confirmer" in router
    assert "enregistrerAcompteIS" in api
    assert "Acomptes provisionnels & liquidation" in page
