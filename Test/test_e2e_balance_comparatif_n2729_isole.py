"""N-2 : Edge réel, source explicite, C3 actualisé, trois rôles et réponses tardives."""
from contextlib import closing
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_comparatif_n2729_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,creer,creer_source,body,url,c3_body,c3_url,BASE)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from browser_support import chromium_executable
SUMMARY='Rattacher une source N-2 aux indicateurs C3'
REGION='Source comparative N-2 de la préparation'
SAVE='Rattacher N-2 dans une nouvelle version'
C3='Consulter les indicateurs comptables C3 depuis les balances'


def ouvrir_n2(page,app,v,lecture=False):
 panel,_=ouvrir(page,app,v,lecture);panel.get_by_text(SUMMARY,exact=True).click()
 detail=panel.get_by_role('region',name=REGION,exact=True)
 expect(detail.get_by_role('button',name='Relire la source N-2 conservée',exact=True)).to_be_visible()
 return panel,detail


def saisir(detail,s,ref='BALANCE FICTIVE729 N-2 explicitement choisie'):
 detail.get_by_label('Préparation N-2 à rattacher',exact=True).select_option(str(s['id']))
 detail.get_by_label('Référence explicite de la source N-2',exact=True).fill(ref)


def sauver(page,panel,detail,v):
 detail.get_by_role('checkbox').check()
 with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
  detail.get_by_role('button',name=SAVE,exact=True).click()
 assert rep.value.status==201,rep.value.text();v=rep.value.json()
 expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible()
 panel.get_by_text(SUMMARY,exact=True).click()
 return v,panel.get_by_role('region',name=REGION,exact=True)


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_729_rattacher_source_c3_fige_actualiser_export_mobile(application,role,largeur,tmp_path):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  s=creer_source(api);v=creer(api);v=ok(api.post(c3_url(v),json=c3_body(v)),201)
  if role=='lecture':
   v=ok(api.post(url(v),json=body(v,s)),201);v=ok(api.post(c3_url(v),json=c3_body(v)),201)
  if role!='admin':
   email=email.replace('@','-'+role+'@');ok(api.post('/api/utilisateurs',json={'nom':'N2 fictif729','email':email,'mot_de_passe':password,'role':role}),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
   errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   panel,detail=ouvrir_n2(page,application,v,role=='lecture')
   if role=='lecture':assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
   else:
    saisir(detail,s,'SOURCE729'+'X'*300);v,detail=sauver(page,panel,detail,v)
    expect(panel).to_contain_text('Une source N-2 est rattachée. Conservez une nouvelle version')
    expect(detail.get_by_role('region',name='Source N-2 conservée',exact=True)).to_contain_text('12.000,00 MAD')
    detail.get_by_label('Référence explicite de la source N-2',exact=True).fill('BROUILLON729')
    assert 'BROUILLON729' not in detail.get_by_role('region',name='Source N-2 conservée',exact=True).inner_text()
   panel.get_by_text(C3,exact=True).click();c=panel.get_by_role('region',name='Indicateurs C3 de la préparation',exact=True)
   c.get_by_label('Période des indicateurs',exact=True).select_option('n2')
   if role!='lecture':
    expect(c).to_contain_text('Source N-2 non fournie')
    c.get_by_role('checkbox').check()
    with page.expect_response(lambda r:r.url.endswith(c3_url(v)) and r.request.method=='POST') as rep:
     c.get_by_role('button',name='Conserver les indicateurs C3 dans une nouvelle version',exact=True).click()
    assert rep.value.status==201;v=rep.value.json()
    expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible()
    panel.get_by_text(C3,exact=True).click();c=panel.get_by_role('region',name='Indicateurs C3 de la préparation',exact=True)
    c.get_by_label('Période des indicateurs',exact=True).select_option('n2')
   expect(c).to_contain_text('11.000,00 MAD');expect(c).to_contain_text('1.000,00 MAD');expect(c).to_contain_text('2.000,00 MAD')
   assert 'Une source N-2 est rattachée. Conservez une nouvelle version' not in panel.inner_text()
   with page.expect_download() as rep:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   dest=tmp_path/'n2729.zip';rep.value.save_as(dest)
   with ZipFile(dest) as z:
    assert 'balance_N2.csv' in z.namelist()
    n=json.loads(z.read('indicateurs_comptables_documentaires.json'))['vue']['periodes']['n2'];assert n['resultat_net']=='1000.00'
    assert json.loads(z.read('comparatif_n2_documentaire.json'))['source_preparation']['id']==s['id']
   c.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'n2729-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and not errors and not serveur,(errors,serveur)
  finally:browser.close()


def test_729_absence_source_et_reference_vide_sans_creation(application):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_n2(page,application,v)
   expect(detail).to_contain_text('Importer d’abord la balance N dans une préparation')
   expect(detail.get_by_role('button',name=SAVE,exact=True)).to_be_disabled()
   s=creer_source(api);detail.get_by_role('button',name='Relire la source N-2 conservée',exact=True).click()
   saisir(detail,s,'   ');detail.get_by_role('checkbox').check();expect(detail.get_by_role('button',name=SAVE,exact=True)).to_be_disabled()
   detail.get_by_label('Référence explicite de la source N-2',exact=True).fill('Référence fictive729')
   detail.get_by_role('checkbox').check();expect(detail.get_by_role('button',name=SAVE,exact=True)).to_be_enabled()
   assert not ok(api.get(url(v)))['conserve']
  finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_729_get_reel_tardif_ignore(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        s=creer_source(api);v=creer(api);v2=ok(api.post(url(v),json=body(v,s)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__n2729Retenu=true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click();page.wait_for_function('window.__n2729Retenu===true')
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


def test_729_post_reel_tardif_ne_remplace_pas_selection(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        s=creer_source(api);v=creer(api);v2=ok(api.post(url(v),json=body(v,s)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_n2(page,application,v);pending=[]
            saisir(detail,s);detail.get_by_role('checkbox').check()
            def retenir(route):
                if route.request.method!='POST':return route.continue_()
                rep=route.fetch();assert rep.status==201
                pending.append((route,rep));page.evaluate('window.__n2729PostRetenu=true')
            page.route('**'+url(v),retenir,times=1);detail.get_by_role('button',name=SAVE,exact=True).click()
            page.wait_for_function('window.__n2729PostRetenu===true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()
