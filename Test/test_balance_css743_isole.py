"""CSS externe : seuils indépendants, inconnus, API native et versions immuables."""
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
from test_balance_cotisation_minimale741_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,source,
 creer as cm_creer,body as cm_body,url as cm_url,b12_body,b12_url,image_data)
from test_balance_contexte_fiscal735_isole import body as contexte_body,url as contexte_url


def url(v):return BASE+f'/{v["id"]}/css-documentaire'
def creer(api,contexte=True):
 v=cm_creer(api);v=ok(api.post(cm_url(v),json=cm_body(v)),201)
 return ok(api.post(contexte_url(v),json=contexte_body(v)),201) if contexte else v
def body(v):
 return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
  {'code':'CSS-N','statut':'documente','justification':'Qualification fictive743 : dernier exercice clos2025 et absence d’exonération permanente explicitement justifiés',
   'lignes':[{'nature':'CSS fictive2026','regime':'Société relevant de l’IS','exercice_reference':'2025',
    'benefice_reference':'2000000','dernier_clos_confirme':'oui','exoneration_permanente':'non','reference_source':'NOTE-CSS2025-743, bénéfice net fiscal servant à l’IS'}]}]}
def controles(v):return v['contenu']['css_documentaire']['controle_css']


@pytest.mark.parametrize('base,taux,montant',[
 ('0','0.000','0.00'),('999999.99','0.000','0.00'),('1000000','1.500','15000.00'),
 ('4999999.99','1.500','75000.00'),('5000000','2.500','125000.00'),('9999999.99','2.500','250000.00'),
 ('10000000','3.500','350000.00'),('39999999.99','3.500','1400000.00'),('40000000','5.000','2000000.00'),
 ('9999999999999.99','5.000','500000000000.00')])
def test_743_seuils_proportionnels_independants(base,taux,montant):
 from services.balance_css_service import calculer_controles
 d=source();d['exercice']=2026;q=body({'empreinte_sha256':'a'*64});q['tables'][0]['lignes'][0]['benefice_reference']=base
 avant=deepcopy(d);c=calculer_controles(d,q)
 assert d==avant and c['taux_proportionnel']==taux and c['montants']['css_proposee']==montant
 assert c['montants']['css_declaree_contexte'] is c['montants']['ecart_css_declaree'] is None
 assert c['date_echeance'] is c['solde_is'] is None and not c['pret_a_deposer']
 json.dumps(c,allow_nan=False)


@pytest.mark.parametrize('cas',['base','reference','regime','exoneration','confirmation','non_confirme','neant','vide','ancien','futur','exonere'])
def test_743_inconnus_sans_emprunter_resultat_comptable(cas):
 from services.balance_css_service import calculer_controles
 d=source();d['exercice']=2026;q=body({'empreinte_sha256':'a'*64});r=q['tables'][0]['lignes'][0]
 if cas=='base':r['benefice_reference']=None
 elif cas=='reference':r['exercice_reference']=''
 elif cas=='regime':r['regime']=''
 elif cas=='exoneration':r['exoneration_permanente']=''
 elif cas=='confirmation':r['dernier_clos_confirme']=''
 elif cas=='non_confirme':r['dernier_clos_confirme']='non'
 elif cas in ('neant','vide'):q['tables'][0].update(statut='neant_declare' if cas=='neant' else 'a_completer',lignes=[])
 elif cas=='ancien':d['exercice']=2025
 elif cas=='futur':d['exercice']=2027
 else:r['exoneration_permanente']='oui'
 c=calculer_controles(d,q)
 assert c['montants']['css_proposee']==('0.00' if cas=='exonere' else None)
 if cas in ('reference','neant','vide'):assert c['exercice_reference_declare'] is None
 assert c['date_echeance'] is None and not c['liquidation_confirmee'] and not c['paiement_confirme']


def test_743_versions_rejeu_lecture_sans_recalcul(application,monkeypatch):
 from services import balance_css_service as s
 from routers.etats import BalanceCssIn
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);avant=donnees_metier(application)
  assert ok(api.get(url(v)))['controle_css'] is None
  r=ok(api.post(url(v),json=b),201);vue=ok(api.get(url(r)))
  assert controles(r)['montants']['css_proposee']==controles(r)['montants']['ecart_css_declaree']=='30000.00'
  assert all(r['contenu'][k]==x for k,x in v['contenu'].items())
  def interdit(*a,**kw):raise AssertionError('Pas de recalcul historique CSS')
  monkeypatch.setattr(s,'calculer_controles',interdit)
  with Session(application['engine']) as db:assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceCssIn.model_validate(b))==r
  assert ok(api.get(url(r)))==vue and api.get(BASE+f'/{r["id"]}/zip').status_code==200
  assert ok(api.get(BASE+f'/{v["id"]}'))==v
  apres=donnees_metier(application);assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')


@pytest.mark.parametrize('champ,valeur',[
 ('benefice_reference','NaN'),('benefice_reference','Infinity'),('benefice_reference',True),('benefice_reference','-1'),
 ('benefice_reference','0.001'),('benefice_reference','1e9999'),('benefice_reference','10000000000000'),
 ('exercice_reference','2027'),('exercice_reference','2025.0'),('exercice_reference',True),('regime','IR'),
 ('exoneration_permanente','temporaire'),('dernier_clos_confirme',False),('reference_source','')])
def test_743_rejets_sans_mutation(application,champ,valeur):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][0]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
  assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant


@pytest.mark.parametrize('cas',['omission','doublon','deux_lignes','solde_injecte','neant'])
def test_743_structures_et_neant(application,cas):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);t=b['tables'][0]
  if cas=='omission':b['tables']=[]
  elif cas=='doublon':b['tables']*=2
  elif cas=='deux_lignes':t['lignes']*=2
  elif cas=='solde_injecte':b['solde_is']='0'
  else:t.update(statut='neant_declare',lignes=[])
  avant=donnees_metier(application);r=api.post(url(v),json=b)
  if cas=='neant':assert controles(ok(r,201))['montants']['css_proposee'] is None
  else:assert r.status_code==422 and donnees_metier(application)==avant


def test_743_changement_contexte_et_comparaison_figee(application):
 with closing(client(application)[0]) as api:
  v=creer(api);r=ok(api.post(url(v),json=body(v)),201);ancien=deepcopy(controles(r))
  q=contexte_body(r);q['tables'][1]['lignes'][0]['montant']='30000'
  v2=ok(api.post(contexte_url(r),json=q),201);vue=ok(api.get(url(v2)))
  assert vue['source_contexte_modifiee'] and vue['controle_css']==ancien
  v3=ok(api.post(url(v2),json=body(v2)),201)
  assert controles(v3)['montants']['ecart_css_declaree']=='0.00' and not ok(api.get(url(v3)))['source_contexte_modifiee']
  assert controles(r)==ancien


def test_743_b12_courant_ne_remplace_pas_reference_fiscale(application):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][0]['lignes'][0]['benefice_reference']=None
  r=ok(api.post(url(v),json=b),201);assert controles(r)['montants']['css_proposee'] is None
  q=b12_body(r);q['tables'][0]['lignes'][0]['taux_is']='10'
  v2=ok(api.post(b12_url(r),json=q),201);assert ok(api.get(url(v2)))['controle_css']==controles(r)


def test_743_droits_societes_devise_hash_concurrence(application):
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
  b['tables'][0]['lignes'][0]['benefice_reference']='1';assert api.post(url(v),json=b).status_code==409
  ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
  assert api.get(url(rs[0].json())).status_code==200


def test_743_exports_logo_formules_sources_et_manifestes(application,tmp_path):
 with closing(client(application)[0]) as api:
  v=creer(api);b=body(v);b['tables'][0]['lignes'][0].update(reference_source='=NOTE743',nature='Source longue '+'justifiée '*100)
  r=ok(api.post(url(v),json=b),201);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
  avant=donnees_metier(application);rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200
  with ZipFile(BytesIO(rep.content)) as z:
   assert z.testzip() is None and json.loads(z.read('css_documentaire.json'))['controle_css']==controles(r)
   m=json.loads(z.read('MANIFESTE_SHA256.json'))
   assert set(z.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
   for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
   w=load_workbook(BytesIO(z.read('preparation.xlsx')));valeurs={r[0]:r[1:] for r in list(w['Calcul CSS'].values)[1:]}
   assert valeurs['CSS proposée selon qualifications déclarées']==(30000,'MAD') and valeurs['Taux proportionnel']==(1.5,'%')
   assert w['Qualification CSS']['I2'].value=='=NOTE743' and w['Qualification CSS']['I2'].data_type=='s'
   with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(n.startswith('xl/media/') for n in x.namelist())
   pdf=PdfReader(BytesIO(z.read('preparation.pdf')));txt='\n'.join(p.extract_text() or '' for p in pdf.pages)
   assert '=NOTE743' in txt and '30 000,00' in txt and any(p.images for p in pdf.pages)
   (tmp_path/'css743.pdf').write_bytes(z.read('preparation.pdf'))
  assert donnees_metier(application)==avant
