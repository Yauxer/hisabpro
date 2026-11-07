"""N-2 explicite : cloisonnement, snapshots, calcul C3 et exports isolés."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date
from io import BytesIO
from zipfile import ZipFile
from uuid import uuid4
import hashlib,json,csv
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from test_balance_indicateurs723_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,creer,source,image_data,
 body as c3_body,url as c3_url)


def url(v):return BASE+f'/{v["id"]}/comparatif-n2'


def lignes(technique=False,variant=False):
 net='1500' if variant else '1000';bank='11500' if variant else '11000'
 r=[{'compte':'1111','debit':'0','credit':'10000'},{'compte':'5141','debit':bank,'credit':'0'}]
 return r+([{'compte':'1191','debit':'0','credit':net}] if technique else [
  {'compte':'7111','debit':'0','credit':'2500' if variant else '2000'},{'compte':'6132','debit':'1000','credit':'0'}])


def creer_source(api,technique=False,variant=False,annee=None):
 annee=date.today().year-2 if annee is None else annee
 exercices=ok(api.get('/api/exercices'))
 if not any(r['annee']==annee for r in exercices):
  ok(api.post('/api/exercices',json={'annee':annee,'date_debut':f'{annee}-01-01','date_fin':f'{annee}-12-31'}),201)
 return ok(api.post(BASE,json={'exercice':annee,'lignes_n':lignes(technique,variant),'fichier_n':'Fictif729_N2.csv'}),201)


def body(v,s):
 return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'source_preparation_id':s['id'],
  'source_empreinte_sha256':s['empreinte_sha256'],'reference_source':'BALANCE FICTIVE729 N-2 explicitement choisie'}


@pytest.mark.parametrize('cas',['normal','legacy119','technique','cpc_absent','ecart','incomplet','non_fini','absent','injection_raw'])
def test_729_oracle_n2_uniquement_source_rattachee(cas):
 from services.balance_indicateurs_service import calculer
 d=source();etats=deepcopy(d['contenu']['preparation']['etats'])
 # Pure test reprend la source723 en N-2 : situation14500, net6000.
 n2={'cle':'fictif729','reference_source':'Source explicitement choisie','source_preparation':{'id':42,'version':1,'exercice':2024,'empreinte_sha256':'b'*64},
  'sources_n2':deepcopy(d['contenu']['sources']['n']),'etats_n2':etats}
 if cas in ('legacy119','technique'):
  n2['sources_n2']=[r for r in n2['sources_n2'] if not r['compte'].startswith(('6','7'))]+[{'compte':'1191','debit':'0','credit':'6000'}]
  n2['etats_n2']['cpc']={'XI':0,'XII':0,'resultat_net':0} if cas=='legacy119' else {'disponible':False}
 elif cas=='cpc_absent':n2['etats_n2'].pop('cpc')
 elif cas=='ecart':n2['etats_n2']['cpc']['resultat_net']=5999.99
 elif cas=='incomplet':n2['sources_n2'][0].pop('debit')
 elif cas=='non_fini':n2['sources_n2'][0]['credit']='Infinity'
 elif cas=='absent':n2['sources_n2']=None
 if cas=='injection_raw':d['contenu']['sources']['n2']=n2['sources_n2']
 else:d['contenu']['comparatif_n2_documentaire']=n2
 avant=deepcopy(d)
 if cas=='non_fini':
  with pytest.raises(ValueError):calculer(d)
  return
 v=calculer(d);assert d==avant and not v['pret_a_deposer'];r=v['periodes']['n2'];json.dumps(v,allow_nan=False)
 assert r['effectif_moyen'] is r['benefices_distribues'] is r['distribution_par_titre'] is None
 if cas in ('absent','incomplet','injection_raw'):assert not r['disponible'] and r['resultat_net'] is None
 elif cas=='cpc_absent':assert r['disponible'] and r['situation_nette'] is r['resultat_net'] is None
 else:
  assert r['situation_nette']=='14500.00'
  if cas in ('legacy119','technique'):assert r['resultat_net'] is r['chiffre_affaires_ht'] is None and r['avertissements']
  else:
   assert r['resultat_net']=='6000.00' and r['chiffre_affaires_ht']=='10000.00'
   assert r['ecart_resultat_net']==('0.01' if cas=='ecart' else '0.00')


def test_729_versions_c3_actualisation_explicitement_tracee(application):
 with closing(client(application)[0]) as api:
  s=creer_source(api);v=creer(api);v=ok(api.post(c3_url(v),json=c3_body(v)),201)
  avant=donnees_metier(application);old=deepcopy(v['contenu']['indicateurs_comptables_documentaires'])
  vue=ok(api.get(url(v)));assert not vue['conserve'] and [r['id'] for r in vue['candidats']]==[s['id']]
  r=ok(api.post(url(v),json=body(v,s)),201);bloc=r['contenu']['comparatif_n2_documentaire']
  assert bloc['sources_n2']==s['contenu']['sources']['n'] and bloc['etats_n2']==s['contenu']['preparation']['etats']
  assert bloc['totaux_exacts']=={'comptes':4,'debit':'12000.00','credit':'12000.00'}
  assert r['contenu']['indicateurs_comptables_documentaires']==old and old['vue']['periodes']['n2']['resultat_net'] is None
  fin=ok(api.post(c3_url(r),json=c3_body(r)),201);c=fin['contenu']['indicateurs_comptables_documentaires']['vue'];n2=c['periodes']['n2']
  assert n2['situation_nette']=='11000.00' and n2['resultat_net']==n2['resultat_avant_impots']=='1000.00'
  assert n2['chiffre_affaires_ht']=='2000.00' and n2['impots_resultats']==n2['salaires_bruts']=='0.00'
  assert c['provenance_n2']['source_preparation']['empreinte_sha256']==s['empreinte_sha256'] and c['provenance_n2']['cle']==bloc['cle']
  assert ok(api.get(BASE+f'/{v["id"]}'))==v and ok(api.get(BASE+f'/{s["id"]}'))==s
  apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
  s2=creer_source(api,variant=True)
  assert ok(api.get(url(fin)))['sources_n2']==bloc['sources_n2']
  r2=ok(api.post(url(fin),json=body(fin,s2)),201)
  assert r2['contenu']['indicateurs_comptables_documentaires']==fin['contenu']['indicateurs_comptables_documentaires']
  f2=ok(api.post(c3_url(r2),json=c3_body(r2)),201)
  assert f2['contenu']['indicateurs_comptables_documentaires']['vue']['periodes']['n2']['resultat_net']=='1500.00'


def test_729_rejeu_et_exports_sans_relecture_ni_calcul_source(application,monkeypatch):
 from services import balance_comparatif_n2_service as s
 from services import balance_indicateurs_service as c3
 from routers.etats import BalanceComparatifN2In
 with closing(client(application)[0]) as api:
  src=creer_source(api);v=creer(api);b=body(v,src);r=ok(api.post(url(v),json=b),201)
  r=ok(api.post(c3_url(r),json=c3_body(r)),201);vue=ok(api.get(url(r)))
  def interdit(*a,**kw):raise AssertionError('Rejeu/lecture/export sans recalcul')
  monkeypatch.setattr(s,'normaliser_balance',interdit);monkeypatch.setattr(c3,'calculer',interdit)
  with Session(application['engine']) as db:
   replay=s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceComparatifN2In.model_validate(b))
  assert replay['contenu']['comparatif_n2_documentaire']==r['contenu']['comparatif_n2_documentaire']
  assert ok(api.get(url(r)))==vue and api.get(BASE+f'/{r["id"]}/zip').status_code==200


@pytest.mark.parametrize('cas',['annee','source_absente','hash_source','hash_parent','reference','bool','colonne','hash_format','uuid'])
def test_729_rejets_sans_mutation(application,cas):
 with closing(client(application)[0]) as api:
  src=creer_source(api,annee=date.today().year-1 if cas=='annee' else None);v=creer(api);b=body(v,src)
  if cas=='source_absente':b['source_preparation_id']=2147483647
  elif cas=='hash_source':b['source_empreinte_sha256']='a'*64
  elif cas=='hash_parent':b['empreinte_parent']='a'*64
  elif cas=='reference':b['reference_source']='  '
  elif cas=='bool':b['source_preparation_id']=True
  elif cas=='colonne':b['sources_n2']=[]
  elif cas=='hash_format':b['source_empreinte_sha256']='incorrect'
  elif cas=='uuid':b['cle']='incorrect'
  avant=donnees_metier(application)
  attendu=404 if cas=='source_absente' else 409 if cas in ('hash_source','hash_parent') else 422
  assert api.post(url(v),json=b).status_code==attendu and donnees_metier(application)==avant


def test_729_cloture_n2_ne_fabrique_pas_activite(application):
 with closing(client(application)[0]) as api:
  src=creer_source(api,technique=True);v=creer(api);r=ok(api.post(url(v),json=body(v,src)),201)
  r=ok(api.post(c3_url(r),json=c3_body(r)),201);n=r['contenu']['indicateurs_comptables_documentaires']['vue']['periodes']['n2']
  assert n['situation_nette']=='11000.00' and n['resultat_net'] is n['chiffre_affaires_ht'] is None and n['avertissements']


def test_729_exports_logo_sources_figees_formules_et_manifestes(application):
 with closing(client(application)[0]) as api:
  src=creer_source(api);v=creer(api);b=body(v,src);b['reference_source']='=SOURCE_FICTIVE729'
  r=ok(api.post(url(v),json=b),201);r=ok(api.post(c3_url(r),json=c3_body(r)),201)
  ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
  rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200
  with ZipFile(BytesIO(rep.content)) as z:
   assert z.testzip() is None;m=json.loads(z.read('MANIFESTE_SHA256.json'))
   assert set(z.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
   for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
   assert json.loads(z.read('comparatif_n2_documentaire.json'))['sources_n2']==src['contenu']['sources']['n']
   assert list(csv.DictReader(z.read('balance_N2.csv').decode('utf8').splitlines(),delimiter=';'))==src['contenu']['sources']['n']
   w=load_workbook(BytesIO(z.read('preparation.xlsx')))
   assert w['Origine N-2']['B3'].value=='=SOURCE_FICTIVE729' and w['Origine N-2']['B3'].data_type=='s'
   assert w['Indicateurs C3 N-2']['B6'].value==1000
   with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(p.startswith('xl/media/') for p in x.namelist())
   pdf=PdfReader(BytesIO(z.read('preparation.pdf')));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
   assert 'Source comparative N-2 rattachée' in t and '=SOURCE_FICTIVE729' in t and any(p.images for p in pdf.pages)
  assert donnees_metier(application)==avant


def test_729_droits_societes_devise_concurrence(application):
 with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
  src=creer_source(api);v=creer(api);b=body(v,src);src_autre=creer_source(autre)
  assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=b).status_code==404
  assert api.post(url(v),json=body(v,src_autre)).status_code==404
  assert all(r['id']!=src_autre['id'] for r in ok(api.get(url(v)))['candidats'])
  sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
  ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
  autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
  assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=b).status_code==403
  with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=b),range(2)))
  assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
  assert api.post(url(v),json={**b,'reference_source':'Autre référence'}).status_code==409
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v,src)).status_code==422
  assert api.get(url(rs[0].json())).status_code==200
