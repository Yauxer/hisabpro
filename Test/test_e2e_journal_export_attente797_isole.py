"""Réponse GET réelle retardée : une création ne doit jamais disparaître de la liste."""
import hashlib,csv,io
from playwright.sync_api import expect
import pytest
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_797_journal_export_attend_lecture_reelle(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'export_attente797r') as (api,page,sid,preuve):
  e=ok(api.post('/api/ecritures',json={'date':'2025-01-01','journal':'BQ','reference':'ATTENTE797','libelle':'Capital fictif pour export retardé','est_validee':True,'lignes':[{'compte':'5141','debit':200000},{'compte':'1111','credit':200000}]}),201)
  capture={}
  def retenir(route):
   if route.request.method=='GET' and not capture:
    rep=route.fetch();assert rep.status==200;capture.update(route=route,reponse=rep);page.evaluate('window.__export797Retenu=true')
   else:route.continue_()
  page.route('**/api/ecritures?**',retenir);page.goto(application['web_url']+'/journal');page.wait_for_function('window.__export797Retenu === true');bouton=page.get_by_role('button',name='Exporter CSV',exact=True);expect(bouton).to_be_disabled();assert capture
  capture['route'].fulfill(response=capture['reponse']);expect(bouton).to_be_enabled()
  with page.expect_download() as sortie:bouton.click()
  fichier=tmp_path/'journal_attente.csv';sortie.value.save_as(fichier);rows=list(csv.DictReader(io.StringIO(fichier.read_text(encoding='utf-8-sig')),delimiter=';'));assert len(rows)==2 and {r['Compte'] for r in rows}=={'5141','1111'}
  preuve['export_attente797']={'lecture_reelle_retenue':True,'export_desactive_pendant_chargement':True,'export_reactive_apres_lecture':True,'lignes_csv':2,'ecriture_id':e['id'],'aucune_donnee_simulee':True}
