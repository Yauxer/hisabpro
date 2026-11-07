"""CAP-01 exactement saisi dans le Journal :aucune écriture attendue injectée parAPI."""
from decimal import Decimal
import pytest
from playwright.sync_api import expect
from sqlalchemy.orm import Session
import models
from cahier_formulaires773_support import laboratoire,ok,champ
from cahier_cycle775_support import identifiants,nouvelle_ecriture,valider_journal
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_783_capital200000_manuel_piece_libelles_validation_fec(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'capital783') as (api,page,sid,preuve):
  comptes={c['numero']:c for c in ok(api.get('/api/plan-comptable'))};assert '5141' in comptes and '1111' in comptes;assert not identifiants(application,sid)
  page.goto(application['web_url']+'/journal');page.get_by_role('button',name='Nouvelle écriture',exact=True).click();m=page.get_by_role('dialog');champ(m,'Date comptable *').fill('2025-01-01');champ(m,'Journal *','select').select_option('BQ');champ(m,'Référence du justificatif').fill('CAP-01');champ(m,"Libellé de l'écriture *").fill('Apport associé Recette');expect(champ(m,'Date du justificatif','input[type="date"]')).to_have_value('2025-01-01')
  rows=m.locator('tbody tr')
  for i,code in enumerate(['5141','1111']):
   rows.nth(i).get_by_placeholder('Ex: 6111',exact=True).fill(code);expect(rows.nth(i).get_by_label('Libellé du compte',exact=True)).to_have_value(comptes[code]['libelle']);expect(rows.nth(i).get_by_label('Libellé du compte',exact=True)).to_have_attribute('readonly','')
  rows.nth(0).locator('td[data-label="Débit (MAD)"] input').fill('200000');rows.nth(1).locator('td[data-label="Crédit (MAD)"] input').fill('200000');m.get_by_label('Valider immédiatement',exact=False).uncheck()
  bouton=m.get_by_role('button',name="Enregistrer l'écriture",exact=True)
  preuve['soumission783']=bouton.evaluate("el=>({disabled:el.disabled,rect:el.getBoundingClientRect().toJSON(),viewport:{width:innerWidth,height:innerHeight},focus:document.activeElement?.getAttribute('type')})")
  page.evaluate("window.__clics783=[];['mousedown','mouseup','click'].forEach(type=>document.addEventListener(type,e=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.includes(\"Enregistrer l'écriture\"));window.__clics783.push({type,target:e.target.tagName,classe:e.target.className,bouton:e.target.closest('button')?.textContent,y:e.clientY,rect:b?.getBoundingClientRect().toJSON()})},true))")
  with page.expect_response(lambda r:r.url.endswith('/api/ecritures') and r.request.method=='POST') as r:
   bouton.click();preuve['soumission783']['clics']=page.evaluate('window.__clics783')
  ec=ok(r.value,201);assert not ec['est_validee'] and ec['numero_ecriture'] is None;m.wait_for(state='hidden');nouvelle_ecriture(application,sid,set(),'CAP-01',preuve)
  with Session(application['engine']) as db:
   e=db.get(models.Ecriture,ec['id']);assert str(e.date_piece)=='2025-01-01' and e.reference=='CAP-01' and e.libelle=='Apport associé Recette';assert {l.compte:l.libelle for l in e.lignes}=={k:comptes[k]['libelle'] for k in ['5141','1111']}
  valider_journal(page,application,1)
  with Session(application['engine']) as db:e=db.get(models.Ecriture,ec['id']);assert e.est_validee and e.numero_ecriture
  fec=api.get('/api/fec/export',params={'exercice':2025});assert fec.status_code==200,fec.text;rows=[l.split('\t') for l in fec.text.rstrip('\r\n').splitlines()];assert len(rows)==3 and all(len(l)==18 for l in rows)
  assert sum(Decimal(l[11].replace(',','.')) for l in rows[1:])==sum(Decimal(l[12].replace(',','.')) for l in rows[1:])==Decimal('200000')
  assert all(l[0]=='BQ' and l[3]=='20250101' and l[8]=='CAP-01' and l[9]=='20250101' for l in rows[1:]);assert {l[4]:l[5] for l in rows[1:]}=={k:comptes[k]['libelle'] for k in ['5141','1111']}
  etats=ok(api.get('/api/etats/liasse/2025'))['etats'];assert etats['bilan']['actif']['total']['net']==etats['bilan']['passif']['total']==200000 and etats['cpc']['resultat_net']==0
  preuve['cas'].append({'id':'HP-CPT-001','statut':'Réussi'});preuve['capital783']={'ecritures':1,'lignes':2,'debit_credit':'200000.00','bilan':200000,'resultat':0,'date_piece_reference':True,'libelles_plan_UI_journal_FEC_identiques':True,'limite':'Société vierge indépendante ;ne pas assimiler àun raccord au sous-parcours marchandises. FECréduit2lignes,non FECannuel complet.'}
