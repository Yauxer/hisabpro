"""SEC010 : brouillon abandonné lors de la bascule vers une société en lecture."""
import httpx,pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_reseau859_isole import naviguer859
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_861_societe_brouillon_droits_et_isolation(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'societe861') as (api,page,sid,preuve):
  me=ok(api.get('/api/auth/me'));nomA=DATA['societe']['raison_sociale'];nomB=f'Société B fictive861 {sid}';brouillon='BROUILLON NON ENREGISTRÉ A861'
  piece={'date':'2025-01-01','date_piece':'2025-01-01','journal':'BQ','reference':'TEMOIN-A-861','libelle':'Témoin fictif isolation861','lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':100}]}
  e=ok(api.post('/api/ecritures',json=piece),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'));initialA=core(application,sid);profilA=ok(api.get('/api/societe/moi'))
  with httpx.Client(base_url=application['api_url']) as bapi:
   r=bapi.post('/api/auth/register',json={'nom':'Principal B fictif861','email':f'b861-{sid}@hisabpro-recette.example','password':DATA['societe']['password_test'],'raison_sociale':nomB});assert r.status_code==200;bapi.headers['Authorization']='Bearer '+r.json()['access_token'];mb=ok(bapi.get('/api/auth/me'));bid=mb['societe_id'];ok(bapi.post('/api/exercices',json={'annee':2025,'date_debut':'2025-01-01','date_fin':'2025-12-31'}),201);ok(bapi.post(f'/api/societes/{bid}/inviter',params={'email':me['email'],'role':'lecture'}));profilB=ok(bapi.get('/api/societe/moi'));initialB=core(application,bid);assert not initialB
   page.goto(application['web_url']+'/journal');expect(page.get_by_text('TEMOIN-A-861',exact=True)).to_be_visible();page.goto(application['web_url']+'/parametres');champ(page,'Raison sociale').fill(brouillon);patch=[];page.on('request',lambda r:patch.append(r.method) if r.method in ['PATCH','PUT'] and r.url.endswith('/api/societe/moi') else None)
   page.get_by_role('button',name=nomA,exact=True).click()
   with page.expect_response(lambda r:r.url.endswith(f'/api/societes/switcher/{bid}') and r.request.method=='POST') as rr:page.get_by_role('button').filter(has=page.get_by_text(nomB,exact=True)).click()
   assert rr.value.status==200;expect(page.get_by_role('button',name=nomB,exact=True)).to_be_visible();page.wait_for_load_state('domcontentloaded');assert page.evaluate("localStorage.getItem('hisabpro_role')")=='lecture';token=page.evaluate("localStorage.getItem('hisabpro_token')");h={'Authorization':'Bearer '+token};r=api.get('/api/auth/me',headers=h);assert r.status_code==200;m=r.json();assert m['id']==me['id'] and m['societe_id']==bid and m['role']=='lecture';assert not page.locator('input').evaluate_all('(els,d)=>els.some(e=>e.value===d)',brouillon)
   page.get_by_label('Exercice comptable',exact=True).select_option('2025');naviguer859(page,'/journal','Comptabilité');expect(page.get_by_text('TEMOIN-A-861',exact=True)).to_have_count(0);expect(page.get_by_role('button',name='Nouvelle écriture',exact=True)).to_be_disabled();assert ok(api.get('/api/ecritures',params={'exercice':2025},headers=h))==[]
   assert api.post('/api/ecritures',headers=h,json=piece).status_code==403;assert not patch and core(application,sid)==initialA and core(application,bid)==initialB and ok(api.get('/api/societe/moi'))==profilA and ok(bapi.get('/api/societe/moi'))==profilB
   preuve['societe861']={'societe_A':sid,'societe_B':bid,'brouillon_non_transmis':True,'profil_A_conserve':True,'profil_B_conserve':True,'role_recharge':'lecture','creation_directe_refusee':403,'temoin_A_invisible_B':True,'core_A_conserve':True,'core_B_vide':True,'aucun_PATCH_profil':True,'limite':'Préconditions créées par API fictive ; formulaire, sélection de société et contrôle des commandes exécutés dans Edge réel. Le rechargement après bascule est le comportement existant.'};preuve['cas'].append({'id':'HP-SEC-010','statut':'Réussi'})
