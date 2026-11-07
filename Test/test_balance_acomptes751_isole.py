"""Acomptes externes : référence2026, affectations exactes et absence de double imputation."""
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
from test_balance_credits749_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,
 creer as credits_creer,body as credits_body,url as credits_url,pure as credits_pure,image_data)


def url(v):return BASE+f'/{v["id"]}/acomptes-is'
def creer(api):
 v=credits_creer(api);return ok(api.post(credits_url(v),json=credits_body(v)),201)
def body(v):
 return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
  {'code':'AP-PROFIL','statut':'documente','justification':'Référence2026 adaptée et solde antérieur fictifs justifiés, mouvements exhaustifs',
   'lignes':[{'nature':'Acomptes fictifs2026','regime':'Société relevant de l’IS','mode':'Quatre acomptes — exercice de douze mois',
    'reference_annuelle':'20000','reference_qualifiee':'oui','exercice_reference':'2025','dernier_clos_confirme':'oui',
    'excedent_anterieur_disponible':'100','origine_excedent':'2025','excedent_qualifie':'oui','exhaustivite':'oui',
    'absence_mouvements':'non','date_controle':'2026-10-23','reference_source':'NOTE-AP751-REF et état excédent170-IV2025'}]},
  {'code':'AP-LIGNES','statut':'documente','justification':'Quittance fictive et affectations exactes des attestations CR749',
   'lignes':[
    {'nature':'Versement et affectations acompte1','numero':'1','date_mouvement':'2026-03-31','verse':'1000','credit_anterieur':'100','retenue':'100','reference_credit':'CR749-A','rattachement_confirme':'oui','reference_source':'AP751-A'},
    {'nature':'Affectation retenue acompte2','numero':'2','date_mouvement':'2026-06-30','verse':'0','credit_anterieur':'0','retenue':'50','reference_credit':'CR749-B','rattachement_confirme':'oui','reference_source':'AP751-B'}]}]}
def controles(v):return v['contenu']['acomptes_is_documentaires']['controle_acomptes']
def pure():
 from services.balance_credits_is_service import calculer_controles
 d,cr=credits_pure();d['contenu']['credits_is_documentaires']={'cle':'cr-fictif751','tables':cr['tables'],'controle_credits':calculer_controles(d,cr)}
 return d,body({'empreinte_sha256':'a'*64})


@pytest.mark.parametrize('cas',['normal','verse_partiel','reference_inconnue','reference_nulle','ref_non_qualifiee','court','regime','inconnu','date_ancienne','date_future','sans_credits','references_inversees','excedent_inconnu','origine2014','absence','neant_seul','ancien','futur','arrondi','decale','minimum','minimum_mauvais_numero'])
def test_751_oracles_calendrier_rapprochement_et_inconnus(cas):
 from services.balance_acomptes_is_service import calculer_controles
 d,b=pure();p=b['tables'][0]['lignes'][0];tl=b['tables'][1];r=tl['lignes'][0]
 if cas=='verse_partiel':r['verse']='400'
 elif cas=='reference_inconnue':p['reference_annuelle']=None
 elif cas=='reference_nulle':p['reference_annuelle']='0'
 elif cas=='ref_non_qualifiee':p['reference_qualifiee']='non'
 elif cas=='court':d['contenu']['periode']['fin']='2026-06-30'
 elif cas=='regime':p['regime']=''
 elif cas=='inconnu':r['verse']=None
 elif cas=='date_ancienne':r['date_mouvement']='2025-12-31'
 elif cas=='date_future':r['date_mouvement']='2026-10-24'
 elif cas=='sans_credits':d['contenu'].pop('credits_is_documentaires')
 elif cas=='references_inversees':r['reference_credit'],tl['lignes'][1]['reference_credit']='CR749-B','CR749-A'
 elif cas=='excedent_inconnu':p['excedent_anterieur_disponible']=None
 elif cas=='origine2014':p['origine_excedent']='2014'
 elif cas in ('absence','neant_seul'):
  tl.update(statut='neant_declare',lignes=[]);d['contenu'].pop('credits_is_documentaires')
  if cas=='absence':p['absence_mouvements']='oui'
 elif cas=='ancien':d['exercice']=2025
 elif cas=='futur':d['exercice']=2027
 elif cas=='arrondi':p['reference_annuelle']='20000.01'
 elif cas=='decale':d['contenu']['periode']={'debut':'2026-04-01','fin':'2027-03-31'}
 elif cas in ('minimum','minimum_mauvais_numero'):
  p.update(mode='Minimum CM3000 — versement unique',reference_annuelle='3000')
  if cas=='minimum':
   tl['lignes']=tl['lignes'][:1]
   cr=d['contenu']['credits_is_documentaires'];cr['tables'][1]['lignes'][1]['deja_impute_acomptes']='0'
   from services.balance_credits_is_service import calculer_controles as recalcul_credit_fictif
   cr['controle_credits']=recalcul_credit_fictif(d,{'tables':cr['tables']})
 avant=deepcopy(d);c=calculer_controles(d,b);m=c['montants'];assert d==avant
 inconnu=cas in ('regime','inconnu','date_ancienne','date_future','sans_credits','references_inversees','excedent_inconnu','origine2014','neant_seul','ancien','futur','decale','minimum_mauvais_numero')
 assert m['acomptes_proposes']==(None if inconnu else {'verse_partiel':'650.00','absence':'0.00','minimum':'1200.00'}.get(cas,'1250.00'))
 assert c['calendrier_disponible']==(cas not in ('reference_inconnue','ref_non_qualifiee','court','regime','ancien','futur'))
 if cas=='normal':
  assert m['versements_declares']=='1000.00' and m['excedent_anterieur_impute']=='100.00' and m['retenues_affectees']=='150.00' and m['excedent_anterieur_restant']=='0.00'
  assert [r['reste'] for r in c['echeancier']]==['3800.00','4950.00','5000.00','5000.00']
  assert [r['statut'] for r in c['echeancier']]==['partiel_en_retard','partiel_en_retard','en_retard','a_venir']
 if cas=='references_inversees':assert m['ecart_retenues']=='0.00' and not all(r['coherent'] for r in c['rapprochement_retenues'])
 if cas=='arrondi':assert m['total_echeances_calcule']=='20000.00' and m['ecart_arrondi_reference']=='-0.01'
 if cas=='decale':assert [r['date_echeance'] for r in c['echeancier']]==['2026-06-30','2026-09-30','2026-12-31','2027-03-31']
 if cas=='minimum':assert len(c['echeancier'])==1 and c['echeancier'][0]['du']=='3000.00'
 assert c['solde_final'] is None and not c['liquidation_confirmee'] and not c['paiement_confirme'];json.dumps(c,allow_nan=False)


def test_751_versions_rejeu_lecture_sans_recalcul(application,monkeypatch):
 from services import balance_acomptes_is_service as s
 from routers.etats import BalanceAcomptesIsIn
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);avant=donnees_metier(application)
  assert ok(api.get(url(v)))['controle_acomptes'] is None
  r=ok(api.post(url(v),json=b),201);vue=ok(api.get(url(r)))
  assert controles(r)['montants']['acomptes_proposes']=='1250.00'
  assert all(r['contenu'][k]==x for k,x in v['contenu'].items())
  def interdit(*a,**kw):raise AssertionError('Pas de recalcul historique crédits')
  monkeypatch.setattr(s,'calculer_controles',interdit)
  with Session(application['engine']) as db:assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceAcomptesIsIn.model_validate(b))==r
  assert ok(api.get(url(r)))==vue and api.get(BASE+f'/{r["id"]}/zip').status_code==200
  assert ok(api.get(BASE+f'/{v["id"]}'))==v
  apres=donnees_metier(application);assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')


@pytest.mark.parametrize('champ,valeur',[
 ('verse','NaN'),('verse','Infinity'),('verse',True),('verse','-1'),('verse','0.001'),('verse','1e9999'),('verse','10000000000000'),
 ('credit_anterieur','101'),('date_mouvement','2026-02-30'),('numero','5'),('rattachement_confirme',True),('reference_source',''),('inconnu','0')])
def test_751_rejets_sans_mutation(application,champ,valeur):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][1]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
  assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant


@pytest.mark.parametrize('cas',['omission','doublon_source','deux_profils','absence_contradictoire','solde_injecte','date_controle','minimum_reference'])
def test_751_structures_et_sources(application,cas):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);p,t=b['tables']
  if cas=='omission':b['tables']=[]
  elif cas=='doublon_source':t['lignes'][1]['reference_source']='  ap751-a  '
  elif cas=='deux_profils':p['lignes']*=2
  elif cas=='absence_contradictoire':p['lignes'][0]['absence_mouvements']='oui'
  elif cas=='solde_injecte':b['solde_final']='0'
  elif cas=='date_controle':p['lignes'][0]['date_controle']='2025-12-31'
  else:p['lignes'][0]['mode']='Minimum CM3000 — versement unique'
  avant=donnees_metier(application);rep=api.post(url(v),json=b)
  assert rep.status_code==422 and donnees_metier(application)==avant


def test_751_credits_change_comparaison_et_versions_figees(application):
 with closing(client(application)[0]) as api:
  v=creer(api);r=ok(api.post(url(v),json=body(v)),201);ancien=deepcopy(controles(r))
  q=credits_body(r);q['tables'][1]['lignes'][0]['montant']='301'
  v2=ok(api.post(credits_url(r),json=q),201);vue=ok(api.get(url(v2)))
  assert vue['source_credits_modifiee'] and vue['controle_acomptes']==ancien
  v3=ok(api.post(url(v2),json=body(v2)),201)
  assert controles(v3)['montants']['acomptes_proposes']=='1250.00' and not ok(api.get(url(v3)))['source_credits_modifiee']
  assert controles(r)==ancien


def test_751_droits_societes_devise_hash_concurrence(application):
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
  b['tables'][1]['lignes'][0]['verse']='1001';assert api.post(url(v),json=b).status_code==409
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
  assert api.get(url(rs[0].json())).status_code==200


def test_751_exports_logo_formules_sources_manifestes(application,tmp_path):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][1]['lignes'][0].update(reference_source='=NOTE751',nature='Source longue '+'justifiée '*100)
  r=ok(api.post(url(v),json=b),201);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
  avant=donnees_metier(application);rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200
  with ZipFile(BytesIO(rep.content)) as z:
   assert z.testzip() is None and json.loads(z.read('acomptes_is_documentaires.json'))['controle_acomptes']==controles(r)
   m=json.loads(z.read('MANIFESTE_SHA256.json'));assert set(z.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
   for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
   w=load_workbook(BytesIO(z.read('preparation.xlsx')));valeurs=dict(list(w['Contrôle acomptes IS'].values)[1:])
   assert valeurs['Acomptes imputables proposés après qualifications']==1250
   assert w['AP-LIGNES']['K2'].value=='=NOTE751' and w['AP-LIGNES']['K2'].data_type=='s'
   assert list(w['Échéancier acomptes IS'].values)[1][4]==3800
   with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(n.startswith('xl/media/') for n in x.namelist())
   pdf=PdfReader(BytesIO(z.read('preparation.pdf')));txt='\n'.join(p.extract_text() or '' for p in pdf.pages)
   assert '=NOTE751' in txt and '1 250,00' in txt and any(p.images for p in pdf.pages)
   (tmp_path/'acomptes751.pdf').write_bytes(z.read('preparation.pdf'))
  assert donnees_metier(application)==avant
