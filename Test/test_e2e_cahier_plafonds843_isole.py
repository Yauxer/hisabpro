"""NEG012/013 : plafonds financiers réels et absence de mutation après refus."""
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def facture843(api,t,type,date,pu,ref):
 f=ok(api.post('/api/factures',json={'type':type,'date':date,'tiers':t['nom'],'tiers_id':t['id'],'reference':ref,'lignes':[{'description':'Service fictif plafond843','quantite':1,'prix_unitaire':pu,'tva':20}]}),201);ok(api.post(f'/api/factures/{f["id"]}/valider'));ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'));return next(x for x in ok(api.get('/api/factures',params={'exercice':2025})) if x['id']==f['id'])

def valider843(api):
 for e in sorted(ok(api.get('/api/ecritures',params={'exercice':2025})),key=lambda e:(e['date'],e['id'])):
  if not e['est_validee']:ok(api.post(f'/api/ecritures/{e["id"]}/valider'))

def etat843(api,app,sid,fid):
 return {'journal':core(app,sid),'reglements':ok(api.get('/api/reglements',params={'exercice':2025})),'acomptes':ok(api.get('/api/acomptes',params={'exercice':2025})),'situation':ok(api.get(f'/api/factures/{fid}/reglements'))}

@pytest.mark.parametrize('largeur',[1440,390])
def test_843_surpaiement_et_acompte_epuise(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'plafonds843') as (api,page,sid,preuve):
  ts={}
  for code in ['F-CONTROLE','C-SERVICE']:
   t=next(t for t in DATA['tiers'] if t['code']==code);ts[code]=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':t['type'],('compte_client' if t['type']=='client' else 'compte_fournisseur'):t['compte']}),201)
  b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201);t=ts['C-SERVICE'];ac=ok(api.post('/api/acomptes',json={'type':'client','tiers':t['nom'],'tiers_id':t['id'],'date':'2025-06-01','montant':24000,'taux_tva':20,'mode':'virement','compte_bancaire_id':banque['id'],'reference':'AC-C01'}),201)
  v=facture843(api,t,'vente','2025-06-15',120000,'VENTE-SERVICE');assert ok(api.post(f'/api/acomptes/{ac["id"]}/imputer',json={'facture_id':v['id'],'montant':24000,'date_imputation':'2025-06-15'}))['montant_disponible']==0
  f=facture843(api,ts['F-CONTROLE'],'achat','2025-12-02',200,'02');valider843(api);avant=etat843(api,application,sid,f['id']);assert avant['situation']['solde_restant']==240
  page.goto(application['web_url']+'/factures');row=page.locator('tbody tr').filter(has_text=ts['F-CONTROLE']['nom']);row.get_by_title('Payer le fournisseur',exact=True).click();m=page.get_by_role('dialog');champ(m,'Montant *').fill('241');champ(m,'Date *').fill('2025-12-03');m.get_by_role('button',name='Enregistrer',exact=True).click();expect(m.get_by_text('Le montant dépasse le solde restant',exact=False)).to_be_visible();assert etat843(api,application,sid,f['id'])==avant
  r=api.post('/api/reglements',json={'facture_id':f['id'],'tiers_id':ts['F-CONTROLE']['id'],'tiers':ts['F-CONTROLE']['nom'],'date':'2025-12-03','montant':241,'mode':'virement','banque':b['banque'],'reference':'REFUS-241'});assert r.status_code in {400,409,422} and ('solde' in r.text.lower() or 'reste' in r.text.lower());assert etat843(api,application,sid,f['id'])==avant
  preuve['surpaiement843']={'solde':240,'tentative':241,'ui_refus':True,'api_statut':r.status_code,'detail':r.json(),'aucune_mutation':True}
  # Contrôle positif de frontière : le montant exact reste payable via le même formulaire.
  champ(m,'Montant *').fill('240');champ(m,'Banque','select').select_option(b['banque']);m.get_by_placeholder('N° chèque, virement...').fill('PAY-02-EXACT')
  with page.expect_response(lambda r:r.url.endswith('/api/reglements') and r.request.method=='POST') as rr:m.get_by_role('button',name='Enregistrer',exact=True).click()
  ok(rr.value,201);m.wait_for(state='hidden');assert ok(api.get(f'/api/factures/{f["id"]}/reglements'))['solde_restant']==0;valider843(api);apres=core(application,sid);nouvelles=[e for e in apres if e[0] not in {e[0] for e in avant['journal']}];assert len(nouvelles)==1 and {(l[1],l[2],l[3]) for l in nouvelles[0][8]}=={('4411',240,0),('5141',0,240)};preuve['surpaiement843']['montant_exact_accepte']=240;preuve['surpaiement843']['ecriture_exacte_4411_5141']=True
  page.goto(application['web_url']+'/acomptes');row=page.locator('tbody tr').filter(has_text=t['nom']);expect(row.get_by_title('Imputer sur une facture',exact=True)).to_have_count(0);avant_ac=etat843(api,application,sid,v['id']);assert avant_ac['situation']['solde_restant']==120000
  r=api.post(f'/api/acomptes/{ac["id"]}/imputer',json={'facture_id':v['id'],'montant':1,'date_imputation':'2025-06-15'});assert r.status_code==409 and 'entièrement imputé' in r.json()['detail'];assert etat843(api,application,sid,v['id'])==avant_ac
  preuve['acompte843']={'montant_initial':24000,'montant_impute':24000,'disponible':0,'tentative':1,'statut':r.status_code,'detail':r.json()['detail'],'commande_indisponible_UI':True,'aucune_mutation':True};preuve['cas'] += [{'id':c,'statut':'Réussi'} for c in ['HP-NEG-012','HP-NEG-013']]
