"""Proposition externe : oracles indépendants, sources synchronisées, aucun paiement confirmé."""
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
from test_balance_acomptes751_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,
 creer as ap_creer,body as ap_body,url as ap_url,pure as ap_pure,image_data,credits_body,credits_url)
from test_balance_cotisation_minimale741_isole import body as cm_body,url as cm_url,b12_body,b12_url
from test_balance_css743_isole import body as css_body,url as css_url


def url(v):return BASE+f'/{v["id"]}/liquidation-is'
def creer(api,css=False):
 v=ap_creer(api);v=ok(api.post(ap_url(v),json=ap_body(v)),201)
 if css:
  q=css_body(v);q['tables'][0]['lignes'][0]['benefice_reference']='100000';v=ok(api.post(css_url(v),json=q),201)
 return v
def body(v):
 return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
  {'code':'LIQ-N','statut':'documente','justification':'Revue fictive753 des justificatifs et ordre de simulation documenté',
   'lignes':[{'nature':'Revue fiscale fictive2026','b12_verifie':'oui','cm_verifiee':'oui','exhaustivite_verifiee':'oui',
    'excedent_verifie':'oui','ordre_examine':'oui','excedent_annuel':'0','reference_source':'REVUE753 et contrôles B12/CM/CR/AP conservés'}]}]}
def controles(v):return v['contenu']['liquidation_is_documentaire']['controle_liquidation']
def pure():
 from services.balance_passage_fiscal_service import calculer_controles as b12
 from services.balance_cotisation_minimale_service import calculer_controles as cm
 from services.balance_acomptes_is_service import calculer_controles as ap
 d,q=ap_pure();b=b12_body({'empreinte_sha256':'a'*64});c=cm_body({'empreinte_sha256':'a'*64})
 d['contenu']['passage_fiscal_documentaire']={'cle':'b12-fictif753','controle_passage_fiscal':b12(d,b)}
 d['contenu']['cotisation_minimale_documentaire']={'cle':'cm-fictif753','controle_cm':cm(d,c)}
 d['contenu']['acomptes_is_documentaires']={'cle':'ap-fictif753','tables':q['tables'],'controle_acomptes':ap(d,q)}
 return d,body({'empreinte_sha256':'a'*64})


@pytest.mark.parametrize('cas',['normal','css_zero','css_30000','b12_absent','cm_absent','cr_absent','ap_absent',
 'b12_revue','cm_revue','exhaustivite','excedent_revue','ordre','direct_inconnu','cm_desynchronisee','ap_desynchronise',
 'cm_incoherente','cr_incoherents','ap_incoherents','ancien_incoherent','nonfini_source','booleen_source','futur',
 'acomptes_excedentaires','credits_excedentaires','excedent_annuel','cm_exoneree'])
def test_753_oracles_coherence_sans_double_utilisation(cas):
 from services.balance_liquidation_is_service import calculer_controles
 from services.balance_acomptes_is_service import calculer_controles as ap
 from services.balance_credits_is_service import calculer_controles as cr
 from services.balance_cotisation_minimale_service import calculer_controles as cm
 from services.balance_css_service import calculer_controles as css
 d,b=pure();co=d['contenu'];r=b['tables'][0]['lignes'][0]
 absents={'b12_absent':'passage_fiscal_documentaire','cm_absent':'cotisation_minimale_documentaire','cr_absent':'credits_is_documentaires','ap_absent':'acomptes_is_documentaires'}
 if cas in absents:co.pop(absents[cas])
 elif cas in ('css_zero','css_30000'):
  q=css_body({'empreinte_sha256':'a'*64});q['tables'][0]['lignes'][0]['benefice_reference']='100000' if cas=='css_zero' else '2000000'
  co['css_documentaire']={'cle':'css-fictif753','controle_css':css(d,q)}
 elif cas in ('b12_revue','cm_revue','exhaustivite','excedent_revue','ordre'):
  r[{'b12_revue':'b12_verifie','cm_revue':'cm_verifiee','exhaustivite':'exhaustivite_verifiee','excedent_revue':'excedent_verifie','ordre':'ordre_examine'}[cas]]=''
 elif cas=='direct_inconnu':r['excedent_annuel']=None
 elif cas=='cm_desynchronisee':co['cotisation_minimale_documentaire']['controle_cm']['source_b12']['cle']='autre-b12'
 elif cas=='ap_desynchronise':co['acomptes_is_documentaires']['controle_acomptes']['source_credits']['cle']='autres-credits'
 elif cas=='cm_incoherente':co['cotisation_minimale_documentaire']['controle_cm']['montants']['impot_avant_imputations_propose']='2999.00'
 elif cas=='cr_incoherents':co['credits_is_documentaires']['controle_credits']['montants']['credits_proposes']='326.00'
 elif cas=='ap_incoherents':co['acomptes_is_documentaires']['controle_acomptes']['montants']['acomptes_proposes']='1251.00'
 elif cas=='ancien_incoherent':co['acomptes_is_documentaires']['controle_acomptes']['montants']['excedent_anterieur_restant']='100.00'
 elif cas=='nonfini_source':co['passage_fiscal_documentaire']['controle_passage_fiscal']['montants']['is_theorique_taux_declare']='NaN'
 elif cas=='booleen_source':co['cotisation_minimale_documentaire']['controle_cm']['montants']['cm_exigible']=False
 elif cas=='futur':d['exercice']=2027
 elif cas=='acomptes_excedentaires':
  q={'tables':co['acomptes_is_documentaires']['tables']};q['tables'][1]['lignes'][0]['verse']='4000';co['acomptes_is_documentaires']['controle_acomptes']=ap(d,q)
 elif cas=='credits_excedentaires':
  q={'tables':co['credits_is_documentaires']['tables']};q['tables'][1]['lignes'][0]['montant']='3975';co['credits_is_documentaires']['controle_credits']=cr(d,q)
  co['acomptes_is_documentaires']['controle_acomptes']=ap(d,{'tables':co['acomptes_is_documentaires']['tables']})
 elif cas=='excedent_annuel':
  q={'tables':co['acomptes_is_documentaires']['tables']};q['tables'][0]['lignes'][0]['excedent_anterieur_disponible']='600';co['acomptes_is_documentaires']['controle_acomptes']=ap(d,q);r['excedent_annuel']='500'
 elif cas=='cm_exoneree':
  q=cm_body({'empreinte_sha256':'a'*64});q['tables'][0]['lignes'][0]['exoneration_totale']='oui';co['cotisation_minimale_documentaire']['controle_cm']=cm(d,q)
 avant=deepcopy(d);c=calculer_controles(d,b);m=c['montants'];assert d==avant
 positifs=('normal','css_zero','css_30000','acomptes_excedentaires','credits_excedentaires','excedent_annuel','cm_exoneree')
 assert c['proposition_disponible']==(cas in positifs)
 assert m['solde_is_propose']==({'acomptes_excedentaires':'0.00','credits_excedentaires':'0.00','excedent_annuel':'925.00','cm_exoneree':'0.00'}.get(cas,'1425.00') if cas in positifs else None)
 if cas=='normal':assert m['credits_disponibles']=='325.00' and m['acomptes_imputables']=='1250.00' and m['excedent_arithmetique']=='0.00'
 if cas in ('acomptes_excedentaires','credits_excedentaires','cm_exoneree'):assert m['excedent_arithmetique']=={'acomptes_excedentaires':'1575.00','credits_excedentaires':'2250.00','cm_exoneree':'115.00'}[cas]
 assert m['css_separee']=={'css_zero':'0.00','css_30000':'30000.00'}.get(cas)
 assert c['total_global_is_css'] is None and not c['liquidation_confirmee'] and not c['paiement_confirme'] and not c['pret_a_deposer'];json.dumps(c,allow_nan=False)


def test_753_versions_rejeu_lecture_sans_recalcul(application,monkeypatch):
 from services import balance_liquidation_is_service as s
 from routers.etats import BalanceLiquidationIsIn
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);avant=donnees_metier(application)
  assert ok(api.get(url(v)))['controle_liquidation'] is None
  r=ok(api.post(url(v),json=b),201);vue=ok(api.get(url(r)))
  assert controles(r)['montants']['solde_is_propose']=='1425.00'
  assert all(r['contenu'][k]==x for k,x in v['contenu'].items())
  def interdit(*a,**kw):raise AssertionError('Pas de recalcul historique crédits')
  monkeypatch.setattr(s,'calculer_controles',interdit)
  with Session(application['engine']) as db:assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceLiquidationIsIn.model_validate(b))==r
  assert ok(api.get(url(r)))==vue and api.get(BASE+f'/{r["id"]}/zip').status_code==200
  assert ok(api.get(BASE+f'/{v["id"]}'))==v
  apres=donnees_metier(application);assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')


@pytest.mark.parametrize('champ,valeur',[
 ('excedent_annuel','NaN'),('excedent_annuel','Infinity'),('excedent_annuel',True),('excedent_annuel','-1'),('excedent_annuel','0.001'),
 ('excedent_annuel','1e9999'),('excedent_annuel','10000000000000'),('excedent_annuel','0.01'),('ordre_examine','probable'),('b12_verifie',True),('reference_source',''),('inconnu','0')])
def test_753_rejets_sans_mutation(application,champ,valeur):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][0]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
  assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant


@pytest.mark.parametrize('cas',['omission','doublon_table','deux_revues','confirmation_injectee','neant'])
def test_753_structures_et_aucune_confirmation(application,cas):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);t=b['tables'][0]
  if cas=='omission':b['tables']=[]
  elif cas=='doublon_table':b['tables']*=2
  elif cas=='deux_revues':t['lignes']*=2
  elif cas=='confirmation_injectee':b['liquidation_confirmee']=True
  else:t.update(statut='neant_declare',lignes=[])
  avant=donnees_metier(application);rep=api.post(url(v),json=b)
  if cas=='neant':assert controles(ok(rep,201))['montants']['solde_is_propose'] is None
  else:assert rep.status_code==422 and donnees_metier(application)==avant


def test_753_sources_synchronisees_ancien_calcul_fige_et_revue_explicitement_reprise(application):
 with closing(client(application)[0]) as api:
  v=creer(api);r=ok(api.post(url(v),json=body(v)),201);ancien=deepcopy(controles(r))
  q=b12_body(r);q['tables'][0]['lignes'][0]['taux_is']='10'
  v2=ok(api.post(b12_url(r),json=q),201);vue=ok(api.get(url(v2)))
  assert vue['sources_is_modifiees'] and vue['controle_liquidation']==ancien
  v3=ok(api.post(url(v2),json=body(v2)),201);assert controles(v3)['montants']['solde_is_propose'] is None
  v4=ok(api.post(cm_url(v3),json=cm_body(v3)),201);v5=ok(api.post(url(v4),json=body(v4)),201)
  assert controles(v5)['montants']['solde_is_propose']=='1425.00' and not ok(api.get(url(v5)))['sources_is_modifiees']
  assert controles(r)==ancien


def test_753_css_separee_n_actualise_pas_is_historique(application):
 with closing(client(application)[0]) as api:
  v=creer(api);r=ok(api.post(url(v),json=body(v)),201);ancien=deepcopy(controles(r))
  q=css_body(r);q['tables'][0]['lignes'][0]['benefice_reference']='100000'
  v2=ok(api.post(css_url(r),json=q),201);vue=ok(api.get(url(v2)))
  assert vue['source_css_modifiee'] and not vue['sources_is_modifiees'] and vue['controle_liquidation']==ancien
  v3=ok(api.post(url(v2),json=body(v2)),201);assert controles(v3)['montants']['css_separee']=='0.00' and controles(v3)['montants']['solde_is_propose']=='1425.00'


def test_753_droits_societes_devise_hash_concurrence(application):
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
  b['tables'][0]['lignes'][0]['nature']='Revue modifiée';assert api.post(url(v),json=b).status_code==409
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
  assert api.get(url(rs[0].json())).status_code==200


def test_753_exports_logo_formules_sources_manifestes(application,tmp_path):
 with closing(client(application)[0]) as api:
  v=creer(api,css=True);b=body(v);b['tables'][0]['lignes'][0].update(reference_source='=NOTE753',nature='Source longue '+'justifiée '*100)
  r=ok(api.post(url(v),json=b),201);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
  avant=donnees_metier(application);rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200
  with ZipFile(BytesIO(rep.content)) as z:
   assert z.testzip() is None and json.loads(z.read('liquidation_is_documentaire.json'))['controle_liquidation']==controles(r)
   m=json.loads(z.read('MANIFESTE_SHA256.json'));assert set(z.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
   for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
   w=load_workbook(BytesIO(z.read('preparation.xlsx')));valeurs=dict(list(w['Proposition IS CM'].values)[1:])
   assert valeurs['Solde IS/CM proposé à payer']==1425 and valeurs['CSS proposée séparément dans sa qualification conservée']==0
   assert w['Revue proposition IS']['J2'].value=='=NOTE753' and w['Revue proposition IS']['J2'].data_type=='s'
   with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(n.startswith('xl/media/') for n in x.namelist())
   pdf=PdfReader(BytesIO(z.read('preparation.pdf')));txt='\n'.join(p.extract_text() or '' for p in pdf.pages)
   assert '=NOTE753' in txt and '1 425,00' in txt and any(p.images for p in pdf.pages)
   (tmp_path/'liquidation753.pdf').write_bytes(z.read('preparation.pdf'))
  assert donnees_metier(application)==avant
