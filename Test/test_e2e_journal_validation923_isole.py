"""Validation réelle puis navigation : aucune alerte asynchrone sur une page quittée."""
from pathlib import Path
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,ok
from navigation823_support import navigations_completes823
from test_factures_conservation923_isole import (
 application,application104,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
def test_923_validation_lot_message_et_navigation_immediate(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'journal_validation923') as (api,page,sid,preuve):
  dialogues=[];page.on('dialog',lambda d:dialogues.append({'type':d.type,'message':d.message}))
  ids=[]
  for i in [1,2]:
   e=ok(api.post('/api/ecritures',json={'date':'2025-01-15','journal':'BQ','reference':f'VALIDATION-FICTIVE923-{i}','libelle':f'Validation fictive923 numéro{i}','lignes':[{'compte':'5141','debit':10*i},{'compte':'1111','credit':10*i}]}),201);ids.append(e['id'])
   page.goto(application['web_url']+'/journal');expect(page.get_by_role('button',name='Valider',exact=True)).to_have_count(1)
   with page.expect_response(lambda r:r.url.endswith('/api/ecritures/valider-lot') and r.request.method=='POST') as rr:page.get_by_role('button',name='Valider les brouillons',exact=True).click()
   assert ok(rr.value)['nb_validees']==1
   if i==1:
    region=page.get_by_role('status',name='Résultat de validation des écritures');expect(region).to_contain_text('1 écriture(s) validée(s).');expect(page.get_by_role('button',name='Valider',exact=True)).to_have_count(0);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    page.screenshot(path=str(R/f'docs/recette/preuves/923_{largeur}_validation.png'))
    region.get_by_role('button',name='Fermer le résultat de validation',exact=True).click();expect(region).to_have_count(0)
   else:
    # On quitte dès la réponse POST, sans attendre le rechargement du contexte.
    # L’ancien alert(msg), après ce rechargement, pouvait bloquer Page.goto.
    page.goto(application['web_url']+'/factures');expect(page.get_by_role('button',name='Nouvelle facture',exact=True)).to_be_visible();page.goto(application['web_url']+'/journal');expect(page.get_by_role('status',name='Résultat de validation des écritures')).to_have_count(0)
  assert len(dialogues)==2 and all(d['type']=='confirm' for d in dialogues),dialogues
  es=ok(api.get('/api/ecritures',params={'exercice':2025}));assert {e['id'] for e in es}==set(ids) and all(e['est_validee'] for e in es)
  for i,e in enumerate(sorted(es,key=lambda e:e['id']),1):assert sum(l['debit'] for l in e['lignes'])==sum(l['credit'] for l in e['lignes'])==10*i
  preuve['validation_journal923']={'confirmation_avant_validation_conservee':True,'aucune_alerte_apres_reponse':True,'navigation_immediate_reussie':True,'deux_ecritures_definitives_uniques':True,'montants_conserves':True}
