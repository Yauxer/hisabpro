import json
import shutil
import subprocess
from pathlib import Path

import pytest
from jsx_syntax import assert_jsx

ROOT = Path(__file__).resolve().parents[1]


def executer_js(comptes, complet=False, sources=None):
    if not shutil.which("node"):
        pytest.skip("Node.js absent")
    code = """
import {preparerLignesComptage} from './src/utils/inventaireComptage.js';
const [comptes,complet,sources]=JSON.parse(process.argv[1]);
const feuille=[{article_id:1,code:'A1',stock_theorique:10,cmup:20},{article_id:2,code:'A2',stock_theorique:10,cmup:20,...(sources || {})}];
try {console.log(JSON.stringify({lignes:preparerLignesComptage(feuille,comptes,{complet})}));}
catch(e) {console.log(JSON.stringify({erreur:e.message}));}
"""
    result = subprocess.run(["node", "--input-type=module", "-e", code,
                             json.dumps([comptes, complet, sources])], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8", timeout=15)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_zero_compte_explicitement_sans_omission():
    assert executer_js({"1": "0", "2": "9.5"}, True)["lignes"] == [
        {"article_id": 1, "quantite_reelle": 0}, {"article_id": 2, "quantite_reelle": 9.5}]


@pytest.mark.parametrize("valeur", ["", "  ", None])
def test_case_vide_de_cloture_ne_devient_pas_zero(valeur):
    result = executer_js({"1": "10", "2": valeur}, True)
    assert "clôture incomplet" in result["erreur"]
    assert "A2" in result["erreur"]


@pytest.mark.parametrize("valeur", ["12abc", "Infinity", "-1", True])
def test_saisie_invalide_ne_devient_pas_un_zero_comptable(valeur):
    result = executer_js({"1": "10", "2": valeur})
    assert "Quantité invalide" in result["erreur"]


def test_comptage_intermediaire_partiel_autorise():
    assert executer_js({"1": "10", "2": ""})["lignes"] == [
        {"article_id": 1, "quantite_reelle": 10}]


@pytest.mark.parametrize("sources", [
    {"stock_theorique": None}, {"stock_theorique": "Infinity"},
    {"stock_theorique": True}, {"cmup": None}, {"cmup": "NaN"},
    {"cmup": -1}, {"cmup": ""}, {"cmup": 1e308, "stock_theorique": 1e308},
])
def test_sources_inconnues_refusees_meme_comptage_saisi(sources):
    result = executer_js({"1": "10", "2": "8"}, sources=sources)
    assert "À vérifier" in result["erreur"]
    assert "A2" in result["erreur"]


def test_stock_et_cout_zero_connus_ne_sont_pas_inconnus():
    result = executer_js({"1": "10", "2": "0"}, True,
                         {"stock_theorique": 0, "cmup": 0})
    assert result["lignes"][1] == {"article_id": 2, "quantite_reelle": 0}


@pytest.mark.parametrize("valeur", [[], {}, [8]])
def test_objets_non_numeriques_refuses(valeur):
    result = executer_js({"1": "10", "2": valeur})
    assert "Quantité invalide" in result["erreur"]


def test_page_et_utilitaire_compilent():
    assert_jsx(["src/pages/Inventaire.jsx", "src/utils/inventaireComptage.js", "src/pages/Cloture.jsx", "src/pages/LivreInventaire.jsx"])
