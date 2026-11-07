"""B12 indépendant : oracles décimaux, inconnus, versions et PostgreSQL nonce."""
from contextlib import closing
from copy import deepcopy
from decimal import Decimal as D
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from zipfile import ZipFile
import hashlib,json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from test_balance_resultat_courant721_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,source,creer,image_data)

def url(v):return BASE+f'/{v["id"]}/passage-fiscal'

def body(v,partiel=False):
 from uuid import uuid4
 return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
  {'code':'B12-N','statut':'documente','justification':'Synthèse fictive725, hypothèses explicitement justifiées',
   'lignes':[{'nature':'Passage fiscal fictif N','reintegrations':'500','deductions':'200',
    'deficit_disponible':None if partiel else '1000','taux_is':'20',
    'regime_avantages':'Régime à revoir, aucun avantage déduit',
    'reference_source':'NOTE FICTIVE725, déficit éligible explicitement déclaré'}]}]}

def calcul(d=None,q=None):
 from services.balance_passage_fiscal_service import calculer_controles
 d=source() if d is None else d;d['exercice']=2026
 return calculer_controles(d,body({'empreinte_sha256':'a'*64}) if q is None else q)

@pytest.mark.parametrize('cas',['normal','deficit_inconnu','taux_inconnu','ri_inconnue','zero','taux_precision',
 'vide','absent','technique','legacy119','inverse','neant','grand','sans_cpc','ancien','futur'])
def test_725_oracles_et_inconnus(cas):
 d=source();d['exercice']=2026;q=body({'empreinte_sha256':'a'*64});r=q['tables'][0]['lignes'][0]
 if cas=='deficit_inconnu':r['deficit_disponible']=None
 elif cas=='taux_inconnu':r['taux_is']=None
 elif cas=='ri_inconnue':r['reintegrations']=None
 elif cas=='zero':r.update(reintegrations='0',deductions='0',deficit_disponible='0',taux_is='0')
 elif cas=='taux_precision':r['taux_is']='19.999'
 elif cas=='vide':d['contenu']['sources']['n']=[]
 elif cas=='absent':d['contenu']['sources']['n']=None
 elif cas=='technique':d['contenu']['preparation']['etats']['cpc']['disponible']=False
 elif cas=='legacy119':d['contenu']['sources']['n']=[{'compte':'1191','debit':'0','credit':'6400'}]
 elif cas=='sans_cpc':d['contenu']['preparation']['etats']={}
 elif cas=='inverse':d['contenu']['sources']['n']=[{'compte':'6132','debit':'2000','credit':'0'}]
 elif cas=='grand':d['contenu']['sources']['n']=[{'compte':'7111','credit':'9999999999999.99','debit':'0'}]*2
 elif cas=='neant':q['tables'][0].update(lignes=[],statut='neant_declare')
 elif cas=='ancien':d['exercice']=2022
 elif cas=='futur':d['exercice']=2027
 from services.balance_passage_fiscal_service import calculer_controles
 avant=deepcopy(d);v=calculer_controles(d,q);m=v['montants'];assert d==avant and not v['pret_a_deposer']
 assert all(x is None for x in v['liquidation'].values());json.dumps(v,allow_nan=False)
 if cas in ('absent','technique','legacy119','sans_cpc'):
  assert not v['disponible'] and m['resultat_net_comptable'] is m['is_theorique_taux_declare'] is None
 elif cas=='inverse':
  assert m['resultat_fiscal_avant_deficit']=='-1700.00' and m['deficit_genere']=='1700.00'
  assert m['deficit_restant']=='1000.00' and m['is_theorique_taux_declare']=='0.00'
 elif cas=='grand':assert m['resultat_net_comptable']=='19999999999999.98'
 elif cas=='vide':assert m['resultat_net_comptable']=='0.00'
 else:
  assert m['resultat_net_comptable']=='6400.00' and m['impots_comptabilises_67']=='1600.00'
  assert m['resultat_avant_impots']=='8000.00'
  if cas=='neant':assert m['autres_reintegrations'] is None and v['alertes']
  elif cas=='ri_inconnue':assert m['resultat_fiscal_avant_deficit'] is None
  elif cas=='zero':assert m['benefice_fiscal_propose']=='8000.00' and m['is_theorique_taux_declare']=='0.00'
  else:
   assert m['resultat_fiscal_avant_deficit']=='8300.00' and m['reintegrations_depuis_net']=='2100.00'
   if cas=='deficit_inconnu':assert m['deficit_impute_propose'] is m['benefice_fiscal_propose'] is m['is_theorique_taux_declare'] is None
   else:
    assert m['benefice_fiscal_propose']=='7300.00' and m['deficit_impute_propose']=='1000.00'
    assert m['is_theorique_taux_declare']==(None if cas in ('taux_inconnu','ancien') else '1459.93' if cas=='taux_precision' else '1460.00')
    if cas in ('ancien','futur'):assert v['alertes']

@pytest.mark.parametrize('valeur',['NaN','Infinity',True,'-1','0.001'])
def test_725_source_invalide(valeur):
 d=source();d['contenu']['sources']['n'][0]['credit']=valeur
 with pytest.raises(ValueError):calcul(d)

@pytest.mark.parametrize('valeur',['NaN','Infinity',True,None])
def test_725_base_pure_refuse_non_fini_ou_inconnu(valeur):
 from services.fiscalite_is_service import calculer_base_fiscale
 with pytest.raises(ValueError):calculer_base_fiscale(resultat_comptable_avant_is=valeur,reintegrations=0,deductions=0)

def test_725_base_pure_deficit_non_deduit():
 from services.fiscalite_is_service import calculer_base_fiscale
 m=calculer_base_fiscale(resultat_comptable_avant_is='8000',reintegrations='500',deductions='200')
 assert m['resultat_fiscal_avant_deficit']==D('8300') and m['benefice_fiscal_imposable'] is None

def test_725_versions_rejeu_sans_recalcul_et_metier(application,monkeypatch):
 from services import balance_passage_fiscal_service as s
 from routers.etats import BalancePassageFiscalIn
 with closing(client(application)[0]) as api:
  v=creer(api);avant=donnees_metier(application);assert ok(api.get(url(v)))['controle_passage_fiscal'] is None
  b=body(v);r=ok(api.post(url(v),json=b),201);vue=ok(api.get(url(r)))
  assert vue['controle_passage_fiscal']['montants']['is_theorique_taux_declare']=='1460.00'
  assert ok(api.get(BASE+f'/{v["id"]}'))==v and all(r['contenu'][k]==x for k,x in v['contenu'].items())
  def interdit(*a,**kw):raise AssertionError('Rejeu/lecture/export sans recalcul')
  monkeypatch.setattr(s,'calculer_controles',interdit);monkeypatch.setattr(s,'detail_cpc',interdit)
  with Session(application['engine']) as db:assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalancePassageFiscalIn.model_validate(b))==r
  assert ok(api.get(url(r)))==vue and api.get(BASE+f'/{r["id"]}/zip').status_code==200
  apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')

@pytest.mark.parametrize('champ,valeur',[('taux_is','NaN'),('taux_is','Infinity'),('taux_is','100.001'),
 ('taux_is','20.0001'),('taux_is',True),('taux_is','-1'),('deductions','0.001'),
 ('deficit_disponible','-1'),('reference_source',''),('nature','')])
def test_725_rejets_sans_mutation(application,champ,valeur):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][0]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
  assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant

def test_725_structures_notes_et_sources_indisponibles(application):
 from services.balance_passage_fiscal_service import presentation,catalogue
 d=source();d['contenu']['notes_etic_documentaires']={'lignes':[{'code':'B12','statut':'non_applicable'}]}
 d['contenu']['passage_fiscal_documentaire']={'catalogue':catalogue(d),'tables':body({'empreinte_sha256':'a'*64})['tables']}
 assert any('note B12' in a for a in presentation(d)['alertes'])
 with closing(client(application)[0]) as api:
  for cas in ('deux_lignes','omission','colonne','champ','technique'):
   v=creer(api,False,technique=cas=='technique');b=body(v)
   if cas=='deux_lignes':b['tables'][0]['lignes']*=2
   elif cas=='omission':b['tables']=[]
   elif cas=='colonne':b['tables'][0]['lignes'][0]['is_theorique']='0'
   elif cas=='champ':b['controle_passage_fiscal']={}
   avant=donnees_metier(application);assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant
  v=creer(api,False,True);b=body(v);b['tables'][0].update(statut='a_completer',justification='',lignes=[])
  r=ok(api.post(url(v),json=b),201);assert not ok(api.get(url(r)))['controle_passage_fiscal']['disponible']

def test_725_exports_logo_inconnus_formules_et_manifestes(application):
 with closing(client(application)[0]) as api:
  v=creer(api,False);b=body(v,True);b['tables'][0]['lignes'][0]['reference_source']='=SOURCE_FICTIVE725'
  r=ok(api.post(url(v),json=b),201);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
  z=api.get(BASE+f'/{r["id"]}/zip');assert z.status_code==200
  with ZipFile(BytesIO(z.content)) as zip:
   assert zip.testzip() is None;vue=json.loads(zip.read('passage_fiscal_documentaire.json'))
   assert vue['controle_passage_fiscal']==r['contenu']['passage_fiscal_documentaire']['controle_passage_fiscal']
   m=json.loads(zip.read('MANIFESTE_SHA256.json'));assert set(zip.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
   for n,h in m['fichiers'].items():assert len(zip.read(n))==h['taille'] and hashlib.sha256(zip.read(n)).hexdigest()==h['sha256']
   wb=load_workbook(BytesIO(zip.read('preparation.xlsx')));ws=wb['Contrôle B12 N'];values=dict(list(ws.values)[1:])
   assert values['Résultat net comptable']=='6400.00' and values['IS théorique selon taux déclaré']=='Indisponible'
   assert wb['Déclaration B12 N']['I2'].value=='=SOURCE_FICTIVE725' and wb['Déclaration B12 N']['I2'].data_type=='s'
   with ZipFile(BytesIO(zip.read('preparation.xlsx'))) as x:assert any(p.startswith('xl/media/') for p in x.namelist())
   pdf=PdfReader(BytesIO(zip.read('preparation.pdf')));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
   assert 'B12' in t and '=SOURCE_FICTIVE725' in t and 'solde final' in t.lower()
   assert any(p.images for p in pdf.pages)
  assert donnees_metier(application)==avant

def test_725_droits_societes_hash_devise_concurrence(application):
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
  b['tables'][0]['lignes'][0]['taux_is']='19.999';assert api.post(url(v),json=b).status_code==409
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
  assert api.get(url(rs[0].json())).status_code==200
