from pathlib import Path
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "services"))

import services.etic_service as service


def _auto_b6():
    return {
        "lignes": [
            {"compte": "3421", "intitule": "Clients", "montant": 1000.00},
            {"compte": "3453", "intitule": "Etat - acomptes IS", "montant": 50.00},
        ]
    }


def test_b6_b7_sont_des_ventilations_structurees():
    meta = {x["code"]: x for x in service.CATALOGUE_ETIC}
    assert meta["B6"]["type_saisie"] == "ventilation"
    assert meta["B7"]["type_saisie"] == "ventilation"


def test_b6_validation_accepte_echeances_reconciliees_et_autres_analyses_neant():
    contenu = {
        "confirme": True,
        "autres_analyses_neant": True,
        "ventilations": {
            "3421": {"plus_un_an": 100, "moins_un_an": 800, "echues": 100},
            "3453": {"plus_un_an": 0, "moins_un_an": 50, "echues": 0},
        },
    }
    assert service._erreurs_ventilation_b6_b7("B6", _auto_b6(), contenu) == []


def test_b6_validation_refuse_une_echeance_qui_ne_reconcilie_pas_le_total():
    contenu = {
        "confirme": True,
        "autres_analyses_neant": True,
        "ventilations": {
            "3421": {"plus_un_an": 100, "moins_un_an": 700, "echues": 100},
            "3453": {"plus_un_an": 0, "moins_un_an": 50, "echues": 0},
        },
    }
    errors = service._erreurs_ventilation_b6_b7("B6", _auto_b6(), contenu)
    assert any("3421" in e and "doit totaliser 1000.00 MAD" in e for e in errors)


def test_b6_validation_ne_suppose_pas_les_autres_analyses_a_zero():
    contenu = {
        "confirme": True,
        "ventilations": {
            "3421": {"plus_un_an": 0, "moins_un_an": 1000, "echues": 0},
            "3453": {"plus_un_an": 0, "moins_un_an": 50, "echues": 0},
        },
    }
    errors = service._erreurs_ventilation_b6_b7("B6", _auto_b6(), contenu)
    assert any("3421" in e and "montant en devises" in e for e in errors)
    assert any("3421" in e and "Etat / organismes publics" in e for e in errors)


def test_b6_etat_est_prefrempli_uniquement_quand_le_compte_est_explicitement_etat():
    contenu = {
        "ventilations": {
            "3421": {"plus_un_an": 0, "moins_un_an": 1000, "echues": 0},
            "3453": {"plus_un_an": 0, "moins_un_an": 50, "echues": 0},
        },
    }
    rows = {x["compte"]: x for x in service._ventilation_publiee("B6", _auto_b6(), contenu)}
    assert rows["3453"]["etat_organismes_publics"] == 50.0
    # Le compte client 3421 pourrait concerner une entité publique : sans confirmation, le moteur ne l'invente pas.
    assert rows["3421"]["etat_organismes_publics"] is None
    assert rows["3421"]["devises"] is None

    contenu["autres_analyses_neant"] = True
    rows = {x["compte"]: x for x in service._ventilation_publiee("B6", _auto_b6(), contenu)}
    # Le zéro n'apparaît qu'après confirmation explicite de l'utilisateur.
    assert rows["3421"]["etat_organismes_publics"] == 0.0
    assert rows["3421"]["devises"] == 0.0


def test_interface_b6_b7_affiche_les_colonnes_officielles_et_un_neant_explicite():
    page = (ROOT / "src" / "pages" / "Etic.jsx").read_text(encoding="utf-8")
    assert "Analyse par échéance" in page
    assert "Échues et non recouvrées" in page
    assert "Échues et non payées" in page
    assert "État / organismes publics" in page
    assert "Autres analyses : je confirme" in page


def test_route_refuse_confirmation_b6_b7_incomplete():
    router = (BACKEND / "routers" / "etats.py").read_text(encoding="utf-8")
    assert "valider_contenu_etic" in router
    assert "Section {code} incomplète" in router


def test_pdf_liasse_integre_la_ventilation_b6_b7():
    pdf = (BACKEND / "services" / "liasse_pdf.py").read_text(encoding="utf-8")
    assert 'sec.get("code") in ("B6", "B7")' in pdf
    assert "État / org. publics" in pdf
    assert "Entreprises liées" in pdf
