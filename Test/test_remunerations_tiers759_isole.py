"""Préparation interne151, API native et invariants sans mutation comptable."""
from contextlib import closing
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from zipfile import ZipFile
import hashlib,json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from tiers759_support import *
from test_logo_societe import image_data

@pytest.mark.parametrize('cas',['normal','inconnu','zero','neant','neant_seul','exhaustivite','identite','sansif_avec_tp','regime_cpu','regime_ae','location','date_hors_periode','date_evenement_hors_periode','date_evenement_vide','sens_vide','categorie_vide','source_non_revue','absence_retenue','identification_partagee','negatif_net','grand'])
def test_759_oracle_inconnus_corrections_et_completude(cas):
 from routers.etats import BalanceRemunerationsTiersIn
 from services.balance_remunerations_tiers_service import normaliser,calculer_controles
 d={'exercice':2026,'contenu':{'periode':{'debut':'2026-01-01','fin':'2026-12-31'}}};b=body({'empreinte_sha256':'a'*64});p,t,m=b['tables'];a=m['lignes'][0]
 if cas=='inconnu':a['soumis']=''
 elif cas=='zero':a.update(soumis='0',retenu='0')
 elif cas in ('neant','neant_seul'):
  t.update(statut='neant_declare',lignes=[]);m.update(statut='neant_declare',lignes=[])
  if cas=='neant':p['lignes'][0]['absence']='oui'
 elif cas=='exhaustivite':p['lignes'][0]['exhaustivite']='non'
 elif cas=='identite':t['lignes'][0]['cnss']=''
 elif cas=='sansif_avec_tp':t['lignes'][0].update(identifiant_fiscal='',identification_tp='TP-FICTIF')
 elif cas=='regime_cpu':t['lignes'][0]['regime']='CPU'
 elif cas=='regime_ae':t['lignes'][0]['regime']='Autoentrepreneur'
 elif cas=='location':a['categorie']='Produits de location — annexe à qualifier'
 elif cas=='date_hors_periode':a['date_comptabilisation']='2025-12-31'
 elif cas=='date_evenement_hors_periode':a['date_evenement']='2027-01-01'
 elif cas=='date_evenement_vide':a['date_evenement']=''
 elif cas=='sens_vide':a['sens']=''
 elif cas=='categorie_vide':a['categorie']=''
 elif cas=='source_non_revue':a['source_revue']='non'
 elif cas=='absence_retenue':a.update(evenement='Aucune retenue déclarée',date_evenement='',soumis='0',retenu='0')
 elif cas=='identification_partagee':t['lignes'][1]['identifiant_fiscal']=t['lignes'][0]['identifiant_fiscal']
 elif cas=='negatif_net':m['lignes'][2].update(comptabilise='2000',soumis='1000',retenu='40')
 elif cas=='grand':a['comptabilise']='9999999999999.99'
 ts=normaliser(d,BalanceRemunerationsTiersIn.model_validate(b).tables);avant=deepcopy(d);c=calculer_controles(d,{'tables':ts});assert d==avant
 assert not c['pret_a_deposer'] and not c['declaration_officielle'] and not c['ecritures_generees'];json.dumps(c,allow_nan=False)
 if cas=='normal':assert c['montants']=={'comptabilise':'1400.00','soumis':'740.00','retenu':'37.00'} and c['revue_documentaire_declaree']
 if cas=='inconnu':assert c['montants']['soumis'] is None and c['montants']['retenu']=='37.00' and not c['revue_documentaire_declaree']
 if cas=='neant':assert c['montants']==dict.fromkeys(('comptabilise','soumis','retenu'),'0.00') and c['absence_exhaustive_confirmee']
 if cas=='neant_seul':assert c['montants']==dict.fromkeys(('comptabilise','soumis','retenu')) and not c['absence_exhaustive_confirmee']
 if cas in ('identite','exhaustivite','regime_cpu','regime_ae','location','date_hors_periode','date_evenement_hors_periode','date_evenement_vide','sens_vide','categorie_vide','source_non_revue'):assert not c['revue_documentaire_declaree']
 if cas=='sansif_avec_tp':assert c['revue_documentaire_declaree']
 if cas=='grand':assert c['montants']['comptabilise']=='10000000000399.99'
 if cas=='negatif_net':assert c['montants']['comptabilise']=='-500.00' and any('négatif' in a for a in c['alertes'])
 if cas=='identification_partagee':assert any('partagée' in a for a in c['alertes'])

@pytest.mark.parametrize('champ,valeur',[('comptabilise','NaN'),('comptabilise','Infinity'),('comptabilise',True),('comptabilise','-1'),('comptabilise','0.001'),('comptabilise','10000000000000'),('comptabilise','1e9999'),('soumis','NaN'),('retenu','NaN'),('retenu','601'),('beneficiaire_ref','B-INCONNU'),('date_comptabilisation','2026-02-30'),('date_evenement','20260710'),('sens','Autre'),('categorie','Salaire'),('evenement','Date facture'),('reference_source',''),('source_revue',True),('inconnu','0')])
def test_759_api_rejets_sans_mutation(application,champ,valeur):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][2]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
  assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant

@pytest.mark.parametrize('cas',['omission','profil_double','benef_double','source_double','correction_sans_origine','correction_meme_origine','allocation_avec_origine','absence_contradictoire','sans_benef_ref','regime_inconnu','neant_contradictoire','montant_absence','date_absence','declaration_injectee'])
def test_759_api_structure_et_provenance(application,cas):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);p,t,m=b['tables']
  if cas=='omission':b['tables'].pop()
  elif cas=='profil_double':p['lignes']*=2
  elif cas=='benef_double':t['lignes'][1]['beneficiaire_ref']='  b759-a '
  elif cas=='source_double':m['lignes'][1]['reference_source']=' m759-a '
  elif cas=='correction_sans_origine':m['lignes'][2]['reference_origine']=''
  elif cas=='correction_meme_origine':m['lignes'][2]['reference_origine']=' m759-c '
  elif cas=='allocation_avec_origine':m['lignes'][0]['reference_origine']='Autre'
  elif cas=='absence_contradictoire':p['lignes'][0]['absence']='oui'
  elif cas=='sans_benef_ref':t['lignes'][0]['beneficiaire_ref']=''
  elif cas=='regime_inconnu':t['lignes'][0]['regime']='Exonéré automatiquement'
  elif cas=='neant_contradictoire':m['statut']='neant_declare'
  elif cas=='montant_absence':m['lignes'][0].update(evenement='Aucune retenue déclarée',date_evenement='')
  elif cas=='date_absence':m['lignes'][0].update(evenement='Aucune retenue déclarée',soumis='0',retenu='0')
  else:b['pret_a_deposer']=True
  avant=donnees_metier(application);assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant

def test_759_versions_rejeu_source_figee_sans_journal(application,monkeypatch):
 from services import balance_remunerations_tiers_service as s
 from routers.etats import BalanceRemunerationsTiersIn
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);avant=donnees_metier(application);r=ok(api.post(url(v),json=b),201);verifier(r)
  assert all(r['contenu'][k]==x for k,x in v['contenu'].items()) and ok(api.get(BASE+f'/{v["id"]}'))==v
  q=body(r);q['tables'][1]['lignes'][0]['nature']='Identité corrigée explicitement'
  r2=ok(api.post(url(r),json=q),201);assert r2['version']==r['version']+1 and ok(api.get(BASE+f'/{r["id"]}'))==r
  def interdit(*a,**kw):raise AssertionError('Aucun recalcul historique')
  monkeypatch.setattr(s,'calculer_controles',interdit)
  assert ok(api.get(url(r)))['controle_tiers']==controles(r)
  with Session(application['engine']) as db:assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceRemunerationsTiersIn.model_validate(b))==r
  assert api.get(BASE+f'/{r["id"]}/zip').status_code==200
  apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')

def test_759_roles_societes_hash_concurrence(application):
 with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
  v=creer(api);b=body(v);assert autre.get(url(v)).status_code==autre.post(url(v),json=b).status_code==404
  assert api.post(url(v),json={**b,'empreinte_parent':'a'*64}).status_code==409
  sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email'];ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
  autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
  assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=b).status_code==403
  with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=b),range(2)))
  assert [x.status_code for x in rs]==[201,201] and rs[0].json()==rs[1].json();verifier(rs[0].json())
  b['tables'][1]['lignes'][0]['adresse']='Autre adresse fictive';assert api.post(url(v),json=b).status_code==409
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422

def verifier_export(raw,v):
 with ZipFile(BytesIO(raw)) as z:
  assert z.testzip() is None and json.loads(z.read('remunerations_tiers_documentaires.json'))['controle_tiers']==controles(v)
  assert json.loads(z.read('liquidation_is_documentaire.json'))['controle_liquidation']['montants']['solde_is_propose']=='3650.00'
  m=json.loads(z.read('MANIFESTE_SHA256.json'));assert set(z.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
  for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
  w=load_workbook(BytesIO(z.read('preparation.xlsx')));assert dict(list(w['Contrôle rémunérations tiers'].values)[1:])=={'Sommes comptabilisées nettes déclarées':1400,'Sommes soumises nettes déclarées':740,'Retenues nettes déclarées':37}
  assert len(list(w['T151-M'].values))==4 and len(list(w['T151-B'].values))==3
  with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(n.startswith('xl/media/') for n in x.namelist())
  pdf=PdfReader(BytesIO(z.read('preparation.pdf')));txt='\n'.join(p.extract_text() or '' for p in pdf.pages)
  assert 'M759-C' in txt and 'CNSS-FICTIF759-A' in txt and '1 400,00' in txt and any(p.images for p in pdf.pages)
  return {'fichiers':len(z.namelist()),'pdf_pages':len(pdf.pages),'excel_feuilles':len(w.sheetnames),'logo':True}

def test_759_exports_sources_logo_sans_ecriture(application):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][1]['lignes'][0]['reference_source']='=SOURCE759'
  r=ok(api.post(url(v),json=b),201);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
  rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200;verifier_export(rep.content,r)
  with ZipFile(BytesIO(rep.content)) as z:
   w=load_workbook(BytesIO(z.read('preparation.xlsx')));c=w['T151-B'].cell(2,12);assert c.value=='=SOURCE759' and c.data_type=='s'
  assert donnees_metier(application)==avant
