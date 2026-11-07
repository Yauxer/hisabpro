"""Variante indépendante du cahier : achat BC→BR→facture et date choisie."""
from decimal import Decimal as D
import pytest
from sqlalchemy import text
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_cycle775_support import officialiser,valider_journal
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_avant_is823_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def etat(app,sid,aid):
 with app['engine'].connect() as db:
  return {'stock':str(db.scalar(text('SELECT stock_actuel FROM articles WHERE id=:aid'),{'aid':aid})), 'mouvements':db.scalar(text('SELECT count(*) FROM mouvements_stock WHERE article_id=:aid AND societe_id=:sid'),{'aid':aid,'sid':sid}),'ecritures':db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid'),{'sid':sid})}

@pytest.mark.parametrize('largeur',[1440,390])
def test_825_achat_bc_br_facture_date_stock_unique(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'achat825') as (api,page,sid,preuve):
  t=next(t for t in DATA['tiers'] if t['code']=='F-MARCH');tiers=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'fournisseur','compte_fournisseur':'4411'}),201)
  a=next(a for a in DATA['articles'] if a['code']=='M-01');article=ok(api.post('/api/articles',json={'code':a['code'],'designation':a['designation'],'is_stockable':True,'stock_actuel':0,'prix_achat_ht':100,'prix_vente_ht':250,'tva':20,'compte_achat':'6111','compte_vente':'7111'}),201);aid=article['id'];assert (ok(api.get('/api/societe/moi')).get('stock_declencheur_achat') or 'facture')=='facture'
  page.goto(application['web_url']+'/commercial');page.get_by_role('button',name='Achat',exact=True).click();page.get_by_role('button',name='Bons de commande',exact=True).click();page.get_by_role('button',name='Nouveau BC',exact=True).click();m=page.get_by_role('dialog',name='Nouveau bon de commande',exact=True);champ(m,'Date').fill('2025-02-01');m.get_by_placeholder('Nom du fournisseur...',exact=True).fill(tiers['nom']);m.get_by_role('option').filter(has_text=tiers['nom']).click();m.get_by_placeholder('Article ou description...',exact=True).fill(article['designation']);m.locator('li').filter(has_text=article['designation']).click();m.get_by_label('Quantité',exact=True).fill('10')
  with page.expect_response(lambda r:r.url.endswith('/api/bons-commande') and r.request.method=='POST') as r:m.get_by_role('button',name='Créer la commande',exact=True).click()
  bc=ok(r.value,201);m.wait_for(state='hidden');assert bc['date']=='2025-02-01' and D(str(bc['total_ttc']))==1200;assert D(etat(application,sid,aid)['stock'])==0 and etat(application,sid,aid)['ecritures']==0
  row=page.locator('tbody tr').filter(has_text=bc['numero']);row.get_by_title('Créer un bon de réception sur le reliquat',exact=True).click();m=page.get_by_role('dialog',name='Nouveau bon de réception',exact=True);m.locator('input[type=date]').fill('2025-02-02');expect(m.locator('input[type=number]')).to_have_value('10')
  with page.expect_response(lambda r:r.url.endswith(f'/api/bons-commande/{bc["id"]}/convertir-bl') and r.request.method=='POST') as r:m.get_by_role('button',name='Créer le bon de réception',exact=True).click()
  br=ok(r.value);m.wait_for(state='hidden');assert br['date']=='2025-02-02' and br['bon_commande_id']==bc['id'];page.get_by_role('button',name='Bons de réception',exact=True).click();row=page.locator('tbody tr').filter(has_text=br['numero'])
  for titre in ['Marquer en cours','Marquer réceptionné']:
   with page.expect_response(lambda r:r.url.endswith(f'/api/bons-reception/{br["id"]}') and r.request.method=='PATCH') as r:row.get_by_title(titre,exact=True).click()
   ok(r.value)
  assert etat(application,sid,aid)['ecritures']==0 and D(etat(application,sid,aid)['stock'])==0
  row.get_by_title('Créer la facture fournisseur depuis ce bon de réception',exact=True).click();m=page.get_by_role('dialog',name='Facturer le bon de réception '+br['numero'],exact=True);date=m.get_by_label('Date de la facture fournisseur',exact=True);date.fill('');expect(m.get_by_role('button',name='Créer la facture en brouillon',exact=True)).to_be_disabled();date.fill('2025-02-03')
  with page.expect_response(lambda r:r.url.endswith(f'/api/bons-livraison/{br["id"]}/convertir-facture') and r.request.method=='POST') as r:m.get_by_role('button',name='Créer la facture en brouillon',exact=True).click()
  f=ok(r.value);m.wait_for(state='hidden');assert f['date']=='2025-02-03' and f['exercice']==2025 and D(str(f['total_ttc']))==1200
  page.goto(application['web_url']+'/factures');row=page.locator('tbody tr').filter(has_text=tiers['nom']);row.get_by_title('Modifier le brouillon',exact=True).click();m=page.get_by_role('dialog');champ(m,'N° facture fournisseur').fill('REC-ACH-BCBR-825');champ(m,'Échéance').fill('2025-02-10')
  with page.expect_response(lambda r:r.url.endswith(f'/api/factures/{f["id"]}') and r.request.method=='PATCH') as r:m.get_by_role('button',name='Enregistrer les modifications',exact=True).click()
  ok(r.value);m.wait_for(state='hidden');f,_=officialiser(page,application,f,tiers);valider_journal(page,application,1);es=ok(api.get('/api/ecritures',params={'exercice':2025}));assert len(es)==1 and es[0]['est_validee'] and es[0]['date']=='2025-02-03' and es[0]['journal']=='AC';assert {l['compte']:(D(str(l['debit'])),D(str(l['credit']))) for l in es[0]['lignes']}=={'6111':(D(1000),D(0)),'34552':(D(200),D(0)),'4411':(D(0),D(1200))};fin=etat(application,sid,aid);assert D(fin['stock'])==10 and fin['mouvements']==1 and fin['ecritures']==1;avant=core(application,sid)
  reliquat=ok(api.get(f'/api/bons-livraison/{br["id"]}/reliquat-facturation'));assert all(D(str(l['reste_a_facturer']))==0 for l in reliquat['lignes']);refus=api.post(f'/api/bons-livraison/{br["id"]}/convertir-facture',json={'date':'2025-02-03'});assert refus.status_code==409
  page.reload();assert etat(application,sid,aid)==fin and core(application,sid)==avant;f=next(x for x in ok(api.get('/api/factures',params={'exercice':2025})) if x['id']==f['id']);assert f['reference']=='REC-ACH-BCBR-825' and f['date_echeance']=='2025-02-10';preuve['achat825']={'bc':bc,'br':br,'facture':f,'ecriture':es[0],'etat':fin,'refus_double':refus.json(),'journal_inchange_apres_refus':True};preuve['cas'].append({'id':'HP-FAC-014','statut':'Réussi'})
