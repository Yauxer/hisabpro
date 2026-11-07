"""Parcours intégré733 : oracles indépendants et tous compléments sur mêmes balances."""
from pathlib import Path
from contextlib import closing
from copy import deepcopy
from datetime import date
from decimal import Decimal
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import csv,hashlib,json
from openpyxl import load_workbook
from pypdf import PdfReader
from test_balance_c3_extra731_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,image_data,c3_body,c3_url)
from test_balance_passage_fiscal725_isole import url as b12_url
from test_balance_resultat_courant721_isole import url as b13_url
from test_balance_tva727_isole import url as b14_url
from test_balance_comparatif_n2729_isole import url as n2_url
from test_balance_c3_extra731_isole import url as extra_url
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'docs/recette/DONNEES_INTEGREES733.json').read_text(encoding='utf8'))


def payload(v,tables):return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':tables}
def tableau(code,rows):return {'code':code,'statut':'documente','justification':'Synthèse intégrée fictive733','lignes':rows}
def b12_body(v):return payload(v,[tableau('B12-N',[D['b12']])])
def b13_body(v):return payload(v,[tableau(r['code'],[{k:x for k,x in r.items() if k!='code'}]) for r in D['b13']])
def b14_body(v):return payload(v,[tableau('B14-N',D['b14'])])
def extra_body(v):return payload(v,[tableau(r['code'],[{k:x for k,x in r.items() if k!='code'}]) for r in D['extra']])
def n2_body(v,s):return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'source_preparation_id':s['id'],
 'source_empreinte_sha256':s['empreinte_sha256'],'reference_source':D['reference_n2']}


def sources(api):
 ok(api.patch('/api/societe/moi',json={'raison_sociale':D['societe_fictive'],'logo_url':image_data('PNG')}))
 ex=ok(api.get('/api/exercices'))
 for annee in (2024,2025,2026):
  if not any(r['annee']==annee for r in ex):ok(api.post('/api/exercices',json={'annee':annee,'date_debut':f'{annee}-01-01','date_fin':f'{annee}-12-31'}),201)
 s=ok(api.post(BASE,json={'exercice':2024,'lignes_n':D['n2'],'fichier_n':'BALANCE_FICTIVE_INTEGREE733_N2.csv'}),201)
 v=ok(api.post(BASE,json={'exercice':2026,'lignes_n':D['n'],'lignes_n1':D['n1'],'fichier_n':'BALANCE_FICTIVE_INTEGREE733_N.csv','fichier_n1':'BALANCE_FICTIVE_INTEGREE733_N1.csv'}),201)
 return s,v


def completer(api,s,v):
 v=ok(api.post(n2_url(v),json=n2_body(v,s)),201);v=ok(api.post(c3_url(v),json=c3_body(v)),201)
 old=deepcopy(v['contenu']['indicateurs_comptables_documentaires'])
 for endpoint,body in [(b12_url,b12_body),(b13_url,b13_body),(b14_url,b14_body),(extra_url,extra_body)]:
  v=ok(api.post(endpoint(v),json=body(v)),201)
  assert v['contenu']['indicateurs_comptables_documentaires']==old
 return ok(api.post(c3_url(v),json=c3_body(v)),201)


def verifier(v):
 c=v['contenu'];a=D['attendus'];vue=c['indicateurs_comptables_documentaires']['vue']
 for p in ('n','n1','n2'):
  r=vue['periodes'][p];assert r['resultat_net']==a['net_'+p] and r['situation_nette']==a['situation_'+p]
  assert r['ecart_resultat_net']==r['ecart_situation_nette']=='0.00'
 assert vue['periodes']['n']['resultat_par_titre']=='60.20' and vue['periodes']['n']['effectif_moyen']=='3.50'
 assert not vue['pret_a_deposer'] and vue['informations_a_completer']==[]
 b12=c['passage_fiscal_documentaire']['controle_passage_fiscal']['montants']
 assert b12['resultat_net_comptable']=='6020.00' and b12['impots_comptabilises_67']==b12['is_theorique_taux_declare']=='1580.00'
 assert b12['resultat_avant_impots']=='7600.00' and b12['resultat_fiscal_avant_deficit']==b12['benefice_fiscal_propose']=='7900.00'
 assert all(x is None for x in c['passage_fiscal_documentaire']['controle_passage_fiscal']['liquidation'].values())
 b13=c['resultat_courant_documentaire']['controle_resultat_courant']['periodes']
 assert b13['n']['resultat_courant']=='6600.00' and b13['n']['base_courante_documentaire']=='6900.00'
 assert b13['n']['courant_apres_impot_declare']=='5220.00' and b13['n1']['courant_apres_impot_declare'] is None
 tva=c['tva_documentaire']['controle_tva'];assert not tva['alertes'] and not tva['depot_confirme']
 assert [r['montants']['solde_fin_reconstitue'] for r in tva['lignes']]==['1000.00','500.00','200.00','700.00','300.00']
 assert all(r['montants']['ecart_fin']=='0.00' for r in tva['lignes'])


def verifier_export(raw,v):
 with ZipFile(BytesIO(raw)) as z:
  assert z.testzip() is None;m=json.loads(z.read('MANIFESTE_SHA256.json'))
  assert set(z.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
  for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
  for p,nom in [('n','N'),('n1','N1'),('n2','N2')]:
   attendues=[{'compte':r['compte'],**{k:format(Decimal(r[k]),'.2f') for k in ('debit','credit')}} for r in sorted(D[p],key=lambda r:r['compte'])]
   assert list(csv.DictReader(z.read(f'balance_{nom}.csv').decode('utf8').splitlines(),delimiter=';'))==attendues
  assert json.loads(z.read('passage_fiscal_documentaire.json'))['controle_passage_fiscal']==v['contenu']['passage_fiscal_documentaire']['controle_passage_fiscal']
  assert json.loads(z.read('indicateurs_comptables_documentaires.json'))['vue']['periodes']['n']['resultat_par_titre']=='60.20'
  w=load_workbook(BytesIO(z.read('preparation.xlsx')))
  assert w['Indicateurs C3 N']['B2'].value==17520 and w['Indicateurs C3 N']['B6'].value==6020
  assert w['Déclarations C3 N']['F2'].value==60.2 and 'personnes' in w['Déclarations C3 N']['D1'].value
  assert dict(list(w['Contrôle B12 N'].values)[1:])['IS théorique selon taux déclaré']=='1580.00'
  assert w['Contrôle B14 N']['H6'].value==0
  with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(p.startswith('xl/media/') for p in x.namelist())
  pdf=PdfReader(BytesIO(z.read('preparation.pdf')));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
  assert len(pdf.pages)<63
  assert all(x in t for x in ['B12','B13','B14','C3','SOURCE INTEGREE733','personnes']) and any(p.images for p in pdf.pages)
 return {'fichiers':len(m['fichiers']),'pdf_pages':len(pdf.pages),'xlsx_feuilles':len(w.sheetnames),'manifestes_et_logo':True}


def test_733_parcours_api_oracles_croises_exports_et_temoins(application):
 with closing(client(application)[0]) as api:
  s,v=sources(api);avant=donnees_metier(application);old=deepcopy(v);r=completer(api,s,v);verifier(r)
  rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200;export=verifier_export(rep.content,r)
  assert ok(api.get(BASE+f'/{s["id"]}'))==s and ok(api.get(BASE+f'/{old["id"]}'))==old
  apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
  (R/'.codex-tests/recette733_api_preuve.json').write_text(json.dumps({'schema':104,'role_sql':application['role_sql'],
   'oracles_croises_valides':True,'metier_hors_preparation_inchange':True,'sources_versions_anciennes_preservees':True,
   'export':export,'exercice':2026,'aucune_base_reelle':True},ensure_ascii=False,indent=2),encoding='utf8')
