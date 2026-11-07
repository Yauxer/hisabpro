"""Crédits externes qualifiés : inconnus, réutilisations et API PostgreSQL isolée."""
from contextlib import closing
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import hashlib,json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from test_balance_css743_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,source,
 creer,b12_body,b12_url,image_data,contexte_body,contexte_url)


def url(v):return BASE+f'/{v["id"]}/credits-is'
def body(v):
 return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
  {'code':'CR-PROFIL','statut':'documente','justification':'Profil fictif et liste exhaustive revus',
   'lignes':[{'nature':'Crédits fictifs2026','regime':'Société IS hors exonération totale',
    'periode_confirmee':'oui','exhaustivite':'oui','absence_credits':'non','reference_source':'NOTE-CR749'}]},
  {'code':'CR-LIGNES','statut':'documente','justification':'Attestations fictives et historique des utilisations',
   'lignes':[
    {'nature':'Attestation banque fictive','type_credit':'PPRF — CGI159','exercice_rattachement':'2026',
     'date_retenue':'2026-03-20','date_allocation':'','categorie_payeur':'','eligibilite_confirmee':'oui','montant':'300','deja_impute_acomptes':'100','autres_utilisations':'25','reference_source':'CR749-A'},
    {'nature':'Attestation client fictive','type_credit':'Rémunérations de tiers — CGI157','exercice_rattachement':'2026',
     'date_retenue':'2026-06-20','date_allocation':'2026-06-20','categorie_payeur':'Public ou filiale publique','eligibilite_confirmee':'oui','montant':'200','deja_impute_acomptes':'50','autres_utilisations':'0','reference_source':'CR749-B'}]}]}
def controles(v):return v['contenu']['credits_is_documentaires']['controle_credits']
def pure():
 d=source();d['exercice']=2026;d['contenu']['periode']={'debut':'2026-01-01','fin':'2026-12-31'}
 return d,body({'empreinte_sha256':'a'*64})


@pytest.mark.parametrize('cas',['normal','sukuk','location','inconnu','autre','date_hors_periode','ancien_credit','periode','exhaustivite','profil','exclu','tous_utilises','absence','neant_seul','ancien','futur','grand','location_avant','allocation_inconnue','banque_avant','banque_apres','prive_avant','prive_apres','payeur_inconnu','allocation_apres_retenue'])
def test_749_oracles_types_dates_et_inconnus(cas):
 from services.balance_credits_is_service import calculer_controles
 d,b=pure();p=b['tables'][0]['lignes'][0];t=b['tables'][1];r=t['lignes'][0]
 if cas=='sukuk':r['type_credit']='Sukuk — CGI159'
 elif cas=='location':r.update(type_credit='Location — CGI157',date_retenue='2026-07-01',date_allocation='2026-07-01',categorie_payeur='Public ou filiale publique')
 elif cas in ('location_avant','allocation_inconnue','banque_avant','banque_apres','prive_avant','prive_apres','payeur_inconnu','allocation_apres_retenue'):
  r.update(type_credit='Location — CGI157' if cas in ('location_avant','allocation_inconnue') else 'Rémunérations de tiers — CGI157',
   date_allocation='2026-06-30' if cas in ('location_avant','banque_avant','prive_avant') else '' if cas=='allocation_inconnue' else '2026-07-02' if cas=='allocation_apres_retenue' else '2026-07-01',
   date_retenue='2026-07-01',categorie_payeur='Banque ou assurance' if cas.startswith('banque') else 'Entreprise privée CA au moins 500 millions MAD' if cas.startswith('prive') else '' if cas=='payeur_inconnu' else 'Public ou filiale publique')
 elif cas=='inconnu':r['autres_utilisations']=None
 elif cas=='autre':r['type_credit']='Autre — à qualifier'
 elif cas=='date_hors_periode':r['date_retenue']='2025-12-31'
 elif cas=='ancien_credit':r['exercice_rattachement']='2025'
 elif cas=='periode':p['periode_confirmee']=''
 elif cas=='exhaustivite':p['exhaustivite']='non'
 elif cas=='profil':p['regime']=''
 elif cas=='exclu':r['eligibilite_confirmee']='non'
 elif cas=='tous_utilises':r.update(autres_utilisations='200',deja_impute_acomptes='100')
 elif cas in ('absence','neant_seul'):
  t.update(statut='neant_declare',lignes=[])
  if cas=='absence':p['absence_credits']='oui'
 elif cas=='ancien':d['exercice']=2025
 elif cas=='futur':d['exercice']=2027
 elif cas=='grand':r.update(montant='9999999999999.99',autres_utilisations='0',deja_impute_acomptes='0')
 avant=deepcopy(d);c=calculer_controles(d,b);m=c['montants'];assert d==avant
 inconnu=cas in ('inconnu','autre','date_hors_periode','ancien_credit','periode','exhaustivite','profil','neant_seul','ancien','futur','location_avant','allocation_inconnue','banque_avant','prive_avant','payeur_inconnu','allocation_apres_retenue')
 assert m['credits_proposes']==(None if inconnu else {'exclu':'150.00','tous_utilises':'150.00','absence':'0.00','grand':'10000000000149.99'}.get(cas,'325.00'))
 assert c['solde_final'] is None and not c['liquidation_confirmee'] and not c['imputation_confirmee']
 if cas=='normal':assert m['montant_total']=='500.00' and m['deja_impute_acomptes']=='150.00' and m['autres_utilisations']=='25.00' and m['disponible_arithmetique']=='325.00'
 json.dumps(c,allow_nan=False)


def test_749_versions_rejeu_lecture_sans_recalcul(application,monkeypatch):
 from services import balance_credits_is_service as s
 from routers.etats import BalanceCreditsIsIn
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);avant=donnees_metier(application)
  assert ok(api.get(url(v)))['controle_credits'] is None
  r=ok(api.post(url(v),json=b),201);vue=ok(api.get(url(r)))
  assert controles(r)['montants']['credits_proposes']=='325.00'
  assert controles(r)['montants']['ecart_montant_contexte']=='-100.00'
  assert controles(r)['montants']['ecart_imputations_contexte']=='0.00'
  assert all(r['contenu'][k]==x for k,x in v['contenu'].items())
  def interdit(*a,**kw):raise AssertionError('Pas de recalcul historique crédits')
  monkeypatch.setattr(s,'calculer_controles',interdit)
  with Session(application['engine']) as db:assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceCreditsIsIn.model_validate(b))==r
  assert ok(api.get(url(r)))==vue and api.get(BASE+f'/{r["id"]}/zip').status_code==200
  assert ok(api.get(BASE+f'/{v["id"]}'))==v
  apres=donnees_metier(application);assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')


@pytest.mark.parametrize('champ,valeur',[
 ('montant','NaN'),('montant','Infinity'),('montant',True),('montant','-1'),('montant','0'),
 ('montant','0.001'),('montant','1e9999'),('montant','10000000000000'),
 ('autres_utilisations','201'),('deja_impute_acomptes','300'),('exercice_rattachement','2027'),
 ('exercice_rattachement','2026.0'),('date_retenue','2026-02-30'),('date_retenue','20260320'),
 ('date_allocation','2026-02-30'),('categorie_payeur','Particulier'),('eligibilite_confirmee',True),('type_credit','TVA'),('reference_source',''),('inconnu','0')])
def test_749_rejets_sans_mutation(application,champ,valeur):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][1]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
  assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant


@pytest.mark.parametrize('cas',['omission','doublon_table','doublon_source','deux_profils','absence_contradictoire','solde_injecte','neant_seul','absence_confirmee'])
def test_749_structures_exhaustivite_absence(application,cas):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);p,t=b['tables']
  if cas=='omission':b['tables']=[]
  elif cas=='doublon_table':b['tables']=[p,p]
  elif cas=='doublon_source':t['lignes'][1]['reference_source']='  cr749-a  '
  elif cas=='deux_profils':p['lignes']*=2
  elif cas=='absence_contradictoire':p['lignes'][0]['absence_credits']='oui'
  elif cas=='solde_injecte':b['solde_final']='0'
  else:
   t.update(statut='neant_declare',lignes=[])
   if cas=='absence_confirmee':p['lignes'][0]['absence_credits']='oui'
  avant=donnees_metier(application);rep=api.post(url(v),json=b)
  if cas in ('neant_seul','absence_confirmee'):
   assert controles(ok(rep,201))['montants']['credits_proposes']==('0.00' if cas=='absence_confirmee' else None)
  else:assert rep.status_code==422 and donnees_metier(application)==avant


def test_749_contexte_change_comparaison_et_versions_figees(application):
 with closing(client(application)[0]) as api:
  v=creer(api);r=ok(api.post(url(v),json=body(v)),201);ancien=deepcopy(controles(r))
  q=contexte_body(r);q['tables'][2]['lignes'][0]['montant']='200'
  v2=ok(api.post(contexte_url(r),json=q),201);vue=ok(api.get(url(v2)))
  assert vue['source_contexte_modifiee'] and vue['controle_credits']==ancien
  v3=ok(api.post(url(v2),json=body(v2)),201)
  assert controles(v3)['montants']['ecart_montant_contexte']=='0.00' and not ok(api.get(url(v3)))['source_contexte_modifiee']
  assert controles(r)==ancien


def test_749_droits_societes_devise_hash_concurrence(application):
 with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
  v=creer(api);b=body(v)
  assert autre.get(url(v)).status_code==autre.post(url(v),json=b).status_code==404
  assert api.post(url(v),json={**b,'empreinte_parent':'a'*64}).status_code==409
  sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
  ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
  autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
  assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=b).status_code==403
  with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=b),range(2)))
  assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
  b['tables'][1]['lignes'][0]['montant']='301';assert api.post(url(v),json=b).status_code==409
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
  assert api.get(url(rs[0].json())).status_code==200


def test_749_exports_logo_formules_sources_manifestes(application,tmp_path):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][1]['lignes'][0].update(reference_source='=NOTE749',nature='Source longue '+'justifiée '*100)
  r=ok(api.post(url(v),json=b),201);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
  avant=donnees_metier(application);rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200
  with ZipFile(BytesIO(rep.content)) as z:
   assert z.testzip() is None and json.loads(z.read('credits_is_documentaires.json'))['controle_credits']==controles(r)
   m=json.loads(z.read('MANIFESTE_SHA256.json'));assert set(z.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
   for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
   w=load_workbook(BytesIO(z.read('preparation.xlsx')));valeurs=dict(list(w['Contrôle crédits IS'].values)[1:])
   assert valeurs['Crédits disponibles proposés après qualifications']==325
   assert w['CR-LIGNES']['M2'].value=='=NOTE749' and w['CR-LIGNES']['M2'].data_type=='s'
   with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(n.startswith('xl/media/') for n in x.namelist())
   pdf=PdfReader(BytesIO(z.read('preparation.pdf')));txt='\n'.join(p.extract_text() or '' for p in pdf.pages)
   assert '=NOTE749' in txt and '325,00' in txt and any(p.images for p in pdf.pages)
   (tmp_path/'credits749.pdf').write_bytes(z.read('preparation.pdf'))
  assert donnees_metier(application)==avant
