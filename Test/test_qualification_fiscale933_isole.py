"""Qualification des cas755 manquants ;préparation interne,API/Edge/PG nonce."""
from contextlib import closing
from copy import deepcopy
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import json,hashlib,httpx,pytest
from pypdf import PdfReader
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright,expect
from fiscal755_support import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,R,D,creer,bodies,verifier,verifier_export,
 credits_url,ap_url,liq_url,b12_url,cm_url)
from test_logo_societe import image_data
from test_balance_documents691_isole import joindre,path as docs_url
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_participations707_isole import ouvrir
from test_e2e_balance_liquidation753_isole import SUMMARY,REGION,SAVE,SELECTION
from browser_support import chromium_executable
from navigation823_support import navigations_completes823

def conserver_preuve(nom,**v):
 (R/f'.codex-tests/fiscal933_{nom}.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')

def dossier(api):
 ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
 e=ok(api.post('/api/ecritures',json={'date':'2026-01-01','journal':'BQ','reference':'TEMOIN-FICTIF933','libelle':'Capital témoin indépendant des balances externes','lignes':[{'compte':'5141','debit':333},{'compte':'1111','credit':333}]}),201)
 ok(api.post(f'/api/ecritures/{e["id"]}/valider'));v=creer(api);verifier(v);return v

def seuls(avant,apres,*autorises):
 assert set(avant)==set(apres)
 assert all(apres[k]==v for k,v in avant.items() if k not in autorises)

def test_933_affectations_inversees_references_exactes_et_ancienne_version(application):
 with closing(client(application)[0]) as api:
  v=dossier(api);avant=donnees_metier(application);b=bodies(v)['acomptes'];r=b['tables'][1]['lignes'];r[0]['reference_credit'],r[1]['reference_credit']=r[1]['reference_credit'],r[0]['reference_credit']
  v2=ok(api.post(ap_url(v),json=b),201);c=v2['contenu']['acomptes_is_documentaires']['controle_acomptes']
  assert c['montants']['ecart_retenues']=='0.00' and c['montants']['acomptes_proposes'] is None and not all(x['coherent'] for x in c['rapprochement_retenues'])
  assert ok(api.get(liq_url(v2)))['sources_is_modifiees']
  v3=ok(api.post(liq_url(v2),json=bodies(v2)['liquidation']),201);assert v3['contenu']['liquidation_is_documentaire']['controle_liquidation']['montants']['solde_is_propose'] is None
  assert ok(api.get(BASE+f'/{v["id"]}'))==v;seuls(avant,donnees_metier(application),'liasse_balances_preparation')
  conserver_preuve('references',fiche='F755-12',references_inversees=True,total_retenues_toujours_150=True,acomptes_et_solde_indisponibles=True,ancienne_version_3650_conservee=True,temoin_comptable_definitif_inchange=True)

def test_933_b12_change_cm_requise_avant_nouvelle_proposition(application):
 with closing(client(application)[0]) as api:
  v=dossier(api);avant=donnees_metier(application);ancien=deepcopy(v['contenu']['liquidation_is_documentaire']['controle_liquidation']);b=bodies(v)['b12'];b['tables'][0]['lignes'][0].update(reintegrations='1000',regime_avantages='Hypothèse fictive933 :réintégration1000,aucun avantage ou déficit déclaré',reference_source='Hypothèse fictive933 de réintégration documentée1000 ;aucune écriture réelle')
  v2=ok(api.post(b12_url(v),json=b),201);vue=ok(api.get(liq_url(v2)));assert vue['sources_is_modifiees'] and vue['controle_liquidation']==ancien
  v3=ok(api.post(liq_url(v2),json=bodies(v2)['liquidation']),201);assert v3['contenu']['liquidation_is_documentaire']['controle_liquidation']['montants']['solde_is_propose'] is None
  v4=ok(api.post(cm_url(v3),json=bodies(v3)['cm']),201);v5=ok(api.post(liq_url(v4),json=bodies(v4)['liquidation']),201)
  m=v5['contenu']['liquidation_is_documentaire']['controle_liquidation']['montants'];assert m['solde_is_propose']=='3850.00'
  assert ok(api.get(BASE+f'/{v["id"]}'))==v;seuls(avant,donnees_metier(application),'liasse_balances_preparation')
  conserver_preuve('sources',fiche='F755-13',ancienne_proposition_figee='3650.00',nouvelle_avant_CM=None,nouvelle_apres_CM='3850.00',oracle='(120000+1000)*20%−350−20000=3850 selon hypothèse du scénario',aucune_liquidation_confirmee=True,temoin_comptable_definitif_inchange=True)

def test_933_piece_fictive_et_exports_manifestes_logo_sources_figees(application):
 with closing(client(application)[0]) as api:
  v=dossier(api);avant=donnees_metier(application);raw=(R/'docs/recette/JUSTIFICATIFS_FICTIFS755.pdf').read_bytes()
  doc=ok(joindre(api,v,raw=raw,nom='JUSTIFICATIFS_FICTIFS755.pdf',reference='Dossier annuel FICTIF755'),201)
  rep=api.get(BASE+f'/{v["id"]}/zip');assert rep.status_code==200;export=verifier_export(rep.content,v)
  with ZipFile(BytesIO(rep.content)) as z:assert any(z.read(n)==raw for n in z.namelist())
  assert ok(api.get(BASE+f'/{v["id"]}'))==v;seuls(avant,donnees_metier(application),'liasse_balance_documents')
  conserver_preuve('piece',fiche='F755-09',piece_sha256=hashlib.sha256(raw).hexdigest(),document_id=doc['id'],export=export,snapshot_et_temoin_comptable_inchanges=True)

@pytest.mark.parametrize('largeur',[1440,390])
def test_933_lecteur_consulte_et_telecharge_le_dossier_annuel755(application,largeur,tmp_path,navigations_completes823):
 with closing(client(application)[0]) as api,sync_playwright() as p:
  v=dossier(api);email=f'lecteur933-{v["id"]}@hisabpro-recette.example';password='LectureFictive933!';ok(api.post('/api/utilisateurs',json={'nom':'Lecteur FICTIF933','email':email,'mot_de_passe':password,'role':'lecture'}),201)
  browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(15000);errors,server=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2026');avant=donnees_metier(application);panel,_=ouvrir(page,application,v,True)
   panel.get_by_text(SUMMARY,exact=True).click();detail=panel.get_by_role('region',name=REGION,exact=True);expect(detail).to_contain_text('3.650,00 MAD');expect(detail.get_by_role('button',name=SAVE,exact=True)).to_have_count(0)
   expect(detail.get_by_label(SELECTION,exact=True)).to_be_enabled()
   for control in detail.locator('input,select,textarea').all():
    if control.get_attribute('aria-label')!=SELECTION:expect(control).to_be_disabled()
   expect(panel.get_by_label('Balance N',exact=True)).to_have_count(0)
   with page.expect_download() as dl:panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
   export=verifier_export(Path(dl.value.path()).read_bytes(),v)
   directs={}
   for format,label in [('pdf','Exporter la préparation PDF'),('xlsx','Exporter la préparation Excel')]:
    with page.expect_download() as dl:panel.get_by_role('button',name=label,exact=True).click()
    flux=Path(dl.value.path()).read_bytes()
    if format=='pdf':
     pdf=PdfReader(BytesIO(flux));assert '3 650,00' in '\n'.join(p.extract_text() or '' for p in pdf.pages) and any(p.images for p in pdf.pages)
    else:
     wb=load_workbook(BytesIO(flux));vals=dict(list(wb['Proposition IS CM'].values)[1:]);assert vals['Solde IS/CM proposé à payer']==3650;wb.close()
     with ZipFile(BytesIO(flux)) as archive:assert any(n.startswith('xl/media/') for n in archive.namelist())
    directs[format]={'sha256':hashlib.sha256(flux).hexdigest(),'montant3650_et_logo_verifies':True}
   token=page.evaluate("localStorage.getItem('hisabpro_token')")
   with httpx.Client(base_url=application['api_url'],headers={'Authorization':'Bearer '+token},timeout=30) as lecteur:
    assert lecteur.post(liq_url(v),json=bodies(v)['liquidation']).status_code==403
   assert donnees_metier(application)==avant and not errors and not server,(errors,server)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');d=R/'docs/recette/preuves';d.mkdir(exist_ok=True);page.screenshot(path=str(d/f'933_{largeur}_lecteur_preparation755.png'))
   conserver_preuve(f'lecteur_{largeur}',fiche='F755-10',largeur=largeur,lecture_et_export_reels=True,creation_absente=True,mutation_API_refusee=403,export=export,exports_individuels_reels=directs,sources_et_temoin_comptable_definitif_inchanges=True)
  finally:browser.close()

@pytest.mark.parametrize('largeur',[1440,390])
def test_933_csv_doublon_et_nan_refuses_dans_le_vrai_import(application,largeur,tmp_path,navigations_completes823):
 api,email,password=client(application)
 with closing(api),sync_playwright() as p:
  v=dossier(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
  try:
   page=browser.new_page(viewport={'width':largeur,'height':1100});page.set_default_timeout(15000);errors,server=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
   page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2026');avant=donnees_metier(application)
   page.goto(application['web_url']+'/liasse-fiscale');panel=page.locator('section').filter(has=page.get_by_role('heading',name='Préparer depuis des balances externes',exact=True));panel.get_by_role('button',name='Importer N / N-1',exact=True).click()
   source=(R/'docs/recette/BALANCE_FICTIVE_FISCALE755_N.csv').read_text(encoding='utf8');lignes=source.splitlines();refus={}
   for cas,texte,motif in [('doublon','\n'.join(lignes+[lignes[1]])+'\n','doublon'),('nan',source.replace('0.00;10000.00','0.00;NaN',1),'fini')]:
    f=tmp_path/f'BALANCE_FICTIVE933_{cas}.csv';f.write_text(texte,encoding='utf8');panel.get_by_label('Balance N',exact=True).set_input_files(str(f))
    with page.expect_response(lambda r:r.url.endswith('/api/etats/liasse/balance/preview') and r.request.method=='POST') as rr:panel.get_by_role('button',name='Contrôler et préparer',exact=True).click()
    assert rr.value.status==422 and motif in rr.value.text().lower(),rr.value.text();expect(panel.get_by_role('alert')).to_be_visible();expect(panel.get_by_role('button',name='Conserver une nouvelle version',exact=True)).to_have_count(0)
    assert donnees_metier(application)==avant;refus[cas]=422
   assert not errors and not server,(errors,server);d=R/'docs/recette/preuves';d.mkdir(exist_ok=True);page.screenshot(path=str(d/f'933_{largeur}_csv_invalide.png'))
   conserver_preuve(f'csv_{largeur}',fiche='F755-14',largeur=largeur,vrais_fichiers_CSV=True,refus=refus,aucune_version_ni_ecriture_creee=True,ancienne_preparation_conservee=ok(api.get(BASE+f'/{v["id"]}'))==v)
  finally:browser.close()
