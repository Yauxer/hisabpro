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


def test_mismatch_expose_decomposition_comptable(monkeypatch):
    monkeypatch.setattr(service, "_ventilation_factures_par_compte", lambda *a, **k: {
        "3421": {
            "plus_un_an": Decimal("0.00"),
            "moins_un_an": Decimal("900.00"),
            "echues": Decimal("100.00"),
            "total_source": Decimal("1000.00"),
            "nb_factures": 2,
        }
    })
    diagnostic = {
        "total": 1200.0,
        "sources": [
            {"source": "facture", "montant": 1500.0, "nb_lignes": 2},
            {"source": "reglement", "montant": -300.0, "nb_lignes": 1},
        ],
        "mouvements": [],
    }
    monkeypatch.setattr(service, "_diagnostic_mouvements_compte", lambda *a, **k: diagnostic)

    lignes = [{"compte": "3421", "montant": 1200.0}]
    service._ajouter_echeances_auto(object(), 1, 2026, lignes, "vente")

    assert lignes[0]["echeance_auto_nb_factures"] == 2
    assert lignes[0]["echeance_auto_ecart"] == 200.0
    assert lignes[0]["echeance_auto_compta_diagnostic"] == diagnostic
    assert "echeance_auto" not in lignes[0]


def test_compteur_factures_reste_entier_dans_source():
    code = (BACKEND / "services" / "etic_service.py").read_text(encoding="utf-8")
    assert 'result[compte]["nb_factures"] = int(vals.get("nb_factures") or 0)' in code


def test_interface_affiche_sources_et_mouvements_du_reliquat():
    page = (ROOT / "src" / "pages" / "Etic.jsx").read_text(encoding="utf-8")
    assert "Décomposition comptable du solde" in page
    assert "Voir les mouvements comptables du compte" in page
    assert "echeance_auto_compta_diagnostic.sources" in page
    assert "echeance_auto_compta_diagnostic.mouvements" in page
