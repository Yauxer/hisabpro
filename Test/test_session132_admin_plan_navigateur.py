"""Layout React réel : plan absent, préparation explicite admin, aucun GET mutant."""
from pathlib import Path
import json
import subprocess
import pytest
from browser_support import chromium_executable

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    target = tmp_path_factory.mktemp("plan-react") / "plan.js"
    script = r'''
const fs=require('node:fs'),esbuild=require('esbuild');
const source=fs.readFileSync('src/components/Layout.jsx','utf8');
const component=source.slice(source.indexOf('const LABEL_STATUT')).replace('export default function Layout','function Layout');
const prefix=`import React,{useEffect,useState,useRef,useCallback} from 'react';import{createRoot}from'react-dom/client';
import{useLocation,MemoryRouter}from'react-router-dom';
import{API_BASE,getToken,planComptableAPI,estAdmin,formatErreurAPI}from'./src/services/api.js';
import{cleCachePlan,restaurerPlanSociete,enregistrerPlanSociete,EVENEMENT_PLAN_MODIFIE}from'./src/data/planComptableCache.js';
const styles=new Proxy({}, {get:(_,key)=>key});
const Sidebar=()=>null,SelecteurSociete=()=>null,Outlet=()=><div>Page société chargée</div>;
const useModules=()=>({societe:{id:1},chargement:false});
const useExercice=()=>({annee:2026,setAnnee:()=>{},exercice:null,exercices:[],chargementExercices:false});`;
esbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById('root')).render(<MemoryRouter><Layout/></MemoryRouter>);`,
loader:'jsx',resolveDir:process.cwd()},bundle:true,format:'iife',platform:'browser',outfile:process.argv[1],
define:{'import.meta.env.VITE_API_URL':'"http://recette.test"','import.meta.env.VITE_APP_VERSION':'"recette"'}});
'''
    result = subprocess.run(["node", "-e", script, str(target)], cwd=ROOT, text=True, encoding="utf-8", capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return target.read_text(encoding="utf-8")


@pytest.mark.parametrize("role", ["admin", "lecture"])
def test_plan_absent_ne_se_prepare_pas_sans_action_admin(bundle, role):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Navigateur Chromium absent")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            appels = []
            rows = []

            def repondre(route):
                req = route.request
                appels.append((req.method, req.url))
                if req.method == "POST":
                    rows.append({"compte": "1111", "libelle": "Capital social", "classe": 1, "type": "SP", "actif": True})
                    route.fulfill(json={"nb_comptes": 1})
                else:
                    route.fulfill(json=rows)

            page.route("**/api/plan-comptable**", repondre)
            page.route("http://recette.test/", lambda route: route.fulfill(body='<div id="root"></div>', content_type="text/html"))
            page.goto("http://recette.test/")
            page.evaluate("role=>{localStorage.setItem('hisabpro_role',role);localStorage.setItem('hisabpro_token','entete.'+btoa(JSON.stringify({sub:'1',societe_id:1}))+'.signature')}", role)
            page.add_script_tag(content=bundle)
            page.get_by_role("alert").filter(has_text="aucun compte").wait_for()
            assert all(method == "GET" for method, _ in appels)
            bouton = page.get_by_role("button", name="Initialiser le plan de cette société", exact=True)
            assert bouton.count() == int(role == "admin")
            if role == "admin":
                bouton.click()
                page.get_by_text("Page société chargée", exact=True).wait_for()
                assert sum(method == "POST" for method, _ in appels) == 1
                assert page.evaluate("sessionStorage.getItem('hisabpro_plan_societe_v1:1:1')") is not None
            else:
                assert page.get_by_text("Page société chargée", exact=True).count() == 0
            assert not errors
        finally:
            browser.close()
