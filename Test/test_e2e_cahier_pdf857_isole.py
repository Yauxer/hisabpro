"""SEC007 : export réel, identité littérale, logo incorporé et intégrité du journal."""
from io import BytesIO
import hashlib,pytest
from pypdf import PdfReader
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from test_logo_societe import image_data
from test_e2e_cahier_plafonds843_isole import facture843,valider843
from navigation823_support import navigations_completes823
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)
NOM='Atlas <SARL> & associés'

def verifier857(pdf):
 assert pdf.startswith(b'%PDF');r=PdfReader(BytesIO(pdf));t=' '.join(' '.join(p.extract_text() or '' for p in r.pages).split());assert NOM in t and 'Réf <PIECE> & 857' in t;assert sum(len(p.images) for p in r.pages)>=1
 return {'pages':len(r.pages),'identite_litterale':NOM,'reference_litterale':'Réf <PIECE> & 857','nb_images':sum(len(p.images) for p in r.pages),'sha256':hashlib.sha256(pdf).hexdigest()}

@pytest.mark.parametrize('largeur',[1440,390])
def test_857_pdf_identite_litterale_et_logo(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'pdf857') as (api,page,sid,preuve):
  logo=image_data();ok(api.patch('/api/societe/moi',json={'raison_sociale':NOM,'logo_url':logo}));t=next(t for t in DATA['tiers'] if t['code']=='C-SERVICE');tiers=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'client','compte_client':'3421'}),201);f=facture843(api,tiers,'vente','2025-01-20',1000,'Réf <PIECE> & 857');valider843(api);avant=core(application,sid);profil=ok(api.get('/api/societe/moi'));assert profil['raison_sociale']==NOM and profil['logo_url']==logo
  page.goto(application['web_url']+'/parametres');expect(champ(page,'Raison sociale')).to_have_value(NOM);page.goto(application['web_url']+'/factures');page.locator('tbody tr').filter(has_text=f['numero']).click()
  with page.expect_download() as dl:page.get_by_role('button',name='Télécharger PDF',exact=True).click()
  p=tmp_path/'facture857.pdf';dl.value.save_as(p);ui=verifier857(p.read_bytes());r=api.get(f'/api/factures/{f["id"]}/pdf');assert r.status_code==200;direct=verifier857(r.content);assert core(application,sid)==avant and ok(api.get('/api/societe/moi'))==profil;preuve['pdf857']={'UI':ui,'API':direct,'journal_identite_logo_conserves':True,'chemin_pdf_ui':str(p),'limite':'PDF facture de cette copie uniquement ;pas une validation de tous les formats ou de conformité réglementaire.'};preuve['cas'].append({'id':'HP-SEC-007','statut':'Réussi'})
