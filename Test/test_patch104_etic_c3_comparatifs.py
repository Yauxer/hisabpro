from pathlib import Path
import sys
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "services"))

import services.etic_service as service


class _CountQuery:
    def filter(self, *args, **kwargs):
        return self

    def count(self):
        return 0


class _FakeDB:
    def query(self, *args, **kwargs):
        return _CountQuery()


def test_c3_comparatifs_sans_source_sont_absents(monkeypatch):
    sources = {
        2024: {"disponible": False, "soldes": {}},
        2025: {"disponible": False, "soldes": {}},
        2026: {
            "disponible": True,
            "soldes": {
                "7111": {"debit": 0.0, "credit": 100.0},
                "6111": {"debit": 20.0, "credit": 0.0},
                "6701": {"debit": 10.0, "credit": 0.0},
            },
        },
    }
    monkeypatch.setattr(service, "source_etats_synthese", lambda db, sid, y: sources[y])
    monkeypatch.setattr(service, "_bornes", lambda db, sid, y: (date(y, 1, 1), date(y, 12, 31)))

    rows = service._section_c3(_FakeDB(), 1, 2026)

    assert rows[0]["exercice"] == 2024
    assert rows[0]["resultat_net"] is None
    assert rows[1]["exercice"] == 2025
    assert rows[1]["resultat_net"] is None
    assert rows[2]["exercice"] == 2026
    assert rows[2]["resultat_avant_impots"] == 80.0
    assert rows[2]["impots_resultats"] == 10.0
    assert rows[2]["resultat_net"] == 70.0


def test_c3_n_utilise_plus_presence_technique_exercice_comme_comparatif():
    code = (BACKEND / "services" / "etic_service.py").read_text(encoding="utf-8")
    section = code.split("def _section_c3", 1)[1].split("def _automatiques", 1)[0]
    assert 'if y != exercice and not src.get("disponible")' in section
    assert "ExerciceComptable.id" not in section
