from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND / "services"))
import fiscalite_is_service as service


def test_bareme_droit_commun_2026_cible_20_35():
    assert service.determiner_taux_is(2026, 250_000).taux == Decimal("20.000")
    assert service.determiner_taux_is(2026, 5_000_000).taux == Decimal("20.000")
    assert service.determiner_taux_is(2026, 100_000_000).taux == Decimal("35.000")


def test_bareme_transition_2025_droit_commun():
    assert service.determiner_taux_is(2025, 250_000).taux == Decimal("17.500")
    assert service.determiner_taux_is(2025, 800_000).taux == Decimal("20.000")
    assert service.determiner_taux_is(2025, 5_000_000).taux == Decimal("22.750")
    assert service.determiner_taux_is(2025, 100_000_000).taux == Decimal("34.000")


def test_categories_speciales_2026():
    assert service.determiner_taux_is(2026, 10_000_000, "industrielle").taux == Decimal("20.000")
    assert service.determiner_taux_is(2026, 150_000_000, "cfc_zai").taux == Decimal("20.000")
    assert service.determiner_taux_is(2026, 150_000_000, "convention_investissement").taux == Decimal("20.000")
    assert service.determiner_taux_is(2026, 10_000_000, "financier_40").taux == Decimal("40.000")
    assert service.determiner_taux_is(2025, 10_000_000, "avantage_20_transition").taux == Decimal("20.000")
    assert service.determiner_taux_is(2025, 150_000_000, "avantage_20_transition").taux == Decimal("31.250")


def test_maintien_seuil_100m_transition_force_taux_haut():
    r = service.determiner_taux_is(2026, 5_000_000, "droit_commun", True)
    assert r.taux == Decimal("35.000")


def test_calcul_resultat_fiscal_deficit_et_is():
    r = service.calculer_is(
        exercice=2026,
        resultat_comptable_avant_is=1_000_000,
        reintegrations=100_000,
        deductions=50_000,
        deficit_reportable_disponible=200_000,
        categorie_is="droit_commun",
    )
    assert r["resultat_fiscal_avant_deficit"] == Decimal("1050000.00")
    assert r["deficit_impute"] == Decimal("200000.00")
    assert r["benefice_fiscal_imposable"] == Decimal("850000.00")
    assert r["taux_is"] == Decimal("20.000")
    assert r["is_theorique"] == Decimal("170000.00")


def test_deficit_fiscal_genere_si_resultat_negatif():
    r = service.calculer_is(
        exercice=2026,
        resultat_comptable_avant_is=-100_000,
        reintegrations=20_000,
        deductions=10_000,
    )
    assert r["resultat_fiscal_avant_deficit"] == Decimal("-90000.00")
    assert r["benefice_fiscal_imposable"] == Decimal("0.00")
    assert r["deficit_fiscal_genere"] == Decimal("90000.00")
    assert r["is_theorique"] == Decimal("0.00")


def test_exercice_futur_utilise_taux_cible_mais_est_marque_provisoire():
    r = service.determiner_taux_is(2027, 5_000_000)
    assert r.taux == Decimal("20.000")
    assert r.provisoire is True


def test_sql_cree_tables_et_contraintes():
    sql = (BACKEND / "021_fiscalite_is.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS fiscal_parametres_exercice" in sql
    assert "CREATE TABLE IF NOT EXISTS fiscal_retraitements" in sql
    assert "deficit_reportable_disponible >= 0" in sql
    assert "avantage_20_transition" in sql
    assert "ck_fiscal_regime_special_justifie" in sql
    assert "type IN ('reintegration','deduction')" in sql
    assert "montant > 0" in sql


def test_router_exclut_brouillons_et_clotures_et_delegue_retraitements():
    src = (BACKEND / "routers" / "fiscalite.py").read_text(encoding="utf-8")
    service_src = (BACKEND / "services" / "fiscalite_retraitements_service.py").read_text(encoding="utf-8")
    assert "if e.est_validee" in src
    assert "journal == \"CL\"" in src
    assert 'ref.startswith("CLOTURE-")' in src
    assert "analyser_retraitements" in src
    assert '"6583"' in service_src
    assert "CGI 2026 art. 11-I" in service_src


def test_frontend_expose_resultat_fiscal_et_is():
    page = (ROOT / "src" / "pages" / "FiscaliteIS.jsx").read_text(encoding="utf-8")
    app = (ROOT / "src" / "App.jsx").read_text(encoding="utf-8")
    sidebar = (ROOT / "src" / "components" / "Sidebar.jsx").read_text(encoding="utf-8")
    assert "Résultat fiscal & IS" in page
    assert "Bénéfice fiscal imposable" in page
    assert 'path="fiscalite-is"' in app
    assert "Résultat fiscal / IS" in sidebar
