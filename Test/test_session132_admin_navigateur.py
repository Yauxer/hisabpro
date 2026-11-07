"""Composant React Utilisateurs réel, API synthétique sans base ni serveur."""
from pathlib import Path
import subprocess
from urllib.parse import parse_qs, urlparse
import pytest
from browser_support import chromium_executable

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    target = tmp_path_factory.mktemp("admin-react") / "admin.js"
    script = r'''
const fs=require('node:fs'), esbuild=require('esbuild');
const source=fs.readFileSync('src/pages/Parametres.jsx','utf8');
const component=source.slice(source.indexOf('function OngletUtilisateurs()'),source.indexOf('function OngletBanques()'));
if(!component.includes('async function supprimer')) throw new Error('Composant utilisateurs introuvable');
const prefix=`import React,{useState,useEffect} from 'react';
import {createRoot} from 'react-dom/client';
const styles=new Proxy({}, {get:(_,key)=>key});
const LIBELLE_ROLE={admin:'Administrateur',lecture:'Consultation seule',comptable:'Comptable'};
const setRole=()=>{};
const authAPI={me:async()=>({role:'admin',societe_id:1})};
const API_BASE='http://recette.test';
const formatErreurAPI=detail=>typeof detail==='string'?detail:'Erreur serveur';
const utilisateursAPI={
 lister:async()=>window.testUsers.map(u=>({...u})),
 roles:async()=>[{code:'admin',libelle:'Administrateur'},{code:'comptable',libelle:'Comptable'},{code:'lecture',libelle:'Consultation seule'}],
 supprimer:async id=>{window.lastDeleted=id;window.testUsers=window.testUsers.filter(u=>u.id!==id)},
 modifier:async(id,body)=>{window.lastModified={id,body};window.testUsers=window.testUsers.map(u=>u.id!==id?u:
  u.acces_invite&&body.actif!==undefined?{...u,actif_acces:body.actif,actif:u.actif_compte!==false&&body.actif}:{...u,...body})},
};`;
esbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById('root')).render(<OngletUtilisateurs/>);`,
loader:'jsx',resolveDir:process.cwd()},bundle:true,format:'iife',platform:'browser',outfile:process.argv[1]});
'''
    result = subprocess.run(["node", "-e", script, str(target)], cwd=ROOT, text=True,
                            encoding="utf-8", capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return target.read_text(encoding="utf-8")


@pytest.mark.parametrize("invite", [False, True])
def test_confirmation_et_actualisation_retrait_acces(bundle, invite):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Navigateur Chromium absent")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.set_content('<div id="root"></div>')
            page.evaluate("invite=>{window.testUsers=[{id:3,nom:'Utilisateur recette',email:'recette@example.test',role:'lecture',actif:true,acces_invite:invite}]}", invite)
            page.add_script_tag(content=bundle)
            page.locator("tbody tr").filter(has_text="Utilisateur recette").wait_for()
            assert page.get_by_text("Accès invité", exact=True).count() == int(invite)
            page.get_by_role("button", name="Ajouter un utilisateur").click()
            assert page.locator('input[autocomplete="new-password"]').get_attribute("type") == "password"
            page.get_by_role("button", name="Annuler", exact=True).click()
            confirmations = []

            def confirmer(dialog):
                confirmations.append(dialog.message)
                dialog.accept()

            page.on("dialog", confirmer)
            page.get_by_title("Retirer l'accès" if invite else "Supprimer", exact=True).click()
            page.wait_for_function("window.lastDeleted===3 && document.querySelectorAll('tbody tr').length===0")
            assert len(confirmations) == 1
            if invite:
                assert "Retirer l'accès" in confirmations[0]
                assert "Son compte restera disponible" in confirmations[0]
            else:
                assert "Supprimer définitivement le compte" in confirmations[0]
            assert not errors
        finally:
            browser.close()


@pytest.mark.parametrize("statut", [200, 404, 409])
def test_invitation_et_erreurs_sans_rechargement(bundle, statut):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Navigateur Chromium absent")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page()
            errors, demandes = [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("http://recette.test/", lambda route: route.fulfill(
                content_type="text/html", body='<div id="root"></div>'))
            page.goto("http://recette.test/")
            page.evaluate("window.testUsers=[];localStorage.setItem('hisabpro_token','recette-fictive')")

            def repondre(route):
                import json
                demandes.append(route.request.url)
                assert route.request.method == "POST"
                assert route.request.headers.get("authorization") == "Bearer recette-fictive"
                if statut == 200:
                    page.evaluate("window.testUsers.push({id:8,nom:'Invité ajouté',email:'invite@recette.test',role:'lecture',actif:true,acces_invite:true})")
                    body = {"message": "Accès accordé"}
                else:
                    body = {"detail": "Utilisateur introuvable" if statut == 404 else "Ce compte est désactivé"}
                route.fulfill(status=statut, content_type="application/json", body=json.dumps(body))

            page.route("**/api/societes/1/inviter?**", repondre)
            page.add_script_tag(content=bundle)
            page.get_by_role("button", name="Donner accès à un utilisateur existant").click()
            page.get_by_label("E-mail du compte existant").fill("invite@recette.test")
            page.get_by_label("Rôle dans cette société").select_option("lecture")
            page.get_by_role("button", name="Accorder cet accès").click()
            if statut == 200:
                page.locator("tbody tr").filter(has_text="Invité ajouté").wait_for()
                assert page.get_by_text("Accès invité", exact=True).count() == 1
                assert page.get_by_label("E-mail du compte existant").count() == 0
            else:
                attendu = "Utilisateur introuvable" if statut == 404 else "Ce compte est désactivé"
                page.get_by_role("alert").filter(has_text=attendu).wait_for()
                assert page.get_by_label("E-mail du compte existant").input_value() == "invite@recette.test"
            assert len(demandes) == 1
            parsed = urlparse(demandes[0])
            assert parsed.path == "/api/societes/1/inviter"
            assert parse_qs(parsed.query) == {"email": ["invite@recette.test"], "role": ["lecture"]}
            assert not errors
        finally:
            browser.close()
