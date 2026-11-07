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


def _source_partielle():
    return {
        "3421": {
            "plus_un_an": Decimal("0.00"),
            "moins_un_an": Decimal("0.00"),
            "echues": Decimal("92090.80"),
            "total_source": Decimal("92090.80"),
            "nb_factures": 28,
            "nb_factures_historiques": 0,
        }
    }


def test_prefill_partiel_conserve_partie_certaine_et_reliquat(monkeypatch):
    monkeypatch.setattr(service, "_ventilation_factures_par_compte", lambda *a, **k: _source_partielle())
    monkeypatch.setattr(service, "_diagnostic_mouvements_compte", lambda *a, **k: {"total": 161302.80, "sources": [], "mouvements": []})
    lignes = [{"compte": "3421", "intitule": "Clients", "montant": 161302.80}]

    service._ajouter_echeances_auto(object(), 1, 2026, lignes, "vente")
    ligne = lignes[0]

    assert "echeance_auto" not in ligne
    assert ligne["echeance_auto_partiel"] == {
        "plus_un_an": 0.0,
        "moins_un_an": 0.0,
        "echues": 92090.8,
    }
    assert ligne["echeance_auto_reliquat"] == 69212.0


def test_publication_affiche_partie_certaine_mais_validation_exige_total_complet(monkeypatch):
    monkeypatch.setattr(service, "_ventilation_factures_par_compte", lambda *a, **k: _source_partielle())
    monkeypatch.setattr(service, "_diagnostic_mouvements_compte", lambda *a, **k: {"total": 161302.80, "sources": [], "mouvements": []})
    lignes = [{"compte": "3421", "intitule": "Clients", "montant": 161302.80}]
    service._ajouter_echeances_auto(object(), 1, 2026, lignes, "vente")
    auto = {"lignes": lignes}
    contenu = {"confirme": True, "autres_analyses_neant": True, "ventilations": {}}

    row = service._ventilation_publiee("B6", auto, contenu)[0]
    assert row["plus_un_an"] == 0.0
    assert row["moins_un_an"] == 0.0
    assert row["echues"] == 92090.8
    errors = service._erreurs_ventilation_b6_b7("B6", auto, contenu)
    assert errors == ["3421 : la ventilation par échéance doit totaliser 161302.80 MAD."]


def test_utilisateur_complete_uniquement_reliquat_et_validation_passe(monkeypatch):
    monkeypatch.setattr(service, "_ventilation_factures_par_compte", lambda *a, **k: _source_partielle())
    monkeypatch.setattr(service, "_diagnostic_mouvements_compte", lambda *a, **k: {"total": 161302.80, "sources": [], "mouvements": []})
    lignes = [{"compte": "3421", "intitule": "Clients", "montant": 161302.80}]
    service._ajouter_echeances_auto(object(), 1, 2026, lignes, "vente")
    auto = {"lignes": lignes}
    contenu = {
        "confirme": True,
        "autres_analyses_neant": True,
        "ventilations": {"3421": {"plus_un_an": 0, "moins_un_an": 69212.0, "echues": 92090.8}},
    }
    assert service._erreurs_ventilation_b6_b7("B6", auto, contenu) == []


def test_source_superieure_au_solde_n_est_jamais_prefill_partiellement(monkeypatch):
    src = _source_partielle()
    src["3421"]["total_source"] = Decimal("170000.00")
    src["3421"]["echues"] = Decimal("170000.00")
    monkeypatch.setattr(service, "_ventilation_factures_par_compte", lambda *a, **k: src)
    monkeypatch.setattr(service, "_diagnostic_mouvements_compte", lambda *a, **k: {"total": 161302.80, "sources": [], "mouvements": []})
    lignes = [{"compte": "3421", "montant": 161302.80}]
    service._ajouter_echeances_auto(object(), 1, 2026, lignes, "vente")
    assert "echeance_auto_partiel" not in lignes[0]


def test_interface_affiche_reliquat_a_ventiler():
    page = (ROOT / "src" / "pages" / "Etic.jsx").read_text(encoding="utf-8")
    assert "Préremplissage partiel appliqué" in page
    assert "Reste à ventiler" in page
    assert "echeance_auto_reliquat" in page
    assert "Répartition source certaine" in page
