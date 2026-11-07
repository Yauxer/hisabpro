"""Simulation TP native : aucune base/classe/émission réelle inventée."""
from contextlib import closing
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from zipfile import ZipFile
import json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from tp761_support import *
from test_logo_societe import image_data
from test_remunerations_tiers759_isole import verifier_export as export_tiers

@pytest.mark.parametrize('cas',['normal','c1','c3','base_vide','classe_vide','base_non_revue','classe_non_revue','periode_non_revue','referentiel','exhaustivite','profil_partiel','annee_vide','annee2025','annee2027','janvier','particulier','sans_local','avis_vide','avis_non_rattache','avis_ref_vide','avis_partage','zero','petit','arrondi','grand','periode_balance_distincte'])
def test_761_oracles_qualification_et_absence_de_du(cas):
 from routers.etats import BalanceTaxeProfessionnelleIn
 from services.balance_taxe_professionnelle_service import normaliser,calculer_controles
 d={'exercice':2026,'contenu':{'periode':{'debut':'2026-01-01','fin':'2026-12-31'}}};b=body({'empreinte_sha256':'a'*64});p,e=b['tables'];a=e['lignes'][0]
 if cas=='c1':a['classe']='C1'
 elif cas=='c3':a['classe']='C3'
 elif cas=='base_vide':a['valeur_locative']=''
 elif cas=='classe_vide':a['classe']=''
 elif cas=='base_non_revue':a['base_revue']='non'
 elif cas=='classe_non_revue':a['classe_revue']=''
 elif cas=='periode_non_revue':p['lignes'][0]['periode_revue']='non'
 elif cas=='referentiel':p['lignes'][0]['referentiel_revu']=''
 elif cas=='exhaustivite':p['lignes'][0]['exhaustivite']='non'
 elif cas=='profil_partiel':p['statut']='a_completer'
 elif cas=='annee_vide':p['lignes'][0]['annee_tp']=''
 elif cas=='annee2025':p['lignes'][0]['annee_tp']='2025'
 elif cas=='annee2027':p['lignes'][0]['annee_tp']='2027';d['exercice']=2027
 elif cas=='janvier':a['situation_janvier_revue']='non'
 elif cas=='particulier':a['regime']='Situation particulière — à qualifier'
 elif cas=='sans_local':e.update(statut='neant_declare',lignes=[])
 elif cas=='avis_vide':a['montant_avis']=''
 elif cas=='avis_non_rattache':a['avis_rattache']='non'
 elif cas=='avis_ref_vide':a['reference_avis']=''
 elif cas=='avis_partage':e['lignes'][1]['reference_avis']=' avis761-a '
 elif cas=='zero':a['valeur_locative']='0'
 elif cas=='petit':a.update(valeur_locative='100',classe='C3')
 elif cas=='arrondi':a.update(valeur_locative='0.05',classe='C3')
 elif cas=='grand':a.update(valeur_locative='9999999999999.99',classe='C1')
 elif cas=='periode_balance_distincte':d['contenu']['periode']={'debut':'2026-07-01','fin':'2027-06-30'}
 ts=normaliser(d,BalanceTaxeProfessionnelleIn.model_validate(b).tables);avant=deepcopy(d);c=calculer_controles(d,{'tables':ts});assert d==avant;json.dumps(c,allow_nan=False)
 assert c['montant_du_confirme'] is None and not c['imposition_confirmee'] and not c['paiement_confirme'] and not c['pret_a_deposer']
 nonqual=cas in ('base_vide','classe_vide','base_non_revue','classe_non_revue','periode_non_revue','referentiel','exhaustivite','profil_partiel','annee_vide','annee2025','annee2027','janvier','particulier','sans_local')
 if nonqual:assert c['montants']['brut_propose'] is None
 if cas=='normal':assert c['montants']['brut_propose']=='7200.00' and c['montants']['ecart_brut_avis']=='-200.00'
 if cas=='c1':assert c['montants']['brut_propose']=='10200.00'
 if cas=='c3':assert c['montants']['brut_propose']=='4200.00'
 if cas in ('avis_vide','avis_non_rattache','avis_ref_vide','avis_partage'):assert c['montants']['avis_comparables'] is None and c['montants']['ecart_brut_avis'] is None
 if cas=='sans_local':assert all(v is None for v in c['montants'].values()) and any('sans local' in x for x in c['alertes'])
 if cas=='zero':assert c['etablissements'][0]['brut_arithmetique']=='0.00'
 if cas=='petit':assert c['montants']['brut_propose']=='1210.00' and any('inférieur' in x for x in c['alertes'])
 if cas=='arrondi':assert c['etablissements'][0]['brut_exact']=='0.005' and c['montants']['brut_propose']=='1200.01'
 if cas=='grand':assert c['montants']['brut_propose']=='3000000001200.00'
 if cas=='periode_balance_distincte':assert c['montants']['brut_propose']=='7200.00' and c['periode_balance']==d['contenu']['periode']

@pytest.mark.parametrize('champ,valeur',[('valeur_locative','NaN'),('valeur_locative','Infinity'),('valeur_locative',True),('valeur_locative','-1'),('valeur_locative','0.001'),('valeur_locative','10000000000000'),('valeur_locative','1e9999'),('montant_avis','NaN'),('montant_avis','-1'),('classe','C4'),('classe',True),('base_revue','automatique'),('regime','Exonéré automatiquement'),('etablissement_ref',''),('reference_source',''),('inconnu','0')])
def test_761_api_rejets_sans_mutation(application,champ,valeur):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][1]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
  assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant

@pytest.mark.parametrize('cas',['omission','profil_double','etablissement_double','annee_invalide','annee_bool','du_injecte','neant_contradictoire','51etablissements'])
def test_761_api_structures(application,cas):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);p,e=b['tables']
  if cas=='omission':b['tables'].pop()
  elif cas=='profil_double':p['lignes']*=2
  elif cas=='etablissement_double':e['lignes'][1]['etablissement_ref']=' e761-a '
  elif cas=='annee_invalide':p['lignes'][0]['annee_tp']='2026.0'
  elif cas=='annee_bool':p['lignes'][0]['annee_tp']=True
  elif cas=='du_injecte':b['montant_du_confirme']=0
  elif cas=='neant_contradictoire':e['statut']='neant_declare'
  else:
   e['lignes']=[{**deepcopy(e['lignes'][0]),'etablissement_ref':f'E-FICTIF-{i}'} for i in range(51)]
  avant=donnees_metier(application);assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant

def test_761_versions_rejeu_sources_hors_journal(application,monkeypatch):
 from services import balance_taxe_professionnelle_service as s
 from routers.etats import BalanceTaxeProfessionnelleIn
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);avant=donnees_metier(application);r=ok(api.post(url(v),json=b),201);verifier(r)
  assert all(r['contenu'][k]==x for k,x in v['contenu'].items())
  q=body(r);q['tables'][1]['lignes'][0]['montant_avis']='6000';r2=ok(api.post(url(r),json=q),201)
  assert controles(r2)['montants']['ecart_brut_avis']=='0.00' and ok(api.get(BASE+f'/{r["id"]}'))==r
  def interdit(*a,**kw):raise AssertionError('Pas de recalcul historique TP')
  monkeypatch.setattr(s,'calculer_controles',interdit)
  assert ok(api.get(url(r)))['controle_tp']==controles(r)
  with Session(application['engine']) as db:assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceTaxeProfessionnelleIn.model_validate(b))==r
  assert api.get(BASE+f'/{r["id"]}/zip').status_code==200 and ok(api.get(BASE+f'/{v["id"]}'))==v
  apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')

def test_761_roles_societes_concurrence(application):
 with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
  v=creer(api);b=body(v);assert autre.get(url(v)).status_code==autre.post(url(v),json=b).status_code==404
  assert api.post(url(v),json={**b,'empreinte_parent':'a'*64}).status_code==409
  sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email'];ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}));autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
  assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=b).status_code==403
  with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=b),range(2)))
  assert [x.status_code for x in rs]==[201,201] and rs[0].json()==rs[1].json();verifier(rs[0].json())
  b['tables'][1]['lignes'][0]['adresse']='Autre adresse';assert api.post(url(v),json=b).status_code==409
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422

def verifier_export(raw,v):
 proof=export_tiers(raw,v)
 with ZipFile(BytesIO(raw)) as z:
  assert json.loads(z.read('taxe_professionnelle_documentaire.json'))['controle_tp']==controles(v)
  w=load_workbook(BytesIO(z.read('preparation.xlsx')));m=dict(list(w['Simulation brute TP'].values)[1:])
  assert m['Brut simulé après revue documentaire déclarée']==7200 and m['Écart brut simulé moins avis déclarés']==-200 and m['Avis saisis et rattachés explicitement']==7400
  assert len(list(w['TP-E'].values))==3
  pdf=PdfReader(BytesIO(z.read('preparation.pdf')));txt='\n'.join(p.extract_text() or '' for p in pdf.pages)
  assert 'AVIS761-A' in txt and 'BASE-CLASSE761-B' in txt and '7 200,00' in txt and '7 400,00' in txt
  proof.update(fichiers=len(z.namelist()),pdf_pages=len(pdf.pages),excel_feuilles=len(w.sheetnames))
 return proof

def test_761_exports_sources_logo_texte(application):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][0]['lignes'][0]['reference_source']='=NOTE761';r=ok(api.post(url(v),json=b),201)
  ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application);rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200;verifier_export(rep.content,r)
  with ZipFile(BytesIO(rep.content)) as z:
   w=load_workbook(BytesIO(z.read('preparation.xlsx')));assert w['TP-P']['H2'].value=='=NOTE761' and w['TP-P']['H2'].data_type=='s'
  assert donnees_metier(application)==avant
