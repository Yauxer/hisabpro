"""Montants visibles avant mutation, puis vraie sortie comptabilisée : Edge/API/PG."""
from pathlib import Path
from decimal import Decimal as D
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,champ,ok
from navigation823_support import navigations_completes823
from test_immobilisations_apercu927_isole import (
 application,application104,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,preparer,demande,url,photo)

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
@pytest.mark.parametrize('nature',['cession','rebut'])
def test_927_consulter_calcul_avant_sortie_sans_ancien_apercu_reutilise(application,largeur,nature,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,f'apercu927_{nature}') as (api,page,sid,preuve):
  i=preparer(api);page.get_by_label('Exercice actif',exact=True).select_option('2026');page.goto(application['web_url']+'/immobilisations');page.locator('tbody tr').filter(has_text=i['designation']).get_by_title('Cession / mise au rebut',exact=True).click();m=page.locator('[class*="modalOverlay"]').filter(has_text='Sortie — '+i['designation'])
  champ(m,'Type de sortie','select').select_option(nature);champ(m,'Date de sortie').fill('2026-01-01')
  if nature=='cession':champ(m,'Prix de cession HT').fill('20000');m.get_by_label('Cession encaissée immédiatement',exact=True).uncheck()
  avant=photo(application,sid);zone=m.get_by_role('region',name='Aperçu de la sortie')
  with page.expect_response(lambda r:r.url.endswith(url(i)+'/apercu') and r.request.method=='POST') as rr:zone.get_by_role('button',name='Calculer avant comptabilisation',exact=True).click()
  a=ok(rr.value);expect(zone.get_by_test_id('sortie-apercu-vnc')).to_have_text('19.186,67 MAD');expect(zone).to_contain_text('bornes inclusives');expect(zone).to_contain_text('13,33 MAD');assert photo(application,sid)==avant
  expect(zone.get_by_test_id('sortie-apercu-resultat_cession')).to_have_text('813,33 MAD' if nature=='cession' else '-19.186,67 MAD')
  if nature=='cession':
   champ(m,'Prix de cession HT').fill('21000');expect(zone.get_by_test_id('sortie-apercu-vnc')).to_have_count(0);champ(m,'Prix de cession HT').fill('20000');expect(zone.get_by_test_id('sortie-apercu-vnc')).to_have_count(0)
   with page.expect_response(lambda r:r.url.endswith(url(i)+'/apercu')) as rr:zone.get_by_role('button',name='Calculer avant comptabilisation',exact=True).click()
   a=ok(rr.value);expect(zone.get_by_test_id('sortie-apercu-vnc')).to_have_text('19.186,67 MAD')
  assert photo(application,sid)==avant;zone.scroll_into_view_if_needed();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');d=R/'docs/recette/preuves';d.mkdir(exist_ok=True);page.screenshot(path=str(d/f'927_{largeur}_{nature}_apercu.png'))
  with page.expect_response(lambda r:r.url.endswith(url(i)) and r.request.method=='POST') as rr:m.get_by_role('button',name='Comptabiliser la sortie',exact=True).click()
  r=ok(rr.value);assert rr.value.request.post_data_json['empreinte_apercu']==a['empreinte_apercu'];m.wait_for(state='hidden');assert all(D(str(r[k]))==D(str(a[k])) for k in ['vnc','cumul_amortissement','tva_cession','ttc_cession','resultat_cession'])
  apres=photo(application,sid);assert all(e in apres['ecritures'] for e in avant['ecritures']) and len(apres['ecritures'])==len(avant['ecritures'])+(3 if nature=='cession' else 2);expect(page.locator('tbody tr').filter(has_text=i['designation'])).to_contain_text('Cédé' if nature=='cession' else 'Rebut')
  preuve['apercu927']={'type_sortie':nature,'immo_id':i['id'],'vnc':'19186.67','dotation2026':'13.33','resultat':str(a['resultat_cession']),'aperçu_sans_mutation_metier_ni_sequence':True,'ancien_apercu_non_reutilise_apres_saisie':True,'sortie_montants_identiques':True,'empreinte_transmise':True,'originaux2025_conserves':True,'limite':'Convention interne conservée,qualification et régularisation TVA toujours à vérifier.'}
