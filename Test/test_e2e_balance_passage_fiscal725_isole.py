"""B12 : Edge réel, trois rôles, mobile, brouillon et réponses retardées."""
from contextlib import closing
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_passage_fiscal725_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,body,url,BASE)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from browser_support import chromium_executable

SUMMARY='Préparer le passage fiscal B12 depuis la balance'
REGION='Passage fiscal de la préparation'
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
    labels={'nature':'Désignation de la synthèse fiscale','reintegrations':'Autres réintégrations hors67',
        'deductions':'Déductions fiscales déclarées','deficit_disponible':'Déficit disponible déclaré et justifié',
        'taux_is':'Taux IS déclaré','regime_avantages':'Régime et avantages à justifier','reference_source':'Référence de source'}
    for i,row in enumerate(table['lignes'],1):
        detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
        for k,v in row.items():
            if v is not None:detail.get_by_label(f'{labels[k]} ligne {i}',exact=True).fill(str(v))


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
def test_725_brouillon_courant_impot_separe_exports_et_mobile(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api)
        if role=='lecture':v=ok(api.post(url(v),json=body(v)),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Passage fictif725','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_courant(page,application,v,role=='lecture')
            if role=='lecture':
                assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
                assert detail.get_by_label('Taux IS déclaré ligne 1',exact=True).is_disabled()
            else:
                for table in body(v)['tables']:saisir(detail,table)
                expect(detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True)).to_be_disabled()
                detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option('B12-N')
                # Longue référence continue : aucune largeur supplémentaire sur390px.
                detail.get_by_label('Référence de source ligne 1',exact=True).fill('JUSTIFICATIF725'+'X'*300)
                v,detail=sauver(page,panel,detail,v)
            controle=detail.get_by_role('region',name='Contrôles du passage fiscal conservés',exact=True)
            expect(controle).to_contain_text('8.000,00 MAD')
            expect(controle).to_contain_text('7.300,00 MAD')
            expect(controle).to_contain_text('1.600,00 MAD')
            expect(controle).to_contain_text('1.460,00 MAD')
            if role!='lecture':
                detail.get_by_label('Taux IS déclaré ligne 1',exact=True).fill('19,999')
                expect(controle).to_contain_text('1.460,00 MAD')
                assert '1.459,93 MAD' not in controle.inner_text()
                v,detail=sauver(page,panel,detail,v)
                expect(detail.get_by_role('region',name='Contrôles du passage fiscal conservés',exact=True)).to_contain_text('1.459,93 MAD')
            with page.expect_download() as d:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
            dest=tmp_path/'passage725.zip';d.value.save_as(dest)
            with ZipFile(dest) as z:
                data=json.loads(z.read('passage_fiscal_documentaire.json'))
                n=data['controle_passage_fiscal']['montants']
                assert n['is_theorique_taux_declare']==('1460.00' if role=='lecture' else '1459.93')
                assert n['impots_comptabilises_67']=='1600.00'
            controle=detail.get_by_role('region',name='Contrôles du passage fiscal conservés',exact=True)
            controle.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'passage725-{role}-{largeur}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors and not serveur,(errors,serveur)
        finally:browser.close()


def test_725_periode_absente_et_rejet_conservent_brouillon(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api,False);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_courant(page,application,v)
            saisir(detail,body(v)['tables'][0])
            detail.get_by_label('Taux IS déclaré ligne 1',exact=True).fill('NaN')
            detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name=SAVE,exact=True).click()
            assert rep.value.status==422
            expect(detail.get_by_role('alert')).to_be_visible()
            expect(detail.get_by_label('Taux IS déclaré ligne 1',exact=True)).to_have_value('NaN')
            detail.get_by_label('Taux IS déclaré ligne 1',exact=True).fill('')
            v,detail=sauver(page,panel,detail,v)
            expect(detail.get_by_role('region',name='Contrôles du passage fiscal conservés',exact=True)).to_contain_text('IS théorique selon taux déclaré : Indisponible')
        finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_725_get_reel_tardif_ignore(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__passage725Retenu=true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click();page.wait_for_function('window.__passage725Retenu===true')
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


def test_725_post_reel_tardif_ne_remplace_pas_selection(application):
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
                pending.append((route,rep));page.evaluate('window.__passage725PostRetenu=true')
            page.route('**'+url(v),retenir,times=1);detail.get_by_role('button',name=SAVE,exact=True).click()
            page.wait_for_function('window.__passage725PostRetenu===true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()
