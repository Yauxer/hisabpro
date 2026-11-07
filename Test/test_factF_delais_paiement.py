from datetime import date
from pathlib import Path
import sys
import os
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.delais_paiement_service import (
    bornes_trimestre, mois_ou_fraction_retard, amende_indicative,
)


def test_bornes_trimestre():
    assert bornes_trimestre(2026, 1) == (date(2026, 1, 1), date(2026, 3, 31))
    assert bornes_trimestre(2026, 4) == (date(2026, 10, 1), date(2026, 12, 31))


def test_mois_ou_fraction_retard():
    due = date(2026, 1, 15)
    assert mois_ou_fraction_retard(due, date(2026, 1, 15)) == 0
    assert mois_ou_fraction_retard(due, date(2026, 1, 16)) == 1
    assert mois_ou_fraction_retard(due, date(2026, 2, 15)) == 1
    assert mois_ou_fraction_retard(due, date(2026, 2, 16)) == 2


def test_amende_indicative_2026_taux_bam_225():
    sim = amende_indicative(10000, date(2026, 1, 15), date(2026, 2, 15))
    assert sim["mois"] == 1
    assert sim["taux_directeur_pct"] == 2.25
    assert sim["taux_total_pct"] == 2.25
    assert sim["amende"] == 225.0

    sim2 = amende_indicative(10000, date(2026, 1, 15), date(2026, 2, 16))
    assert sim2["mois"] == 2
    assert sim2["taux_total_pct"] == 3.10
    assert sim2["amende"] == 310.0


def test_migration_factf_contient_metadonnees_et_index():
    sql = (BACKEND / "044_factF_delais_paiement.sql").read_text(encoding="utf-8")
    for token in (
        "date_livraison_service", "litige_judiciaire", "reference_litige",
        "delais_paiement_hors_champ", "idx_factures_factf_achats_echeance",
    ):
        assert token in sql


def test_factf_est_branche_dans_api_et_front():
    main = (BACKEND / "main.py").read_text(encoding="utf-8")
    app = (ROOT / "src" / "App.jsx").read_text(encoding="utf-8")
    sidebar = (ROOT / "src" / "components" / "Sidebar.jsx").read_text(encoding="utf-8")
    assert "delais_paiement.router" in main
    assert 'path="delais-paiement"' in app
    assert "/delais-paiement" in sidebar
