"""Modales React réelles des effets ; API simulée, aucun accès au PostgreSQL réel."""
from pathlib import Path
import subprocess

import pytest
from browser_support import chromium_executable

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    target = tmp_path_factory.mktemp("effets-react") / "effets.js"
    script = r'''
const fs=require('node:fs');
const esbuild=require('esbuild');
const source=fs.readFileSync('src/pages/Effets.jsx','utf8');
const start=source.indexOf('function ModalTransition(');
const end=source.indexOf('// ── Page principale',start);
if(start<0||end<0) throw new Error('Limites ModalTransition introuvables');
const prefix=`import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import Modal from './src/components/Modal.jsx';
import {formatMAD} from './src/data/donnees.js';
import {dateLocaleISO} from './src/utils/formUtils.js';
async function apiFetch(url,opts){window.transitionCalls.push({url,data:JSON.parse(opts.body)});return {};}`;
const harness=`window.transitionCalls=[];window.successCount=0;
createRoot(document.getElementById('root')).render(<ModalTransition
reglement={window.testReglement} action={window.testAction}
onFermer={()=>{window.modalClosed=true}} onSuccess={()=>{window.successCount++}}/>);`;
esbuild.build({stdin:{contents:prefix+source.slice(start,end)+harness,loader:'jsx',resolveDir:process.cwd()},
 bundle:true,platform:'browser',format:'iife',jsx:'automatic',outfile:process.argv[1],
 plugins:[{name:'css-tests',setup(build){build.onLoad({filter:/\.module\.css$/},()=>({contents:'export default new Proxy({}, {get:(_,key)=>key});',loader:'js'}));}}]})
 .then(()=>esbuild.stop()).catch(e=>{process.stderr.write(String(e));process.exitCode=1;esbuild.stop();});
'''
    result = subprocess.run(["node", "-e", script, str(target)], cwd=ROOT,
                            text=True, encoding="utf-8", capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return target.read_text(encoding="utf-8")


@pytest.mark.parametrize("action", ["remettre", "rejeter", "encaisser", "payer"])
@pytest.mark.parametrize("width", [1366, 390])
def test_toutes_operations_transmettent_date_choisie_et_rafraichissent(bundle, action, width):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Navigateur Chromium local absent")
    css = (ROOT / "src/components/Modal.module.css").read_text(encoding="utf-8")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.set_default_timeout(5000)
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.set_content('<style>*{box-sizing:border-box}body{margin:0}' + css + '</style><div id="root"></div>')
            page.evaluate("action=>{window.testAction=action;window.testReglement={id:7,mode:'effet',date:'2025-01-02',montant:120}}", action)
            page.add_script_tag(content=bundle)
            field = page.locator('input[type="date"]')
            field.wait_for()
            field.fill("2025-02-05")
            page.locator('button').last.click()
            page.wait_for_function("window.successCount===1 && window.modalClosed===true")
            calls = page.evaluate("window.transitionCalls")
            assert calls == [{"url": "/api/reglements/7/transition",
                             "data": {"action": action, "frais": 0, "date_effective": "2025-02-05"}}]
            assert page.evaluate("document.documentElement.scrollWidth") <= width + 1
            assert not errors
        finally:
            browser.close()


@pytest.mark.parametrize('zone,heure', [('Europe/Paris', 0), ('America/New_York', 23)])
@pytest.mark.parametrize('action', ['remettre', 'rejeter', 'encaisser', 'payer'])
def test_date_par_defaut_et_maximum_restent_locales(bundle, zone, heure, action):
    from datetime import date
    jour = date.today()
    pw = pytest.importorskip('playwright.sync_api')
    with pw.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(timezone_id=zone)
            page.set_content('<div id="root"></div>')
            page.evaluate('''({year,month,day,hour}) => {
                const NativeDate = Date;
                const now = new NativeDate(year,month-1,day,hour,30).getTime();
                window.Date = class extends NativeDate {
                    constructor(...args) { super(...(args.length ? args : [now])); }
                    static now() { return now; }
                };
            }''', {'year':jour.year, 'month':jour.month, 'day':jour.day, 'hour':heure})
            # Les deux côtés de minuit : UTC la veille ou le lendemain.
            assert page.evaluate('new Date().toISOString().slice(0,10)') != jour.isoformat()
            page.evaluate('action=>{window.testAction=action;window.testReglement={id:7,mode:"effet",date:"2025-01-02",montant:120}}', action)
            page.add_script_tag(content=bundle)
            field = page.locator('input[type="date"]')
            pw.expect(field).to_have_value(jour.isoformat())
            pw.expect(field).to_have_attribute('max', jour.isoformat())
            page.locator('button').last.click()
            page.wait_for_function('window.successCount===1 && window.modalClosed===true')
            assert page.evaluate('window.transitionCalls')[0]['data']['date_effective'] == jour.isoformat()
        finally:
            browser.close()
