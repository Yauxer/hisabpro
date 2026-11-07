"""NEG023 : liens bancaires un-à-un, remplacement explicitement dépointé."""
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)
DATES={'date_debut':'2025-01-01','date_fin':'2025-12-31'}
def situation849(api):return ok(api.get('/api/rapprochement/5141/situation',params=DATES))
@pytest.mark.parametrize('largeur',[1440,390])
def test_849_remplacement_lien_et_double_utilisation(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'pointage849') as (api,page,sid,preuve):
  b=DATA['banque'];ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201);lignes=[]
  for ref in ['CAP-01','TEMOIN-849']:
   e=ok(api.post('/api/ecritures',json={'date':'2025-01-01','date_piece':'2025-01-01','journal':'BQ','reference':ref,'libelle':'Témoin fictif pointage849','lignes':[{'compte':'5141','debit':100000},{'compte':'1111','credit':100000}]}),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'));lignes.append(next(l['id'] for l in e['lignes'] if l['compte']=='5141'))
  imp=ok(api.post('/api/rapprochement/import',json={'compte':'5141','lignes':[{'date':'2025-01-01','libelle':ref,'sens':'credit','montant':100000} for ref in ['CAP-01','SECOND-849']]}),201);rl=imp['lignes'];a=next(l for l in rl if l['libelle']=='CAP-01');b=next(l for l in rl if l['libelle']=='SECOND-849');initial=core(application,sid)
  page.goto(application['web_url']+'/rapprochement');row=lambda ref:page.locator('tbody tr').filter(has_text=ref).filter(has=page.locator('select'))
  with page.expect_response(lambda r:r.url.endswith(f'/api/rapprochement/{a["id"]}/rapprocher') and r.request.method=='POST') as rr:row('CAP-01').locator('select').select_option(str(lignes[0]))
  ok(rr.value);avant=situation849(api)
  with page.expect_response(lambda r:r.url.endswith(f'/api/rapprochement/{a["id"]}/rapprocher') and r.request.method=='POST') as rr:row('CAP-01').locator('select').select_option(str(lignes[1]))
  assert rr.value.status==409;expect(page.get_by_text('Dérapprochez',exact=False)).to_be_visible();assert situation849(api)==avant and core(application,sid)==initial
  r=api.post(f'/api/rapprochement/{b["id"]}/rapprocher',json={'ecriture_ligne_id':lignes[0]});assert r.status_code==409 and 'déjà rapprochée' in r.json()['detail'];assert situation849(api)==avant
  # Le chemin explicite reste possible et met à jour uniquement les liens.
  with page.expect_response(lambda r:r.url.endswith(f'/api/rapprochement/{a["id"]}/derapprocher') and r.request.method=='POST') as rr:row('CAP-01').locator('select').select_option('')
  ok(rr.value)
  with page.expect_response(lambda r:r.url.endswith(f'/api/rapprochement/{a["id"]}/rapprocher') and r.request.method=='POST') as rr:row('CAP-01').locator('select').select_option(str(lignes[1]))
  ok(rr.value);page.reload(wait_until='domcontentloaded');expect(row('CAP-01').locator('select')).to_have_value(str(lignes[1]));fin=situation849(api);assert next(l for l in fin['lignes_releve'] if l['id']==a['id'])['ecriture_ligne_id']==lignes[1] and core(application,sid)==initial
  preuve['pointage849']={'remplacement_direct_refuse':409,'double_utilisation_refusee':409,'etats_conserves_apres_refus':True,'depointage_repointage_explicite':True,'journal_conserve':True};preuve['cas'].append({'id':'HP-NEG-023','statut':'Réussi'})
