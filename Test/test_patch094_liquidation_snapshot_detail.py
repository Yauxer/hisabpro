from datetime import date
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
SERVICE = BACKEND / "services" / "fiscalite_acomptes_service.py"
ROUTER = BACKEND / "routers" / "fiscalite.py"
MODELS = BACKEND / "models.py"
SQL = BACKEND / "066_liquidation_is_snapshot_detail.sql"
PAGE = ROOT / "src" / "pages" / "FiscaliteIS.jsx"

def _load_service():
    spec = spec_from_file_location("fiscalite_acomptes_service_patch094", SERVICE)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_snapshot_fige_les_quatre_echeances_references_credits_et_solde():
    mod = _load_service()
    situation = {
        "exercice": 2026,
        "parametres": {"categorie_is": "droit_commun", "taux_is_force": None, "acomptes_reference_forcee": Decimal("20000.00"), "acomptes_justification_reference_forcee": "Reprise dossier test"},
        "calcul": {"benefice_fiscal_imposable": Decimal("124864.88")},
        "acomptes": {
            "reference": {"disponible": True, "source": "manuel", "montant_annuel": Decimal("20000.00")},
            "acomptes": [
                {"numero": 1, "date_echeance": date(2026, 3, 31), "montant_du": Decimal("5000.00"), "montant_verse": Decimal("5000.00"), "reference_paiement": "TEST-ACP-2026-01", "statut": "solde", "reste_a_couvrir": Decimal("0.00")},
                {"numero": 2, "date_echeance": date(2026, 6, 30), "montant_du": Decimal("5000.00"), "montant_verse": Decimal("2000.00"), "reference_paiement": "TEST-ACP-2026-02", "statut": "partiel_en_retard", "reste_a_couvrir": Decimal("3000.00")},
                {"numero": 3, "date_echeance": date(2026, 9, 30), "montant_du": Decimal("5000.00"), "montant_verse": Decimal("0.00"), "reference_paiement": None, "statut": "a_venir", "reste_a_couvrir": Decimal("5000.00")},
                {"numero": 4, "date_echeance": date(2026, 12, 31), "montant_du": Decimal("5000.00"), "montant_verse": Decimal("0.00"), "reference_paiement": None, "statut": "a_venir", "reste_a_couvrir": Decimal("5000.00")},
            ],
            "total_du": Decimal("20000.00"), "total_verse": Decimal("7000.00"), "credit_n_1_initial": Decimal("0.00"), "credit_n_1_impute": Decimal("0.00"), "credit_ras_initial": Decimal("0.00"), "credit_ras_impute": Decimal("0.00"), "total_imputable": Decimal("7000.00"),
        },
        "credits_is": {"lignes": [], "par_type": {"pprf": Decimal("0.00"), "retenue_tiers": Decimal("0.00"), "autre": Decimal("0.00")}, "total_montant": Decimal("0.00"), "total_deja_impute_acomptes": Decimal("0.00"), "total_disponible_liquidation": Decimal("0.00")},
        "liquidation": {"is_theorique": Decimal("24972.98"), "cm_exigible": Decimal("0.00"), "impot_du_avant_acomptes": Decimal("24972.98"), "nature_impot_du": "IS", "credits_is_disponibles_liquidation": Decimal("0.00"), "credits_is_appliques": Decimal("0.00"), "credits_is_appliques_detail": {}, "acomptes_verses": Decimal("7000.00"), "credit_n_1_impute_sur_acomptes": Decimal("0.00"), "credits_ras_deja_imputes_sur_acomptes": Decimal("0.00"), "acomptes_et_credit_imputables": Decimal("7000.00"), "solde_a_payer": Decimal("17972.98"), "excedent_acomptes": Decimal("0.00"), "excedent_credits_is": Decimal("0.00"), "excedent_total": Decimal("0.00"), "nature_solde": "a_payer"},
    }
    snap = mod.construire_snapshot_liquidation(situation)
    assert snap["version"] == 1
    assert len(snap["acomptes"]) == 4
    assert snap["acomptes"][0]["reference_paiement"] == "TEST-ACP-2026-01"
    assert snap["acomptes"][1]["reference_paiement"] == "TEST-ACP-2026-02"
    assert snap["acomptes"][1]["statut"] == "partiel_en_retard"
    assert snap["acomptes"][1]["reste_a_couvrir"] == "3000.00"
    assert snap["totaux_acomptes"]["total_verse"] == "7000.00"
    assert snap["calcul"]["is_theorique"] == "24972.98"
    assert snap["liquidation"]["solde_a_payer"] == "17972.98"
    assert snap["parametres_fiscaux"]["acomptes_reference_forcee"] == "20000.00"
    assert snap["parametres_fiscaux"]["acomptes_justification_reference_forcee"] == "Reprise dossier test"

def test_modele_migration_et_routeur_persistent_le_snapshot_detaille():
    models = MODELS.read_text(encoding="utf-8")
    sql = SQL.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    assert "snapshot_detail           = Column(JSON, nullable=True)" in models
    assert "ADD COLUMN IF NOT EXISTS snapshot_detail JSONB" in sql
    assert "trg_hisabpro_fiscal_liquidation_immutable" in sql
    assert '"detail": getattr(l, "snapshot_detail", None)' in router
    assert "snapshot_detail = construire_snapshot_liquidation(situation)" in router
    assert "snapshot_detail=snapshot_detail" in router

def test_frontend_lit_les_acomptes_et_credits_du_snapshot_apres_confirmation():
    page = PAGE.read_text(encoding="utf-8")
    assert "const snapshotDetail = liquidationLive.snapshot?.detail || {}" in page
    assert "Array.isArray(snapshotDetail.acomptes)" in page
    assert "reference: snapshotDetail.reference_acomptes" in page
    assert "snapshotDetail.credits_is" in page
    assert "leurs références de paiement" in page
