"""C3 extra : déclarations sourcées, unités, inconnus et versions isolées."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import hashlib,json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from test_balance_comparatif_n2729_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,source,image_data,creer_source,
 creer as creer_c3,body as n2_body,url as n2_url,c3_body,c3_url)


def url(v):return BASE+f'/{v["id"]}/c3-extra'


def creer(api,comparatif=True,n2=True):
 v=creer_c3(api,comparatif)
 if n2:
  s=creer_source(api);v=ok(api.post(n2_url(v),json=n2_body(v,s)),201)
 return v


def body(v,partiel=False,zeros=False,cohab=False):
 rows=[]
 for code,e,b,r,d in [('C3-N','3.50','2000','60','20'),('C3-N1','3','1000','30','10'),('C3-N2','2','0','10','0')]:
  rows.append({'code':code,'statut':'documente','justification':'Déclarations fictives731, sources à revoir',
   'lignes':[{'nature':'Synthèse fictive731 '+code,'effectif_moyen':None if partiel else '0' if zeros else e,
    'benefices_distribues':None if partiel else '0' if zeros else b,'resultat_par_titre':None if partiel else '0' if zeros else r,
    'distribution_par_titre':None if partiel else '0' if zeros else d,
    'affectations_justifiees':'PV FICTIF731 '+code+', cent titres ; décision et qualification à vérifier',
    'reference_source':'NOTE EXTRA FICTIVE731 '+code}]})
 if cohab:
  rows[0]['lignes'][0].update(benefices_distribues='500',resultat_par_titre='20',distribution_par_titre='5')
  rows[1]['lignes'][0].update(benefices_distribues='0',resultat_par_titre='0',distribution_par_titre='0')
 return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':rows}


@pytest.mark.parametrize('cas',['normal','effectif_141','partiel','zero','negatif','sans_ligne','absent','nan','inf','bool','neg_effectif','neg_distribution','precision','reference','nature'])
def test_731_oracles_declarations_distinctes_et_inconnus(cas):
 from services.balance_indicateurs_service import calculer
 from services.balance_c3_extra_service import declarations
 d=source();q=body({'empreinte_sha256':'a'*64},partiel=cas=='partiel',zeros=cas=='zero');r=q['tables'][0]['lignes'][0]
 if cas=='effectif_141':r['effectif_moyen']='141.25'
 elif cas=='negatif':r['resultat_par_titre']='-10.01'
 elif cas=='sans_ligne':
  for t in q['tables']:t.update(lignes=[],statut='a_completer')
 elif cas in ('nan','inf','bool','neg_effectif','neg_distribution','precision'):
  champ='distribution_par_titre' if cas=='neg_distribution' else 'effectif_moyen'
  r[champ]={'nan':'NaN','inf':'Infinity','bool':True,'neg_effectif':'-1','neg_distribution':'-1','precision':'0.001'}[cas]
 elif cas=='reference':r['reference_source']=''
 elif cas=='nature':r['nature']=''
 if cas!='absent':d['contenu']['extra_c3_documentaire']={'cle':'FICTIF731','declarations_c3':declarations(q)}
 avant=deepcopy(d)
 if cas in ('nan','inf','bool','neg_effectif','neg_distribution','precision','reference','nature'):
  with pytest.raises(ValueError):calculer(d)
  assert d==avant;return
 v=calculer(d);assert d==avant and not v['pret_a_deposer'];json.dumps(v,allow_nan=False)
 n=v['periodes']['n'];n1=v['periodes']['n1'];n2=v['periodes']['n2']
 assert n['resultat_net']=='6000.00' and not n1['disponible'] and not n2['disponible']
 if cas in ('partiel','sans_ligne','absent'):
  assert n['effectif_moyen'] is n['benefices_distribues'] is n['resultat_par_titre'] is None
 elif cas=='zero':assert n['effectif_moyen']==n['distribution_par_titre']=='0.00'
 else:
  assert n['effectif_moyen']==('141.25' if cas=='effectif_141' else '3.50') and n['benefices_distribues']=='2000.00'
  assert n['resultat_par_titre']==('-10.01' if cas=='negatif' else '60.00')
  assert n1['effectif_moyen']=='3.00' and n2['resultat_par_titre']=='10.00'
 if cas!='absent':assert v['provenance_extra_c3']['cle']=='FICTIF731'


def test_731_versions_c3_actualisation_et_metier_inchange(application):
 with closing(client(application)[0]) as api:
  v=creer(api);v=ok(api.post(c3_url(v),json=c3_body(v)),201);old=deepcopy(v['contenu']['indicateurs_comptables_documentaires'])
  avant=donnees_metier(application);r=ok(api.post(url(v),json=body(v)),201)
  assert r['contenu']['indicateurs_comptables_documentaires']==old and old['vue']['periodes']['n']['effectif_moyen'] is None
  r2=ok(api.post(c3_url(r),json=c3_body(r)),201);vue=r2['contenu']['indicateurs_comptables_documentaires']['vue']
  n,n1,n2=[vue['periodes'][p] for p in ('n','n1','n2')]
  assert n['effectif_moyen']=='3.50' and n['resultat_par_titre']=='60.00' and n['resultat_net']=='6000.00'
  assert n1['resultat_par_titre']=='30.00' and n1['resultat_net']=='3000.00'
  assert n2['effectif_moyen']=='2.00' and n2['resultat_net']=='1000.00'
  assert vue['provenance_extra_c3']['cle']==r['contenu']['extra_c3_documentaire']['cle']
  assert vue['informations_a_completer']==[] and not vue['pret_a_deposer']
  assert ok(api.get(BASE+f'/{v["id"]}'))==v
  apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
  b=body(r2);b['tables'][0]['lignes'][0].update(resultat_par_titre='61',effectif_moyen='141.25')
  r3=ok(api.post(url(r2),json=b),201);r3=ok(api.post(c3_url(r3),json=c3_body(r3)),201)
  assert r3['contenu']['indicateurs_comptables_documentaires']['vue']['periodes']['n']['resultat_par_titre']=='61.00'
  assert r3['contenu']['indicateurs_comptables_documentaires']['vue']['periodes']['n']['resultat_net']=='6000.00'
  assert r3['contenu']['indicateurs_comptables_documentaires']['vue']['periodes']['n']['effectif_moyen']=='141.25'


def test_731_rejeu_export_sans_recalcul(application,monkeypatch):
 from services import balance_c3_extra_service as s
 from services import balance_indicateurs_service as c3
 from routers.etats import BalanceC3ExtraIn
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);r=ok(api.post(url(v),json=b),201);r=ok(api.post(c3_url(r),json=c3_body(r)),201);vue=ok(api.get(url(r)))
  def interdit(*a,**kw):raise AssertionError('Rejeu/lecture/export sans recalcul')
  monkeypatch.setattr(s,'declarations',interdit);monkeypatch.setattr(c3,'calculer',interdit)
  with Session(application['engine']) as db:
   rep=s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceC3ExtraIn.model_validate(b))
  assert rep['contenu']['extra_c3_documentaire']==r['contenu']['extra_c3_documentaire']
  assert ok(api.get(url(r)))==vue and api.get(BASE+f'/{r["id"]}/zip').status_code==200


@pytest.mark.parametrize('cas',['nan','inf','bool','precision','neg_effectif','neg_distribution','reference','nature','deux_lignes','doublon','omission','colonne','champ'])
def test_731_rejets_sans_mutation(application,cas):
 with closing(client(application)[0]) as api:
  v=creer(api,n2=False);b=body(v);r=b['tables'][0]['lignes'][0]
  if cas in ('nan','inf','bool','precision','neg_effectif'):r['effectif_moyen']={'nan':'NaN','inf':'Infinity','bool':True,'precision':'0.001','neg_effectif':'-1'}[cas]
  elif cas=='neg_distribution':r['distribution_par_titre']='-1'
  elif cas=='reference':r['reference_source']=''
  elif cas=='nature':r['nature']=''
  elif cas=='deux_lignes':b['tables'][0]['lignes']*=2
  elif cas=='doublon':b['tables'][1]['code']='C3-N'
  elif cas=='omission':b['tables'].pop()
  elif cas=='colonne':r['calcul_paies']=True
  elif cas=='champ':b['declarations_c3']={}
  avant=donnees_metier(application);assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant


def test_731_declarations_sans_balances_comparatives_ne_fabriquent_pas_comptabilite(application):
 with closing(client(application)[0]) as api:
  v=creer(api,False,False);r=ok(api.post(url(v),json=body(v)),201);r=ok(api.post(c3_url(r),json=c3_body(r)),201)
  n1=r['contenu']['indicateurs_comptables_documentaires']['vue']['periodes']['n1']
  assert not n1['disponible'] and n1['resultat_net'] is None and n1['effectif_moyen']=='3.00'
 from services.balance_c3_extra_service import presentation,catalogue
 d=source();d['contenu']['extra_c3_documentaire']={'catalogue':catalogue(d),'tables':body({'empreinte_sha256':'a'*64})['tables']}
 d['contenu']['notes_etic_documentaires']={'lignes':[{'code':'C3','statut':'non_applicable'}]}
 assert any('note C3' in a for a in presentation(d)['alertes'])


def test_731_exports_logo_unites_inconnus_formules_manifestes(application):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v,True);b['tables'][0]['lignes'][0]['reference_source']='=SOURCE_FICTIVE731'
  r=ok(api.post(url(v),json=b),201);r=ok(api.post(c3_url(r),json=c3_body(r)),201)
  ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
  rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200
  with ZipFile(BytesIO(rep.content)) as z:
   assert z.testzip() is None;m=json.loads(z.read('MANIFESTE_SHA256.json'))
   assert set(z.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
   for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
   assert json.loads(z.read('extra_c3_documentaire.json'))['declarations_c3']['n']['effectif_moyen'] is None
   w=load_workbook(BytesIO(z.read('preparation.xlsx')))
   assert w['Déclarations C3 N']['D2'].value=='Indisponible' and 'personnes' in w['Déclarations C3 N']['D1'].value
   assert w['Déclarations C3 N']['I2'].value=='=SOURCE_FICTIVE731' and w['Déclarations C3 N']['I2'].data_type=='s'
   with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(p.startswith('xl/media/') for p in x.namelist())
   pdf=PdfReader(BytesIO(z.read('preparation.pdf')));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
   assert 'personnes' in t and 'MAD / titre' in t and '=SOURCE_FICTIVE731' in t and any(p.images for p in pdf.pages)
  assert donnees_metier(application)==avant


def test_731_droits_societes_devise_hash_concurrence(application):
 with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
  v=creer(api,n2=False);b=body(v)
  assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=b).status_code==404
  assert api.post(url(v),json={**b,'empreinte_parent':'a'*64}).status_code==409
  sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
  ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
  autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
  assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=b).status_code==403
  with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=b),range(2)))
  assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
  b['tables'][0]['lignes'][0]['effectif_moyen']='4';assert api.post(url(v),json=b).status_code==409
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
  assert api.get(url(rs[0].json())).status_code==200

def test_731_perte_n2_et_resultat_par_titre_negatif_explicitement_sources(application):
 from datetime import date
 with closing(client(application)[0]) as api:
  v=creer(api);s=ok(api.post(BASE,json={'exercice':date.today().year-2,'fichier_n':'PERTE FICTIVE731 N2.csv',
   'lignes_n':[{'compte':'1111','credit':'10000'},{'compte':'5141','debit':'8999'},{'compte':'6132','debit':'1001'}]}),201)
  v=ok(api.post(n2_url(v),json=n2_body(v,s)),201);b=body(v)
  b['tables'][2]['lignes'][0].update(resultat_par_titre='-10.01',reference_source='PERTE FICTIVE731 N2 :100 titres, net -1001')
  r=ok(api.post(url(v),json=b),201);r=ok(api.post(c3_url(r),json=c3_body(r)),201)
  n=r['contenu']['indicateurs_comptables_documentaires']['vue']['periodes']['n2']
  assert n['resultat_net']=='-1001.00' and n['situation_nette']=='8999.00' and n['resultat_par_titre']=='-10.01'
