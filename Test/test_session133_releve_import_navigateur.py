"""Fichier CSV déposé dans la vraie page bancaire React ; API synthétique."""
from pathlib import Path
import subprocess

import pytest
from browser_support import chromium_executable

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    target = tmp_path_factory.mktemp("releve-import-react") / "releve.js"
    script = r'''
const esbuild=require('esbuild');
esbuild.build({stdin:{contents:`import React from 'react';import {createRoot} from 'react-dom/client';
import Banque from './src/pages/RapprochementBancaire.jsx';createRoot(document.getElementById('root')).render(<Banque/>);`,
loader:'jsx',resolveDir:process.cwd()},bundle:true,platform:'browser',format:'iife',jsx:'automatic',
define:{'import.meta.env':'{}'},outfile:process.argv[1],plugins:[{name:'isolated-fixtures',setup(b){
b.onLoad({filter:/ExerciceContext\.jsx$/},()=>({contents:`export function useExercice(){return {annee:2025,exercice:{date_debut:'2025-01-01',date_fin:'2025-12-31',statut:'ouvert'}}}`,loader:'js'}));
b.onLoad({filter:/ModulesContext\.jsx$/},()=>({contents:'export function useModules(){return {societe:{id:1}}}',loader:'js'}));
b.onLoad({filter:/\.module\.css$/},()=>({contents:'export default new Proxy({}, {get:(_,key)=>key});',loader:'js'}));
}}]}).then(()=>esbuild.stop()).catch(e=>{process.stderr.write(String(e));process.exitCode=1;esbuild.stop()});
'''
    result = subprocess.run(["node", "-e", script, str(target)], cwd=ROOT, text=True,
                            encoding="utf-8", capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return target.read_text(encoding="utf-8")


@pytest.mark.parametrize("width", [1366, 390])
@pytest.mark.parametrize("encodage", ["utf-8-sig", "cp1252"])
def test_import_csv_fr_transmet_dates_et_montants_exacts_et_rafraichit(bundle, width, encodage):
    executer(bundle, width, encodage, erreur=False)


def test_csv_invalide_affiche_ligne_fautive_et_ne_poste_rien(bundle):
    executer(bundle, 1366, "utf-8", erreur=True)


def executer(bundle, width, encodage, *, erreur):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Navigateur Chromium local absent")
    css = (ROOT / "src/pages/RapprochementBancaire.module.css").read_text(encoding="utf-8")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.set_default_timeout(6000)
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.route("http://recette.test/**", lambda route: route.fulfill(
                body='<style>*{box-sizing:border-box}body{margin:0}' + css + '</style><div id="root"></div>', content_type="text/html"))
            page.goto("http://recette.test/")
            page.evaluate("""()=>{
                localStorage.setItem('hisabpro_token','recette-fictive');localStorage.setItem('hisabpro_role','admin');
                window.calls=[];window.rows=[];
                window.fetch=async(url,opts={})=>{
                    const path=new URL(url).pathname,method=opts.method||'GET';window.calls.push({path,method,body:opts.body?JSON.parse(opts.body):null});
                    if(path.endsWith('/import')){window.rows=JSON.parse(opts.body).lignes.map((l,i)=>({...l,id:i+1,rapprochee:false}));
                        return new Response(JSON.stringify({nb_creees:window.rows.length,nb_ignorees:0}),{status:201});}
                    if(path.includes('/situation'))return new Response(JSON.stringify({lignes_releve:window.rows,ecritures:[],solde_initial:10000,
                        solde_final:null,solde_comptable_final:11200,lecture_seule:false}),{status:200});
                    return new Response(JSON.stringify([]),{status:200});
                };
            }""")
            page.add_script_tag(content=bundle)
            page.get_by_role("button", name="Import Excel / CSV", exact=True).click()
            csv = "Date;Libellé;Débit;Crédit\r\n03/04/2025;002;;1 234,56\r\n04/04/2025;Frais réglés;34,56;"
            if erreur:
                csv += "\r\n31/02/2025;Date impossible;10;"
            page.locator('input[type="file"]').set_input_files({"name": "releve-fictif.csv", "mimeType": "text/csv", "buffer": csv.encode(encodage)})
            if erreur:
                page.get_by_text("Ligne 4 : Date inexistante.", exact=True).wait_for()
                assert page.get_by_role("button", name="Enregistrer le relevé", exact=True).count() == 0
                assert not [c for c in page.evaluate("window.calls") if c["path"].endswith("/import")]
            else:
                enregistrer = page.get_by_role("button", name="Enregistrer le relevé", exact=True)
                enregistrer.wait_for()
                assert "2025-04-03" in page.locator(".tableImport").inner_text()
                assert "002" in page.locator(".tableImport").inner_text()
                enregistrer.click()
                page.get_by_text("Import enregistré : 2 ligne(s), 0 doublon(s) ignoré(s).", exact=True).wait_for()
                posts = [c for c in page.evaluate("window.calls") if c["path"].endswith("/import")]
                assert posts == [{"path": "/api/rapprochement/import", "method": "POST", "body": {"compte": "5141", "lignes": [
                    {"date": "2025-04-03", "libelle": "002", "montant": 1234.56, "sens": "credit"},
                    {"date": "2025-04-04", "libelle": "Frais réglés", "montant": 34.56, "sens": "debit"}]}}]
                assert page.get_by_text("002", exact=True).count() > 0
            assert page.evaluate("document.documentElement.scrollWidth") <= width + 1
            assert not errors
        finally:
            browser.close()
