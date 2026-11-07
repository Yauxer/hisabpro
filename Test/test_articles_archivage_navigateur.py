"""Page Articles réelle dans Edge ; réponses synthétiques, aucune API métier."""
from pathlib import Path
import subprocess

import pytest
from browser_support import chromium_executable

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    target = tmp_path_factory.mktemp("articles-react") / "articles.js"
    script = r'''
const esbuild=require('esbuild');
esbuild.build({stdin:{contents:`import React from 'react';import {createRoot} from 'react-dom/client';
import Articles from './src/pages/Articles.jsx';createRoot(document.getElementById('root')).render(<Articles/>);`,
loader:'jsx',resolveDir:process.cwd()},bundle:true,platform:'browser',format:'iife',jsx:'automatic',
define:{'import.meta.env':'{}'},outfile:process.argv[1],plugins:[{name:'isolated-fixtures',setup(b){
b.onLoad({filter:/ExerciceContext\.jsx$/},()=>({contents:'export function useExercice(){return {annee:2025}}',loader:'js'}));
b.onLoad({filter:/\.module\.css$/},()=>({contents:'export default new Proxy({}, {get:(_,key)=>key});',loader:'js'}));
}}]}).then(()=>esbuild.stop()).catch(e=>{process.stderr.write(String(e));process.exitCode=1;esbuild.stop()});
'''
    result = subprocess.run(["node", "-e", script, str(target)], cwd=ROOT, text=True,
                            encoding="utf-8", capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return target.read_text(encoding="utf-8")


@pytest.mark.parametrize("refus", [True, False])
def test_suppression_affiche_refus_ou_retire_ligne_sans_F5(bundle, refus):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Navigateur Chromium local absent")
    css = (ROOT / "src/pages/Articles.module.css").read_text(encoding="utf-8")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page(viewport={"width": 1366, "height": 900})
            page.set_default_timeout(5000)
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.route("http://recette.test/**", lambda route: route.fulfill(
                body='<style>*{box-sizing:border-box}' + css + '</style><div id="root"></div>',
                content_type="text/html"))
            page.goto("http://recette.test/")
            page.evaluate("""refus=>{
                window.calls=[];window.refus=refus;window.confirm=()=>true;
                window.fetch=async(url,opts={})=>{
                    window.calls.push({url,method:opts.method||'GET'});
                    if(opts.method==='DELETE') return window.refus
                        ? new Response(JSON.stringify({detail:'Un article avec du stock ne peut pas être archivé.'}),{status:409})
                        : new Response(null,{status:204});
                    const rows=String(url).endsWith('/api/articles')?[{id:7,code:'A-ARCH',designation:'Article de recette',
                        stock_actuel:window.refus?10:0,is_stockable:true,cmup:100,prix_vente_ht:200,tva:20}]:[];
                    return new Response(JSON.stringify(rows),{status:200});
                };
            }""", refus)
            page.add_script_tag(content=bundle)
            page.locator("tbody tr").wait_for()
            page.locator("tbody tr button").last.click()
            if refus:
                page.get_by_role("alert").wait_for()
                assert "avec du stock" in page.get_by_role("alert").inner_text()
                assert page.locator("tbody tr").count() == 1
            else:
                page.wait_for_function("document.querySelectorAll('tbody tr').length===0")
                assert page.get_by_role("alert").count() == 0
            assert len([c for c in page.evaluate("window.calls") if c["method"] == "DELETE"]) == 1
            assert not errors
        finally:
            browser.close()
