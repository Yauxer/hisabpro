"""Tiers759 : formulaires réels, trois rôles, mobile, erreurs et réponses tardives."""
from contextlib import closing
from pathlib import Path
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from tiers759_support import *
from test_remunerations_tiers759_isole import verifier_export
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from test_e2e_session401739_isole import client_http
from test_logo_societe import image_data
from browser_support import chromium_executable
SUMMARY='Préparer les rémunérations des tiers'
REGION='Rémunérations des tiers de la préparation'
SAVE='Conserver les rémunérations des tiers dans une nouvelle version'
SELECTION='Rubrique tiers à documenter'
ROOT=Path(__file__).resolve().parents[1]
LABELS={'nature':{'T151-P':'Désignation du dossier tiers','T151-B':'Nom ou raison sociale du bénéficiaire','T151-M':'Désignation du mouvement tiers'},'periode_confirmee':'Période comptable vérifiée','exhaustivite':'Exhaustivité des sources revue','absence':'Absence de rémunérations confirmée','beneficiaire_ref':{'T151-B':'Identifiant interne du bénéficiaire','T151-M':'Bénéficiaire du mouvement'},'adresse':'Adresse du bénéficiaire','activite':'Profession ou activité du bénéficiaire','identifiant_fiscal':'Identification fiscale du bénéficiaire','identification_tp':'Identification taxe professionnelle','cnss':'CNSS du bénéficiaire','regime':'Régime déclaré du bénéficiaire','identite_revue':'Identité revue sur pièces','categorie':'Catégorie déclarée de rémunération','sens':'Sens documentaire du mouvement','date_comptabilisation':'Date comptable source','comptabilise':'Somme comptabilisée','evenement':'Événement fiscal déclaré','date_evenement':'Date de cet événement justifiée','soumis':'Somme soumise à retenue','retenu':'Montant retenu','reference_origine':'Référence du mouvement corrigé','source_revue':'Source du mouvement revue','reference_source':'Référence de source'}
CHOIX={'periode_confirmee','exhaustivite','absence','regime','identite_revue','categorie','sens','evenement','source_revue'}
def ouvrir_extra(page,app,v,lecture=False):
 panel,_=ouvrir(page,app,v,lecture);panel.get_by_text(SUMMARY,exact=True).click();detail=panel.get_by_role('region',name=REGION,exact=True)
 expect(detail.get_by_label(SELECTION,exact=True)).to_be_visible();return panel,detail

def saisir(detail,t):
 detail.get_by_label(SELECTION,exact=True).select_option(t['code'])
 detail.get_by_label('Déclaration du tableau',exact=True).select_option(t['statut']);detail.get_by_label('Justification du tableau',exact=True).fill(t['justification'])
 for i,row in enumerate(t['lignes'],1):
  detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
  for k,v in row.items():
   if v is not None:
    label=LABELS[k][t['code']] if isinstance(LABELS[k],dict) else LABELS[k]
    el=detail.get_by_label(f'{label} ligne {i}',exact=True)
    if k in CHOIX:el.select_option(v)
    else:el.fill(str(v))

def remplir(detail,b):
 for t in b['tables']:saisir(detail,t)

def sauver(page,panel,detail,v):
 detail.get_by_role('checkbox').check()
 with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:detail.get_by_role('button',name=SAVE,exact=True).click()
 assert rep.value.status==201,rep.value.text();v=rep.value.json()
 expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible();panel.get_by_text(SUMMARY,exact=True).click()
 return v,panel.get_by_role('region',name=REGION,exact=True)

@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_759_formulaire_natif_roles_versions_exports(application,role,largeur,tmp_path):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
  if role=='lecture':v=ok(api.post(url(v),json=body(v)),201)
  if role!='admin':
   email=email.replace('@','-'+role+'@');ok(api.post('/api/utilisateurs',json={'nom':'Tiers fictif759','email':email,'mot_de_passe':password,'role':role}),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
   errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   panel,detail=ouvrir_extra(page,application,v,role=='lecture');avant=donnees_metier(application)
   if role=='lecture':
    assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
    assert detail.get_by_label('Désignation du dossier tiers ligne 1',exact=True).is_disabled()
   else:remplir(detail,body(v));v,detail=sauver(page,panel,detail,v)
   verifier(v);ctrl=detail.get_by_role('region',name='Contrôles de préparation des tiers',exact=True)
   expect(ctrl).to_contain_text('Sommes comptabilisées nettes déclarées : 1.400,00 MAD')
   expect(ctrl).to_contain_text('Sommes soumises nettes déclarées : 740,00 MAD');expect(ctrl).to_contain_text('Retenues nettes déclarées : 37,00 MAD')
   expect(ctrl).to_contain_text('Revue documentaire déclarée')
   if role!='lecture':
    detail.get_by_label(SELECTION,exact=True).select_option('T151-M');detail.get_by_label('Somme comptabilisée ligne 1',exact=True).fill('999')
    expect(ctrl).to_contain_text('1.400,00 MAD')
   with page.expect_download() as rep:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   dest=tmp_path/'tiers759.zip';rep.value.save_as(dest);proof=verifier_export(dest.read_bytes(),v)
   ctrl.scroll_into_view_if_needed();page.screenshot(path=str(ROOT/f'.codex-tests/tiers759-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and not errors and not serveur,(errors,serveur)
   apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
   if role=='lecture':assert apres==avant
   (ROOT/f'.codex-tests/tiers759_{role}_preuve.json').write_text(json.dumps({'role':role,'largeur':largeur,'formulaire_reel':True,'totaux':controles(v)['montants'],'export':proof,'aucune_ecriture':True},ensure_ascii=False,indent=2),encoding='utf8')
  finally:browser.close()

@pytest.mark.parametrize('montant_invalide',['NaN','Infinity'])
def test_759_nan_refuse_identite_incomplete_puis_reprise_sans_f5(application,montant_invalide):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   b=body(v);b['tables'][1]['lignes'][0]['cnss']='';remplir(detail,b)
   champ=detail.get_by_label('Somme comptabilisée ligne 1',exact=True);champ.fill(montant_invalide);detail.get_by_role('checkbox').check();avant=donnees_metier(application)
   with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:detail.get_by_role('button',name=SAVE,exact=True).click()
   assert rep.value.status==422;expect(detail.get_by_role('alert')).to_be_visible();expect(champ).to_have_value(montant_invalide);assert donnees_metier(application)==avant
   champ.fill('1000');v,detail=sauver(page,panel,detail,v)
   ctrl=detail.get_by_role('region',name='Contrôles de préparation des tiers',exact=True);expect(ctrl).to_contain_text('Préparation à compléter ou à qualifier');expect(ctrl).to_contain_text('1.400,00 MAD')
   detail.get_by_label(SELECTION,exact=True).select_option('T151-B');detail.get_by_label('CNSS du bénéficiaire ligne 1',exact=True).fill('CNSS-FICTIF759-A')
   v,detail=sauver(page,panel,detail,v);verifier(v);expect(detail.get_by_role('region',name='Contrôles de préparation des tiers',exact=True)).to_contain_text('Revue documentaire déclarée')
  finally:browser.close()

@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_759_get_reel_tardif_ignore(application,action):
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


def test_759_post_reel_tardif_ne_remplace_pas_selection(application):
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


