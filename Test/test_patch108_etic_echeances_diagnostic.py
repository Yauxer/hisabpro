from decimal import Decimal
from pathlib import Path
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "services"))

import services.etic_service as service


def test_diagnostic_est_expose_quand_factures_et_solde_ne_recoupent_pas(monkeypatch):
    monkeypatch.setattr(service, "_ventilation_factures_par_compte", lambda *a, **k: {
        "3421": {
            "plus_un_an": Decimal("100.00"),
            "moins_un_an": Decimal("800.00"),
            "echues": Decimal("100.00"),
            "total_source": Decimal("1000.00"),
            "nb_factures": 3,
        }
    })
    lignes = [{"compte": "3421", "montant": 1200.00}]
    service._ajouter_echeances_auto(object(), 1, 2026, lignes, "vente")
    ligne = lignes[0]
    assert "echeance_auto" not in ligne
    assert ligne["echeance_auto_total"] == 1000.0
    assert ligne["echeance_auto_ecart"] == 200.0
    assert ligne["echeance_auto_nb_factures"] == 3
    assert ligne["echeance_auto_diagnostic"] == {
        "plus_un_an": 100.0,
        "moins_un_an": 800.0,
        "echues": 100.0,
    }


def test_interface_affiche_ecart_factures_comptabilite_sans_prefill_force():
    page = (ROOT / "src" / "pages" / "Etic.jsx").read_text(encoding="utf-8")
    assert "Préremplissage non appliqué pour" in page
    assert "echeance_auto_nb_factures" in page
    assert "echeance_auto_diagnostic" in page
    assert "contre {afficherValeur('montant', ligne.montant)} MAD en comptabilité" in page
