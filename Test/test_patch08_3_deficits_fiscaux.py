from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND / "services"))

import fiscalite_deficits_service as service


def D(id, annee, ordinaire=0, amort=0):
    return {
        "id": id,
        "exercice_origine": annee,
        "montant_ordinaire": Decimal(str(ordinaire)),
        "montant_amortissements": Decimal(str(amort)),
        "source": "manuel",
    }


def I(deficit_id, cible, ordinaire=0, amort=0):
    return {
        "deficit_id": deficit_id,
        "exercice_cible": cible,
        "montant_ordinaire": Decimal(str(ordinaire)),
        "montant_amortissements": Decimal(str(amort)),
    }


def test_deficit_ordinaire_est_eligible_jusqua_quatrieme_exercice_inclus():
    d = [D(1, 2022, ordinaire=1000)]
    r_2026 = service.construire_situation_deficits(deficits=d, imputations=[], exercice_cible=2026, base_avant_deficit=5000)
    r_2027 = service.construire_situation_deficits(deficits=d, imputations=[], exercice_cible=2027, base_avant_deficit=5000)
    assert r_2026["disponible_ordinaire"] == Decimal("1000.00")
    assert r_2026["ordinaire_expire"] == Decimal("0.00")
    assert r_2027["disponible_ordinaire"] == Decimal("0.00")
    assert r_2027["ordinaire_expire"] == Decimal("1000.00")


def test_fraction_amortissements_ne_subit_pas_limite_de_quatre_exercices():
    r = service.construire_situation_deficits(
        deficits=[D(1, 2010, amort=2500)], imputations=[], exercice_cible=2026, base_avant_deficit=1000
    )
    assert r["disponible_amortissements"] == Decimal("2500.00")
    assert r["total_propose"] == Decimal("1000.00")
    assert r["proposition"][0]["nature"] == "amortissements"


def test_un_deficit_nest_pas_imputable_sur_son_exercice_dorigine():
    r = service.construire_situation_deficits(
        deficits=[D(1, 2026, ordinaire=1000, amort=500)], imputations=[], exercice_cible=2026, base_avant_deficit=5000
    )
    assert r["disponible_total"] == Decimal("0.00")
    assert r["total_propose"] == Decimal("0.00")


def test_proposition_priorise_ordinaire_proche_expiration_puis_amortissements():
    r = service.construire_situation_deficits(
        deficits=[
            D(1, 2024, ordinaire=1000, amort=1000),
            D(2, 2022, ordinaire=800, amort=500),
        ],
        imputations=[], exercice_cible=2026, base_avant_deficit=2200,
    )
    assert [(x["deficit_id"], x["nature"], x["montant"]) for x in r["proposition"]] == [
        (2, "ordinaire", Decimal("800.00")),
        (1, "ordinaire", Decimal("1000.00")),
        (2, "amortissements", Decimal("400.00")),
    ]


def test_imputations_anterieures_reduisent_les_soldes_disponibles():
    r = service.construire_situation_deficits(
        deficits=[D(1, 2023, ordinaire=1000, amort=600)],
        imputations=[I(1, 2024, ordinaire=300), I(1, 2025, ordinaire=200, amort=100)],
        exercice_cible=2026,
        base_avant_deficit=5000,
    )
    lot = r["lots"][0]
    assert lot["ordinaire_restant_avant_exercice"] == Decimal("500.00")
    assert lot["amortissements_restants_avant_exercice"] == Decimal("500.00")
    assert r["disponible_total"] == Decimal("1000.00")


def test_confirmation_courante_est_comparee_a_la_proposition_sans_reduire_le_solde_avant_exercice():
    deficits = [D(1, 2024, ordinaire=1000)]
    r = service.construire_situation_deficits(
        deficits=deficits,
        imputations=[I(1, 2026, ordinaire=750)],
        exercice_cible=2026,
        base_avant_deficit=750,
    )
    assert r["disponible_ordinaire"] == Decimal("1000.00")
    assert r["total_confirme"] == Decimal("750.00")
    assert r["confirmation_a_jour"] is True


def test_ventilation_deficit_genere_plafonne_fraction_amortissements_au_deficit():
    r = service.ventiler_deficit_genere(1000, 1500)
    assert r["part_ordinaire"] == Decimal("0.00")
    assert r["part_amortissements"] == Decimal("1000.00")
    r2 = service.ventiler_deficit_genere(2500, 600)
    assert r2["part_ordinaire"] == Decimal("1900.00")
    assert r2["part_amortissements"] == Decimal("600.00")


def test_detection_amortissements_exclut_les_provisions():
    total = service.montant_amortissements_comptabilises({
        "61933": Decimal("1000"),
        "6195": Decimal("9000"),
        "6391": Decimal("200"),
        "65913": Decimal("300"),
    })
    assert total == Decimal("1200.00")


def test_sql_022_cree_millesimes_imputations_trigger_et_permissions():
    sql = (BACKEND / "022_deficits_fiscaux_millesimes.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS fiscal_deficits" in sql
    assert "CREATE TABLE IF NOT EXISTS fiscal_deficit_imputations" in sql
    assert "exercice_cible > v_origine + 4" in sql
    assert "hisabpro_check_fiscal_deficit_imputation" in sql
    assert "ON DELETE RESTRICT" in sql
    assert "v_ordinaire_deja + NEW.montant_ordinaire > v_ordinaire_initial" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_deficits TO hisabpro" in sql
    assert "fiscal_deficit_imputations_id_seq" in sql


def test_router_et_frontend_exposent_le_suivi_par_millesime():
    router = (BACKEND / "routers" / "fiscalite.py").read_text(encoding="utf-8")
    api = (ROOT / "src" / "services" / "api.js").read_text(encoding="utf-8")
    page = (ROOT / "src" / "pages" / "FiscaliteIS.jsx").read_text(encoding="utf-8")
    assert '"deficits": {' in router
    assert "construire_situation_deficits" in router
    assert "confirmer-imputation" in router
    assert "enregistrer-genere" in router
    assert "confirmerImputationDeficits" in api
    assert "Déficits fiscaux reportables" in page
    assert "Report limité à N+4" in page
    assert "Fraction amortissements" in page
