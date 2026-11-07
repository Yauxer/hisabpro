"""PAY020 : annulation tracée dans2026, conservation stricte du journal2025."""
from decimal import Decimal as D
from datetime import date
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from cahier_cycle775_support import valider_journal
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_ras_capture_isole import ouvrir
from test_e2e_cahier_avant_is823_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_831_annulation_virement_2026_origine_2025_conservee(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'annulation831') as (api,page,sid,preuve):
  t=next(t for t in DATA['tiers'] if t['code']=='C-MARCH');tiers=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'client','compte_client':'3421'}),201)
  a=next(a for a in DATA['articles'] if a['code']=='M-01');article=ok(api.post('/api/articles',json={'code':a['code'],'designation':a['designation'],'is_stockable':True,'stock_actuel':0,'prix_achat_ht':110,'prix_vente_ht':250,'tva':20,'compte_vente':'7111'}),201);aid=article['id'];ok(api.patch(f'/api/articles/{aid}/stock',json={'stock_actuel':200,'date':'2025-01-01','reference':'COPIE-PAY020-STOCK','note':'Précondition fictive indépendante,avantvente2025.'}));b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  f=ok(api.post('/api/factures',json={'type':'vente','date':'2025-01-20','date_echeance':'2025-01-26','tiers':tiers['nom'],'tiers_id':tiers['id'],'reference':'VENTE-01','lignes':[{'article_id':aid,'description':article['designation'],'quantite':100,'prix_unitaire':250,'tva':20}]}),201);fid=f['id'];ok(api.post(f'/api/factures/{fid}/valider'));ok(api.post(f'/api/factures/{fid}/comptabiliser'))
  r10=ok(api.post('/api/reglements',json={'facture_id':fid,'tiers_id':tiers['id'],'tiers':tiers['nom'],'date':'2025-01-25','montant':10000,'mode':'virement','banque':banque['banque'],'reference':'VENTE-01-PAY','comptabiliser':True}),201)
  r20=ok(api.post('/api/reglements',json={'facture_id':fid,'tiers_id':tiers['id'],'tiers':tiers['nom'],'date':'2025-01-26','montant':20000,'mode':'cheque','banque':banque['banque'],'reference':'CHQ-01','comptabiliser':True}),201)
  for action,jour in [('remettre','2025-02-01'),('encaisser','2025-02-05')]:ok(api.post(f'/api/reglements/{r20["id"]}/transition',json={'action':action,'date_effective':jour,'frais':0}))
  for e in sorted(ok(api.get('/api/ecritures',params={'exercice':2025})),key=lambda e:(e['date'],e['id'])):ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
  originaux=ok(api.get('/api/ecritures',params={'exercice':2025}));assert len(originaux)==5 and all(e['est_validee'] for e in originaux);initial=core(application,sid);source=next(e for e in originaux if e['reference']=='VENTE-01-PAY');avant_etats=ok(api.get('/api/etats/liasse/2025'))['etats'];assert ok(api.get(f'/api/factures/{fid}/reglements'))['solde_restant']==0 and ok(api.get('/api/ecritures',params={'exercice':2026}))==[]
  ouvrir(page,application,'vente');row=page.locator('tbody tr').filter(has_text='VENTE-01-PAY');row.get_by_title('Annuler par contrepassation',exact=True).click();m=page.get_by_role('dialog',name='Annuler le règlement',exact=True);expect(m.get_by_label('Date d’annulation *',exact=True)).to_have_value(date.today().isoformat());m.get_by_label('Date d’annulation *',exact=True).fill('2026-10-06');motif='Variante PAY020 — annulation fictive du virement initial';m.get_by_label('Motif (facultatif)',exact=True).fill(motif)
  with page.expect_response(lambda r:r.url.endswith(f'/api/reglements/{r10["id"]}/annuler') and r.request.method=='POST') as r:m.get_by_role('button',name='Confirmer l’annulation',exact=True).click()
  annulation=ok(r.value);assert r.value.request.post_data_json=={'date_annulation':'2026-10-06','motif':motif};m.wait_for(state='hidden');expect(row).to_contain_text('annule');assert annulation['statut']=='annule'
  assert ok(api.get('/api/ecritures',params={'exercice':2025}))==originaux;inverse=ok(api.get('/api/ecritures',params={'exercice':2026}));assert len(inverse)==1;e=inverse[0];assert e['date']==e['date_piece']=='2026-10-06' and not e['est_validee'] and e['journal']=='BQ' and e['contrepassation_de_id']==source['id'] and e['motif_correction']==motif;assert {l['compte']:(D(str(l['debit'])),D(str(l['credit']))) for l in e['lignes']}=={'3421':(D(10000),D(0)),'5141':(D(0),D(10000))}
  situation=ok(api.get(f'/api/factures/{fid}/reglements'));assert situation['solde_restant']==10000 and len(situation['reglements'])==2 and next(x for x in situation['reglements'] if x['id']==r10['id'])['statut']=='annule'
  page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2026');valider_journal(page,application,1);apres=core(application,sid);assert all(e in apres for e in initial) and len(apres)==6 and all(e[7] for e in apres);assert ok(api.get('/api/ecritures',params={'exercice':2025}))==originaux
  etats=ok(api.get('/api/etats/liasse/2025'))['etats']
  for k in ['bilan','cpc','esg']:assert etats[k]==avant_etats[k]
  resultat=ok(api.get('/api/ecritures',params={'exercice':2026}));assert resultat[0]['est_validee'];rejeu=ok(api.post(f'/api/reglements/{r10["id"]}/annuler',json={'date_annulation':'2026-10-06','motif':motif}));assert core(application,sid)==apres
  page.reload();expect(page.get_by_text('ANN-VENTE-01-PAY',exact=True).first).to_be_visible();preuve['annulation831']={'facture':f,'reglement_initial':r10,'autre_cheque':r20,'annulation':annulation,'contrepassation':resultat[0],'situation_apres':situation,'originaux2025_conserves':True,'etats2025_conserves':True,'rejeu_sans_doublon':True,'date_operation':'2026-10-06','date_audit_execution':date.today().isoformat()};preuve['cas'].append({'id':'HP-PAY-020','statut':'Réussi'})
