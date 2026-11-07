"""Edge réel697 : tableaux B8/B9, mobile, droits, reprises et contextes tardifs."""
from contextlib import closing
from io import BytesIO
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_etic_tables697_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,tables,url,BASE)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_echeances687_isole import ouvrir
from browser_support import chromium_executable


def ouvrir_tables(page,app,v,lecture=False):
    panel,_=ouvrir(page,app,v,lecture)
    panel.get_by_text('Documenter les tableaux ETIC B8 et B9',exact=True).click()
    detail=panel.get_by_role('region',name='Tableaux documentaires ETIC de la préparation',exact=True)
    expect(detail.get_by_label('Tableau ETIC à documenter',exact=True)).to_be_visible()
    return panel,detail


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_697_tableaux_sources_export_et_droits(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api)
        if role=='lecture':v=ok(api.post(url(v),json=tables(v)),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Tableaux fictifs697','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_tables(page,application,v,role=='lecture')
            if role=='lecture':
                expect(detail.get_by_label('Montant couvert ligne 1',exact=True)).to_have_value('12345.67')
                assert detail.get_by_label('Montant couvert ligne 1',exact=True).is_disabled()
                assert detail.get_by_role('button',name='Conserver les tableaux ETIC dans une nouvelle version',exact=True).count()==0
            else:
                detail.get_by_label('Déclaration du tableau',exact=True).select_option('documente')
                detail.get_by_label('Justification du tableau',exact=True).fill('Source fictive697 sûreté')
                detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
                detail.get_by_label('Nature ligne 1',exact=True).fill('Hypothèque fictive697')
                detail.get_by_label('Montant couvert ligne 1',exact=True).fill('12345,67')
                detail.get_by_label('Référence de source ligne 1',exact=True).fill('Annexe A fictive697')
                detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option('B9')
                detail.get_by_label('Déclaration du tableau',exact=True).select_option('neant_declare')
                detail.get_by_label('Justification du tableau',exact=True).fill('Revue fictive697, aucun engagement')
                detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option('B8')
                expect(detail.get_by_label('Montant couvert ligne 1',exact=True)).to_have_value('12345,67')
                detail.get_by_role('checkbox').check()
                with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                    detail.get_by_role('button',name='Conserver les tableaux ETIC dans une nouvelle version',exact=True).click()
                assert rep.value.status==201,rep.value.text();v=rep.value.json()
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
                panel.get_by_text('Documenter les tableaux ETIC B8 et B9',exact=True).click()
                detail=panel.get_by_role('region',name='Tableaux documentaires ETIC de la préparation',exact=True)
                expect(detail.get_by_label('Montant couvert ligne 1',exact=True)).to_have_value('12345.67')
                expect(detail.get_by_label('Valeur nette comptable ligne 1',exact=True)).to_have_value('')
            with page.expect_download() as download:
                panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
            dest=tmp_path/'tables697.zip';download.value.save_as(dest)
            with ZipFile(dest) as zip:
                vue=json.loads(zip.read('tables_etic_documentaires.json'))
                assert not vue['pret_a_deposer'] and vue['tables'][0]['lignes'][0]['montant_couvert']=='12345.67'
            detail.get_by_label('Montant couvert ligne 1',exact=True).scroll_into_view_if_needed()
            page.screenshot(path=str(tmp_path/f'tables697-{role}-{largeur}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors and not serveur,(errors,serveur)
        finally:browser.close()


def test_697_refus_preserve_brouillon_et_retrait_explicite(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_tables(page,application,v)
            detail.get_by_label('Déclaration du tableau',exact=True).select_option('documente')
            detail.get_by_label('Justification du tableau',exact=True).fill('Source fictive697')
            detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
            detail.get_by_label('Nature ligne 1',exact=True).fill('Caution fictive697')
            detail.get_by_label('Montant couvert ligne 1',exact=True).fill('NaN')
            detail.get_by_label('Référence de source ligne 1',exact=True).fill('Annexe fictive697')
            detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name='Conserver les tableaux ETIC dans une nouvelle version',exact=True).click()
            assert rep.value.status==422;expect(detail.get_by_role('alert')).to_contain_text('fini')
            expect(detail.get_by_label('Montant couvert ligne 1',exact=True)).to_have_value('NaN')
            detail.get_by_label('Montant couvert ligne 1',exact=True).fill('0')
            assert not detail.get_by_role('checkbox').is_checked()
            detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
            detail.get_by_role('button',name='Retirer la ligne 2 du brouillon',exact=True).click()
            detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name='Conserver les tableaux ETIC dans une nouvelle version',exact=True).click()
            assert rep.value.status==201
            assert rep.value.json()['contenu']['tables_etic_documentaires']['tables'][0]['lignes'][0]['montant_couvert']=='0.00'
        finally:browser.close()


def test_697_post_reel_tardif_ne_selectionne_pas_ancienne_version(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=tables(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_tables(page,application,v);pending=[]
            detail.get_by_label('Justification du tableau',exact=True).fill('Brouillon fictif697 conservé sur la version source')
            detail.get_by_role('checkbox').check()
            def retenir(route):
                if route.request.method!='POST':return route.continue_()
                rep=route.fetch();assert rep.status==201
                pending.append((route,rep));page.evaluate('window.__notes697PostRetenu = true')
            page.route('**'+url(v),retenir,times=1)
            detail.get_by_role('button',name='Conserver les tableaux ETIC dans une nouvelle version',exact=True).click()
            page.wait_for_function('window.__notes697PostRetenu === true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
            assert ok(api.get(url(v2)))['tables'][0]['justification']==tables(v2)['tables'][0]['justification']
        finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_697_reponse_tardive_abandonnee(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=tables(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__notes697Retenues = true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text('Documenter les tableaux ETIC B8 et B9',exact=True).click()
            page.wait_for_function('window.__notes697Retenues === true')
            if action=='version':
                panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            elif action=='fermeture':panel.get_by_role('button',name='Masquer',exact=True).click()
            else:page.evaluate('t => localStorage.setItem("hisabpro_token",t)',autre.headers['Authorization'].split(' ',1)[1])
            route,rep=pending.pop()
            with page.expect_response(lambda r:r.url.endswith(url(v))):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            assert panel.get_by_label('Justification du tableau',exact=True).count()==0
        finally:browser.close()
