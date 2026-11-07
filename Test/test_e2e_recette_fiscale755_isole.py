"""Deux parcours annuels depuis inscription UI, logo, CSV N/N-1 et six contrôles réels."""
from contextlib import closing
from uuid import uuid4
import json,hashlib
import httpx,pytest
from playwright.sync_api import sync_playwright,expect
from fiscal755_support import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,ok,BASE,donnees_metier,R,D,bodies,verifier,verifier_export)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_passage_fiscal725_isole import SUMMARY as S12,REGION as R12,saisir as saisir12,sauver as sauver12
from test_e2e_balance_cotisation_minimale741_isole import SUMMARY as SCM,REGION as RCM,saisir as saisircm,sauver as sauvercm
from test_e2e_balance_css743_isole import SUMMARY as SCSS,REGION as RCSS,saisir as saisircss,sauver as sauvercss
from test_e2e_balance_credits749_isole import SUMMARY as SCR,REGION as RCR,saisir as saisircr,sauver as sauvercr
from test_e2e_balance_acomptes751_isole import SUMMARY as SAP,REGION as RAP,saisir as saisirap,sauver as sauverap
from test_e2e_balance_liquidation753_isole import SUMMARY as SL,REGION as RL,saisir as saisirl,sauver as sauverl
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390)])
def test_755_inscription_logo_csv_b12_cm_css_credits_acomptes_solde_exports(application,role,largeur,tmp_path):
 c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
 email=f'fiscal755-{uuid4().hex[:12]}@example.com';password='Recette755!Local2026'
 with httpx.Client(base_url=application['api_url'],timeout=30) as api,sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(12000)
   errors,serveur=observer(page,application['api_url']);page.goto(application['web_url'])
   page.get_by_role('button',name='Créer un compte',exact=True).click()
   page.get_by_placeholder('Prénom NOM',exact=True).fill('Admin recette fiscale755')
   page.get_by_placeholder('Ma Société SARL',exact=True).fill(D['societe_fictive']+' '+role)
   page.get_by_placeholder('Casablanca',exact=True).fill('Casablanca')
   page.get_by_placeholder('admin@societe.ma',exact=True).fill(email);page.get_by_placeholder('••••••••',exact=True).fill(password)
   with page.expect_response(lambda r:r.url.endswith('/api/auth/register') and r.request.method=='POST') as rep:page.get_by_role('button',name='Créer mon compte',exact=True).click()
   assert rep.value.status==200,rep.value.text();page.wait_for_function('Boolean(localStorage.getItem("hisabpro_token"))')
   api.headers['Authorization']='Bearer '+page.evaluate('localStorage.getItem("hisabpro_token")')
   assert ok(api.get(BASE,params={'exercice':2026}))==[]
   page.goto(application['web_url']+'/parametres')
   page.get_by_label('Logo de la société',exact=True).set_input_files(str(R/'docs/recette/LOGO_FICTIF755.png'))
   expect(page.get_by_alt_text('Aperçu du logo de la société',exact=True)).to_be_visible()
   with page.expect_response(lambda r:r.url.endswith('/api/societe/moi') and r.request.method=='PATCH') as logo:page.get_by_role('button',name='Enregistrer',exact=True).click()
   assert logo.value.status==200 and ok(api.get('/api/societe/moi'))['logo_url'].startswith('data:image/png;base64,')
   if role=='comptable':
    user=email.replace('@','-comptable@');ok(api.post('/api/utilisateurs',json={'nom':'Comptable recette755','email':user,'mot_de_passe':password,'role':'comptable'}),201)
    page.evaluate('localStorage.clear()');connexion(page,application['web_url'],user,password)
   page.goto(application['web_url']+'/liasse-fiscale')
   panel=page.locator('section').filter(has=page.get_by_role('heading',name='Préparer depuis des balances externes',exact=True))
   panel.get_by_role('button',name='Importer N / N-1',exact=True).click();avant=donnees_metier(application)
   panel.get_by_label('Balance N',exact=True).set_input_files(str(R/'docs/recette/BALANCE_FICTIVE_FISCALE755_N.csv'))
   panel.get_by_label('Balance N-1 facultative',exact=True).set_input_files(str(R/'docs/recette/BALANCE_FICTIVE_FISCALE755_N1.csv'))
   panel.get_by_role('button',name='Contrôler et préparer',exact=True).click()
   expect(panel.get_by_text('Balances contrôlées — préparation à compléter. Aucune écriture créée.',exact=True)).to_be_visible()
   with page.expect_response(lambda r:r.url.endswith(BASE) and r.request.method=='POST') as saved:panel.get_by_role('button',name='Conserver une nouvelle version',exact=True).click()
   assert saved.value.status==201,saved.value.text();v=saved.value.json();premiere=v
   expect(panel.get_by_text('Version 1 conservée',exact=False)).to_be_visible()
   for cle,summary,region,saisir,sauver in [('b12',S12,R12,saisir12,sauver12),('cm',SCM,RCM,saisircm,sauvercm),('css',SCSS,RCSS,saisircss,sauvercss),('credits',SCR,RCR,saisircr,sauvercr),('acomptes',SAP,RAP,saisirap,sauverap),('liquidation',SL,RL,saisirl,sauverl)]:
    panel.get_by_text(summary,exact=True).click();detail=panel.get_by_role('region',name=region,exact=True)
    for table in bodies(v)[cle]['tables']:saisir(detail,table)
    v,detail=sauver(page,panel,detail,v)
   verifier(v);assert v['version']==7
   expect(detail).to_contain_text('Solde IS/CM proposé à payer : 3.650,00 MAD')
   expect(detail).to_contain_text('Acomptes justifiés proposés : 20.000,00 MAD')
   expect(detail).to_contain_text('Crédits qualifiés disponibles après utilisations antérieures : 350,00 MAD')
   expect(detail).to_contain_text('CSS proposée séparément dans sa qualification conservée : 0,00 MAD')
   with page.expect_download() as rep:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   raw=rep.value.path().read_bytes();export=verifier_export(raw,v)
   (tmp_path/'dossier755.zip').write_bytes(raw)
   apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
   assert ok(api.get(BASE+f'/{premiere["id"]}'))==premiere
   ctrl=detail.get_by_role('region',name='Contrôles de la proposition IS CM',exact=True);ctrl.scroll_into_view_if_needed()
   page.screenshot(path=str(R/f'.codex-tests/fiscal755-{role}-{largeur}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and not errors and not serveur,(errors,serveur)
   (R/f'.codex-tests/fiscal755_{role}_preuve.json').write_text(json.dumps({'role':role,'largeur':largeur,'inscription_et_logo_reels_ui':True,'csv_n_n1_reels_ui':True,'six_controles_reels_ui':True,
    'versions':v['version'],'solde_is_propose':'3650.00','aucune_ecriture_ou_liquidation_confirmee':True,'hors_preparations_inchange':True,'premiere_version_preservee':True,'export':export,'erreurs_navigateur':errors,'erreurs_serveur':serveur},ensure_ascii=False,indent=2),encoding='utf-8')
  finally:browser.close()
