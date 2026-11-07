from datetime import date
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


def test_classement_echeances_b6_b7_a_la_date_de_cloture():
    rows = [
        {"date_echeance": date(2026, 12, 31), "reste_du": 100},
        {"date_echeance": date(2027, 6, 30), "reste_du": 200},
        {"date_echeance": date(2028, 1, 1), "reste_du": 300},
        {"date_echeance": date(2027, 1, 15), "reste_du": 0},
    ]
    got = service._classer_echeances_ouvertes(rows, date(2026, 12, 31))
    assert got == {
        "plus_un_an": Decimal("300.00"),
        "moins_un_an": Decimal("200.00"),
        "echues": Decimal("100.00"),
    }


def test_prefill_echeance_n_est_applique_que_si_source_recoupe_solde(monkeypatch):
    monkeypatch.setattr(service, "_ventilation_factures_par_compte", lambda *a, **k: {
        "3421": {
            "plus_un_an": Decimal("100.00"),
            "moins_un_an": Decimal("800.00"),
            "echues": Decimal("100.00"),
            "total_source": Decimal("1000.00"),
        },
        "3427": {
            "plus_un_an": Decimal("0.00"),
            "moins_un_an": Decimal("400.00"),
            "echues": Decimal("0.00"),
            "total_source": Decimal("400.00"),
        },
    })
    lignes = [
        {"compte": "3421", "montant": 1000.00},
        {"compte": "3427", "montant": 500.00},
    ]
    service._ajouter_echeances_auto(object(), 1, 2026, lignes, "vente")
    assert lignes[0]["echeance_auto"] == {"plus_un_an": 100.0, "moins_un_an": 800.0, "echues": 100.0}
    assert "echeance_auto" not in lignes[1]
    assert lignes[1]["echeance_auto_ecart"] == 100.0


def test_validation_et_publication_utilisent_prefill_auto_sans_re_saisie():
    auto = {
        "lignes": [{
            "compte": "3421",
            "intitule": "Clients",
            "montant": 1000.00,
            "echeance_auto": {"plus_un_an": 100.0, "moins_un_an": 800.0, "echues": 100.0},
        }]
    }
    contenu = {"confirme": True, "autres_analyses_neant": True, "ventilations": {}}
    assert service._erreurs_ventilation_b6_b7("B6", auto, contenu) == []
    row = service._ventilation_publiee("B6", auto, contenu)[0]
    assert row["plus_un_an"] == 100.0
    assert row["moins_un_an"] == 800.0
    assert row["echues"] == 100.0


def test_saisie_utilisateur_reste_prioritaire_sur_prefill_auto():
    auto = {
        "lignes": [{
            "compte": "3421",
            "intitule": "Clients",
            "montant": 1000.00,
            "echeance_auto": {"plus_un_an": 100.0, "moins_un_an": 800.0, "echues": 100.0},
        }]
    }
    contenu = {
        "autres_analyses_neant": True,
        "ventilations": {"3421": {"plus_un_an": 0, "moins_un_an": 900, "echues": 100}},
    }
    row = service._ventilation_publiee("B6", auto, contenu)[0]
    assert row["plus_un_an"] == 0.0
    assert row["moins_un_an"] == 900.0


def test_calcul_source_ignore_les_evenements_post_cloture_dans_le_code():
    code = (BACKEND / "services" / "etic_service.py").read_text(encoding="utf-8")
    assert "models.Reglement.date <= fin" in code
    assert "models.ImputationAcompte.date_imputation <= fin" in code
    assert "models.UtilisationAvoir.date_utilisation <= fin" in code
    assert "models.Avoir.date <= fin" in code
    assert "abs(ecart) <= Decimal(\"0.02\")" in code


def test_interface_affiche_les_prefills_de_toutes_les_colonnes_d_echeance():
    page = (ROOT / "src" / "pages" / "Etic.jsx").read_text(encoding="utf-8")
    assert "Les échéances des factures sont préremplies" in page
    assert "if (ligne?.[cle] !== undefined && ligne?.[cle] !== null) return ligne[cle]" in page
