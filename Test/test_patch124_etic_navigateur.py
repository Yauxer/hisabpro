"""Recette du composant React réel B6/B7 avec des données synthétiques.

Aucun serveur backend ni requête vers PostgreSQL : bundle React local, CSS réel.
"""
from pathlib import Path
import json
import subprocess
import pytest
from browser_support import chromium_executable

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    folder = tmp_path_factory.mktemp("etic-react")
    target = folder / "etic.js"
    script = r'''
const fs=require('node:fs');
const esbuild=require('esbuild');
const source=fs.readFileSync('src/pages/Etic.jsx','utf8');
const end=source.indexOf('function SectionETIC');
if(end<0) throw new Error('Limite du composant introuvable');
const components=source.slice(source.indexOf('const GROUPES'),end);
if(!components.includes('function TableauVentilation')) throw new Error('Composant introuvable');
const prefix=`import React,{Fragment,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {formatMAD} from './src/data/donnees.js';
const styles=new Proxy({}, {get:(_,key)=>key});`;
const harness=`function Harness(){
 const [contenu,setContenu]=useState(window.testSection.contenu);
 window.contenuTest=contenu;
 return <TableauVentilation section={window.testSection} contenu={contenu} setContenu={setContenu} ecriture={window.testEcriture}/>;
}
createRoot(document.getElementById('root')).render(<Harness/>);`;
esbuild.buildSync({stdin:{contents:prefix+components+harness,loader:'jsx',resolveDir:process.cwd()},
 bundle:true,platform:'browser',format:'iife',outfile:process.argv[1]});
'''
    result = subprocess.run(["node", "-e", script, str(target)], cwd=ROOT,
                            text=True, encoding="utf-8", capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return target.read_text(encoding="utf-8")


@pytest.mark.parametrize("code", ["B6", "B7"])
@pytest.mark.parametrize("width", [1366, 390])
@pytest.mark.parametrize("ecriture", [True, False])
def test_ventilation_saisies_diagnostics_et_scroll_local(bundle, code, width, ecriture):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Navigateur Chromium local absent")
    compte = "3421" if code == "B6" else "4411"
    section = {"code": code, "contenu": {"ventilations": {compte: {"moins_un_an": "17"}}},
        "automatique": {"lignes": [{"compte": compte, "intitule": "Tiers", "montant": 120,
            "echeance_auto_total": 120, "echeance_auto_ecart": 0, "echeance_auto_non_qualifie": 40,
            "echeance_auto_partiel": {"echues": 80}, "echeance_auto_reliquat": 40,
            "echeance_auto_anomalies_sources": [{"facture_id": 1, "numero": "02", "reste_du": 40, "motifs": ["Écriture absente"]}],
            "echeance_auto_sources_hors_solde": [{"compte": "44110001", "total_source": 960, "anomalies_sources": []}]}]},
        "ventilation": [{"compte": compte, "plus_un_an": 0, "moins_un_an": 0, "echues": 80}]}
    css = (ROOT / "src/pages/Etic.module.css").read_text(encoding="utf-8")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page(viewport={"width": width, "height": 900})
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.set_content('<style>*{box-sizing:border-box}body{margin:0;padding:12px}' + css + '</style><div id="root"></div>')
            page.evaluate("s=>{window.testSection=s.section;window.testEcriture=s.ecriture}", {"section": section, "ecriture": ecriture})
            page.add_script_tag(content=bundle)
            fields = page.locator(".ventilationTable input")
            fields.first.wait_for()
            assert fields.count() == 7
            assert fields.nth(0).input_value() == "0"
            assert fields.nth(1).input_value() == "17"  # La saisie gagne sur la publication.
            assert fields.nth(2).input_value() == "80"
            if ecriture:
                fields.nth(2).fill("90")
                assert page.evaluate("window.contenuTest.ventilations[window.testSection.ventilation[0].compte].echues") == "90"
                page.locator(".confirmCheck input").check()
                assert fields.nth(3).input_value() == "0"
            else:
                assert all(field.is_disabled() for field in fields.all())
                assert page.locator(".confirmCheck input").is_disabled()
            assert fields.nth(1).input_value() == "17"
            for summary in page.locator("summary").all():
                summary.click()
            assert "Écriture absente" in page.inner_text("body")
            assert "44110001" in page.inner_text("body")
            assert page.evaluate("document.documentElement.scrollWidth") <= width + 1
            scroll_necessaire = page.locator(".ventilationWrap").evaluate("e=>e.scrollWidth>e.clientWidth")
            assert scroll_necessaire is (width < 1280)
            page.locator(".ventilationWrap").evaluate("e=>e.scrollLeft=e.scrollWidth")
            assert fields.last.is_visible()
            assert not errors
        finally:
            browser.close()
