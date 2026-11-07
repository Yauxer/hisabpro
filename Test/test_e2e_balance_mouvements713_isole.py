"""Edge713 : mouvements documentaires, droits, mobile et contrôles conservés."""
from contextlib import closing
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_mouvements713_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,body,url,BASE)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from browser_support import chromium_executable
SUMMARY='Documenter les mouvements d’immobilisations et provisions'
REGION='Déclarations des mouvements de la préparation'
SAVE='Conserver les tableaux ETIC dans une nouvelle version'


def ouvrir_mouvements(page,app,v,lecture=False):
    panel,_=ouvrir(page,app,v,lecture);panel.get_by_text(SUMMARY,exact=True).click()
    detail=panel.get_by_role('region',name=REGION,exact=True)
    expect(detail.get_by_label('Tableau ETIC à documenter',exact=True)).to_be_visible()
    return panel,detail


def saisir(detail,v):
    for table in body(v)['tables']:
        detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option(table['code'])
        detail.get_by_label('Déclaration du tableau',exact=True).select_option(table['statut'])
        detail.get_by_label('Justification du tableau',exact=True).fill(table['justification'])
        aug='Acquisitions et augmentations déclarées' if table['code']=='B2' else 'Dotations déclarées'
        dim={'B2':'Sorties et diminutions déclarées','B2bis':'Amortissements sortis déclarés','B5':'Reprises et utilisations déclarées'}[table['code']]
        labels={'nature':'Nature déclarée','debut':'Ouverture déclarée','augmentations':aug,'diminutions':dim,'fin':'Clôture déclarée','reference_source':'Référence de source'}
        detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
        for k,val in table['lignes'][0].items():detail.get_by_label(labels[k]+' ligne 1',exact=True).fill(val)
    detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option('B2')
    expect(detail.get_by_label('Nature déclarée ligne 1',exact=True)).to_have_value('Matériel de transport fictif')


def sauver(page,panel,detail,v):
    detail.get_by_role('checkbox').check()
    with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
        detail.get_by_role('button',name=SAVE,exact=True).click()
    assert rep.value.status==201,rep.value.text();v=rep.value.json()
    expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible()
    panel.get_by_text(SUMMARY,exact=True).click()
    return v,panel.get_by_role('region',name=REGION,exact=True)


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_713_brouillon_ecart_export_et_droits(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api)
        if role=='lecture':v=ok(api.post(url(v),json=body(v)),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Mouvements fictives713','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_mouvements(page,application,v,role=='lecture')
            if role=='lecture':
                assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
                assert detail.get_by_label('Nature déclarée ligne 1',exact=True).is_disabled()
            else:saisir(detail,v);v,detail=sauver(page,panel,detail,v)
            controle=detail.get_by_role('region',name='Contrôles des mouvements conservés',exact=True)
            expect(controle).to_contain_text('0,00 MAD')
            if role!='lecture':
                detail.get_by_label('Clôture déclarée ligne 1',exact=True).fill('10999,99')
                expect(controle).to_contain_text('0,00 MAD')
                assert '-0,01 MAD' not in controle.inner_text()
                v,detail=sauver(page,panel,detail,v)
                expect(detail.get_by_role('region',name='Contrôles des mouvements conservés',exact=True)).to_contain_text('-0,01 MAD')
            with page.expect_download() as d:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
            dest=tmp_path/'mouvements713.zip';d.value.save_as(dest)
            with ZipFile(dest) as z:
                data=json.loads(z.read('mouvements_documentaires.json'))
                assert data['controle_mouvements']['tableaux']['B2']['totaux']['ecart_fin']==('0.00' if role=='lecture' else '-0.01')
                assert data['tables'][2]['lignes'][0]['fin']=='700.00'
            detail.get_by_label('Nature déclarée ligne 1',exact=True).scroll_into_view_if_needed()
            page.screenshot(path=str(tmp_path/f'mouvements713-{role}-{largeur}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors and not serveur,(errors,serveur)
        finally:browser.close()


def test_713_erreur_preserve_brouillon(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_mouvements(page,application,v);saisir(detail,v)
            detail.get_by_label('Acquisitions et augmentations déclarées ligne 1',exact=True).fill('-1');detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name=SAVE,exact=True).click()
            assert rep.value.status==422;expect(detail.get_by_role('alert')).to_be_visible()
            expect(detail.get_by_label('Acquisitions et augmentations déclarées ligne 1',exact=True)).to_have_value('-1')
            detail.get_by_label('Acquisitions et augmentations déclarées ligne 1',exact=True).fill('2000')
            detail.get_by_label('Clôture déclarée ligne 1',exact=True).fill('10999.99')
            assert not detail.get_by_role('checkbox').is_checked()
            v,detail=sauver(page,panel,detail,v)
            expect(detail.get_by_role('region',name='Contrôles des mouvements conservés',exact=True)).to_contain_text('-0,01 MAD')
        finally:browser.close()


def test_713_post_reel_tardif_ne_selectionne_pas_ancienne_version(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_mouvements(page,application,v);pending=[]
            detail.get_by_label('Justification du tableau',exact=True).fill('Brouillon fictif713 conservé sur la version source')
            detail.get_by_role('checkbox').check()
            def retenir(route):
                if route.request.method!='POST':return route.continue_()
                rep=route.fetch();assert rep.status==201
                pending.append((route,rep));page.evaluate('window.__notes713PostRetenu = true')
            page.route('**'+url(v),retenir,times=1)
            detail.get_by_role('button',name='Conserver les tableaux ETIC dans une nouvelle version',exact=True).click()
            page.wait_for_function('window.__notes713PostRetenu === true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
            assert ok(api.get(url(v2)))['tables'][0]['justification']==body(v2)['tables'][0]['justification']
        finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_713_reponse_tardive_abandonnee(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__notes713Retenues = true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click()
            page.wait_for_function('window.__notes713Retenues === true')
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
