"""Étape avant IS du vrai parcours annuel, sans changer les données attendues."""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import base64,csv,io,hashlib,re
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,referentiels,DATA,ok
from cahier_suite777_support import core
from cahier_etats803_support import nombre,telecharger,valeurs_pdf
from test_e2e_cahier_immobilisation785_isole import capital,acquisition
from cahier_semestre789_support import semestre
from cahier_annuel791_support import annuel
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

R=Path(__file__).resolve().parents[1];DOC=R/'docs/recette';SOURCE=DOC/'balance_avant_is_2025.csv'

def fichier(preuve,p):preuve.setdefault('fichiers817',[]).append({'chemin':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})

def observer_navigation(page,preuve):
 pending={};echecs=[];preuve['navigation817']={'en_attente':pending,'echecs_reseau':echecs}
 page.on('request',lambda r:pending.update({str(id(r)):{'url':r.url,'type':r.resource_type}}))
 page.on('requestfinished',lambda r:pending.pop(str(id(r)),None))
 def echec(r):
  pending.pop(str(id(r)),None);echecs.append({'url':r.url,'erreur':r.failure})
 page.on('requestfailed',echec)

@pytest.mark.parametrize('largeur',[1440,390])
def test_817_filtre_statuts_export_et_validation(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'statuts817') as (api,page,sid,preuve):
  es=[]
  for ref,montant,validee in [('BROUILLON817',100,False),('VALIDEE817',200,True)]:
   e=ok(api.post('/api/ecritures',json={'date':'2025-01-01','journal':'BQ','reference':ref,'libelle':'Contrôle fictif filtre817','lignes':[{'compte':'5141','debit':montant},{'compte':'1111','credit':montant}]}),201)
   if validee:ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
   es.append(e)
  avant=core(application,sid);page.goto(application['web_url']+'/journal');filtre=page.get_by_label('État des écritures',exact=True);filtre.select_option('brouillons')
  expect(page.get_by_text('BROUILLON817',exact=True)).to_be_visible();expect(page.get_by_text('VALIDEE817',exact=True)).to_have_count(0)
  p=telecharger(page,'Exporter CSV',tmp_path,'brouillons817.csv');rows=list(csv.DictReader(io.StringIO(p.read_text(encoding='utf-8-sig')),delimiter=';'));assert len(rows)==2 and {r['Référence pièce'] for r in rows if r['Référence pièce']}=={'BROUILLON817'};fichier(preuve,p)
  filtre.select_option('validees');expect(page.get_by_text('VALIDEE817',exact=True)).to_be_visible();expect(page.get_by_text('BROUILLON817',exact=True)).to_have_count(0);assert core(application,sid)==avant
  filtre.select_option('brouillons')
  with page.expect_response(lambda r:r.url.endswith(f'/api/ecritures/{es[0]["id"]}/valider') and r.request.method=='POST') as r:page.get_by_role('button',name='Valider',exact=True).click()
  ok(r.value);expect(page.get_by_text('BROUILLON817',exact=True)).to_have_count(0);filtre.select_option('validees');expect(page.get_by_text('BROUILLON817',exact=True)).to_be_visible();expect(page.get_by_text('VALIDEE817',exact=True)).to_be_visible()
  apres=core(application,sid);assert len(apres)==2 and all(e[7] for e in apres) and [e[-1] for e in apres]==[e[-1] for e in avant];preuve['statuts817']={'filtre_et_export_coherents':True,'validation_rafraichie_sans_f5':True,'lignes_financieres_preservees':True}

def verifier_avant_is(api,page,app,sid,preuve,tmp_path,tiers):
 avant=core(app,sid);srcsha=hashlib.sha256(SOURCE.read_bytes()).hexdigest();es=ok(api.get('/api/ecritures',params={'exercice':2025}));assert len(es)==48 and all(e['est_validee'] for e in es) and not any(l['compte'].startswith('67') for e in es for l in e['lignes'])
 with SOURCE.open(encoding='utf-8-sig') as f:oracle={r['compte']:D(r['debit'])-D(r['credit']) for r in csv.DictReader(f,delimiter=';')}
 params={'exercice':2025,'date_from':'2025-01-01','date_to':'2025-12-31'};balance=ok(api.get('/api/ecritures/reporting/balance',params=params));assert balance['nb_ecritures']==48 and {r['compte']:D(str(r['solde_final'])) for r in balance['comptes'] if D(str(r['solde_final']))}=={k:v for k,v in oracle.items() if v};assert D(str(balance['controle']['mouvement_debit']))==D(str(balance['controle']['mouvement_credit']))==D('947940')
 etats=ok(api.get('/api/etats/liasse/2025'))['etats'];assert D(str(etats['cpc']['resultat_net']))==D('129830') and oracle['3453']==D('200') and oracle['5141']==D('287730')
 page.goto(app['web_url']+'/balances');expect(page.get_by_text('Balance équilibrée',exact=False)).to_be_visible()
 for genre,cle,solde in [('generale','5141','287730'),('clients',tiers['C-IMPAYE']['nom'],'14400'),('fournisseurs',tiers['F-CONTROLE']['nom'],'-480')]:
  if genre=='clients':page.get_by_role('button',name='Balance Auxiliaire',exact=False).click()
  if genre=='fournisseurs':page.get_by_role('button',name='Fournisseurs (4411)',exact=True).click()
  expect(page.get_by_text(cle,exact=True).first).to_be_visible();x=telecharger(page,'Exporter Excel',tmp_path,'avant_is_'+genre+'.xlsx');wb=load_workbook(x,data_only=True);rows=list(wb['Balance'].values);row=next(r for r in rows if r[0]==cle);assert D(str(row[-2] or 0))-D(str(row[-1] or 0))==D(solde)
  if genre=='generale':assert {str(r[0]):D(str(r[-2] or 0))-D(str(r[-1] or 0)) for r in rows if re.fullmatch('[1-7][0-9]{3,9}',str(r[0])) and (r[-2] or r[-1])}=={k:v for k,v in oracle.items() if v}
  p=telecharger(page,'Exporter PDF',tmp_path,'avant_is_'+genre+'.pdf');reader=PdfReader(p);texte='\n'.join(p.extract_text() or '' for p in reader.pages);assert cle in texte and abs(D(solde)) in valeurs_pdf(texte) and any(p.images for p in reader.pages);fichier(preuve,x);fichier(preuve,p)
  aux='3421' if genre=='clients' else '4411' if genre=='fournisseurs' else None
  if aux:assert sum((D(str(r['solde_final'])) for r in balance['auxiliaire'][aux]),D(0))==oracle[aux] and all(r['identifie'] for r in balance['auxiliaire'][aux])
 page.goto(app['web_url']+'/grand-livre');rapport=ok(api.get('/api/ecritures/reporting/grand-livre',params=params));p=telecharger(page,'Exporter CSV',tmp_path,'avant_is_grand_livre.csv');rows=list(csv.DictReader(io.StringIO(p.read_text(encoding='utf-8-sig')),delimiter=';'));attendus=[l for o in DATA['operations'] if o['reference_recette'] not in ['IS-2025','PPRF-IMP'] for l in o['lignes']];assert len(rows)==len(attendus)==114 and Counter((r['Compte'],nombre(r['Débit']),nombre(r['Crédit'])) for r in rows)==Counter((l['compte'],D(l['debit']),D(l['credit'])) for l in attendus);assert {'02','002'}<={r['Référence'] for r in rows};fichier(preuve,p)
 for compte in ['5141','3421','4411']:
  c=next(r for r in rapport['comptes'] if r['compte']==compte);assert D(str(c['solde_final']))==oracle[compte];table=page.locator('table').first;row=table.locator('tbody tr').filter(has=page.get_by_text(compte,exact=True));expect(row).to_have_count(1);assert nombre(row.locator('td').nth(5).inner_text())==oracle[compte];row.click();detail=page.locator('table').nth(1);expect(detail.locator('tbody tr')).to_have_count(len(c['mouvements']));assert nombre(detail.locator('tbody tr').last.locator('td').nth(8).inner_text())==oracle[compte]
  if compte!='5141':
   for a in balance['auxiliaire'][compte]:expect(detail.get_by_text(a['tiers'],exact=True).first).to_be_visible()
 page.goto(app['web_url']+'/journal');page.get_by_label('État des écritures',exact=True).select_option('brouillons');expect(page.get_by_role('button',name='Valider',exact=True)).to_have_count(0);assert core(app,sid)==avant and hashlib.sha256(SOURCE.read_bytes()).hexdigest()==srcsha
 preuve['avant_is817']={'balance':balance,'grand_livre':rapport,'ecritures2025':48,'lignes':114,'debit_credit':'947940','resultat_avant_is':'129830','credit3453':'200','journal_inchange_pendant_exports':True,'source_sha256':srcsha};preuve['cas'].append({'id':'HP-CPT-004','statut':'Réussi'})

@pytest.mark.parametrize('largeur',[1440,390])
def test_817_cahier_connecte_balance_et_grand_livre_avant_is(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'avant_is817') as (api,page,sid,preuve):
  observer_navigation(page,preuve)
  logo='data:image/png;base64,'+base64.b64encode((DOC/'images/LOGO_RECETTE_FICTIF.png').read_bytes()).decode();ok(api.patch('/api/societe/moi',json={'logo_url':logo}));tiers,articles=referentiels(api,page,application,sid,preuve);b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  capital(page,application,sid,preuve);immo=acquisition(api,page,application,sid,tiers['F-IMMO'],preuve);semestre(api,page,application,sid,tiers,articles,banque,preuve,tmp_path)
  annuel(api,page,application,sid,tiers,articles,banque,immo,preuve,avant_is=lambda:verifier_avant_is(api,page,application,sid,preuve,tmp_path,tiers));assert preuve['avant_is817']['journal_inchange_pendant_exports'] and preuve['annuel791']['ecritures2025']==50
