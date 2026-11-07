"""B14 : Edge réel, trois rôles, mobile, brouillon et réponses retardées."""
from contextlib import closing
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_tva727_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,body,url,BASE)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from browser_support import chromium_executable

SUMMARY='Documenter les flux TVA B14 depuis les balances'
REGION='TVA documentaire de la préparation'
SAVE='Conserver les tableaux ETIC dans une nouvelle version'


def ouvrir_courant(page,app,v,lecture=False):
    panel,_=ouvrir(page,app,v,lecture)
    panel.get_by_text(SUMMARY,exact=True).click()
    detail=panel.get_by_role('region',name=REGION,exact=True)
    expect(detail.get_by_label('Tableau ETIC à documenter',exact=True)).to_be_visible()
    return panel,detail


def saisir(detail,table):
    detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option(table['code'])
    detail.get_by_label('Déclaration du tableau',exact=True).select_option(table['statut'])
    detail.get_by_label('Justification du tableau',exact=True).fill(table['justification'])
    labels={'nature':'Famille TVA (4455/34552/34551)','solde_debut':'Solde de début déclaré',
        'operations':'Opérations déclarées','declarations':'Déclarations justifiées',
        'references_declarations':'Références des déclarations ou du néant justifié','reference_source':'Référence de source'}
    for i,row in enumerate(table['lignes'],1):
        detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
        for k,v in row.items():
            if v is not None:
                champ=detail.get_by_label(f'{labels[k]} ligne {i}',exact=True)
                if k=='nature':champ.select_option(str(v))
                else:champ.fill(str(v))


def sauver(page,panel,detail,v):
    detail.get_by_role('checkbox').check()
    with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
        detail.get_by_role('button',name=SAVE,exact=True).click()
    assert rep.value.status==201,rep.value.text()
    result=rep.value.json()
    expect(panel.get_by_text(f'Version {result["version"]} conservée',exact=False)).to_be_visible()
    panel.get_by_text(SUMMARY,exact=True).click()
    return result,panel.get_by_role('region',name=REGION,exact=True)


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_727_brouillon_courant_impot_separe_exports_et_mobile(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api)
        if role=='lecture':v=ok(api.post(url(v),json=body(v)),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'TVA fictive727','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_courant(page,application,v,role=='lecture')
            if role=='lecture':
                assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
                assert detail.get_by_label('Opérations déclarées ligne 1',exact=True).is_disabled()
            else:
                for table in body(v)['tables']:saisir(detail,table)
                expect(detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True)).to_be_disabled()
                detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option('B14-N')
                # Longue référence continue : aucune largeur supplémentaire sur390px.
                detail.get_by_label('Référence de source ligne 1',exact=True).fill('JUSTIFICATIF727'+'X'*300)
                v,detail=sauver(page,panel,detail,v)
            controle=detail.get_by_role('region',name='Contrôles TVA conservés',exact=True)
            collecte=controle.get_by_role('region',name='TVA facturée / collectée',exact=True)
            expect(collecte).to_contain_text('Solde de fin reconstitué : 1.000,00 MAD')
            expect(collecte).to_contain_text('Écart fin reconstituée moins balance N : 0,00 MAD')
            expect(controle.get_by_role('region',name='Net TVA documentaire',exact=True)).to_contain_text('Solde de fin reconstitué : 300,00 MAD')
            if role!='lecture':
                detail.get_by_label('Opérations déclarées ligne 1',exact=True).fill('1999,99')
                expect(collecte).to_contain_text('Solde de fin reconstitué : 1.000,00 MAD')
                v,detail=sauver(page,panel,detail,v)
                expect(detail.get_by_role('region',name='TVA facturée / collectée',exact=True)).to_contain_text('Écart fin reconstituée moins balance N : -0,01 MAD')
            with page.expect_download() as d:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
            dest=tmp_path/'tva727.zip';d.value.save_as(dest)
            with ZipFile(dest) as z:
                data=json.loads(z.read('tva_documentaire.json'))
                n=data['controle_tva']['lignes'][0]['montants']
                assert n['solde_fin_reconstitue']==('1000.00' if role=='lecture' else '999.99')
                assert n['solde_fin_balance_n']=='1000.00'
            controle=detail.get_by_role('region',name='Contrôles TVA conservés',exact=True)
            controle.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'tva727-{role}-{largeur}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors and not serveur,(errors,serveur)
        finally:browser.close()


def test_727_periode_absente_et_rejet_conservent_brouillon(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api,False);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_courant(page,application,v)
            saisir(detail,body(v)['tables'][0])
            detail.get_by_label('Opérations déclarées ligne 1',exact=True).fill('NaN')
            detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name=SAVE,exact=True).click()
            assert rep.value.status==422
            expect(detail.get_by_role('alert')).to_be_visible()
            expect(detail.get_by_label('Opérations déclarées ligne 1',exact=True)).to_have_value('NaN')
            detail.get_by_label('Opérations déclarées ligne 1',exact=True).fill('')
            v,detail=sauver(page,panel,detail,v)
            expect(detail.get_by_role('region',name='Contrôles TVA conservés',exact=True)).to_contain_text('Solde de fin reconstitué : Indisponible')
        finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_727_get_reel_tardif_ignore(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__tva727Retenu=true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click();page.wait_for_function('window.__tva727Retenu===true')
            if action=='version':
                panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            elif action=='fermeture':panel.get_by_role('button',name='Masquer',exact=True).click()
            else:page.evaluate('t=>localStorage.setItem("hisabpro_token",t)',autre.headers['Authorization'].split(' ',1)[1])
            route,rep=pending.pop()
            with page.expect_response(lambda r:r.url.endswith(url(v))):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            assert panel.get_by_role('region',name=REGION,exact=True).get_by_role('checkbox').count()==0
        finally:browser.close()


def test_727_post_reel_tardif_ne_remplace_pas_selection(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_courant(page,application,v);pending=[]
            saisir(detail,body(v)['tables'][0]);detail.get_by_role('checkbox').check()
            def retenir(route):
                if route.request.method!='POST':return route.continue_()
                rep=route.fetch();assert rep.status==201
                pending.append((route,rep));page.evaluate('window.__tva727PostRetenu=true')
            page.route('**'+url(v),retenir,times=1);detail.get_by_role('button',name=SAVE,exact=True).click()
            page.wait_for_function('window.__tva727PostRetenu===true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()
