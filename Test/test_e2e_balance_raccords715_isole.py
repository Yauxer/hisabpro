"""Edge715 : rattachements explicites, contrôles anciens, droits et contexte."""
from contextlib import closing
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_raccords715_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,creer,body,url,BASE,mv_body,mv_url)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from browser_support import chromium_executable
SUMMARY='Raccorder les clôtures de mouvements aux comptes sources'
REGION='Rattachements des mouvements de la préparation'
SAVE='Conserver les rattachements dans une nouvelle version'


def ouvrir_raccords(page,app,v,lecture=False):
 panel,_=ouvrir(page,app,v,lecture);panel.get_by_text(SUMMARY,exact=True).click()
 detail=panel.get_by_role('region',name=REGION,exact=True)
 expect(detail.get_by_label('Tableau de rattachement',exact=True)).to_be_visible()
 return panel,detail


def rattacher(detail):
 for code,compte in [('B2','2340'),('B2bis','2834'),('B5','1511')]:
  detail.get_by_label('Tableau de rattachement',exact=True).select_option(code)
  detail.get_by_label(f'Compte source {code} ligne 1',exact=True).select_option(compte)
 detail.get_by_label('Tableau de rattachement',exact=True).select_option('B2')
 expect(detail.get_by_label('Compte source B2 ligne 1',exact=True)).to_have_value('2340')


def sauver(page,panel,detail,v):
 detail.get_by_role('checkbox').check()
 with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:detail.get_by_role('button',name=SAVE,exact=True).click()
 assert rep.value.status==201,rep.value.text();v=rep.value.json()
 expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible()
 panel.get_by_text(SUMMARY,exact=True).click()
 return v,panel.get_by_role('region',name=REGION,exact=True)


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_715_rattachements_export_reel_mobile_et_droits(application,role,largeur,tmp_path):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api)
  if role=='comptable':
   long=mv_body(v);long['tables'][0]['lignes'][0]['reference_source']='R'*300
   v=ok(api.post(mv_url(v),json=long),201)
  if role=='lecture':v=ok(api.post(url(v),json=body(v)),201)
  if role!='admin':
   email=email.replace('@','-'+role+'@');ok(api.post('/api/utilisateurs',json={'nom':'Raccords fictifs715','email':email,'mot_de_passe':password,'role':role}),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
   errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   panel,detail=ouvrir_raccords(page,application,v,role=='lecture')
   if role=='lecture':
    assert detail.get_by_role('button',name=SAVE,exact=True).count()==0 and detail.get_by_label('Compte source B2 ligne 1',exact=True).is_disabled()
   else:
    expect(detail.get_by_label('Compte source B2 ligne 1',exact=True)).to_have_value('')
    rattacher(detail);v,detail=sauver(page,panel,detail,v)
   controle=detail.get_by_role('region',name='Contrôles des rattachements conservés',exact=True)
   expect(controle).to_contain_text('11.000,00 MAD');expect(controle).to_contain_text('0,00 MAD')
   detail.get_by_label('Tableau de rattachement',exact=True).select_option('B2bis');expect(controle).to_contain_text('4.500,00 MAD')
   detail.get_by_label('Tableau de rattachement',exact=True).select_option('B5');expect(controle).to_contain_text('700,00 MAD')
   detail.get_by_label('Tableau de rattachement',exact=True).select_option('B2')
   with page.expect_download() as d:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   dest=tmp_path/'raccords715.zip';d.value.save_as(dest)
   with ZipFile(dest) as z:
    data=json.loads(z.read('raccords_mouvements.json'));assert data['actuel'] and data['snapshot']['controle_raccords']['tableaux']['B2']['comptes'][0]['ecart']=='0.00'
   detail.get_by_label('Compte source B2 ligne 1',exact=True).scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'raccords715-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1') and not errors and not serveur,(errors,serveur)
  finally:browser.close()


def test_715_non_rattache_et_brouillon_distinct(application):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);v=ok(api.post(url(v),json=body(v)),201);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_raccords(page,application,v)
   controle=detail.get_by_role('region',name='Contrôles des rattachements conservés',exact=True)
   detail.get_by_label('Compte source B2 ligne 1',exact=True).select_option('')
   expect(controle).to_contain_text('0,00 MAD');expect(controle).to_contain_text('conservé : aucune')
   assert not detail.get_by_role('checkbox').is_checked();v,detail=sauver(page,panel,detail,v)
   controle=detail.get_by_role('region',name='Contrôles des rattachements conservés',exact=True)
   expect(controle).to_contain_text('Indisponible');expect(controle).to_contain_text('conservé : 1')
   assert ok(api.get(url(v)))['snapshot']['controle_raccords']['tableaux']['B2']['comptes'][0]['ecart'] is None
  finally:browser.close()


def test_715_nouveaux_mouvements_rendent_ancien_le_raccord(application):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);r=ok(api.post(url(v),json=body(v)),201);q=mv_body(r);q['tables'][0]['lignes'][0]['fin']='10999.99'
  v=ok(api.post(mv_url(r),json=q),201);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_raccords(page,application,v)
   controle=detail.get_by_role('region',name='Contrôles des rattachements conservés',exact=True)
   expect(controle).to_contain_text('doit être refait');expect(controle).to_contain_text('11.000,00 MAD')
   expect(detail.get_by_label('Compte source B2 ligne 1',exact=True)).to_have_value('')
   expect(detail).to_contain_text('10.999,99 MAD')
   rattacher(detail);v,detail=sauver(page,panel,detail,v)
   controle=detail.get_by_role('region',name='Contrôles des rattachements conservés',exact=True)
   expect(controle).to_contain_text('-0,01 MAD');assert 'doit être refait' not in controle.inner_text()
   assert ok(api.get(url(r)))['actuel'] and ok(api.get(url(v)))['actuel']
  finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_715_get_tardif_abandonne(application,action):
 api,email,password=client(application)
 with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
  v=creer(api);v2=ok(api.post(url(v),json=body(v)),201);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,_=ouvrir(page,application,v);pending=[]
   def retenir(route):
    rep=route.fetch();assert rep.status==200;pending.append((route,rep));page.evaluate('window.__raccord715Retenu=true')
   page.route('**'+url(v),retenir,times=1);panel.get_by_text(SUMMARY,exact=True).click();page.wait_for_function('window.__raccord715Retenu===true')
   if action=='version':
    panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']));expect(panel.get_by_text(f'Version {v2["version"]} conservée',exact=False)).to_be_visible()
   elif action=='fermeture':panel.get_by_role('button',name='Masquer',exact=True).click()
   else:page.evaluate('t=>localStorage.setItem("hisabpro_token",t)',autre.headers['Authorization'].split(' ',1)[1])
   route,rep=pending.pop()
   with page.expect_response(lambda r:r.url.endswith(url(v))):route.fulfill(response=rep)
   page.wait_for_load_state('networkidle');assert panel.get_by_label('Compte source B2 ligne 1',exact=True).count()==0
  finally:browser.close()


def test_715_post_tardif_ne_remplace_pas_selection(application):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);v2=ok(api.post(url(v),json=body(v)),201);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_raccords(page,application,v);pending=[]
   rattacher(detail);detail.get_by_role('checkbox').check()
   def retenir(route):
    if route.request.method!='POST':return route.continue_()
    rep=route.fetch();assert rep.status==201;pending.append((route,rep));page.evaluate('window.__raccord715PostRetenu=true')
   page.route('**'+url(v),retenir,times=1);detail.get_by_role('button',name=SAVE,exact=True).click();page.wait_for_function('window.__raccord715PostRetenu===true')
   panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']));expect(panel.get_by_text(f'Version {v2["version"]} conservée',exact=False)).to_be_visible()
   route,rep=pending.pop();saved=rep.json()
   with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
   page.wait_for_load_state('networkidle');expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
   assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
  finally:browser.close()
