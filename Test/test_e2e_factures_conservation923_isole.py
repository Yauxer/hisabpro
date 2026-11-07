"""FAC013 : conservation et retéléchargement réel, Edge1440/390 → API → PG limité."""
from pathlib import Path
from io import BytesIO
import hashlib,pytest
from pypdf import PdfReader
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from navigation823_support import navigations_completes823
from test_factures_conservation923_isole import (
 application,application104,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,path,comptabilite)
from test_logo_societe import image_data
from test_e2e_cahier_plafonds843_isole import facture843,valider843

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
def test_923_conserver_recharger_telecharger_et_operations_disponibles(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'conservation923') as (api,page,sid,preuve):
  ok(api.patch('/api/societe/moi',json={'logo_url':image_data()}));t=ok(api.post('/api/tiers',json={'nom':'Client conservation FICTIF923','type':'client','compte_client':'3421'}),201);f=facture843(api,t,'vente','2025-01-20',1000,'CONSERVATION-FICTIVE923')
  b=DATA['banque'];ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201);ok(api.post('/api/reglements',json={'facture_id':f['id'],'tiers_id':t['id'],'tiers':t['nom'],'date':'2025-01-21','montant':1200,'mode':'virement','banque':b['banque'],'reference':'SOLDE-COPIE-FICTIF923'}),201)
  assert ok(api.get(f'/api/factures/{f["id"]}/reglements'))['solde_restant']==0;valider843(api);avant=comptabilite(application,sid)
  page.goto(application['web_url']+'/factures');page.locator('tbody tr').filter(has_text=f['numero']).click();region=page.get_by_role('region',name='Conservation du PDF de facture');region.get_by_text('Conserver une copie figée',exact=True).click();region.get_by_label('Motif de conservation',exact=True).fill('Conservation FICTIVE923 <copie> & partenaire');region.get_by_role('checkbox').check()
  with page.expect_response(lambda r:r.url.endswith(path(f)) and r.request.method=='POST') as r:region.get_by_role('button',name='Conserver ce PDF',exact=True).click()
  a=ok(r.value,201);expect(region).to_contain_text('PDF figé le');expect(region).to_contain_text(a['pdf_sha256']);assert region.get_by_role('button',name='Conserver ce PDF',exact=True).count()==0
  with page.expect_download() as dl:region.get_by_role('button',name='Télécharger la copie conservée',exact=True).click()
  p=tmp_path/'copie923.pdf';dl.value.save_as(p);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==a['pdf_sha256'];doc=PdfReader(BytesIO(raw));assert sum(len(p.images) for p in doc.pages)==1 and f['numero'] in ''.join(p.extract_text() or '' for p in doc.pages)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');region.scroll_into_view_if_needed();d=R/'docs/recette/preuves';d.mkdir(exist_ok=True);page.screenshot(path=str(d/f'923_{largeur}_copie.png'))
  expect(page.get_by_role('button',name='Créer un avoir',exact=True)).to_be_visible();assert comptabilite(application,sid)==avant
  page.reload();page.locator('tbody tr').filter(has_text=f['numero']).click();region=page.get_by_role('region',name='Conservation du PDF de facture');expect(region).to_contain_text(a['pdf_sha256'])
  with page.expect_download() as dl:region.get_by_role('button',name='Télécharger la copie conservée',exact=True).click()
  q=tmp_path/'copie_rechargee923.pdf';dl.value.save_as(q);assert q.read_bytes()==raw and comptabilite(application,sid)==avant
  preuve['conservation923']={'id':a['id'],'facture_id':f['id'],'sha256':a['pdf_sha256'],'logo':True,'retour_apres_rechargement':True,'octets_identiques':True,'journal_et_facture_inchanges':True,'aucun_statut_archive_definitive':True};preuve['cas'].append({'id':'HP-FAC-013','statut':'Réussi','portee':'Conservation interne de facture vente ; pas certification légale ni pièce fournisseur d’origine.'})
