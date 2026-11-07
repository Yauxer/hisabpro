"""Campagne annuelle connectée et garde-fous comptables, PostgreSQL natif isolé."""
from decimal import Decimal as D
from sqlalchemy import text
import pytest
from playwright.sync_api import expect
from navigation823_support import navigations_completes823
from cahier_formulaires773_support import laboratoire,referentiels,DATA,ok
from test_e2e_cahier_immobilisation785_isole import capital,acquisition
from cahier_semestre789_support import semestre
from cahier_annuel791_support import annuel
from cahier_cloture793_support import cloturer_cahier
from cahier_etats803_support import verifier_etats
from cahier_suite777_support import core
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def refus839(r,codes):
 assert r.status_code in codes,r.text
 return {'statut':r.status_code,'detail':r.json().get('detail')}


@pytest.fixture
def navigation_observee839(navigations_completes823,monkeypatch,tmp_path):
 from playwright.sync_api import Page
 import json
 from pathlib import Path
 original=Page.goto;actifs={};recents=[];installees=set()
 def aller(page,url,**kw):
  if id(page) not in installees:
   installees.add(id(page))
   def debut(r):actifs[id(r)]={'methode':r.method,'url':r.url.split('?')[0],'type':r.resource_type}
   def fin(r):actifs.pop(id(r),None)
   def reponse(r):
    recents.append({'statut':r.status,'url':r.url.split('?')[0]})
    if len(recents)>30:recents.pop(0)
   page.on('request',debut);page.on('requestfinished',fin);page.on('requestfailed',fin);page.on('response',reponse)
  try:return original(page,url,**kw)
  except BaseException as exc:
   preuve={'erreur':repr(exc),'destination':url.split('?')[0],'en_attente':list(actifs.values()),'dernieres_reponses':recents,'aucun_secret_enregistre':True}
   (Path(__file__).resolve().parents[1]/'.codex-tests'/f'navigation839_{page.viewport_size["width"]}_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
   raise
 monkeypatch.setattr(Page,'goto',aller)

@pytest.mark.parametrize('largeur',[1440,390])
def test_839_cycle_annuel_et_integrite(application,largeur,tmp_path,navigation_observee839):
 with laboratoire(application,largeur,tmp_path,'integrite839') as (api,page,sid,preuve):
  tiers,articles=referentiels(api,page,application,sid,preuve);b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  capital(page,application,sid,preuve);immo=acquisition(api,page,application,sid,tiers['F-IMMO'],preuve);semestre(api,page,application,sid,tiers,articles,banque,preuve,tmp_path)
  avant=core(application,sid);uid=ok(api.get('/api/auth/me'))['id'];fid=preuve['cycle']['factures'][2];f=next(x for x in ok(api.get('/api/factures',params={'exercice':2025})) if x['id']==fid);assert f['est_validee'] and f['est_comptabilisee'];assert any(D(str(l['prix_unitaire']))==250 for l in f['lignes'])
  page.goto(application['web_url']+'/factures');row=page.locator('tbody tr').filter(has_text=f['numero']);expect(row.get_by_title('Modifier le brouillon',exact=True)).to_have_count(0);expect(row.get_by_title("Générer l'écriture comptable de cette facture",exact=True)).to_have_count(0)
  res={};preuve['integrite839']=res;res['HP-NEG-010']=refus839(api.post(f'/api/factures/{fid}/comptabiliser'),{409})
  modification={'lignes':[{'article_id':articles['M-01']['id'],'description':'Marchandise fictive VENTE-01','quantite':100,'prix_unitaire':251,'tva':20}]};res['HP-NEG-011']=refus839(api.patch(f'/api/factures/{fid}',json=modification),{400,409,423})
  eid=avant[0][0];res['journal_definitif']={'edition':refus839(api.patch(f'/api/ecritures/{eid}',json={'libelle':'Tentative interdite839'}),{423}),'suppression':refus839(api.delete(f'/api/ecritures/{eid}'),{423})};assert core(application,sid)==avant and next(x for x in ok(api.get('/api/factures',params={'exercice':2025})) if x['id']==fid)==f
  page.goto(application['web_url']+'/cloture');janvier=next(p for p in ok(api.get('/api/exercices/2025/periodes')) if p['numero']==1)
  with page.expect_response(lambda r:r.url.endswith('/api/exercices/2025/periodes/1') and r.request.method=='PATCH') as rr:page.get_by_title('Fermer '+janvier['libelle'],exact=True).click()
  assert rr.value.status==200
  tentative={'date':'2025-01-15','journal':'BQ','reference':'REFUS-839','libelle':'Tentative période fermée fictive','lignes':[{'compte':'5141','debit':1},{'compte':'1111','credit':1}]};ferme=refus839(api.post('/api/ecritures',json=tentative),{423});assert core(application,sid)==avant
  with page.expect_response(lambda r:r.url.endswith('/api/exercices/2025/periodes/1') and r.request.method=='PATCH') as rr:page.get_by_title('Ouvrir '+janvier['libelle'],exact=True).click()
  assert rr.value.status==200 and core(application,sid)==avant
  with application['engine'].connect() as db:
   audit=db.execute(text('SELECT ancien_statut,nouveau_statut,acteur_id,motif FROM audit_periodes_comptables a JOIN exercices_comptables e ON e.id=a.exercice_id WHERE e.societe_id=:sid AND e.annee=2025 AND a.numero=1 ORDER BY a.id'),{'sid':sid}).all()
   assert [(a.ancien_statut,a.nouveau_statut,a.acteur_id) for a in audit]==[('ouverte','fermee',uid),('fermee','ouverte',uid)] and all(a.motif for a in audit)
  res['HP-NEG-037']={'refus_creation':ferme,'fermeture_reouverture_UI':200,'audit_deux_transitions_acteur':True,'originaux_conserves':True}
  ok(api.post('/api/exercices',json={'annee':2027,'date_debut':'2027-01-01','date_fin':'2027-12-31'}),201);res['HP-NEG-038']=refus839(api.post('/api/cloture/cloturer',params={'exercice':2027}),{409});assert 'prématur' in res['HP-NEG-038']['detail'].lower() and core(application,sid)==avant
  annuel(api,page,application,sid,tiers,articles,banque,immo,preuve)
  import re
  from test_e2e_cahier_lettrage815_isole import lire,choisir
  avant_lettres=core(application,sid);preuve['lettrage_connecte839']=[];page.goto(application['web_url']+'/lettrage')
  for compte,cle in [('3421','C-MARCH'),('3421','C-SERVICE'),('4411','F-SERVICE')]:
   nom=tiers[cle]['nom'];lignes=[l for l in lire(api,compte) if l['tiers']==nom];assert len(lignes)>=2 and not any(l['code_lettrage'] for l in lignes);debit=sum(D(str(l['debit'])) for l in lignes);credit=sum(D(str(l['credit'])) for l in lignes);assert debit==credit and debit>0
   choisir(page,compte,nom);boxes=page.locator('tbody input[type=checkbox]');expect(boxes).to_have_count(len(lignes))
   for box in boxes.all():box.check()
   with page.expect_response(lambda r:r.url.endswith('/api/lettrage/comptable/lettrer') and r.request.method=='POST') as rr:page.get_by_role('button',name=f'Lettrer {len(lignes)} lignes',exact=True).click()
   lettre=ok(rr.value);assert lettre['nb']==len(lignes) and set(lettre['ligne_ids'])=={l['ligne_id'] for l in lignes} and re.fullmatch('[A-Z]{3,10}',lettre['code']);page.reload(wait_until='domcontentloaded');choisir(page,compte,nom);expect(page.get_by_text(f'{len(lignes)} lettrée(s)',exact=True)).to_be_visible();assert all(l['code_lettrage']==lettre['code'] for l in lire(api,compte) if l['tiers']==nom)
   preuve['lettrage_connecte839'].append({'tiers':cle,'compte':compte,'nb':len(lignes),'code':lettre['code'],'debit':str(debit),'credit':str(credit)})
  assert core(application,sid)==avant_lettres and len({l['code'] for l in preuve['lettrage_connecte839']})==3
  cloturer_cahier(api,page,application,sid,preuve)
  clos=core(application,sid);tentative['date']='2025-12-31';res['HP-NEG-039']={'creation':refus839(api.post('/api/ecritures',json=tentative),{423}),'edition':refus839(api.patch(f'/api/ecritures/{eid}',json={'libelle':'Interdit après clôture'}),{423}),'suppression':refus839(api.delete(f'/api/ecritures/{eid}'),{423}),'reouverture':refus839(api.patch('/api/exercices/2025/periodes/1',json={'statut':'ouverte'}),{423}),'facture':refus839(api.patch(f'/api/factures/{fid}',json=modification),{400,409,423})}
  res['HP-NEG-040']=refus839(api.post('/api/cloture/cloturer',params={'exercice':2025}),{400});assert core(application,sid)==clos
  with application['engine'].connect() as db:assert db.scalar(text("SELECT count(*) FROM ecritures WHERE societe_id=:sid AND exercice=2026 AND journal='AN'"),{'sid':sid})==1
  verifier_etats(api,page,application,sid,preuve,tmp_path);assert core(application,sid)==clos;res['originaux_conserves']=True;res['report_AN_unique']=True;res['aucun_contournement_cloture']=True
  preuve['cas'] += [{'id':c,'statut':'Réussi'} for c in res if c.startswith('HP-NEG-')]

  # CLO009 : archive annuelle figée, puis opération distincte dans l'exercice suivant.
  from services.livre_inventaire_service import empreinte_snapshot
  from cahier_etats803_support import telecharger,enregistrer,valeurs_pdf
  from pypdf import PdfReader
  page.goto(application['web_url']+'/livre-inventaire');expect(page.get_by_role('button',name='Archiver définitivement',exact=True)).to_be_enabled();avant_archive=core(application,sid)
  with page.expect_response(lambda r:'/api/inventaire/livre/archiver?exercice=2025' in r.url and r.request.method=='POST') as rr:page.get_by_role('button',name='Archiver définitivement',exact=True).click()
  fige=ok(rr.value);archive=fige['archive'];assert archive['cree_par']==uid and archive['date_etablissement'] and archive['version']>=2;assert empreinte_snapshot(fige['snapshot'])==archive['empreinte_sha256'];expect(page.get_by_text('Archive v'+str(archive['version'])+' figée',exact=True)).to_be_visible();assert core(application,sid)==avant_archive
  pdf=telecharger(page,'Exporter PDF',tmp_path,'livre839_archive.pdf');txt='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert set(map(D,['337010','6600','24000','4800','19200']))<=valeurs_pdf(txt);enregistrer(preuve,pdf,'Livre inventaire archivé839 PDF')
  page.get_by_label('Exercice comptable',exact=True).select_option('2026');ok(api.post('/api/ecritures',json={'date':'2026-01-02','date_piece':'2026-01-02','journal':'BQ','reference':'TEMOIN-2026-839','libelle':'Témoin fictif année suivante pour conservation archive','est_validee':True,'lignes':[{'compte':'5141','debit':1},{'compte':'1111','credit':1}]}),201)
  assert [e for e in core(application,sid) if e[1].year==2025]==[e for e in avant_archive if e[1].year==2025];assert ok(api.get('/api/inventaire/livre',params={'exercice':2025}))==fige;assert api.post('/api/inventaire/livre/archiver',params={'exercice':2025}).status_code==409
  page.get_by_label('Exercice comptable',exact=True).select_option('2025');page.goto(application['web_url']+'/livre-inventaire');expect(page.get_by_text(archive['empreinte_sha256'],exact=False)).to_be_visible();expect(page.get_by_role('button',name='Archiver définitivement',exact=True)).to_have_count(0)
  preuve['archive839']={'archive':archive,'empreinte_recalculee':True,'snapshot_identique_apres_ecriture2026':True,'originaux2025_conserves':True,'double_archive_refusee':409,'pdf_montants_verifies':True};preuve['cas'].append({'id':'HP-CLO-009','statut':'Réussi'})
