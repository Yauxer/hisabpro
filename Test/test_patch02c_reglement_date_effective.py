from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "hisabpro-backend"


def test_transition_enregistre_date_effective():
    src = (ROOT / "routers" / "commercial.py").read_text(encoding="utf-8")
    assert "r.date_encaissement = date_effective" in src
    assert "r.statut = \"encaisse\"" in src
    assert "r.statut = \"paye\"" in src


def test_modele_interdit_statut_final_sans_date():
    src = (ROOT / "models.py").read_text(encoding="utf-8")
    assert "ck_reglements_statut_date_effective" in src
    assert "date_encaissement IS NOT NULL" in src
