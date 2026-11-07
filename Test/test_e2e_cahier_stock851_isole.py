"""NEG025/026 : inventaire négatif et faux stock de service refusés sans mutation."""
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from test_e2e_inventaire_nombres_isole import photo
from navigation823_support import navigations_completes823
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_851_physique_negatif_service_sans_stock(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'stock851') as (api,page,sid,preuve):
  e=ok(api.post('/api/ecritures',json={'date':'2025-01-01','date_piece':'2025-01-01','journal':'BQ','reference':'TEMOIN-851','libelle':'Témoin fictif invariant851','lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':100}]}),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
  a=ok(api.post('/api/articles',json={'code':'M-01','designation':'Marchandise fictive851','is_stockable':True,'stock_actuel':0,'cmup':110,'prix_achat_ht':110,'prix_vente_ht':250,'tva':20,'compte_vente':'7111','compte_achat':'6111'}),201);ok(api.patch(f'/api/articles/{a["id"]}/stock',json={'stock_actuel':60,'date':'2025-01-01','reference':'PRECONDITION-851','note':'Stock fictif60avantcomptage2025.'}));s=ok(api.post('/api/articles',json={'code':'S-VTE','designation':'Service fictif851','is_stockable':False,'stock_actuel':0,'prix_vente_ht':1000,'tva':20,'compte_vente':'7124'}),201);avant=photo(application,sid);journal=core(application,sid)
  page.goto(application['web_url']+'/inventaire');page.locator('input[type=date]').fill('2025-12-31');page.get_by_placeholder('Référence inventaire',exact=True).fill('NEG-025');row=page.locator('tbody tr').filter(has_text=a['designation']);row.locator('input[type=number]').fill('-1');page.get_by_role('button',name='Valider l’inventaire',exact=True).click();expect(page.get_by_text('Quantité invalide pour M-01',exact=False)).to_be_visible();assert photo(application,sid)==avant;expect(page.locator('tbody tr').filter(has_text=s['designation'])).to_have_count(0)
  body={'date':'2025-12-31','reference':'NEG-025','lignes':[{'article_id':a['id'],'quantite_reelle':-1}]};refus=[]
  for route in ['/api/inventaire/simuler','/api/inventaire/valider']:
   r=api.post(route,json=body);assert r.status_code in {400,409,422} and 'négative' in r.text;assert photo(application,sid)==avant;refus.append({'route':route,'statut':r.status_code,'detail':r.json()})
  preuve['inventaire851']={'quantite_refusee':-1,'UI_validation_refusee':True,'refus':refus,'aucune_mutation':True}
  page.goto(application['web_url']+'/articles');page.locator('tbody tr').filter(has_text=s['designation']).click();m=page.get_by_role('dialog',name="Modifier l'article",exact=True);expect(m.get_by_text('Stock actuel',exact=True)).to_have_count(0);expect(m.get_by_role('button',name='Service / frais',exact=True)).to_be_visible();m.get_by_role('button',name='Annuler',exact=True).click();avant_s=photo(application,sid);refus=[]
  for route,payload in [(f'/api/articles/{s["id"]}',{'stock_actuel':10}),(f'/api/articles/{s["id"]}/stock',{'stock_actuel':10,'date':'2025-12-31','reference':'NEG-026'})]:
   r=api.patch(route,json=payload);assert r.status_code in {400,409,422};assert photo(application,sid)==avant_s;refus.append({'route':route,'statut':r.status_code,'detail':r.json()})
  service=next(x for x in ok(api.get('/api/articles')) if x['id']==s['id']);assert service['stock_actuel']==0 and service['is_stockable'] is False;assert not ok(api.get(f'/api/articles/{s["id"]}/mouvements'));preuve['service851']={'stock_refuse':10,'stock_reel':0,'champ_absent_UI':True,'refus':refus,'aucun_mouvement':True,'aucune_mutation':True}
  # Le comptage exact reste validable : seul un snapshot d'inventaire est ajouté.
  page.goto(application['web_url']+'/inventaire');page.locator('input[type=date]').fill('2025-12-31');page.get_by_placeholder('Référence inventaire',exact=True).fill('STOCK-851-EXACT');page.locator('tbody tr').filter(has_text=a['designation']).locator('input[type=number]').fill('60')
  with page.expect_response(lambda r:r.url.endswith('/api/inventaire/valider') and r.request.method=='POST') as rr:page.get_by_role('button',name='Valider l’inventaire',exact=True).click()
  positif=ok(rr.value);assert positif['nb_articles']==1 and positif['nb_regularises']==0 and core(application,sid)==journal;fin=photo(application,sid);assert fin['articles']==avant['articles'] and fin['mouvements']==avant['mouvements'] and fin['archives']==avant['archives'] and len(fin['inventaires'])==1
  preuve['positif851']={'comptage':60,'nb_articles':1,'nb_regularises':0,'journal_et_stock_conserves':True};preuve['cas'] += [{'id':c,'statut':'Réussi'} for c in ['HP-NEG-025','HP-NEG-026']]
