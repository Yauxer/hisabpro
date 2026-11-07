from pathlib import Path
import sys
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "services"))

from services.etic_service import _calcul_c3_depuis_soldes


def test_c3_situation_nette_integre_resultat_courant_non_cloture_technique():
    # Cas réel de recette 2026 après Patch 101 : la source des états exclut les
    # écritures CL, donc 1191 n'embarque pas le résultat courant dans les soldes.
    soldes = {
        "116": {"debit": 0.0, "credit": 6861.11},
        "2117": {"debit": 7000.0, "credit": 0.0},
        "7111": {"debit": 0.0, "credit": 15500.0},
        "7124": {"debit": 0.0, "credit": 128440.0},
        "6111": {"debit": 34100.0, "credit": 0.0},
        "6114": {"debit": 0.0, "credit": 44626.0},
        "6125": {"debit": 7500.0, "credit": 0.0},
        "6134": {"debit": 0.0, "credit": 1200.0},
        "61934": {"debit": 10866.67, "credit": 0.0},
        "61935": {"debit": 9134.45, "credit": 0.0},
        "6195": {"debit": 1500.0, "credit": 0.0},
        "61961": {"debit": 800.0, "credit": 0.0},
        "61964": {"debit": 1000.0, "credit": 0.0},
        "6701": {"debit": 24972.98, "credit": 0.0},
    }
    ligne = _calcul_c3_depuis_soldes(soldes)
    assert Decimal(str(ligne["resultat_avant_impots"])) == Decimal("124864.88")
    assert Decimal(str(ligne["impots_resultats"])) == Decimal("24972.98")
    assert Decimal(str(ligne["resultat_net"])) == Decimal("99891.90")
    assert Decimal(str(ligne["situation_nette"])) == Decimal("99753.01")


def test_c3_code_ne_transforme_pas_comparatif_indisponible_en_zero():
    service = (BACKEND / "services" / "etic_service.py").read_text(encoding="utf-8")
    assert 'if y != exercice and not src.get("disponible")' in service
    assert '"situation_nette": None' in service
    assert '"resultat_net": None' in service
    assert "comparatif disponible" in service
