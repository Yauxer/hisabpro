from pathlib import Path
import sys
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "services"))

import services.etic_service as service


class _ImmoQuery:
    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return []


class _FakeDB:
    def query(self, *args, **kwargs):
        return _ImmoQuery()


def test_b2_non_valeur_2117_est_suivie_par_les_mouvements_comptables(monkeypatch):
    monkeypatch.setattr(service, "_bornes", lambda db, sid, ex: (date(2026, 1, 1), date(2026, 12, 31)))
    monkeypatch.setattr(
        service,
        "_mouvements_comptes",
        lambda db, sid, ex, prefixes: {
            "2117": {"OD": [service.money(7000), service.money(0)]}
        },
    )

    lignes = service._section_b2(
        _FakeDB(),
        1,
        2026,
        {"2117": {"debit": 7000.0, "credit": 0.0}},
    )

    assert len(lignes) == 1
    ligne = lignes[0]
    assert ligne["compte"] == "2117"
    assert ligne["debut"] == 0.0
    assert ligne["augmentations"] == 7000.0
    assert ligne["diminutions"] == 0.0
    assert ligne["fin_module"] == 7000.0
    assert ligne["solde_comptable_fin"] == 7000.0
    assert ligne["ecart"] == 0.0


def test_b2_non_valeur_avec_an_et_reduction(monkeypatch):
    monkeypatch.setattr(service, "_bornes", lambda db, sid, ex: (date(2027, 1, 1), date(2027, 12, 31)))
    monkeypatch.setattr(
        service,
        "_mouvements_comptes",
        lambda db, sid, ex, prefixes: {
            "2117": {
                "AN": [service.money(7000), service.money(0)],
                "OD": [service.money(1000), service.money(2500)],
            }
        },
    )

    lignes = service._section_b2(
        _FakeDB(),
        1,
        2027,
        {"2117": {"debit": 8000.0, "credit": 2500.0}},
    )
    ligne = lignes[0]
    assert ligne["debut"] == 7000.0
    assert ligne["augmentations"] == 1000.0
    assert ligne["diminutions"] == 2500.0
    assert ligne["fin_module"] == 5500.0
    assert ligne["solde_comptable_fin"] == 5500.0
    assert ligne["ecart"] == 0.0


def test_b2_libelle_interface_ne_parle_plus_uniquement_de_registre():
    page = (ROOT / "src" / "pages" / "Etic.jsx").read_text(encoding="utf-8")
    assert "fin_module: 'Fin — suivi'" in page
    assert "fin_module: 'Fin — registre'" not in page
