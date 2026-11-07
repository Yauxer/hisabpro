"""Enregistrer un acompte ne doit pas effacer une autre ligne déjà remplie."""
from decimal import Decimal as D
import pytest
from playwright.sync_api import expect
from sqlalchemy.orm import Session
import models
from cahier_formulaires773_support import laboratoire,ok
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_795_acompte1_enregistre_conserve_saisie_acompte2(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'saisie_acompte795') as (api,page,sid,preuve):
  ok(api.put('/api/fiscalite/is/2026/parametres',json={'acomptes_reference_forcee':'26766','acomptes_justification_reference_forcee':'Référence synthétique du contrôle de saisie, société temporaire uniquement.'}));page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2026');page.goto(application['web_url']+'/fiscalite-is');rows=page.locator('tr').filter(has=page.get_by_placeholder('Réf. paiement',exact=True));expect(rows).to_have_count(4)
  for idx,montant,date_,ref in [(0,'6691.50','2026-03-31','AP1-SAISIE795'),(1,'2000','2026-06-30','AP2-SAISIE795')]:
   row=rows.nth(idx);row.get_by_placeholder('Montant',exact=True).fill(montant);row.locator('input[type="date"]').fill(date_);row.get_by_placeholder('Réf. paiement',exact=True).fill(ref)
  with page.expect_response(lambda r:r.url.endswith('/api/fiscalite/is/2026') and r.request.method=='GET') as lecture:
   with page.expect_response(lambda r:r.url.endswith('/api/fiscalite/is/2026/acomptes/1') and r.request.method=='PUT') as ecriture:rows.nth(0).get_by_role('button',name='Enregistrer',exact=True).click()
  ok(ecriture.value);ok(lecture.value);expect(rows.nth(0).get_by_placeholder('Montant',exact=True)).to_have_attribute('value','6691.5')
  preuve['saisie_acompte795']={'reference_forcee':'26766.00','raison':'Repère technique isolé, aucun lien avec la vraie société ni aucune écriture comptable.','apres_enregistrement1':{'montant2':rows.nth(1).get_by_placeholder('Montant',exact=True).input_value(),'date2':rows.nth(1).locator('input[type="date"]').input_value(),'reference2':rows.nth(1).get_by_placeholder('Réf. paiement',exact=True).input_value()}}
  expect(rows.nth(1).get_by_placeholder('Montant',exact=True)).to_have_value('2000');expect(rows.nth(1).locator('input[type="date"]')).to_have_value('2026-06-30');expect(rows.nth(1).get_by_placeholder('Réf. paiement',exact=True)).to_have_value('AP2-SAISIE795')
  with page.expect_response(lambda r:r.url.endswith('/api/fiscalite/is/2026/acomptes/2') and r.request.method=='PUT') as r:rows.nth(1).get_by_role('button',name='Enregistrer',exact=True).click()
  ok(r.value);data=ok(api.get('/api/fiscalite/is/2026'));assert [D(str(a['montant_verse'])) for a in data['acomptes']['acomptes']]==list(map(D,['6691.5','2000','0','0']))
  with Session(application['engine']) as db:assert db.query(models.Ecriture).filter_by(societe_id=sid).count()==0
  preuve['saisie_acompte795']['deux_paiements_fiscaux_conserves']=True

  rows.nth(1).get_by_placeholder('Montant',exact=True).fill('2500')
  with page.expect_response(lambda r:r.url.endswith('/api/fiscalite/is/2026/acomptes/2') and r.request.method=='DELETE') as r:rows.nth(1).get_by_role('button',name='Effacer',exact=True).click()
  assert r.value.status==204,r.value.text();expect(rows.nth(1).get_by_placeholder('Montant',exact=True)).to_have_value('');assert D(str(ok(api.get('/api/fiscalite/is/2026'))['acomptes']['acomptes'][1]['montant_verse']))==0;preuve['saisie_acompte795']['effacement_explicite_respecte']=True
