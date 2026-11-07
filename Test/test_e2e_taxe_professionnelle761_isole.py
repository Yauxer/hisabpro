"""Tiers759 : formulaires réels, trois rôles, mobile, erreurs et réponses tardives."""
from contextlib import closing
from pathlib import Path
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from tp761_support import *
from test_taxe_professionnelle761_isole import verifier_export
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from test_e2e_session401739_isole import client_http
from test_logo_societe import image_data
from browser_support import chromium_executable
SUMMARY='Préparer la taxe professionnelle'
REGION='Taxe professionnelle de la préparation'
SAVE='Conserver la préparation TP dans une nouvelle version'
SELECTION='Rubrique TP à documenter'
ROOT=Path(__file__).resolve().parents[1]
LABELS={'nature':{'TP-P':'Désignation du dossier TP','TP-E':'Désignation de l’établissement'},'annee_tp':'Année civile TP déclarée','periode_revue':'Période fiscale revue','exhaustivite':'Liste des établissements exhaustive revue','referentiel_revu':'Référentiel applicable revu sur pièces','etablissement_ref':'Identifiant interne de l’établissement','commune':'Commune déclarée','adresse':'Adresse de l’établissement','activite':'Activité principale déclarée','classe':'Classe déclarée et justifiée','valeur_locative':'Valeur locative annuelle fournie','base_revue':'Base annuelle complète revue','classe_revue':'Classe revue sur référence','regime':'Périmètre déclaré de l’établissement','situation_janvier_revue':'Situation au premier janvier revue','montant_avis':'Montant de l’avis fourni','reference_avis':'Référence de l’avis fourni','avis_rattache':'Avis rattaché à l’année TP déclaré','reference_source':'Référence de source'}
CHOIX={'periode_revue','exhaustivite','referentiel_revu','classe','base_revue','classe_revue','regime','situation_janvier_revue','avis_rattache'}
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
def test_761_formulaire_natif_roles_versions_exports(application,role,largeur,tmp_path):
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
    assert detail.get_by_label('Désignation du dossier TP ligne 1',exact=True).is_disabled()
   else:remplir(detail,body(v));v,detail=sauver(page,panel,detail,v)
   verifier(v);ctrl=detail.get_by_role('region',name='Contrôles de préparation TP',exact=True)
   expect(ctrl).to_contain_text('Brut simulé après revue documentaire déclarée : 7.200,00 MAD')
   expect(ctrl).to_contain_text('Avis saisis et rattachés explicitement : 7.400,00 MAD');expect(ctrl).to_contain_text('Écart brut simulé moins avis déclarés : -200,00 MAD')
   expect(ctrl).to_contain_text('Revue documentaire déclarée')
   if role!='lecture':
    detail.get_by_label(SELECTION,exact=True).select_option('TP-E');detail.get_by_label('Valeur locative annuelle fournie ligne 1',exact=True).fill('999')
    expect(ctrl).to_contain_text('7.200,00 MAD')
   with page.expect_download() as rep:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   dest=tmp_path/'tp761.zip';rep.value.save_as(dest);proof=verifier_export(dest.read_bytes(),v)
   ctrl.scroll_into_view_if_needed();page.screenshot(path=str(ROOT/f'.codex-tests/tp761-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and not errors and not serveur,(errors,serveur)
   apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
   if role=='lecture':assert apres==avant
   (ROOT/f'.codex-tests/tp761_{role}_preuve.json').write_text(json.dumps({'role':role,'largeur':largeur,'formulaire_reel':True,'totaux':controles(v)['montants'],'export':proof,'aucune_ecriture':True},ensure_ascii=False,indent=2),encoding='utf8')
  finally:browser.close()

@pytest.mark.parametrize('montant_invalide',['NaN','Infinity'])
def test_761_nan_refuse_base_incomplete_puis_reprise_sans_f5(application,montant_invalide):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   b=body(v);b['tables'][1]['lignes'][0]['base_revue']='';remplir(detail,b)
   champ=detail.get_by_label('Valeur locative annuelle fournie ligne 1',exact=True);champ.fill(montant_invalide);detail.get_by_role('checkbox').check();avant=donnees_metier(application)
   with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:detail.get_by_role('button',name=SAVE,exact=True).click()
   assert rep.value.status==422;expect(detail.get_by_role('alert')).to_be_visible();expect(champ).to_have_value(montant_invalide);assert donnees_metier(application)==avant
   champ.fill('30000');v,detail=sauver(page,panel,detail,v)
   ctrl=detail.get_by_role('region',name='Contrôles de préparation TP',exact=True);expect(ctrl).to_contain_text('Préparation TP à compléter ou à qualifier');expect(ctrl).to_contain_text('Brut simulé après revue documentaire déclarée : Indisponible')
   detail.get_by_label(SELECTION,exact=True).select_option('TP-E');detail.get_by_label('Base annuelle complète revue ligne 1',exact=True).select_option('oui')
   v,detail=sauver(page,panel,detail,v);verifier(v);expect(detail.get_by_role('region',name='Contrôles de préparation TP',exact=True)).to_contain_text('Revue documentaire déclarée')
  finally:browser.close()

@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_761_get_reel_tardif_ignore(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__tp761Retenu=true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click();page.wait_for_function('window.__tp761Retenu===true')
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


def test_761_post_reel_tardif_ne_remplace_pas_selection(application):
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
                pending.append((route,rep));page.evaluate('window.__tp761PostRetenu=true')
            page.route('**'+url(v),retenir,times=1);detail.get_by_role('button',name=SAVE,exact=True).click()
            page.wait_for_function('window.__tp761PostRetenu===true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text(f'Version {v2["version"]} conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()


