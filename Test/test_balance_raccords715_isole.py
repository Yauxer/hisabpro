"""Raccords715 : sources exactes, non-rattachés et contrôles historiques explicites."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile
from uuid import uuid4
import hashlib,json
import pytest
from sqlalchemy.orm import Session
from openpyxl import load_workbook
from pypdf import PdfReader
from test_balance_mouvements713_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,creer as creer_base,body as mv_body,url as mv_url,BASE)
from test_permissions_tva_runtime_isole import donnees_metier
from test_logo_societe import image_data


def url(v):return BASE+f'/{v["id"]}/raccords-mouvements'


def creer(api):
 v=creer_base(api);return ok(api.post(mv_url(v),json=mv_body(v)),201)


def body(v,vides=False):
 comptes={'B2':'2340','B2bis':'2834','B5':'1511'}
 return {'empreinte_parent':v['empreinte_sha256'],'cle':str(uuid4()),'tables':[
  {'code':t['code'],'lignes':[{'ligne':i,'compte':'' if vides else comptes[t['code']]} for i,_ in enumerate(t['lignes'],1)]}
  for t in v['contenu']['mouvements_documentaires']['tables']]}


def source():
 from routers.etats import BalanceMouvementsIn
 from services import balance_mouvements_service as mv
 d={'id':1,'version':1,'empreinte_sha256':'a'*64,'contenu':{'sources':{'n':[
  {'compte':'2340','debit':'11000.00','credit':'0.00'},
  {'compte':'2834','debit':'0.00','credit':'4500.00'},
  {'compte':'1511','debit':'0.00','credit':'700.00'}]}}}
 t=mv.normaliser(d,BalanceMouvementsIn.model_validate(mv_body(d)).tables)
 d['contenu'][mv.BLOC]={'catalogue':mv.catalogue(d),'tables':t}
 return d


@pytest.mark.parametrize('cas',['connus','multi_ligne','non_rattache','inconnu','inverse','source_absente','compte_sans_detail','grand','zero','ecart','duplique_source'])
def test_715_oracles_raccords_explicites(cas):
 from routers.etats import BalanceRaccordsMouvementsIn
 from services import balance_raccords_mouvements_service as s
 d=source();r=d['contenu']['mouvements_documentaires']['tables'][0]['lignes'][0];src=d['contenu']['sources']['n']
 if cas=='multi_ligne':r['fin']='6000.00';autre=deepcopy(r);autre['fin']='5000.00';d['contenu']['mouvements_documentaires']['tables'][0]['lignes'].append(autre)
 elif cas=='inconnu':r['fin']=None
 elif cas=='inverse':r['fin']='-100.00';src[0].update(debit='0.00',credit='100.00')
 elif cas=='source_absente':d['contenu']['sources']['n']=None
 elif cas=='compte_sans_detail':src.append({'compte':'2341','debit':'25.00','credit':'0.00'})
 elif cas=='grand':
  r['fin']='9999999999999.99';d['contenu']['mouvements_documentaires']['tables'][0]['lignes'].append(deepcopy(r))
  src[0]['debit']='9999999999999.99';src.append(deepcopy(src[0]))
 elif cas=='zero':r['fin']='0.00';src[0]['debit']='0.00'
 elif cas=='ecart':r['fin']='10999.99'
 elif cas=='duplique_source':r['fin']='11100.00';src.append({'compte':'2340','debit':'100.00','credit':'0.00'})
 q=body(d,cas=='source_absente')
 if cas=='non_rattache':q['tables'][0]['lignes'][0]['compte']=''
 avant=deepcopy(d);norm=s.normaliser(d,BalanceRaccordsMouvementsIn.model_validate(q).tables)
 c=s.calculer_controles(d,{'tables':norm,'catalogue':s.catalogue(d)})
 assert d==avant and not s.presentation(d)['conserve'];json.dumps(c,allow_nan=False)
 b2=c['tableaux']['B2']
 if cas=='source_absente':assert not c['source_disponible'] and not b2['comptes'] and b2['non_rattachees']==[1];return
 r=b2['comptes'][0]
 if cas in ('non_rattache','inconnu'):assert r['somme_clotures_declarees'] is r['ecart'] is None
 else:assert r['ecart']==('-0.01' if cas=='ecart' else '0.00')
 if cas=='multi_ligne':assert r['lignes']==2 and r['somme_clotures_declarees']=='11000.00'
 if cas=='grand':assert r['solde_source']==r['somme_clotures_declarees']=='19999999999999.98'
 if cas=='compte_sans_detail':assert b2['comptes'][1]['somme_clotures_declarees'] is b2['comptes'][1]['ecart'] is None
 assert b2['non_rattachees']==([1] if cas=='non_rattache' else [])
 assert c['tableaux']['B2bis']['comptes'][0]['solde_source']=='4500.00' and c['tableaux']['B5']['comptes'][0]['solde_source']=='700.00'


@pytest.mark.parametrize('cas',['absent_compte','hors_perimetre','ligne_bool','ligne_zero','ligne_inconnue','ligne_texte','ligne_double','omission','colonne','table_absente','table_double','cle','empreinte','controle'])
def test_715_rejets_sans_mutation(application,cas):
 with closing(client(application)[0]) as api:
  v=creer(api);q=body(v);r=q['tables'][0]['lignes'][0]
  if cas=='absent_compte':r['compte']='2349'
  elif cas=='hors_perimetre':r['compte']='2834'
  elif cas.startswith('ligne_') and cas!='ligne_double':r['ligne']={'ligne_bool':True,'ligne_zero':0,'ligne_inconnue':2,'ligne_texte':'1'}[cas]
  elif cas=='ligne_double':q['tables'][0]['lignes'].append(deepcopy(r))
  elif cas=='omission':q['tables'][0]['lignes']=[]
  elif cas=='colonne':r['fin']='masqué'
  elif cas=='table_absente':q['tables'].pop()
  elif cas=='table_double':q['tables'][2]['code']='B2'
  elif cas=='cle':q['cle']='invalide'
  elif cas=='empreinte':q['empreinte_parent']='0'*64
  elif cas=='controle':q['controle_raccords']={}
  avant=donnees_metier(application);assert api.post(url(v),json=q).status_code==(409 if cas=='empreinte' else 422)
  assert donnees_metier(application)==avant


def test_715_snapshot_rejeu_et_controle_ancien(application,monkeypatch):
 from routers.etats import BalanceRaccordsMouvementsIn
 from services import balance_raccords_mouvements_service as s
 with closing(client(application)[0]) as api:
  v=creer(api);q=body(v);avant=donnees_metier(application);r=ok(api.post(url(v),json=q),201);vue=ok(api.get(url(r)))
  assert vue['actuel'] and all(r['contenu'][k]==x for k,x in v['contenu'].items())
  apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
  nouveau=mv_body(r);nouveau['tables'][0]['lignes'][0]['fin']='10999.99'
  r2=ok(api.post(mv_url(r),json=nouveau),201);ancien=ok(api.get(url(r2)))
  assert not ancien['actuel'] and ancien['snapshot']==vue['snapshot'] and ancien['courant'][0]['lignes'][0]['compte']==''
  assert ancien['snapshot']['catalogue'][0]['lignes'][0]['fin']=='11000.00' and ancien['courant'][0]['lignes'][0]['fin']=='10999.99'
  r3=ok(api.post(url(r2),json=body(r2)),201);assert ok(api.get(url(r3)))['snapshot']['controle_raccords']['tableaux']['B2']['comptes'][0]['ecart']=='-0.01'
  assert ok(api.get(url(r)))==vue and ok(api.get(BASE+f'/{v["id"]}'))==v
  def interdit(*a,**k):raise AssertionError('Recalcul ancien/rejeu interdit')
  monkeypatch.setattr(s,'calculer_controles',interdit)
  with Session(application['engine']) as db:assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceRaccordsMouvementsIn.model_validate(q))==r
  assert not s.presentation(r2)['actuel'] and s.presentation(r2)['snapshot']==vue['snapshot']
  copie=deepcopy(r);copie['contenu']['sources']['n'][1]['debit']='11001.00';assert not s.presentation(copie)['actuel']
  copie=deepcopy(r);copie['contenu']['note_independante']='sans modifier mouvements ni sources';assert s.presentation(copie)['actuel']


def test_715_exports_stables_logo_et_grands_montants(application):
 with closing(client(application)[0]) as api:
  v=creer_base(api);q=mv_body(v);q['tables'][0]['lignes'][0]['nature']='=1+2\n<Transport fictif & preuve>'
  v=ok(api.post(mv_url(v),json=q),201);r=ok(api.post(url(v),json=body(v)),201);snap=ok(api.get(url(r)))['snapshot']
  nouveau=mv_body(r);nouveau['tables'][0]['lignes'][0]['fin']='10999.99';r2=ok(api.post(mv_url(r),json=nouveau),201)
  ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
  rep=api.get(BASE+f'/{r2["id"]}/zip');assert rep.status_code==200
  with ZipFile(BytesIO(rep.content)) as z:
   vue=json.loads(z.read('raccords_mouvements.json'));assert not vue['actuel'] and vue['snapshot']==snap
   w=load_workbook(BytesIO(z.read('preparation.xlsx')))
   assert w['Raccord B2']['B2'].data_type=='s' and w['Raccord B2']['B2'].value.startswith('=1+2')
   assert w['Raccord B2']['C2'].value==11000 and w['Mouvements B2']['E2'].value==10999.99
   assert w['Contrôle raccord B2']['D2'].value==0 and 'refaire' in w['Origine raccords']['B3'].value
   p=PdfReader(BytesIO(z.read('preparation.pdf')));txt='\n'.join(x.extract_text() or '' for x in p.pages)
   assert '<Transport fictif & preuve>' in txt and 'refaire' in txt and any(list(x.images) for x in p.pages)
   m=json.loads(z.read('MANIFESTE_SHA256.json'))
   for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
  assert donnees_metier(application)==avant
  grand=mv_body(r2);lg=grand['tables'][0]['lignes'][0];lg['fin']='9999999999999.99';grand['tables'][0]['lignes'].append(deepcopy(lg))
  g=ok(api.post(mv_url(r2),json=grand),201);g=ok(api.post(url(g),json=body(g)),201)
  rep=api.get(BASE+f'/{g["id"]}/xlsx');assert rep.status_code==200;w=load_workbook(BytesIO(rep.content))
  assert w['Contrôle raccord B2']['C2'].value=='19999999999999.98' and w['Contrôle raccord B2']['C2'].data_type=='s'


def test_715_permissions_concurrence_et_dependance(application):
 with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
  base=creer_base(api);assert ok(api.get(url(base)))['courant']==[]
  incomplet={'empreinte_parent':base['empreinte_sha256'],'cle':str(uuid4()),'tables':[{'code':c,'lignes':[]} for c in ('B2','B2bis','B5')]}
  assert api.post(url(base),json=incomplet).status_code==422
  v=creer(api);q=body(v);assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=q).status_code==404
  with ThreadPoolExecutor(max_workers=2) as ex:rs=list(ex.map(lambda _:api.post(url(v),json=q),range(2)))
  assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
  bad=deepcopy(q);bad['tables'][0]['lignes'][0]['compte']='';assert api.post(url(v),json=bad).status_code==409
  sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
  ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
  autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
  assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=q).status_code==403
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
  assert autre.get(url(rs[0].json())).status_code==200
