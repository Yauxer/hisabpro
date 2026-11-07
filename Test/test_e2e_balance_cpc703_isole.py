"""Edge B11 : trois rôles, mobile et réponses API réelles retardées."""
from contextlib import closing
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_cpc703_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,body,url,BASE)
from test_e2e_balance_echeances687_isole import ouvrir
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable

SUMMARY='Détailler le CPC depuis les balances conservées'
REGION='Détail CPC de la préparation'
SAVE='Conserver le détail CPC dans une nouvelle version'


def ouvrir_cpc(page,app,v,lecture=False):
    panel,_=ouvrir(page,app,v,lecture)
    panel.get_by_text(SUMMARY,exact=True).click()
    detail=panel.get_by_role('region',name=REGION,exact=True)
    expect(detail.get_by_role('button',name='Relire le détail CPC conservé',exact=True)).to_be_visible()
    return panel,detail


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_703_conservation_cpc_export_reel_et_mobile(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api,comparatif=False)
        if role=='lecture':v=ok(api.post(url(v),json=body(v)),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'CPC fictif703','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_cpc(page,application,v,role=='lecture')
            if role=='lecture':assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
            else:
                expect(detail).to_contain_text('Aucun détail CPC conservé')
                assert detail.get_by_role('button',name=SAVE,exact=True).is_disabled()
                detail.get_by_role('checkbox').check()
                with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                    detail.get_by_role('button',name=SAVE,exact=True).click()
                assert rep.value.status==201;v=rep.value.json()
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
                panel.get_by_text(SUMMARY,exact=True).click()
                detail=panel.get_by_role('region',name=REGION,exact=True)
            expect(detail).to_contain_text('2.000,00 MAD')
            expect(detail.get_by_role('cell',name='Produit',exact=True)).to_be_visible()
            expect(detail.get_by_role('rowheader').filter(has_text='7111')).to_contain_text('Libellé non conservé')
            detail.get_by_label('Période du détail CPC',exact=True).select_option('n1')
            expect(detail.get_by_role('note')).to_contain_text('absente')
            detail.get_by_label('Période du détail CPC',exact=True).select_option('n')
            with page.expect_download() as d:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
            dest=tmp_path/'cpc703.zip';d.value.save_as(dest)
            with ZipFile(dest) as z:
                vzip=json.loads(z.read('detail_cpc_documentaire.json'))
                assert vzip['vue']['periodes']['n']['resultat']=='2000.00'
                assert vzip['vue']['periodes']['n1']['resultat'] is None
            detail.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'cpc703-{role}-{largeur}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors and not serveur,(errors,serveur)
        finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_703_reponse_get_tardive_abandonnee(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__cpc703Retenu=true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click()
            page.wait_for_function('window.__cpc703Retenu===true')
            if action=='version':
                panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            elif action=='fermeture':panel.get_by_role('button',name='Masquer',exact=True).click()
            else:page.evaluate('t=>localStorage.setItem("hisabpro_token",t)',autre.headers['Authorization'].split(' ',1)[1])
            route,rep=pending.pop()
            with page.expect_response(lambda r:r.url.endswith(url(v))):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            assert panel.get_by_role('checkbox',name='Je confirme la conservation du détail depuis les seules balances de cette version.',exact=True).count()==0
        finally:browser.close()


def test_703_post_reel_tardif_ne_remplace_pas_selection(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_cpc(page,application,v);pending=[]
            detail.get_by_role('checkbox').check()
            def retenir(route):
                if route.request.method!='POST':return route.continue_()
                rep=route.fetch();assert rep.status==201
                pending.append((route,rep));page.evaluate('window.__cpc703PostRetenu=true')
            page.route('**'+url(v),retenir,times=1)
            detail.get_by_role('button',name=SAVE,exact=True).click()
            page.wait_for_function('window.__cpc703PostRetenu===true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()
