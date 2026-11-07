"""Téléchargement natif du dossier et abandon d'une réponse d'ancien contexte."""
from contextlib import closing
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_dossier689_isole import (
    application,application102,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,application089,
    application087,migration,client,ok,creer,demande,chemin,BASE,donnees_metier,verifier_bundle)
from test_e2e_balance_echeances687_isole import ouvrir
from test_e2e_administration_isole import connexion,observer
from test_logo_societe import image_data
from browser_support import chromium_executable


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_689_dossier_zip_telecharge_et_ouvert_dans_edge(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v1=creer(api);v2=ok(api.post(chemin(v1),json=demande(v1)),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Dossier fictif689','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v2,role=='lecture');avant=donnees_metier(application)
            ecritures=[];page.on('request',lambda r:ecritures.append(r.url) if r.method in ('POST','PATCH','DELETE') else None)
            with page.expect_download() as export:
                panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
            assert export.value.suggested_filename==f'HisabPro_Dossier_Preparation_{v2["exercice"]}_v2.zip'
            dest=tmp_path/'preparation689.zip';export.value.save_as(dest);verifier_bundle(dest.read_bytes(),v2)
            assert donnees_metier(application)==avant and not ecritures
            expect(panel.get_by_text('Dossier interne à compléter',exact=False)).to_be_visible()
            panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).scroll_into_view_if_needed()
            page.screenshot(path=str(tmp_path/f'dossier689-{role}-{largeur}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors and not serveur,(errors,serveur)
        finally:browser.close()


def test_689_zip_reel_retarde_ignore_apres_changement_de_jeton(application):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000},accept_downloads=True);page.set_default_timeout(10000)
            connexion(page,application['web_url'],email,password);panel,_=ouvrir(page,application,v)
            pending=[];downloads=[];page.on('download',lambda d:downloads.append(d))
            path=BASE+f'/{v["id"]}/zip'
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                verifier_bundle(rep.body(),v,False)
                pending.append((route,rep));page.evaluate('window.__dossier689Retenu = true')
            page.route('**'+path,retenir,times=1)
            panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
            page.wait_for_function('window.__dossier689Retenu === true')
            page.evaluate('t => localStorage.setItem("hisabpro_token",t)',autre.headers['Authorization'].split(' ',1)[1])
            route,rep=pending.pop()
            with page.expect_response(lambda r:r.url.endswith(path)):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            assert not downloads
        finally:browser.close()
