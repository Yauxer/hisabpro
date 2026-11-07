"""112 navigations financières réelles, conservation comptable et diagnostic sans retry."""
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,ok
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_integrite839_isole import navigation_observee839
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_841_navigations_financieres_sans_retry(application,largeur,tmp_path,navigation_observee839):
 with laboratoire(application,largeur,tmp_path,'navigation841') as (api,page,sid,preuve):
  e=ok(api.post('/api/ecritures',json={'date':'2025-01-01','date_piece':'2025-01-01','journal':'BQ','reference':'NAVIGATION-841','libelle':'Témoin fictif navigation sans mutation','lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':100}]}),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'));avant=core(application,sid);routes=['/cloture','/factures','/avoirs','/journal','/lettrage','/rapprochement','/livre-inventaire'];chargements=[]
  for tour in range(8):
   for route in routes:
    r=page.goto(application['web_url']+route);assert r.status==200 and page.url.rstrip('/')==application['web_url']+route;expect(page.get_by_role('main')).to_be_visible();expect(page.get_by_role('main').get_by_role('heading',level=1)).to_be_visible();assert page.evaluate("document.fonts.status")=='loaded'
    if route=='/cloture':expect(page.get_by_label('Exercice actif',exact=True)).to_have_value('2025')
    if route=='/journal':expect(page.get_by_text('NAVIGATION-841',exact=True)).to_be_visible()
    chargements.append({'tour':tour+1,'route':route,'statut':r.status})
  assert len(chargements)==56 and core(application,sid)==avant;preuve['navigation841']={'chargements':chargements,'nb':56,'tous_200':True,'polices_chargees':True,'temoin_comptable_conserve':True,'retry':0,'timeout_navigation_ms':15000,'limite':'Lecture sur société fictive et témoin100MAD ;ne reproduit pas toutes les saisies du scénario annuel ni la cause de l’arrêt mobile historique.'}
