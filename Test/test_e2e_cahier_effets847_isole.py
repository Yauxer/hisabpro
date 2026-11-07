"""NEG017–020 : transitions bancaires invalides sans mutation, puis net réel."""
from datetime import date,timedelta
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_plafonds843_isole import facture843,valider843
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def etat847(api,app,sid):return {'journal':core(app,sid),'reglements':ok(api.get('/api/reglements',params={'exercice':2025})),'factures':ok(api.get('/api/factures',params={'exercice':2025}))}
def transition847(api,r,action,jour,frais=0):return api.post(f'/api/reglements/{r["id"]}/transition',json={'action':action,'date_effective':jour,'frais':frais})

@pytest.mark.parametrize('largeur',[1440,390])
def test_847_effets_dates_frais_et_statuts(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'effets847') as (api,page,sid,preuve):
  t=next(t for t in DATA['tiers'] if t['code']=='C-MARCH');t=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'client','compte_client':'3421'}),201);b=DATA['banque'];ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  f=facture843(api,t,'vente','2025-01-20',25000,'VENTE-01-CHQ');chq=ok(api.post('/api/reglements',json={'facture_id':f['id'],'tiers':t['nom'],'date':'2025-01-26','montant':20000,'mode':'cheque','banque':b['banque'],'reference':'CHQ-01'}),201);ok(transition847(api,chq,'remettre','2025-02-01'));ok(transition847(api,chq,'encaisser','2025-02-05'));valider843(api);avant=etat847(api,application,sid)
  page.goto(application['web_url']+'/effets');champ(page,'Statut','select').select_option('tous');row=page.locator('tbody tr').filter(has_text='CHQ-01');expect(row.get_by_title('Déclarer impayé',exact=True)).to_have_count(0);expect(row.get_by_title('Déclarer impayé après encaissement',exact=True)).to_have_count(1);r=transition847(api,chq,'rejeter','2025-02-04');assert r.status_code==400 and 'précéder' in r.json()['detail'];assert etat847(api,application,sid)==avant;preuve['rejet847']={'statut':400,'impaye_apres_encaissement_propose':True,'rejet_anterieur_refuse':True,'aucune_mutation':True}
  f=facture843(api,t,'vente','2025-03-20',10000,'VENTE-EFF');eff=ok(api.post('/api/reglements',json={'facture_id':f['id'],'tiers':t['nom'],'date':'2025-04-01','date_echeance':'2025-05-15','montant':10000,'mode':'effet','banque':b['banque'],'reference':'EFF-C01'}),201);ok(transition847(api,eff,'remettre','2025-05-01'));valider843(api);avant=etat847(api,application,sid)
  page.goto(application['web_url']+'/effets');champ(page,'Statut','select').select_option('tous');page.locator('tbody tr').filter(has_text='EFF-C01').get_by_title("Confirmer l'encaissement",exact=True).click();m=page.get_by_role('dialog');m.locator('input[type=date]').fill('2025-05-14')
  with page.expect_response(lambda r:r.url.endswith(f'/api/reglements/{eff["id"]}/transition') and r.request.method=='POST') as rr:m.get_by_role('button',name="Confirmer l'encaissement",exact=True).click()
  assert rr.value.status==400;expect(m.get_by_text("l'encaissement ne peut pas être constaté avant cette date",exact=False)).to_be_visible();assert etat847(api,application,sid)==avant;preuve['echeance847']={'date':'2025-05-14','echeance':'2025-05-15','statut':400,'aucune_mutation':True}
  m.locator('input[type=date]').fill('2025-05-16');m.get_by_placeholder('0.00',exact=True).fill('10001');m.get_by_role('button',name="Confirmer l'encaissement",exact=True).click();expect(m.get_by_text('Les frais ne peuvent pas dépasser le montant du règlement.',exact=True)).to_be_visible();r=transition847(api,eff,'encaisser','2025-05-16',10001);assert r.status_code==422 and 'frais' in r.json()['detail'];assert etat847(api,application,sid)==avant;preuve['frais847']={'montant':10000,'frais_refuses':10001,'statut':422,'UI_refus':True,'aucune_mutation':True}
  m.get_by_placeholder('0.00',exact=True).fill('0');dates=[]
  for jour,motif in [((date.today()+timedelta(days=1)).isoformat(),'future'),('2025-03-31','précéder')]:
   m.locator('input[type=date]').fill(jour)
   with page.expect_response(lambda r:r.url.endswith(f'/api/reglements/{eff["id"]}/transition') and r.request.method=='POST') as rr:m.get_by_role('button',name="Confirmer l'encaissement",exact=True).click()
   assert rr.value.status==400 and motif in rr.value.json()['detail'];assert etat847(api,application,sid)==avant;dates.append({'date':jour,'motif':motif,'statut':400})
  preuve['dates847']={'tentatives':dates,'aucune_mutation':True}
  m.locator('input[type=date]').fill('2025-05-16');m.get_by_placeholder('0.00',exact=True).fill('10')
  with page.expect_response(lambda r:r.url.endswith(f'/api/reglements/{eff["id"]}/transition') and r.request.method=='POST') as rr:m.get_by_role('button',name="Confirmer l'encaissement",exact=True).click()
  ok(rr.value);m.wait_for(state='hidden');valider843(api);fin=core(application,sid);n=[e for e in fin if e[0] not in {e[0] for e in avant['journal']}];assert len(n)==1 and n[0][1].isoformat()=='2025-05-16' and {(l[1],l[2],l[3]) for l in n[0][8]}=={('5141',9990,0),('61472',10,0),('51132',0,10000)} and all(e in fin for e in avant['journal']);preuve['positif847']={'brut':10000,'frais':10,'net_banque':9990,'contrepartie':'51132','une_seule_ecriture':True,'originaux_conserves':True};preuve['cas'] += [{'id':f'HP-NEG-{n:03d}','statut':'Réussi'} for n in range(17,21)]
