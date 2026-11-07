"""CM qualifiée : vraie API, Edge, droits, versions et retards natifs."""
from contextlib import closing
from pathlib import Path
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_acomptes751_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,creer,body,url,BASE,donnees_metier)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from browser_support import chromium_executable
from test_logo_societe import image_data
from exports_qualification941_support import verifier_exports
SUMMARY='Qualifier les acomptes IS — 2026'
REGION='Acomptes IS de la préparation'
SAVE='Conserver les acomptes IS dans une nouvelle version'
SELECTION='Qualification acomptes à documenter'
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
 labels={'nature':'Désignation du profil acomptes' if t['code']=='AP-PROFIL' else 'Désignation du mouvement acompte',
  'regime':'Périmètre IS des acomptes','mode':'Régime de versements déclaré','reference_annuelle':'Référence annuelle ajustée2026 justifiée',
  'reference_qualifiee':'Référence annuelle fiscalement qualifiée','exercice_reference':'Exercice de référence déclaré',
  'dernier_clos_confirme':'Dernier exercice clos confirmé','excedent_anterieur_disponible':'Excédent antérieur disponible avant acomptes',
  'origine_excedent':'Exercice d’origine de l’excédent170-IV','excedent_qualifie':'Excédent170-IV et solde disponible qualifiés',
  'exhaustivite':'Mouvements et affectations exhaustifs','absence_mouvements':'Absence de tout mouvement confirmée','date_controle':'Date de contrôle déclarée',
  'numero':'Numéro de l’acompte','date_mouvement':'Date du mouvement justifiée','verse':'Versement effectif','credit_anterieur':'Excédent antérieur affecté',
  'retenue':'Retenue affectée','reference_credit':'Référence exacte du justificatif crédit','rattachement_confirme':'Rattachement et justificatif confirmés','reference_source':'Référence de source'}
 for i,row in enumerate(t['lignes'],1):
  detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
  for k,v in row.items():
   if v is not None and v != '':
    el=detail.get_by_label(f'{labels[k]} ligne {i}',exact=True)
    if k in ('regime','mode','reference_qualifiee','dernier_clos_confirme','excedent_qualifie','exhaustivite','absence_mouvements','numero','rattachement_confirme'):el.select_option(v)
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
def test_751_acomptes_droits_exports_brouillon_mobile(application,role,largeur,tmp_path):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
  if role=='lecture':v=ok(api.post(url(v),json=body(v)),201)
  if role!='admin':
   email=email.replace('@','-'+role+'@');ok(api.post('/api/utilisateurs',json={'nom':'Acomptes fictifs751','email':email,'mot_de_passe':password,'role':role}),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
   errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   panel,detail=ouvrir_extra(page,application,v,role=='lecture');avant=donnees_metier(application)
   if role=='lecture':
    assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
    detail.get_by_label(SELECTION,exact=True).select_option('AP-LIGNES')
    assert detail.get_by_label('Versement effectif ligne 1',exact=True).is_disabled()
   else:
    for table in body(v)['tables']:saisir(detail,table)
    detail.get_by_label('Référence de source ligne 1',exact=True).fill('NOTE751'+'X'*300)
    v,detail=sauver(page,panel,detail,v)
   ctrl=detail.get_by_role('region',name='Contrôles acomptes IS conservés',exact=True)
   expect(ctrl).to_contain_text('Versements effectifs déclarés : 1.000,00 MAD')
   expect(ctrl).to_contain_text('Acomptes imputables proposés après qualifications : 1.250,00 MAD')
   expect(ctrl).to_contain_text('Retenues affectées aux acomptes : 150,00 MAD')
   expect(ctrl.get_by_role('region',name='Échéancier déclaré des acomptes IS')).to_contain_text('Reste : 3.800,00 MAD · Partiel — en retard')
   if role!='lecture':
    detail.get_by_label(SELECTION,exact=True).select_option('AP-LIGNES')
    detail.get_by_label('Versement effectif ligne 1',exact=True).fill('0')
    expect(ctrl).to_contain_text('Acomptes imputables proposés après qualifications : 1.250,00 MAD')
   with page.expect_download() as rep:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   dest=tmp_path/'acomptes751.zip';rep.value.save_as(dest)
   with ZipFile(dest) as z:
    c=json.loads(z.read('acomptes_is_documentaires.json'))['controle_acomptes']
    assert c['montants']['acomptes_proposes']=='1250.00' and c['solde_final'] is None and not c['paiement_confirme']
   directs=verifier_exports(page,panel,'Contrôle acomptes IS','Acomptes imputables proposés après qualifications',1250,'1 250,00')
   ctrl.scroll_into_view_if_needed();page.screenshot(path=str(ROOT/f'.codex-tests/acomptes751-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and not errors and not serveur,(errors,serveur)
   apres=donnees_metier(application);assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')
   if role=='lecture':assert apres==avant
   (ROOT/f'.codex-tests/is941_ap_{role}.json').write_text(json.dumps({'role':role,'largeur':largeur,'acomptes_proposes':'1250.00','exports_individuels':directs,'ZIP_snapshot_verifie':True,'sources_hors_preparations_inchangees':True},ensure_ascii=False,indent=2),encoding='utf8')
  finally:browser.close()


def test_751_nan_refuse_puis_reference_credit_corrigee_sans_f5(application):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   for table in body(v)['tables']:saisir(detail,table)
   detail.get_by_label('Versement effectif ligne 1',exact=True).fill('NaN');detail.get_by_role('checkbox').check()
   avant=donnees_metier(application)
   with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:detail.get_by_role('button',name=SAVE,exact=True).click()
   assert rep.value.status==422;expect(detail.get_by_role('alert')).to_be_visible()
   expect(detail.get_by_label('Versement effectif ligne 1',exact=True)).to_have_value('NaN');assert donnees_metier(application)==avant
   detail.get_by_label('Versement effectif ligne 1',exact=True).fill('1000')
   detail.get_by_label('Référence exacte du justificatif crédit ligne 1',exact=True).fill('CR749-B')
   v,detail=sauver(page,panel,detail,v)
   expect(detail).to_contain_text('Acomptes imputables proposés après qualifications : Indisponible')
   expect(detail).to_contain_text('Écart retenues affectées moins déjà utilisées côté crédits : 0,00 MAD')
   detail.get_by_label(SELECTION,exact=True).select_option('AP-LIGNES');detail.get_by_label('Référence exacte du justificatif crédit ligne 1',exact=True).fill('CR749-A')
   v,detail=sauver(page,panel,detail,v)
   expect(detail).to_contain_text('Acomptes imputables proposés après qualifications : 1.250,00 MAD')
  finally:browser.close()


def test_751_credits_changes_actualisation_explicite_interface(application):
 from test_e2e_balance_credits749_isole import SUMMARY as CR_SUMMARY,REGION as CR_REGION,sauver as sauver_cr,SELECTION as CR_SELECTION
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);v=ok(api.post(url(v),json=body(v)),201);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   panel.get_by_text(CR_SUMMARY,exact=True).click();cr=panel.get_by_role('region',name=CR_REGION,exact=True)
   cr.get_by_label(CR_SELECTION,exact=True).select_option('CR-LIGNES');cr.get_by_label('Montant total du justificatif ligne 1',exact=True).fill('301')
   v,cr=sauver_cr(page,panel,cr,v)
   panel.get_by_text(SUMMARY,exact=True).click();detail=panel.get_by_role('region',name=REGION,exact=True)
   expect(detail).to_contain_text('Les crédits qualifiés ont changé : contrôle acomptes conservé pour mémoire')
   expect(detail).to_contain_text('Acomptes imputables proposés après qualifications : 1.250,00 MAD')
   v,detail=sauver(page,panel,detail,v)
   assert not ok(api.get(url(v)))['source_credits_modifiee']
  finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_751_get_reel_tardif_ignore(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__cm751Retenu=true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click();page.wait_for_function('window.__cm751Retenu===true')
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


def test_751_post_reel_tardif_ne_remplace_pas_selection(application):
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
                pending.append((route,rep));page.evaluate('window.__cm751PostRetenu=true')
            page.route('**'+url(v),retenir,times=1);detail.get_by_role('button',name=SAVE,exact=True).click()
            page.wait_for_function('window.__cm751PostRetenu===true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text(f'Version {v2["version"]} conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()


