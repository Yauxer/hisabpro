from datetime import date
from pathlib import Path

from services.echeancier_service import normaliser_echeances, repartition_fifo

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_echeancier_30_40_30_est_valide():
    rows = normaliser_echeances([
        {"date_echeance": "2026-09-11", "montant": 300},
        {"date_echeance": "2026-10-11", "montant": 400},
        {"date_echeance": "2026-11-11", "montant": 300},
    ], 1000, date(2026, 9, 1))
    assert [x["montant"] for x in rows] == [300, 400, 300]
    assert sum(x["montant"] for x in rows) == 1000


def test_echeancier_refuse_total_different_du_ttc():
    try:
        normaliser_echeances([
            {"date_echeance": "2026-09-11", "montant": 300},
            {"date_echeance": "2026-10-11", "montant": 600},
        ], 1000, date(2026, 9, 1))
    except ValueError as exc:
        assert "doit être égal au TTC" in str(exc)
    else:
        raise AssertionError("Un échéancier à 900 MAD ne doit pas valider une facture à 1000 MAD")


def test_affectation_fifo_regle_les_echeances_les_plus_anciennes():
    calc = repartition_fifo([
        {"id": 1, "ordre": 1, "date_echeance": date(2026, 7, 1), "montant": 300, "libelle": None},
        {"id": 2, "ordre": 2, "date_echeance": date(2026, 8, 1), "montant": 400, "libelle": None},
        {"id": 3, "ordre": 3, "date_echeance": date(2026, 10, 1), "montant": 300, "libelle": None},
    ], 500, date_reference=date(2026, 9, 11))
    e1, e2, e3 = calc["echeances"]
    assert e1["reste_du"] == 0
    assert e2["impute"] == 200
    assert e2["reste_du"] == 200
    assert e2["jours_retard"] == 41
    assert e2["tranche_age"] == "31_60"
    assert e3["reste_du"] == 300
    assert calc["reste_du"] == 500
    assert calc["montant_en_retard"] == 200


def test_migration_fact8_cree_echeances_imputations_backfill_et_permissions():
    sql = read("hisabpro-backend/035_echeanciers_acomptes.sql")
    assert "CREATE TABLE IF NOT EXISTS echeances_facture" in sql
    assert "CREATE TABLE IF NOT EXISTS imputations_acomptes" in sql
    assert "Backfill" in sql
    assert "a.statut = 'impute'" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE echeances_facture TO hisabpro" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE imputations_acomptes TO hisabpro" in sql
    assert "COMMIT;" in sql


def test_api_echeancier_expose_lecture_et_modification_securisee():
    src = read("hisabpro-backend/routers/echeanciers.py")
    assert '@router.get("/{facture_id}/echeancier")' in src
    assert '@router.put("/{facture_id}/echeancier")' in src
    assert "total_effectif" in src
    assert "déjà reçu un règlement" in src
    assert "exercice_est_clos" in src


def test_acomptes_supportent_imputation_partielle_et_multi_factures():
    src = read("hisabpro-backend/acomptes.py")
    assert "montant_disponible" in src
    assert "partiellement_impute" in src
    assert "models.ImputationAcompte" in src
    assert "montant: Optional[float]" in src
    assert "Un acompte peut" not in src  # le métier reste backend, pas de message UI ici


def test_recouvrement_fact8_utilise_echeances_et_imputations_reelles():
    src = read("hisabpro-backend/services/recouvrement_service.py")
    assert "models.ImputationAcompte" in src
    assert "echeances_persistantes_ou_defaut" in src
    assert "repartition_fifo" in src
    assert 'bloc["tranches"][ech["tranche_age"]]' in src


def test_frontend_facture_propose_presets_et_affiche_echeancier():
    src = read("src/pages/Factures.jsx")
    assert "Échéancier" in src
    assert "30 / 40 / 30" in src
    assert "4 × 25 %" in src
    assert "echeancesCalculees" in src
    assert "/echeancier" in src
    assert "Échéancier de paiement" in src


def test_frontend_acompte_permet_imputation_partielle():
    src = read("src/pages/Acomptes.jsx")
    assert "montantImputation" in src
    assert "montant_disponible" in src
    assert "partiellement_impute" in src
    assert "plusieurs factures" in src


def test_main_enregistre_router_echeanciers():
    src = read("hisabpro-backend/main.py")
    assert "echeanciers" in src
    assert "app.include_router(echeanciers.router)" in src
