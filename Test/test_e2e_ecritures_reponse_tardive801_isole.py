"""Une réponse réelle ancienne ne doit pas masquer la nouvelle écriture."""
from urllib.parse import urlsplit,parse_qs
import hashlib
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,ok,champ
from cahier_suite777_support import core
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_801_ecriture_creee_survit_get_vide_ancien_et_validation(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'race_ecriture801') as (api,page,sid,preuve):
  capture={}
  def retenir(route):
   annee=parse_qs(urlsplit(route.request.url).query).get('exercice')
   if route.request.method=='GET' and annee==['2025'] and not capture:
    reponse=route.fetch();assert reponse.status==200 and reponse.json()==[];capture.update(route=route,reponse=reponse);page.evaluate('window.__lectureEcriture801Retenue=true')
   else:route.continue_()
  page.route('**/api/ecritures?**',retenir);page.goto(application['web_url']+'/journal');page.wait_for_function('window.__lectureEcriture801Retenue === true')
  page.get_by_role('button',name='Nouvelle écriture',exact=True).click();m=page.get_by_role('dialog')
  for label,val in [('Date comptable *','2025-01-01'),('Référence du justificatif','RACE-801'),("Libellé de l'écriture *",'Capital fictif test réponse tardive')]:champ(m,label).fill(val)
  champ(m,'Journal *','select').select_option('BQ');rows=m.locator('tbody tr')
  for i,compte,colonne in [(0,'5141','Débit (MAD)'),(1,'1111','Crédit (MAD)')]:
   rows.nth(i).get_by_placeholder('Ex: 6111',exact=True).fill(compte);rows.nth(i).locator(f'td[data-label="{colonne}"] input').fill('100')
  m.get_by_label('Valider immédiatement',exact=False).uncheck()
  with page.expect_response(lambda r:r.url.endswith('/api/ecritures') and r.request.method=='POST') as r:m.get_by_role('button',name="Enregistrer l'écriture",exact=True).click()
  e=ok(r.value,201);m.wait_for(state='hidden');serveur=ok(api.get('/api/ecritures',params={'exercice':2025}));assert len(serveur)==1 and serveur[0]['id']==e['id'] and not serveur[0]['est_validee'];avant=core(application,sid)
  preuve['race801']={'get_avant':capture['reponse'].json(),'get_sha256':hashlib.sha256(capture['reponse'].body()).hexdigest(),'post201_id':e['id'],'api_apres_ids':[x['id'] for x in serveur],'transport':'Réponse GET réelle retenue sans modifier les données ;POST etvalidation réels.'}
  capture['route'].fulfill(response=capture['reponse']);ligne=page.locator('tr').filter(has=page.get_by_text('RACE-801',exact=True));expect(ligne).to_have_count(1);preuve['race801']['creation_preservee_apres_get_ancien']=True
  with page.expect_response(lambda r:r.url.endswith(f'/api/ecritures/{e["id"]}/valider') and r.request.method=='POST') as r:ligne.get_by_role('button',name='Valider',exact=True).click()
  ok(r.value);expect(ligne.get_by_role('button',name='Contrepasser',exact=True)).to_be_visible();expect(ligne.get_by_role('button',name='Supprimer',exact=True)).to_have_count(0)
  apres=core(application,sid);assert len(apres)==1 and apres[0][-1]==avant[0][-1] and apres[0][7] and apres[0][6];expect(ligne.get_by_text(apres[0][6],exact=True)).to_be_visible();preuve['race801']['numero_officiel_affiche']=apres[0][6];preuve['race801']['validation_reelle_et_montants_preserves']=True
