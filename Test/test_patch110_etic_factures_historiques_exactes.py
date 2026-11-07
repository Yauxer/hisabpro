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


def test_diagnostic_expose_nombre_factures_historiques_recuperees(monkeypatch):
    monkeypatch.setattr(service, "_ventilation_factures_par_compte", lambda *a, **k: {
        "3421": {
            "plus_un_an": Decimal("0.00"),
            "moins_un_an": Decimal("0.00"),
            "echues": Decimal("900.00"),
            "total_source": Decimal("900.00"),
            "nb_factures": 3,
            "nb_factures_historiques": 2,
        }
    })
    monkeypatch.setattr(service, "_diagnostic_mouvements_compte", lambda *a, **k: {
        "total": 1000.0, "sources": [], "mouvements": []
    })
    lignes = [{"compte": "3421", "montant": 1000.0}]
    service._ajouter_echeances_auto(object(), 1, 2026, lignes, "vente")
    assert lignes[0]["echeance_auto_nb_factures"] == 3
    assert lignes[0]["echeance_auto_nb_factures_historiques"] == 2
    assert lignes[0]["echeance_auto_ecart"] == 100.0


def test_recuperation_historique_reutilise_le_rapprochement_fec_deterministe():
    code = (BACKEND / "services" / "etic_service.py").read_text(encoding="utf-8")
    assert "from services.fec_source_recovery_service import choisir_facture_source" in code
    assert "facture = choisir_facture_source(ecriture, candidates)" in code
    assert "if facture.id not in directes and usages.get(facture.id) == 1" in code


def test_facture_non_marquee_comptabilisee_n_est_pas_pris_sans_ecriture_exacte():
    code = (BACKEND / "services" / "etic_service.py").read_text(encoding="utf-8")
    assert 'bool(getattr(f, "est_validee", False))' in code
    assert 'bool(getattr(f, "est_comptabilisee", False))' in code
    assert "recuperees[facture.id] = facture" in code
    assert "toutes.update(recuperees)" in code
    assert "_choisir_facture_historique_etic(ecriture, candidates, type_facture)" in code


def test_interface_signale_les_factures_historiques_retrouvees():
    page = (ROOT / "src" / "pages" / "Etic.jsx").read_text(encoding="utf-8")
    assert "echeance_auto_nb_factures_historiques" in page
    assert "retrouvée(s) via une écriture historique exacte" in page
