"""Réponse GET réelle retardée : une création ne doit jamais disparaître de la liste."""
import hashlib
from playwright.sync_api import expect
import pytest
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_795_facture_creee_survit_get_ancien_puis_suppression_brouillon(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'race_facture795') as (api,page,sid,preuve):
  t=next(t for t in DATA['tiers'] if t['code']=='C-SERVICE');tier=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'client','compte_client':'3421'}),201);a=next(a for a in DATA['articles'] if a['code']=='S-VTE');ok(api.post('/api/articles',json={'code':a['code'],'designation':a['designation'],'prix_vente_ht':a['prix_vente'],'tva':20,'is_stockable':False,'compte_vente':'7124'}),201)
  capture={}
  def retarder(route):
   if route.request.method=='GET' and not capture.get('capturefaite'):
    capture['capturefaite']=True;rep=route.fetch();assert rep.status==200;capture['route']=route;capture['reponse']=rep;capture['avant']=rep.json();assert capture['avant']==[]
   else:route.continue_()
  page.route('**/api/factures?**',retarder);page.goto(application['web_url']+'/factures');page.get_by_role('button',name='Nouvelle facture',exact=True).click();m=page.get_by_role('dialog',name='Nouvelle facture',exact=True);champ(m,'Date *').fill('2025-06-15');m.get_by_placeholder('Rechercher un',exact=False).fill(tier['nom']);m.get_by_text(tier['nom'],exact=True).click();m.get_by_placeholder('N° BC, bon de commande...').fill('RACE-FACTURE795');m.get_by_label('Échéance de la nouvelle facture',exact=True).fill('2025-06-30');m.get_by_placeholder('Description ou article...').fill(a['designation']);m.locator('li').filter(has_text=a['designation']).click();m.get_by_role('button',name='Enregistrer en brouillon',exact=False).click()
  with page.expect_response(lambda r:r.url.endswith('/api/factures') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer le brouillon',exact=True).click()
  f=ok(r.value,201);m.wait_for(state='hidden');apres=ok(api.get('/api/factures',params={'exercice':2025}));assert len(apres)==1 and apres[0]['id']==f['id'];preuve['race_facture795']={'get_reel_avant':capture['avant'],'get_sha256':hashlib.sha256(capture['reponse'].body()).hexdigest(),'post_reel201_id':f['id'],'api_reelle_apres_ids':[x['id'] for x in apres],'retard':'Transport GET réel retenu, données non modifiées ;POST etDELETE réels. Aucun calcul métier simulé.'}
  capture['route'].fulfill(response=capture['reponse']);row=page.locator('tbody tr').filter(has_text=tier['nom']);expect(row).to_have_count(1);preuve['race_facture795']['creation_preservee_apres_get_tardif']=True
  with page.expect_response(lambda r:r.url.endswith(f'/api/factures/{f["id"]}') and r.request.method=='DELETE') as r:row.get_by_role('button',name='Supprimer',exact=True).click()
  assert r.value.status==204,r.value.text();expect(row).to_have_count(0);assert ok(api.get('/api/factures',params={'exercice':2025}))==[];preuve['race_facture795']['suppression_brouillon_ui204']=True
