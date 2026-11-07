# -*- coding: utf-8 -*-
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

sys.modules.setdefault("models", types.SimpleNamespace())
from services.liasse_service import calculer_cpc, calculer_tableau_financement, _merge_lignes_n_n1


def _soldes_n():
    return {
        "1111": {"debit": 0, "credit": 100000},
        "2310": {"debit": 50000, "credit": 0},
        "3421": {"debit": 30000, "credit": 0},
        "4411": {"debit": 0, "credit": 10000},
        "5141": {"debit": 30000, "credit": 0},
        "7111": {"debit": 0, "credit": 20000},
        "6111": {"debit": 10000, "credit": 0},
    }


def test_tableau_financement_sans_n1_ne_fabrique_pas_de_variations_depuis_zero():
    soldes = _soldes_n()
    cpc = calculer_cpc(soldes)
    tf = calculer_tableau_financement(
        soldes, {}, cpc, calculer_cpc({}),
        flux_financement={"acquisitions_immobilisations_corporelles": 50000},
        flux_financement_n1={},
        n1_disponible=False,
    )
    assert tf["applicable"] is False
    assert "Aucune donnée N-1" in tf["motif_non_applicable"]
    assert tf["variation_fonds_roulement"] is None
    assert tf["variation_bfg"] is None
    assert tf["variation_tresorerie"] is None
    assert tf["controle"] is None
    assert tf["masses_n1"] is None
    assert all(r["n1"] is None and r["emploi"] is None and r["ressource"] is None for r in tf["synthese"])
    assert all(r["n1"] is None for r in tf["ressources"] + tf["emplois"])
    # Les flux N restent disponibles en interne, sans les présenter comme une variation N/N-1.
    assert tf["emplois"][0]["montant"] == 50000.0


def test_tableau_financement_avec_n1_conserve_le_calcul_comparatif():
    soldes = _soldes_n()
    soldes_n1 = {"1111": {"debit": 0, "credit": 80000}, "2310": {"debit": 40000, "credit": 0}}
    tf = calculer_tableau_financement(
        soldes, soldes_n1, calculer_cpc(soldes), calculer_cpc(soldes_n1),
        n1_disponible=True,
    )
    assert tf["applicable"] is True
    assert tf["variation_fonds_roulement"] is not None
    assert tf["synthese"][0]["n1"] is not None
    assert tf["synthese"][0]["emploi"] is not None
    assert tf["synthese"][0]["ressource"] is not None


def test_lignes_n1_absentes_sont_nulles_et_non_zero_artificiel():
    rows = [{"libelle": "Clients", "net": 1200.0}, {"libelle": "Banque", "net": 0.0}]
    out = _merge_lignes_n_n1(rows, [], n1_disponible=False)
    assert [r["net_n1"] for r in out] == [None, None]


def test_frontend_liasse_affiche_non_applicable_et_tirets_pour_n1_absent():
    page = (ROOT / "src" / "pages" / "LiasseFiscale.jsx").read_text(encoding="utf-8")
    assert "if (v === null || v === undefined || v === '') return '—'" in page
    assert "tf.applicable === false" in page
    assert "motif_non_applicable" in page
    assert "Comparatif N-1 indisponible" in page


def test_exports_liasse_ne_presentent_pas_un_faux_tableau_comparatif_sans_n1():
    page = (ROOT / "src" / "pages" / "LiasseFiscale.jsx").read_text(encoding="utf-8")
    pdf = (BACK / "services" / "liasse_pdf.py").read_text(encoding="utf-8")
    assert "if (tf.applicable === false)" in page
    assert "['Non applicable', tf.motif_non_applicable" in page
    assert 'if tf.get("applicable", True) is False:' in pdf
    assert 'tf.get("motif_non_applicable")' in pdf
