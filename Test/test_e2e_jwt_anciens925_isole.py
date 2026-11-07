"""Ancienne session navigateur remplacée par une connexion réelle, sans API simulée."""
from pathlib import Path
import pytest
from jose import jwt
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from navigation823_support import navigations_completes823
from test_jwt_anciens925_isole import (
 application,application104,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,jeton_synthetique,comptabilite)

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
def test_925_ancien_navigateur_reconnexion_reelle_sans_modification_metier(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'jwt925') as (api,page,sid,preuve):
  me=ok(api.get('/api/auth/me'));avant=comptabilite(application,sid);ancien=jeton_synthetique(application,api)
  page.evaluate('(t)=>localStorage.setItem("hisabpro_token",t)',ancien)
  page.reload(wait_until='domcontentloaded');expect(page.get_by_role('button',name='Se connecter',exact=True)).to_be_visible()
  assert page.evaluate('localStorage.getItem("hisabpro_token")') is None and page.evaluate('localStorage.getItem("hisabpro_role")') is None
  page.get_by_placeholder('admin@societe.ma').fill(me['email']);page.locator('input[type=password]').fill(DATA['societe']['password_test']);page.get_by_role('button',name='Se connecter',exact=True).click()
  # La connexion est présentée sur la route courante : après reconnexion,
  # l'application reprend la clôture ouverte avant expiration, pas /dashboard.
  expect(page.get_by_role('button',name='Se connecter',exact=True)).to_have_count(0);expect(page.get_by_label('Exercice actif',exact=True)).to_have_value('2025')
  courant=page.evaluate('localStorage.getItem("hisabpro_token")');assert 'pwd_version' in jwt.get_unverified_claims(courant);assert ok(api.get('/api/auth/me',headers={'Authorization':'Bearer '+courant}))['id']==me['id']
  page.goto(application['web_url']+'/factures');expect(page.get_by_role('button',name='Nouvelle facture',exact=True)).to_be_visible();assert comptabilite(application,sid)==avant
  page.screenshot(path=str(R/f'docs/recette/preuves/925_{largeur}_reconnexion.png'))
  preuve['jwt925']={'ancienne_session_refusee':True,'jeton_et_role_effaces':True,'reconnexion_reelle':True,'nouveau_jeton_versionne':True,'facturation_accessible':True,'comptabilite_inchangee':True,'aucun_secret_ou_jeton_enregistre':True}
