"""NEG014–016 : crédit tiers/plafond et retour excessif, avec copie chiffrée exacte."""
from decimal import Decimal as D
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_avoir829_isole import stock829
from test_e2e_cahier_plafonds843_isole import facture843,valider843
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def etat845(api,app,sid,aid):
 return {'journal':core(app,sid),'stock':stock829(app,sid,aid),'avoirs':ok(api.get('/api/avoirs',params={'exercice':2025})),'factures':ok(api.get('/api/factures',params={'exercice':2025})),'reglements':ok(api.get('/api/reglements',params={'exercice':2025}))}

@pytest.mark.parametrize('largeur',[1440,390])
def test_845_credit_mauvais_tiers_plafond_et_retour(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'credits845') as (api,page,sid,preuve):
  ts={}
  for code in ['C-MARCH','C-IMPAYE']:
   t=next(t for t in DATA['tiers'] if t['code']==code);ts[code]=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'client','compte_client':'3421'}),201)
  t=ts['C-MARCH'];art=ok(api.post('/api/articles',json={'code':'M-01','designation':'Marchandise fictive845','is_stockable':True,'stock_actuel':0,'prix_achat_ht':110,'prix_vente_ht':250,'tva':20,'compte_vente':'7111','compte_achat':'6111'}),201);aid=art['id'];ok(api.patch(f'/api/articles/{aid}/stock',json={'stock_actuel':200,'date':'2025-01-01','reference':'PRECONDITION-845','note':'Stock fictif indépendant avant vente2025.'}));b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  f=ok(api.post('/api/factures',json={'type':'vente','date':'2025-01-20','tiers':t['nom'],'tiers_id':t['id'],'reference':'VENTE-01','lignes':[{'article_id':aid,'description':art['designation'],'quantite':100,'prix_unitaire':250,'tva':20}]}),201);ok(api.post(f'/api/factures/{f["id"]}/valider'));ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'));ok(api.post('/api/reglements',json={'facture_id':f['id'],'tiers':t['nom'],'date':'2025-01-26','montant':30000,'mode':'virement','banque':b['banque'],'reference':'PAY-VENTE-01'}),201)
  cible=facture843(api,t,'vente','2025-02-01',10000,'CIBLE-845');autre=facture843(api,ts['C-IMPAYE'],'vente','2025-02-01',12000,'AUTRE-TIERS-845');valider843(api);f=next(x for x in ok(api.get('/api/factures',params={'exercice':2025})) if x['id']==f['id']);assert D(stock829(application,sid,aid)['quantite'])==100
  avant=etat845(api,application,sid,aid);page.goto(application['web_url']+'/factures');page.locator('tbody tr').filter(has_text=f['numero']).click();page.get_by_role('button',name='Créer un avoir',exact=True).click();m=page.get_by_role('dialog',name='Créer un avoir',exact=False);champ(m,"Date de l'avoir *").fill('2025-02-10');champ(m,"Nature de l'avoir",'select').select_option('retour_annulation');m.get_by_placeholder('Retour marchandise, remise après facture...').fill('AV-01 fictif845');m.get_by_role('checkbox',name='Retour physique de marchandise',exact=False).check();ligne=m.locator('tbody tr').filter(has_text=art['designation']);ligne.get_by_role('checkbox').check();ligne.locator('input[type=number]').fill('101');m.get_by_role('button',name="Créer l'avoir",exact=False).click();expect(m.get_by_text('La quantité dépasse le maximum autorisé',exact=False)).to_be_visible();assert etat845(api,application,sid,aid)==avant
  payload={'facture_id':f['id'],'date':'2025-02-10','motif':'AV-01 fictif845','retour_stock':True,'lignes':[{'facture_ligne_id':f['lignes'][0]['id'],'quantite':101}]};r=api.post('/api/avoirs',json=payload);assert r.status_code==409 and 'supérieure' in r.json()['detail'];assert etat845(api,application,sid,aid)==avant;preuve['retour845']={'vendu':100,'tentative':101,'UI_refus':True,'statut':r.status_code,'stock_et_journal_conserves':True}
  # Même formulaire : retour autorisé de10 unités, crédit exact3000 sur facture payée.
  ligne.locator('input[type=number]').fill('10')
  with page.expect_response(lambda r:r.url.endswith('/api/avoirs') and r.request.method=='POST') as rr:m.get_by_role('button',name="Créer l'avoir",exact=False).click()
  av=ok(rr.value,201);m.wait_for(state='hidden');ok(api.post(f'/api/avoirs/{av["id"]}/comptabiliser'));valider843(api);av=next(x for x in ok(api.get('/api/avoirs',params={'exercice':2025})) if x['id']==av['id']);assert av['montant_disponible']==3000 and D(stock829(application,sid,aid)['quantite'])==110;avant=etat845(api,application,sid,aid)
  page.goto(application['web_url']+'/avoirs');page.locator('tbody tr').filter(has_text=av['numero']).click();page.get_by_role('button',name='Imputer sur une facture',exact=True).click();m=page.get_by_role('dialog',name='Imputer le crédit — '+av['numero'],exact=True);champ(m,'Facture cible','select').select_option(str(cible['id']));expect(champ(m,'Facture cible','select').locator(f'option[value="{autre["id"]}"]')).to_have_count(0)
  data={'type_utilisation':'imputation','date_utilisation':'2025-02-10','montant':1,'facture_id':autre['id']};r=api.post(f'/api/avoirs/{av["id"]}/utiliser',json=data);assert r.status_code==422 and 'même tiers' in r.json()['detail'];assert etat845(api,application,sid,aid)==avant;preuve['tiers845']={'statut':r.status_code,'facture_autre_tiers_absente_UI':True,'aucune_mutation':True}
  champ(m,'Montant (MAD)').fill('3001');champ(m,'Date').fill('2025-02-10');m.get_by_role('button',name='Imputer le crédit',exact=True).click();expect(m.get_by_text('Le maximum disponible est de',exact=False)).to_be_visible();assert etat845(api,application,sid,aid)==avant;r=api.post(f'/api/avoirs/{av["id"]}/utiliser',json={**data,'facture_id':cible['id'],'montant':3001});assert r.status_code==409 and 'Crédit disponible insuffisant' in r.json()['detail'];assert etat845(api,application,sid,aid)==avant;preuve['plafond845']={'credit':3000,'tentative':3001,'statut':r.status_code,'UI_refus':True,'aucune_mutation':True}
  champ(m,'Montant (MAD)').fill('3000')
  with page.expect_response(lambda r:r.url.endswith(f'/api/avoirs/{av["id"]}/utiliser') and r.request.method=='POST') as rr:m.get_by_role('button',name='Imputer le crédit',exact=True).click()
  fin=ok(rr.value);m.wait_for(state='hidden');assert fin['montant_disponible']==0 and ok(api.get(f'/api/factures/{cible["id"]}/reglements'))['solde_restant']==9000;assert stock829(application,sid,aid)==avant['stock'];preuve['plafond845']['montant_exact_accepte']=3000;preuve['cas'] += [{'id':c,'statut':'Réussi'} for c in ['HP-NEG-014','HP-NEG-015','HP-NEG-016']]
