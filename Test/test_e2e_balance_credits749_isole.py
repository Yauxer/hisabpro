"""CM qualifiée : vraie API, Edge, droits, versions et retards natifs."""
from contextlib import closing
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import json,hashlib
from pypdf import PdfReader
from openpyxl import load_workbook
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_credits749_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,creer,body,url,BASE,donnees_metier)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from browser_support import chromium_executable
from test_logo_societe import image_data
SUMMARY='Qualifier les crédits IS — 2026'
REGION='Crédits IS de la préparation'
SAVE='Conserver les crédits IS dans une nouvelle version'
SELECTION='Qualification crédits à documenter'
ROOT=Path(__file__).resolve().parents[1]


def ouvrir_extra(page,app,v,lecture=False):
 panel,_=ouvrir(page,app,v,lecture);panel.get_by_text(SUMMARY,exact=True).click()
 detail=panel.get_by_role('region',name=REGION,exact=True)
 expect(detail.get_by_label(SELECTION,exact=True)).to_be_visible()
 return panel,detail


def saisir(detail,t):
 detail.get_by_label(SELECTION,exact=True).select_option(t['code'])
 detail.get_by_label('Déclaration du tableau',exact=True).select_option(t['statut'])
 detail.get_by_label('Justification du tableau',exact=True).fill(t['justification'])
 labels={'nature':'Désignation du profil crédits' if t['code']=='CR-PROFIL' else 'Désignation du justificatif crédit',
  'regime':'Périmètre IS des crédits','periode_confirmee':'Période source confirmée','exhaustivite':'Liste des crédits exhaustive',
  'absence_credits':'Absence de tout crédit confirmée','type_credit':'Type juridique du crédit',
  'date_allocation':'Date d’allocation du produit justifiée','categorie_payeur':'Catégorie du payeur article157 déclarée','exercice_rattachement':'Exercice fiscal de rattachement','date_retenue':'Date de la retenue justifiée',
  'eligibilite_confirmee':'Éligibilité IS de cette ligne confirmée','montant':'Montant total du justificatif',
  'deja_impute_acomptes':'Part déjà imputée sur acomptes','autres_utilisations':'Autres utilisations ou restitutions','reference_source':'Référence de source'}
 for i,row in enumerate(t['lignes'],1):
  detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
  for k,v in row.items():
   if v is not None and v != '':
    el=detail.get_by_label(f'{labels[k]} ligne {i}',exact=True)
    if k in ('regime','periode_confirmee','exhaustivite','absence_credits','type_credit','categorie_payeur','eligibilite_confirmee'):el.select_option(v)
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
def test_749_credits_droits_exports_brouillon_mobile(application,role,largeur,tmp_path):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
  if role=='lecture':v=ok(api.post(url(v),json=body(v)),201)
  if role!='admin':
   email=email.replace('@','-'+role+'@');ok(api.post('/api/utilisateurs',json={'nom':'Crédits fictifs749','email':email,'mot_de_passe':password,'role':role}),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
   errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   panel,detail=ouvrir_extra(page,application,v,role=='lecture');avant=donnees_metier(application)
   if role=='lecture':
    assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
    detail.get_by_label(SELECTION,exact=True).select_option('CR-LIGNES')
    assert detail.get_by_label('Montant total du justificatif ligne 1',exact=True).is_disabled()
   else:
    for table in body(v)['tables']:saisir(detail,table)
    detail.get_by_label('Référence de source ligne 1',exact=True).fill('NOTE749'+'X'*300)
    v,detail=sauver(page,panel,detail,v)
   ctrl=detail.get_by_role('region',name='Contrôles crédits IS conservés',exact=True)
   expect(ctrl).to_contain_text('Montant total des justificatifs saisis : 500,00 MAD')
   expect(ctrl).to_contain_text('Crédits disponibles proposés après qualifications : 325,00 MAD')
   expect(ctrl).to_contain_text('Part déjà imputée sur acomptes : 150,00 MAD')
   if role!='lecture':
    detail.get_by_label(SELECTION,exact=True).select_option('CR-LIGNES')
    detail.get_by_label('Éligibilité IS de cette ligne confirmée ligne 1',exact=True).select_option('non')
    detail.get_by_label('Montant total du justificatif ligne 1',exact=True).fill('999')
    expect(ctrl).to_contain_text('Crédits disponibles proposés après qualifications : 325,00 MAD')
   with page.expect_download() as rep:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   dest=tmp_path/'credits749.zip';rep.value.save_as(dest)
   with ZipFile(dest) as z:
    c=json.loads(z.read('credits_is_documentaires.json'))['controle_credits']
    assert c['montants']['credits_proposes']=='325.00' and c['solde_final'] is None and not c['imputation_confirmee']
   directs={}
   for format,label in [('pdf','Exporter la préparation PDF'),('xlsx','Exporter la préparation Excel')]:
    with page.expect_download() as dl:panel.get_by_role('button',name=label,exact=True).click()
    flux=Path(dl.value.path()).read_bytes()
    if format=='pdf':
     pdf=PdfReader(BytesIO(flux));assert '325,00' in '\n'.join(p.extract_text() or '' for p in pdf.pages) and any(p.images for p in pdf.pages)
    else:
     w=load_workbook(BytesIO(flux));assert dict(list(w['Contrôle crédits IS'].values)[1:])['Crédits disponibles proposés après qualifications']==325;w.close()
     with ZipFile(BytesIO(flux)) as z:assert any(n.startswith('xl/media/') for n in z.namelist())
    directs[format]={'sha256':hashlib.sha256(flux).hexdigest(),'montant325_et_logo_verifies':True}
   ctrl.scroll_into_view_if_needed();page.screenshot(path=str(ROOT/f'.codex-tests/credits749-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and not errors and not serveur,(errors,serveur)
   apres=donnees_metier(application);assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')
   if role=='lecture':assert apres==avant
   (ROOT/f'.codex-tests/credits939_{role}_preuve.json').write_text(json.dumps({'role':role,'largeur':largeur,'exports_individuels_reels':directs,'ZIP_credits325_verifie':True,'brouillon_non_confondu_snapshot':True,'hors_preparations_inchange':True},ensure_ascii=False,indent=2),encoding='utf8')
  finally:browser.close()


def test_749_nan_refuse_puis_part_exclue_sans_f5(application):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   for table in body(v)['tables']:saisir(detail,table)
   detail.get_by_label('Montant total du justificatif ligne 1',exact=True).fill('NaN');detail.get_by_role('checkbox').check()
   avant=donnees_metier(application)
   with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:detail.get_by_role('button',name=SAVE,exact=True).click()
   assert rep.value.status==422;expect(detail.get_by_role('alert')).to_be_visible()
   expect(detail.get_by_label('Montant total du justificatif ligne 1',exact=True)).to_have_value('NaN');assert donnees_metier(application)==avant
   detail.get_by_label('Montant total du justificatif ligne 1',exact=True).fill('300')
   detail.get_by_label('Éligibilité IS de cette ligne confirmée ligne 1',exact=True).select_option('non')
   v,detail=sauver(page,panel,detail,v)
   expect(detail).to_contain_text('Crédits disponibles proposés après qualifications : 150,00 MAD')
   expect(detail).to_contain_text('Exclu selon déclaration')
  finally:browser.close()


def test_749_contexte_change_actualisation_explicite_interface(application):
 from test_e2e_balance_contexte_fiscal735_isole import SUMMARY as CF_SUMMARY,REGION as CF_REGION,sauver as sauver_cf
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);v=ok(api.post(url(v),json=body(v)),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   expect(detail).to_contain_text('Écart total saisi moins total du contexte fiscal : -100,00 MAD')
   panel.get_by_text(CF_SUMMARY,exact=True).click();cf=panel.get_by_role('region',name=CF_REGION,exact=True)
   cf.get_by_label('Rubrique du contexte fiscal',exact=True).select_option('CF-CREDITS')
   cf.get_by_label('Montant total du crédit ligne 1',exact=True).fill('200');v,cf=sauver_cf(page,panel,cf,v)
   panel.get_by_text(SUMMARY,exact=True).click();detail=panel.get_by_role('region',name=REGION,exact=True)
   expect(detail).to_contain_text('Le contexte fiscal a changé : comparaison crédits conservée pour mémoire')
   expect(detail).to_contain_text('Écart total saisi moins total du contexte fiscal : -100,00 MAD')
   v,detail=sauver(page,panel,detail,v)
   expect(detail).to_contain_text('Écart total saisi moins total du contexte fiscal : 0,00 MAD')
   assert not ok(api.get(url(v)))['source_contexte_modifiee']
  finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_749_get_reel_tardif_ignore(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api,False);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__cm749Retenu=true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click();page.wait_for_function('window.__cm749Retenu===true')
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


def test_749_post_reel_tardif_ne_remplace_pas_selection(application):
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
                pending.append((route,rep));page.evaluate('window.__cm749PostRetenu=true')
            page.route('**'+url(v),retenir,times=1);detail.get_by_role('button',name=SAVE,exact=True).click()
            page.wait_for_function('window.__cm749PostRetenu===true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text(f'Version {v2["version"]} conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()


@pytest.mark.parametrize('cas,attendu',[('location_avant','Indisponible'),('location_apres','325,00 MAD'),('banque_avant','Indisponible')])
def test_749_date_allocation_payeur_et_entree_en_vigueur_interface(application,cas,attendu):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);b=body(v);r=b['tables'][1]['lignes'][0]
  r.update(type_credit='Location — CGI157' if cas.startswith('location') else 'Rémunérations de tiers — CGI157',date_retenue='2026-07-01',
   date_allocation='2026-07-01' if cas.endswith('apres') else '2026-06-30',categorie_payeur='Banque ou assurance' if cas.startswith('banque') else 'Public ou filiale publique')
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':390,'height':1100});connexion(page,application['web_url'],email,password)
   panel,detail=ouvrir_extra(page,application,v)
   for table in b['tables']:saisir(detail,table)
   v,detail=sauver(page,panel,detail,v)
   expect(detail).to_contain_text('Crédits disponibles proposés après qualifications : '+attendu)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  finally:browser.close()
