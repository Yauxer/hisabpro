"""C3 extra : Edge réel, unités, brouillon, intégration explicite et droits."""
from contextlib import closing
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_c3_extra731_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,creer,body,url,c3_body,c3_url,BASE)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from browser_support import chromium_executable
SUMMARY='Documenter les données extra-comptables C3'
REGION='Données extra-comptables C3 de la préparation'
SAVE='Conserver les tableaux ETIC dans une nouvelle version'
C3='Consulter les indicateurs comptables C3 depuis les balances'


def ouvrir_extra(page,app,v,lecture=False):
 panel,_=ouvrir(page,app,v,lecture);panel.get_by_text(SUMMARY,exact=True).click()
 detail=panel.get_by_role('region',name=REGION,exact=True)
 expect(detail.get_by_label('Tableau ETIC à documenter',exact=True)).to_be_visible()
 return panel,detail


def saisir(detail,t):
 detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option(t['code'])
 detail.get_by_label('Déclaration du tableau',exact=True).select_option(t['statut'])
 detail.get_by_label('Justification du tableau',exact=True).fill(t['justification'])
 labels={'nature':'Désignation de la déclaration C3','effectif_moyen':'Effectif moyen déclaré',
  'benefices_distribues':'Bénéfices distribués déclarés','resultat_par_titre':'Résultat par titre déclaré',
  'distribution_par_titre':'Distribution par titre déclarée','affectations_justifiees':'Décisions et affectations à justifier',
  'reference_source':'Référence de source'}
 for i,row in enumerate(t['lignes'],1):
  detail.get_by_role('button',name='Ajouter une ligne au tableau',exact=True).click()
  for k,v in row.items():
   if v is not None:detail.get_by_label(f'{labels[k]} ligne {i}',exact=True).fill(str(v))


def sauver(page,panel,detail,v):
 detail.get_by_role('checkbox').check()
 with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
  detail.get_by_role('button',name=SAVE,exact=True).click()
 assert rep.value.status==201,rep.value.text();v=rep.value.json()
 expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible()
 panel.get_by_text(SUMMARY,exact=True).click()
 return v,panel.get_by_role('region',name=REGION,exact=True)


def actualiser_c3(page,panel,v,ancienne=True):
 panel.get_by_text(C3,exact=True).click();c=panel.get_by_role('region',name='Indicateurs C3 de la préparation',exact=True)
 if ancienne:expect(c.get_by_role('region',name='Déclarations extra-comptables C3',exact=True)).to_contain_text('Effectif moyen déclaré : Indisponible')
 c.get_by_role('checkbox').check()
 with page.expect_response(lambda r:r.url.endswith(c3_url(v)) and r.request.method=='POST') as rep:
  c.get_by_role('button',name='Conserver les indicateurs C3 dans une nouvelle version',exact=True).click()
 assert rep.value.status==201;v=rep.value.json()
 expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible()
 panel.get_by_text(C3,exact=True).click()
 return v,panel.get_by_role('region',name='Indicateurs C3 de la préparation',exact=True)


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_731_declarations_brouillon_c3_export_unites_mobile(application,role,largeur,tmp_path):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api);v=ok(api.post(c3_url(v),json=c3_body(v)),201)
  if role=='lecture':v=ok(api.post(url(v),json=body(v)),201);v=ok(api.post(c3_url(v),json=c3_body(v)),201)
  if role!='admin':
   email=email.replace('@','-'+role+'@');ok(api.post('/api/utilisateurs',json={'nom':'Extra fictif731','email':email,'mot_de_passe':password,'role':role}),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
   errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   panel,detail=ouvrir_extra(page,application,v,role=='lecture')
   if role=='lecture':
    assert detail.get_by_role('button',name=SAVE,exact=True).count()==0
    assert detail.get_by_label('Effectif moyen déclaré ligne 1',exact=True).is_disabled()
   else:
    for t in body(v)['tables']:saisir(detail,t)
    detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option('C3-N')
    detail.get_by_label('Référence de source ligne 1',exact=True).fill('SOURCE731'+'X'*300)
    v,detail=sauver(page,panel,detail,v)
    expect(panel).to_contain_text('Un complément extra-comptable C3 est conservé. Conservez une nouvelle version')
    controle=detail.get_by_role('region',name='Déclarations C3 conservées',exact=True)
    expect(controle).to_contain_text('3,50 personnes');expect(controle).to_contain_text('60,00 MAD / titre')
    detail.get_by_label('Effectif moyen déclaré ligne 1',exact=True).fill('141,25')
    expect(controle).to_contain_text('3,50 personnes')
   if role=='lecture':
    panel.get_by_text(C3,exact=True).click();c=panel.get_by_role('region',name='Indicateurs C3 de la préparation',exact=True)
   else:v,c=actualiser_c3(page,panel,v)
   extra=c.get_by_role('region',name='Déclarations extra-comptables C3',exact=True)
   expect(extra).to_contain_text('Effectif moyen déclaré : 3,50 personnes')
   expect(extra).to_contain_text('Bénéfices distribués déclarés : 2.000,00 MAD')
   expect(extra).to_contain_text('Résultat par titre déclaré : 60,00 MAD / titre')
   assert 'Informations à documenter séparément :' not in c.inner_text()
   c.get_by_label('Période des indicateurs',exact=True).select_option('n2')
   expect(extra).to_contain_text('Effectif moyen déclaré : 2,00 personnes')
   expect(c).to_contain_text('1.000,00 MAD')
   assert 'Un complément extra-comptable C3 est conservé. Conservez une nouvelle version' not in panel.inner_text()
   with page.expect_download() as rep:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   dest=tmp_path/'extra731.zip';rep.value.save_as(dest)
   with ZipFile(dest) as z:
    assert json.loads(z.read('extra_c3_documentaire.json'))['declarations_c3']['n']['effectif_moyen']=='3.50'
    assert json.loads(z.read('indicateurs_comptables_documentaires.json'))['vue']['periodes']['n']['effectif_moyen']=='3.50'
   extra.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'extra731-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and not errors and not serveur,(errors,serveur)
  finally:browser.close()


def test_731_rejet_nan_brouillon_et_declarations_comparatives_independantes(application):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=creer(api,False,False);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page();connexion(page,application['web_url'],email,password);panel,detail=ouvrir_extra(page,application,v)
   for t in body(v)['tables']:saisir(detail,t)
   detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option('C3-N')
   detail.get_by_label('Effectif moyen déclaré ligne 1',exact=True).fill('NaN');detail.get_by_role('checkbox').check()
   with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:detail.get_by_role('button',name=SAVE,exact=True).click()
   assert rep.value.status==422;expect(detail.get_by_role('alert')).to_be_visible()
   expect(detail.get_by_label('Effectif moyen déclaré ligne 1',exact=True)).to_have_value('NaN')
   detail.get_by_label('Effectif moyen déclaré ligne 1',exact=True).fill('3,50');v,detail=sauver(page,panel,detail,v)
   v,c=actualiser_c3(page,panel,v,ancienne=False)
   c.get_by_label('Période des indicateurs',exact=True).select_option('n1')
   expect(c).to_contain_text('Source détaillée absente')
   expect(c.get_by_role('region',name='Déclarations extra-comptables C3',exact=True)).to_contain_text('Effectif moyen déclaré : 3,00 personnes')
  finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_731_get_reel_tardif_ignore(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api,n2=False);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__extra731Retenu=true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text(SUMMARY,exact=True).click();page.wait_for_function('window.__extra731Retenu===true')
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


def test_731_post_reel_tardif_ne_remplace_pas_selection(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api,n2=False);v2=ok(api.post(url(v),json=body(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_extra(page,application,v);pending=[]
            saisir(detail,body(v)['tables'][0]);detail.get_by_role('checkbox').check()
            def retenir(route):
                if route.request.method!='POST':return route.continue_()
                rep=route.fetch();assert rep.status==201
                pending.append((route,rep));page.evaluate('window.__extra731PostRetenu=true')
            page.route('**'+url(v),retenir,times=1);detail.get_by_role('button',name=SAVE,exact=True).click()
            page.wait_for_function('window.__extra731PostRetenu===true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()
