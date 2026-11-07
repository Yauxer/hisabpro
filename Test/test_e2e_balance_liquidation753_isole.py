"""CM qualifiée : vraie API, Edge, droits, versions et retards natifs."""
from contextlib import closing
from pathlib import Path
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_liquidation753_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,creer,body,url,BASE,donnees_metier)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from browser_support import chromium_executable
from test_logo_societe import image_data
from exports_qualification941_support import verifier_exports
SUMMARY='Proposer le solde IS/CM — 2026'
REGION='Proposition IS CM de la préparation'
SAVE='Conserver la proposition IS/CM dans une nouvelle version'
SELECTION='Revue fiscale à documenter'
ROOT=Path(__file__).resolve().parents[1]


def ouvrir_extra(page,app,v,lecture=False):
 panel,_=ouvrir(page,app,v,lecture);panel.get_by_text(SUMMARY,exact=True).click()
 detail=panel.get_by_role('region',name=REGION,exact=True)
 expect(detail.get_by_label(SELECTION,exact=True)).to_be_visible()
 return panel,detail


def saisir(detail,t):
 detail.get_by_label('Déclaration du tableau',exact=True).select_option(t['statut'])
 detail.get_by_label('Justification du tableau',exact=True).fill(t['justification'])
 labels={'nature':'Désignation de la revue fiscale','b12_verifie':'Taux, régime et déficits B12 vérifiés',
  'cm_verifiee':'Qualification CM vérifiée','exhaustivite_verifiee':'Crédits et acomptes exhaustifs vérifiés',
  'excedent_verifie':'Solde d’excédent antérieur vérifié','ordre_examine':'Ordre de simulation examiné et justifié',
  'excedent_annuel':'Excédent antérieur à utiliser dans cette simulation annuelle','reference_source':'Référence de source'}
 for i,row in enumerate(t['lignes'],1):
  detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
  for k,v in row.items():
   if v is not None:
    el=detail.get_by_label(f'{labels[k]} ligne {i}',exact=True)
    if k in ('b12_verifie','cm_verifiee','exhaustivite_verifiee','excedent_verifie','ordre_examine'):el.select_option(v)
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
def test_753_proposition_droits_exports_brouillon_mobile(application,role,largeur,tmp_path):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api,css=True);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
  if role=='lecture':v=ok(api.post(url(v),json=body(v)),201)
  if role!='admin':
   email=email.replace('@','-'+role+'@');ok(api.post('/api/utilisateurs',json={'nom':'Revue fictive753','email':email,'mot_de_passe':password,'role':role}),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
   errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   panel,detail=ouvrir_extra(page,application,v,role=='lecture');avant=donnees_metier(application)
   if role=='lecture':
    assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
    assert detail.get_by_label('Excédent antérieur à utiliser dans cette simulation annuelle ligne 1',exact=True).is_disabled()
   else:
    saisir(detail,body(v)['tables'][0]);detail.get_by_label('Référence de source ligne 1',exact=True).fill('NOTE753'+'X'*300)
    v,detail=sauver(page,panel,detail,v)
   ctrl=detail.get_by_role('region',name='Contrôles de la proposition IS CM',exact=True)
   expect(ctrl).to_contain_text('Maximum IS/CM proposé avant imputations : 3.000,00 MAD')
   expect(ctrl).to_contain_text('Crédits qualifiés disponibles après utilisations antérieures : 325,00 MAD')
   expect(ctrl).to_contain_text('Acomptes justifiés proposés : 1.250,00 MAD')
   expect(ctrl).to_contain_text('Solde IS/CM proposé à payer : 1.425,00 MAD')
   expect(ctrl).to_contain_text('CSS proposée séparément dans sa qualification conservée : 0,00 MAD')
   if role!='lecture':
    detail.get_by_label('Taux, régime et déficits B12 vérifiés ligne 1',exact=True).select_option('non')
    expect(ctrl).to_contain_text('Solde IS/CM proposé à payer : 1.425,00 MAD')
   with page.expect_download() as rep:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   dest=tmp_path/'liquidation753.zip';rep.value.save_as(dest)
   with ZipFile(dest) as z:
    c=json.loads(z.read('liquidation_is_documentaire.json'))['controle_liquidation']
    assert c['montants']['solde_is_propose']=='1425.00' and c['total_global_is_css'] is None and not c['liquidation_confirmee'] and not c['paiement_confirme']
   directs=verifier_exports(page,panel,'Proposition IS CM','Solde IS/CM proposé à payer',1425,'1 425,00')
   ctrl.scroll_into_view_if_needed();page.screenshot(path=str(ROOT/f'.codex-tests/liquidation753-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and not errors and not serveur,(errors,serveur)
   apres=donnees_metier(application);assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')
   if role=='lecture':assert apres==avant
   (ROOT/f'.codex-tests/is941_liq_{role}.json').write_text(json.dumps({'role':role,'largeur':largeur,'solde_propose':'1425.00','exports_individuels':directs,'ZIP_snapshot_verifie':True,'aucune_liquidation_ou_paiement_confirme':True,'sources_hors_preparations_inchangees':True},ensure_ascii=False,indent=2),encoding='utf8')
  finally:browser.close()


def test_753_nan_refuse_puis_revue_incomplete_et_reprise_sans_f5(application):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   saisir(detail,body(v)['tables'][0]);champ=detail.get_by_label('Excédent antérieur à utiliser dans cette simulation annuelle ligne 1',exact=True)
   champ.fill('NaN');detail.get_by_role('checkbox').check();avant=donnees_metier(application)
   with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:detail.get_by_role('button',name=SAVE,exact=True).click()
   assert rep.value.status==422;expect(detail.get_by_role('alert')).to_be_visible();expect(champ).to_have_value('NaN');assert donnees_metier(application)==avant
   champ.fill('0');detail.get_by_label('Ordre de simulation examiné et justifié ligne 1',exact=True).select_option('non')
   v,detail=sauver(page,panel,detail,v);expect(detail).to_contain_text('Solde IS/CM proposé à payer : Indisponible')
   detail.get_by_label('Ordre de simulation examiné et justifié ligne 1',exact=True).select_option('oui')
   v,detail=sauver(page,panel,detail,v);expect(detail).to_contain_text('Solde IS/CM proposé à payer : 1.425,00 MAD')
  finally:browser.close()


def test_753_b12_change_cm_actualisee_avant_nouvelle_proposition_interface(application):
 from test_e2e_balance_passage_fiscal725_isole import SUMMARY as B_SUMMARY,REGION as B_REGION,sauver as sauver_b
 from test_e2e_balance_cotisation_minimale741_isole import SUMMARY as C_SUMMARY,REGION as C_REGION,sauver as sauver_cm
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);v=ok(api.post(url(v),json=body(v)),201);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   panel.get_by_text(B_SUMMARY,exact=True).click();bp=panel.get_by_role('region',name=B_REGION,exact=True)
   bp.get_by_label('Taux IS déclaré ligne 1',exact=True).fill('10');v,bp=sauver_b(page,panel,bp,v)
   panel.get_by_text(SUMMARY,exact=True).click();detail=panel.get_by_role('region',name=REGION,exact=True)
   expect(detail).to_contain_text('Proposition historique — sources modifiées')
   expect(detail).to_contain_text('Solde IS/CM proposé à payer : 1.425,00 MAD')
   v,detail=sauver(page,panel,detail,v);expect(detail).to_contain_text('Solde IS/CM proposé à payer : Indisponible')
   panel.get_by_text(C_SUMMARY,exact=True).click();cp=panel.get_by_role('region',name=C_REGION,exact=True);v,cp=sauver_cm(page,panel,cp,v)
   panel.get_by_text(SUMMARY,exact=True).click();detail=panel.get_by_role('region',name=REGION,exact=True)
   v,detail=sauver(page,panel,detail,v);expect(detail).to_contain_text('Solde IS/CM proposé à payer : 1.425,00 MAD')
   assert not ok(api.get(url(v)))['sources_is_modifiees']
  finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_753_get_reel_tardif_ignore(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__cm753Retenu=true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click();page.wait_for_function('window.__cm753Retenu===true')
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


def test_753_post_reel_tardif_ne_remplace_pas_selection(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_extra(page,application,v);pending=[]
            [saisir(detail,t) for t in body(v)['tables']];detail.get_by_role('checkbox').check()
            def retenir(route):
                if route.request.method!='POST':return route.continue_()
                rep=route.fetch();assert rep.status==201
                pending.append((route,rep));page.evaluate('window.__cm753PostRetenu=true')
            page.route('**'+url(v),retenir,times=1);detail.get_by_role('button',name=SAVE,exact=True).click()
            page.wait_for_function('window.__cm753PostRetenu===true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text(f'Version {v2["version"]} conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()


