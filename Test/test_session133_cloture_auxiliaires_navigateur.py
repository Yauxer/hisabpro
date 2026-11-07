"""Aperçu réel des AN : auxiliaires lisibles, même sur mobile."""
from pathlib import Path
import subprocess

import pytest
from browser_support import chromium_executable

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    target = tmp_path_factory.mktemp("cloture-aux-react") / "cloture.js"
    script = r'''
const fs=require('node:fs'), esbuild=require('esbuild');
const source=fs.readFileSync('src/pages/Cloture.jsx','utf8');
const marker=source.indexOf('Aperçu des à-nouveaux sur {annee + 1}');
const begin=source.lastIndexOf('<details',marker),end=source.indexOf('</details>',marker)+10;
if(begin<0||end<10) throw new Error('Apercu AN introuvable');
const body=`import React from 'react';import {createRoot} from 'react-dom/client';
import {formatMAD} from './src/data/donnees.js';import {trouverCompte} from './src/data/planComptes.js';
const etat=window.etatTest,annee=2025,styles=new Proxy({}, {get:(_,k)=>k});
createRoot(document.getElementById('root')).render(${source.slice(begin,end)});`;
esbuild.buildSync({stdin:{contents:body,loader:'jsx',resolveDir:process.cwd()},bundle:true,
platform:'browser',format:'iife',jsx:'automatic',outfile:process.argv[1]});esbuild.stop();
'''
    result = subprocess.run(["node", "-e", script, str(target)], cwd=ROOT, text=True,
                            encoding="utf-8", capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return target.read_text(encoding="utf-8")


@pytest.mark.parametrize("width", [1366, 390])
def test_auxiliaires_et_soldes_opposes_restent_visibles(bundle, width):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Navigateur Chromium local absent")
    css = (ROOT / "src/pages/GrandLivre.module.css").read_text(encoding="utf-8")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.set_default_timeout(5000)
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.set_content('<style>*{box-sizing:border-box}body{margin:0}' + css + '</style><div id="root"></div>')
            page.evaluate("""()=>{window.etatTest={total_an_debit:500,total_an_credit:500,apercu_a_nouveaux:[
                {compte:'3421',debit:500,credit:0,compte_auxiliaire_snapshot:'C00000001',libelle_auxiliaire_snapshot:'Client A <SARL> & historique'},
                {compte:'3421',debit:0,credit:500,compte_auxiliaire_snapshot:'C00000002',libelle_auxiliaire_snapshot:'Client B historique'}]}}""")
            page.add_script_tag(content=bundle)
            page.locator("summary").click()
            assert "2 lignes" in page.locator("summary").inner_text()
            table = page.get_by_role("table")
            assert "Client A <SARL> & historique" in table.inner_text()
            assert "C00000002 · Client B historique" in table.inner_text()
            assert table.get_by_role("row", include_hidden=True).count() == 4
            assert page.evaluate("document.documentElement.scrollWidth") <= width + 1
            assert not errors
        finally:
            browser.close()
