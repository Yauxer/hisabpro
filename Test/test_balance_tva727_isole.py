"""B14 : flux sourcés, inconnus, versions et PostgreSQL natif isolé."""
from contextlib import closing
from copy import deepcopy
from datetime import date
from io import BytesIO
from zipfile import ZipFile
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import hashlib,json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from test_balance_passage_fiscal725_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,image_data)

def url(v):return BASE+f'/{v["id"]}/tva-documentaire'

def lignes(n1=False):
 def row(c,d='0',cr='0'):return {'compte':c,'debit':d,'credit':cr}
 return [row('1111',cr='10000'),row('5141',d='10150' if n1 else '10300'),
  row('4455',cr='300' if n1 else '1000'),row('34552',d='100' if n1 else '500'),row('34551',d='50' if n1 else '200')]

def creer(api,comparatif=True):
 return ok(api.post(BASE,json={'exercice':date.today().year,'lignes_n':lignes(),
  'lignes_n1':lignes(True) if comparatif else None,'fichier_n':'Fictif727_N.csv',
  'fichier_n1':'Fictif727_N1.csv' if comparatif else None}),201)

def source():return {'contenu':{'sources':{'n':lignes(),'n1':lignes(True)}}}

def body(v,partiel=False,zeros=False):
 return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
  {'code':'B14-N','statut':'documente','justification':'Synthèse fictive727, déclarations explicitement justifiées',
   'lignes':[{'nature':f,'solde_debut':'0' if zeros else d,'operations':'0' if zeros else o,'declarations':None if partiel else '0' if zeros else t,
    'references_declarations':'' if partiel else 'DECL FICTIVE727 '+f,
    'reference_source':'NOTE FICTIVE727 '+f} for f,d,o,t in
    [('4455','300','2000','1300'),('34552','100','800','400'),('34551','50','300','150')]]}]}

@pytest.mark.parametrize('cas',['normal','partiel','n1_absent','n_absent','incomplet','vide','inverse','ecart','neant','zero','grand','n1_differe'])
def test_727_oracles_flux_inconnus_et_comparatif_non_ouverture(cas):
 from services.balance_tva_documentaire_service import calculer_controles
 d=source();q=body({'empreinte_sha256':'a'*64},cas=='partiel');rows=q['tables'][0]['lignes']
 if cas=='n1_absent':d['contenu']['sources']['n1']=None
 elif cas=='n_absent':d['contenu']['sources']['n']=None
 elif cas=='incomplet':d['contenu']['sources']['n'][0].pop('debit')
 elif cas=='vide':d['contenu']['sources']['n']=[]
 elif cas=='inverse':rows[0].update(solde_debut='-300',operations='2000',declarations='700')
 elif cas=='ecart':rows[0]['operations']='1999.99'
 elif cas=='neant':q['tables'][0].update(statut='neant_declare',lignes=[])
 elif cas=='zero':
  for row in rows:row.update(solde_debut='0',operations='0',declarations='0')
 elif cas=='grand':d['contenu']['sources']['n']=[{'compte':'4455'+str(i),'debit':'0','credit':'9999999999999.99'} for i in range(2)]
 elif cas=='n1_differe':d['contenu']['sources']['n1'][2]['credit']='299'
 avant=deepcopy(d);v=calculer_controles(d,q);assert d==avant
 assert not v['pret_a_deposer'] and not v['depot_confirme'] and not v['liquidation_calculee'];json.dumps(v,allow_nan=False)
 a,b,c,rec,net=[r['montants'] for r in v['lignes']]
 if cas in ('n_absent','incomplet'):assert a['solde_fin_balance_n'] is None and not v['sources']['n']['disponible']
 elif cas=='vide':assert a['solde_fin_balance_n']=='0.00'
 elif cas=='grand':assert a['solde_fin_balance_n']=='19999999999999.98'
 else:
  assert a['solde_fin_balance_n']=='1000.00' and rec['solde_fin_balance_n']=='700.00' and net['solde_fin_balance_n']=='300.00'
  if cas in ('partiel','neant'):assert a['solde_fin_reconstitue'] is rec['solde_fin_reconstitue'] is net['ecart_fin'] is None
  elif cas=='zero':assert a['solde_fin_reconstitue']=='0.00' and a['ecart_fin']=='-1000.00'
  elif cas=='ecart':assert a['solde_fin_reconstitue']=='999.99' and a['ecart_fin']=='-0.01' and v['alertes']
  else:assert a['solde_fin_reconstitue']=='1000.00' and a['ecart_fin']=='0.00' and net['solde_fin_reconstitue']=='300.00'
 if cas=='n1_differe':assert a['solde_debut_declare']=='300.00' and a['solde_fin_balance_n1_memoire']=='299.00'
 elif cas=='n1_absent':assert a['solde_fin_balance_n1_memoire'] is None
 else:assert a['solde_fin_balance_n1_memoire']=='300.00'
 if cas=='neant':assert v['alertes']

@pytest.mark.parametrize('valeur',['NaN','Infinity',True,'-1','0.001'])
def test_727_source_invalide(valeur):
 from services.balance_tva_documentaire_service import calculer_controles
 d=source();d['contenu']['sources']['n'][2]['credit']=valeur
 with pytest.raises(ValueError):calculer_controles(d,body({'empreinte_sha256':'a'*64}))

def test_727_versions_rejeu_sans_recalcul_metier_et_notes(application,monkeypatch):
 from services import balance_tva_documentaire_service as s
 from routers.etats import BalanceTvaIn
 with closing(client(application)[0]) as api:
  v=creer(api);avant=donnees_metier(application);assert ok(api.get(url(v)))['controle_tva'] is None
  b=body(v);r=ok(api.post(url(v),json=b),201);vue=ok(api.get(url(r)))
  assert vue['controle_tva']['lignes'][4]['montants']['solde_fin_reconstitue']=='300.00'
  assert ok(api.get(BASE+f'/{v["id"]}'))==v and all(r['contenu'][k]==x for k,x in v['contenu'].items())
  def interdit(*a,**kw):raise AssertionError('Rejeu/lecture/export sans calcul')
  monkeypatch.setattr(s,'calculer_controles',interdit);monkeypatch.setattr(s,'sources',interdit)
  with Session(application['engine']) as db:assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceTvaIn.model_validate(b))==r
  assert ok(api.get(url(r)))==vue and api.get(BASE+f'/{r["id"]}/zip').status_code==200
  apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
 d=source();d['contenu']['notes_etic_documentaires']={'lignes':[{'code':'B14','statut':'non_applicable'}]}
 d['contenu'][s.BLOC]={'catalogue':s.catalogue(d),'tables':b['tables']}
 assert any('note B14' in a for a in s.presentation(d)['alertes'])

@pytest.mark.parametrize('cas',['nan','inf','bool','precision','hors_limites','references','source','nature','doublon','quatre','colonne','omission','champ'])
def test_727_rejets_sans_mutation(application,cas):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);r=b['tables'][0]['lignes'][0]
  if cas in ('nan','inf','bool','precision','hors_limites'):r['operations']={'nan':'NaN','inf':'Infinity','bool':True,'precision':'0.001','hors_limites':'10000000000000'}[cas]
  elif cas=='references':r['references_declarations']=''
  elif cas=='source':r['reference_source']=''
  elif cas=='nature':r['nature']='4456'
  elif cas=='doublon':b['tables'][0]['lignes'][1]['nature']='4455'
  elif cas=='quatre':b['tables'][0]['lignes'].append(deepcopy(r))
  elif cas=='colonne':r['depot_confirme']=True
  elif cas=='omission':b['tables']=[]
  elif cas=='champ':b['controle_tva']={}
  avant=donnees_metier(application);assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant

def test_727_exports_logo_inconnus_formules_manifestes(application):
 with closing(client(application)[0]) as api:
  v=creer(api,False);b=body(v,True);b['tables'][0]['lignes'][0]['reference_source']='=SOURCE_FICTIVE727'
  r=ok(api.post(url(v),json=b),201);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
  z=api.get(BASE+f'/{r["id"]}/zip');assert z.status_code==200
  with ZipFile(BytesIO(z.content)) as zip:
   assert zip.testzip() is None;vue=json.loads(zip.read('tva_documentaire.json'))
   assert vue['controle_tva']==r['contenu']['tva_documentaire']['controle_tva']
   m=json.loads(zip.read('MANIFESTE_SHA256.json'));assert set(zip.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
   for n,h in m['fichiers'].items():assert len(zip.read(n))==h['taille'] and hashlib.sha256(zip.read(n)).hexdigest()==h['sha256']
   wb=load_workbook(BytesIO(zip.read('preparation.xlsx')));ws=wb['Contrôle B14 N']
   assert ws['E2'].value=='Indisponible' and ws['F2'].value==1000 and ws['G2'].value=='Indisponible'
   assert wb['Déclaration B14 N']['H2'].value=='=SOURCE_FICTIVE727' and wb['Déclaration B14 N']['H2'].data_type=='s'
   with ZipFile(BytesIO(zip.read('preparation.xlsx'))) as x:assert any(p.startswith('xl/media/') for p in x.namelist())
   pdf=PdfReader(BytesIO(zip.read('preparation.pdf')));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
   assert 'B14' in t and '=SOURCE_FICTIVE727' in t and 'Aucun dépôt confirmé' in t and any(p.images for p in pdf.pages)
  assert donnees_metier(application)==avant

def test_727_droits_societes_hash_devise_concurrence(application):
 with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
  v=creer(api);b=body(v)
  assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=b).status_code==404
  assert api.post(url(v),json={**b,'empreinte_parent':'a'*64}).status_code==409
  sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
  ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
  autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
  assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=b).status_code==403
  with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=b),range(2)))
  assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
  b['tables'][0]['lignes'][0]['operations']='1999.99';assert api.post(url(v),json=b).status_code==409
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
  assert api.get(url(rs[0].json())).status_code==200

def test_727_signes_et_zero_declares_sans_comparatif(application):
 with closing(client(application)[0]) as api:
  v=creer(api,False);b=body(v);b['tables'][0]['lignes'][0].update(solde_debut='-300',declarations='700')
  r=ok(api.post(url(v),json=b),201);c=ok(api.get(url(r)))['controle_tva'];m=c['lignes'][0]['montants']
  assert m['solde_debut_declare']=='-300.00' and m['solde_fin_reconstitue']=='1000.00' and m['solde_fin_balance_n1_memoire'] is None
  b=body(r,zeros=True);r=ok(api.post(url(r),json=b),201);c=ok(api.get(url(r)))['controle_tva']
  assert c['lignes'][0]['montants']['solde_fin_reconstitue']=='0.00' and c['alertes']
  from services.balance_tva_documentaire_service import calculer_controles
  from services.balance_preparation_export_service import generer_preparation_xlsx
  d=deepcopy(r);d['contenu']['sources']['n']=[{'compte':'4455'+str(i),'debit':'0','credit':'9999999999999.99'} for i in range(2)]
  d['contenu']['tva_documentaire']['controle_tva']=calculer_controles(d,b)
  w=load_workbook(BytesIO(generer_preparation_xlsx(d,{'raison_sociale':'Fictif727'})))
  assert w['Contrôle B14 N']['F2'].value=='19999999999999.98' and w['Contrôle B14 N']['F2'].data_type=='s'
