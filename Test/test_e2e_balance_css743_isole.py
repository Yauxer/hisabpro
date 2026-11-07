"""CM qualifiée : vraie API, Edge, droits, versions et retards natifs."""
from contextlib import closing
from pathlib import Path
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_css743_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,creer,body,url,BASE,donnees_metier)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from browser_support import chromium_executable
SUMMARY='Calculer la CSS — 2026'
REGION='CSS de la préparation'
SAVE='Conserver le calcul CSS dans une nouvelle version'
SELECTION='Qualification CSS à documenter'
ROOT=Path(__file__).resolve().parents[1]


def ouvrir_extra(page,app,v,lecture=False):
 panel,_=ouvrir(page,app,v,lecture);panel.get_by_text(SUMMARY,exact=True).click()
 detail=panel.get_by_role('region',name=REGION,exact=True)
 expect(detail.get_by_label(SELECTION,exact=True)).to_be_visible()
 return panel,detail


def saisir(detail,t):
 detail.get_by_label('Déclaration du tableau',exact=True).select_option(t['statut'])
 detail.get_by_label('Justification du tableau',exact=True).fill(t['justification'])
 labels={'nature':'Désignation de la qualification CSS','regime':'Périmètre CSS déclaré',
  'exercice_reference':'Exercice fiscal de référence déclaré','benefice_reference':'Bénéfice net fiscal du dernier exercice clos',
  'dernier_clos_confirme':'Source du dernier exercice clos confirmée','exoneration_permanente':'Exonération permanente d’IS justifiée',
  'reference_source':'Référence de source'}
 for i,row in enumerate(t['lignes'],1):
  detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
  for k,v in row.items():
   if v is not None:
    el=detail.get_by_label(f'{labels[k]} ligne {i}',exact=True)
    if k in ('regime','dernier_clos_confirme','exoneration_permanente'):el.select_option(v)
    else:el.fill(str(v))


def sauver(page,panel,detail,v):
 detail.get_by_role('checkbox').check()
 with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
  detail.get_by_role('button',name=SAVE,exact=True).click()
 assert rep.value.status==201,rep.value.text();v=rep.value.json()
 expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible()
 panel.get_by_text(SUMMARY,exact=True).click()
 return v,panel.get_by_role('region',name=REGION,exact=True)


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_743_cm_droits_export_brouillon_mobile(application,role,largeur,tmp_path):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api)
  if role=='lecture':v=ok(api.post(url(v),json=body(v)),201)
  if role!='admin':
   email=email.replace('@','-'+role+'@');ok(api.post('/api/utilisateurs',json={'nom':'CM fictif743','email':email,'mot_de_passe':password,'role':role}),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
   errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   panel,detail=ouvrir_extra(page,application,v,role=='lecture');avant=donnees_metier(application)
   if role=='lecture':
    assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
    assert detail.get_by_label('Bénéfice net fiscal du dernier exercice clos ligne 1',exact=True).is_disabled()
   else:
    saisir(detail,body(v)['tables'][0]);detail.get_by_label('Référence de source ligne 1',exact=True).fill('NOTE743'+'X'*300)
    expect(detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True)).to_be_disabled()
    v,detail=sauver(page,panel,detail,v)
   ctrl=detail.get_by_role('region',name='Contrôles CSS conservés',exact=True)
   expect(ctrl).to_contain_text('Bénéfice net fiscal de référence déclaré : 2.000.000,00 MAD')
   expect(ctrl).to_contain_text('CSS proposée selon qualifications déclarées : 30.000,00 MAD')
   expect(ctrl).to_contain_text('Taux proportionnel : 1,500 %')
   expect(ctrl).to_contain_text('CSS distincte de l’IS/CM')
   if role!='lecture':
    detail.get_by_label('Exonération permanente d’IS justifiée ligne 1',exact=True).select_option('oui')
    expect(ctrl).to_contain_text('CSS proposée selon qualifications déclarées : 30.000,00 MAD')
   with page.expect_download() as rep:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   dest=tmp_path/'css743.zip';rep.value.save_as(dest)
   with ZipFile(dest) as z:
    c=json.loads(z.read('css_documentaire.json'))['controle_css']
    assert c['montants']['css_proposee']=='30000.00' and c['solde_is'] is None and not c['liquidation_confirmee']
   ctrl.scroll_into_view_if_needed();page.screenshot(path=str(ROOT/f'.codex-tests/css743-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and not errors and not serveur,(errors,serveur)
   apres=donnees_metier(application);assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')
   if role=='lecture':assert apres==avant
  finally:browser.close()


def test_743_nan_refuse_puis_exoneration_declaree_sans_f5(application):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   saisir(detail,body(v)['tables'][0]);detail.get_by_label('Bénéfice net fiscal du dernier exercice clos ligne 1',exact=True).fill('NaN');detail.get_by_role('checkbox').check()
   avant=donnees_metier(application)
   with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:detail.get_by_role('button',name=SAVE,exact=True).click()
   assert rep.value.status==422;expect(detail.get_by_role('alert')).to_be_visible()
   expect(detail.get_by_label('Bénéfice net fiscal du dernier exercice clos ligne 1',exact=True)).to_have_value('NaN');assert donnees_metier(application)==avant
   detail.get_by_label('Bénéfice net fiscal du dernier exercice clos ligne 1',exact=True).fill('2000000')
   detail.get_by_label('Exonération permanente d’IS justifiée ligne 1',exact=True).select_option('oui')
   v,detail=sauver(page,panel,detail,v)
   expect(detail).to_contain_text('CSS proposée selon qualifications déclarées : 0,00 MAD')
   expect(detail).to_contain_text('Taux proportionnel : 1,500 %')
  finally:browser.close()


def test_743_contexte_change_actualisation_explicite_interface(application):
 from test_e2e_balance_contexte_fiscal735_isole import SUMMARY as CF_SUMMARY,REGION as CF_REGION,sauver as sauver_cf
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);v=ok(api.post(url(v),json=body(v)),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   expect(detail).to_contain_text('Écart CSS proposée moins CSS déclarée : 30.000,00 MAD')
   panel.get_by_text(CF_SUMMARY,exact=True).click();cf=panel.get_by_role('region',name=CF_REGION,exact=True)
   cf.get_by_label('Rubrique du contexte fiscal',exact=True).select_option('CF-CSS')
   cf.get_by_label('CSS déclarée ligne 1',exact=True).fill('30000');v,cf=sauver_cf(page,panel,cf,v)
   panel.get_by_text(SUMMARY,exact=True).click();detail=panel.get_by_role('region',name=REGION,exact=True)
   expect(detail).to_contain_text('Le contexte fiscal a changé : comparaison CSS conservée pour mémoire')
   expect(detail).to_contain_text('Écart CSS proposée moins CSS déclarée : 30.000,00 MAD')
   v,detail=sauver(page,panel,detail,v)
   expect(detail).to_contain_text('Écart CSS proposée moins CSS déclarée : 0,00 MAD')
   assert not ok(api.get(url(v)))['source_contexte_modifiee']
  finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_743_get_reel_tardif_ignore(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api,False);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__cm743Retenu=true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click();page.wait_for_function('window.__cm743Retenu===true')
            if action=='version':
                panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
                expect(panel.get_by_text(f'Version {v2["version"]} conservée',exact=False)).to_be_visible()
            elif action=='fermeture':panel.get_by_role('button',name='Masquer',exact=True).click()
            else:page.evaluate('t=>localStorage.setItem("hisabpro_token",t)',autre.headers['Authorization'].split(' ',1)[1])
            route,rep=pending.pop()
            with page.expect_response(lambda r:r.url.endswith(url(v))):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            assert panel.get_by_role('region',name=REGION,exact=True).get_by_role('checkbox').count()==0
        finally:browser.close()


def test_743_post_reel_tardif_ne_remplace_pas_selection(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api,False);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_extra(page,application,v);pending=[]
            [saisir(detail,t) for t in body(v)['tables']];detail.get_by_role('checkbox').check()
            def retenir(route):
                if route.request.method!='POST':return route.continue_()
                rep=route.fetch();assert rep.status==201
                pending.append((route,rep));page.evaluate('window.__cm743PostRetenu=true')
            page.route('**'+url(v),retenir,times=1);detail.get_by_role('button',name=SAVE,exact=True).click()
            page.wait_for_function('window.__cm743PostRetenu===true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text(f'Version {v2["version"]} conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()
