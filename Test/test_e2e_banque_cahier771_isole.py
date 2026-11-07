"""HP-ADM-005 : nom de banque fictif saisi réellement au clavier, aucun serveur réel."""
from pathlib import Path
from uuid import uuid4
from contextlib import closing
import json
import httpx,pytest
from playwright.sync_api import sync_playwright,expect
from sqlalchemy import text
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion,observer
from test_e2e_facturation_isole import application,champ
ROOT=Path(__file__).resolve().parents[1]

def ok(r,status=200):
 code=r.status_code if isinstance(r,httpx.Response) else r.status
 assert code==status,(r.text if isinstance(r,httpx.Response) else r.text())
 return r.json()

@pytest.mark.parametrize('largeur',[1440,390])
def test_771_banque_cahier_nom_libre_creation_reouverture_et_edition(application,largeur,tmp_path):
 c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
 data=json.loads((ROOT/'docs/recette/jeu_donnees_recette.json').read_text(encoding='utf8'));s=data['societe'];b=data['banque']
 email=f'banque771-{uuid4().hex[:8]}@hisabpro-recette.example';password=s['password_test']
 with httpx.Client(base_url=application['api_url']) as api,sync_playwright() as p:
  auth=ok(api.post('/api/auth/register',json={'nom':s['nom_admin'],'email':email,'password':password,'raison_sociale':s['raison_sociale']}));api.headers['Authorization']='Bearer '+auth['access_token'];sid=ok(api.get('/api/societe/moi'))['id']
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
  erreurs,serveur=observer(page,application['api_url'])
  try:
   connexion(page,application['web_url'],email,password)
   page.goto(application['web_url']+'/parametres',wait_until='domcontentloaded');page.get_by_role('button',name='Comptes bancaires',exact=True).click()
   page.get_by_role('button',name='Ajouter un compte',exact=True).click();champ(page,'Banque *','select').select_option('Autre')
   nom=page.get_by_placeholder('Nom de la banque...',exact=True);nom.press_sequentially(b['banque'])
   expect(nom).to_be_visible();expect(nom).to_have_value(b['banque'])
   # Le libellé de choix Autre ne doit pas devenir un nom de banque implicite.
   nom.fill('');expect(page.get_by_role('button',name='Créer',exact=True)).to_be_disabled();nom.press_sequentially(b['banque'])
   champ(page,'RIB').fill(b['rib']);champ(page,'Compte CGNC','select').select_option(b['compte_comptable'])
   with page.expect_response(lambda r:r.url.endswith('/api/banques') and r.request.method=='POST') as response:page.get_by_role('button',name='Créer',exact=True).click()
   record=ok(response.value,201);assert record['banque']==b['banque'] and record['rib']==b['rib'] and record['compte_comptable']=='5141' and record['devise']=='MAD'
   expect(page.get_by_text(b['banque'],exact=True)).to_be_visible()
   def ouvrir():page.locator('button').filter(has=page.locator('i.ti-pencil')).click()
   ouvrir();expect(champ(page,'Banque *','select')).to_have_value('Autre');expect(nom).to_have_value(b['banque']);expect(champ(page,'RIB')).to_have_value(b['rib'])
   champ(page,'Agence').fill('Agence fictive Recette')
   with page.expect_response(lambda r:r.url.endswith(f'/api/banques/{record["id"]}') and r.request.method=='PATCH') as response:page.get_by_role('button',name='Modifier',exact=True).click()
   record=ok(response.value);assert record['banque']==b['banque'] and record['agence']=='Agence fictive Recette'
   page.reload(wait_until='domcontentloaded');page.get_by_role('button',name='Comptes bancaires',exact=True).click();ouvrir();expect(nom).to_have_value(b['banque']);expect(champ(page,'Agence')).to_have_value('Agence fictive Recette')
   # Même formulaire : le choix prédéfini reste disponible et persistant.
   champ(page,'Banque *','select').select_option('Attijariwafa Bank');expect(nom).to_have_count(0)
   with page.expect_response(lambda r:r.url.endswith(f'/api/banques/{record["id"]}') and r.request.method=='PATCH') as response:page.get_by_role('button',name='Modifier',exact=True).click()
   assert ok(response.value)['banque']=='Attijariwafa Bank'
   ouvrir();expect(champ(page,'Banque *','select')).to_have_value('Attijariwafa Bank');champ(page,'Banque *','select').select_option('Autre');nom.press_sequentially(b['banque'])
   with page.expect_response(lambda r:r.url.endswith(f'/api/banques/{record["id"]}') and r.request.method=='PATCH') as response:page.get_by_role('button',name='Modifier',exact=True).click()
   assert ok(response.value)['banque']==b['banque']
   banques=ok(api.get('/api/banques'));assert len(banques)==1 and banques[0]['rib']==b['rib']
   with application['engine'].connect() as db:assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid'),{'sid':sid})==0
   assert not erreurs and not serveur,(erreurs,serveur)
   page.screenshot(path=str(ROOT/f'.codex-tests/banque771_{largeur}.png'),full_page=True)
  except BaseException:
   print('NAVIGATEUR',erreurs,serveur,page.locator('body').inner_text()[-3000:]);page.screenshot(path=str(tmp_path/'banque771_echec.png'),full_page=True);raise
  finally:browser.close()
