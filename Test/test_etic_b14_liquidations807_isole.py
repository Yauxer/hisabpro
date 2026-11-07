"""B14 : liquidation comptable OD, sans prétendre prouver un dépôt fiscal."""
from contextlib import closing
from pathlib import Path
from decimal import Decimal as D
from types import SimpleNamespace as N
from uuid import uuid4
import hashlib,json
import httpx
import pytest
from postgres_isole import verifier_cible_isolee
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/recette/jeu_donnees_recette.json'
DATA=json.loads(SOURCE.read_text(encoding='utf8'))

def ok(r,code=200):
 assert r.status_code==code,r.text
 return r.json()

def client(app):
 c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
 api=httpx.Client(base_url=app['api_url'],timeout=30)
 s=DATA['societe'];a=ok(api.post('/api/auth/register',json={'nom':s['nom_admin'],'email':f'b14-{uuid4().hex}@hisabpro-recette.example','password':s['password_test'],'raison_sociale':s['raison_sociale']}))
 api.headers['Authorization']='Bearer '+a['access_token']
 ok(api.patch('/api/societe/moi',json={k:s[k] for k in ['raison_sociale','forme_juridique','ville','adresse','capital_social','devise','identifiant_fiscal','ice','rc','patente','exercice_debut','regime_fiscal','regime_tva','periodicite_tva']}))
 return api

def poster(api,journal,jour,lignes,ref,valider=True):
 e=ok(api.post('/api/ecritures',json={'date':jour,'date_piece':jour,'journal':journal,'libelle':'Test fictif B14','reference':ref,'lignes':lignes,'est_validee':False}),201)
 return ok(api.post(f'/api/ecritures/{e["id"]}/valider')) if valider else e

def b14(api):return next(s for s in ok(api.get('/api/etats/etic/2025'))['sections'] if s['code']=='B14')

def test_807_b14_cinquante_operations_od_du_cahier(application):
 preuve={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'erreur':None}
 try:
  with closing(client(application)) as api:
   tiers={}
   for t in DATA['tiers']:
    tiers[t['code']]=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':t['type'],('compte_client' if t['type']=='client' else 'compte_fournisseur'):t['compte']}),201)
   for o in sorted(DATA['operations'],key=lambda x:x['date']):
    lignes=[{'compte':l['compte'],'debit':l['debit'],'credit':l['credit'],'libelle':o['description'],**({'tiers_id':tiers[l['tiers']]['id']} if l['tiers'] else {})} for l in o['lignes']]
    poster(api,o['journal'],o['date'],lignes,o['reference_recette'])
   avant=ok(api.get('/api/ecritures',params={'exercice':2025}));assert len(avant)==50
   s=b14(api);preuve['b14']=s
   lignes=s['automatique']['lignes'];a,b,charges,immo,c=lignes
   for row,operations,declarations,fin in [(a,'33900','33900','0'),(b,'11680','11600','80'),(charges,'6880','6800','80'),(immo,'4800','4800','0'),(c,'22220','22300','-80')]:
    assert [D(str(row[k])) for k in ['operations','declarations','solde_fin']]==list(map(D,[operations,declarations,fin])),row
   assert not s['complete'] # Aucun dépôt ou confirmation extra-comptable inventé.
   assert ok(api.get('/api/ecritures',params={'exercice':2025}))==avant
   preuve.update(journal_inchange=True,nombre_operations=50)
 except Exception as e:
  preuve['erreur']=repr(e);raise
 finally:(ROOT/'.codex-tests/b14_807_cahier_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')

@pytest.mark.parametrize('journal,comptes,attendu',[
 ('OD',[('4455',200,0),('4456',0,200)],True),
 ('OD',[('3456',200,0),('34552',0,200)],True),
 ('OD',[('4455',100,0),('34552',0,100)],False), # Pas de compte de liquidation : correction indéterminée.
 ('BQ',[('4455',200,0),('4456',0,200)],False),
 ('OD',[('4455',200,0),('5141',0,200)],False),
 ('OD',[('4455',200,0),('4456',0,199)],False),
 ('OD',[('4455',200,0),('4456',0,200),('6583',1,0),('5141',0,1)],False),
 ('OD',[('4455',200,0),('4456-inconnu',0,200)],False),
 ('OD',[('4455',float('nan'),0),('4456',0,200)],False),
 ('OD',[('4455',200,0),('4456',0,float('inf'))],False),
])
def test_807_classification_stricte_sans_heuristique(journal,comptes,attendu):
 from services.etic_service import _est_liquidation_od_tva
 e=N(journal=journal,lignes=[N(compte=c,debit=d,credit=cr) for c,d,cr in comptes],reference='TVA-déclarée',libelle='Déclaration TVA')
 assert _est_liquidation_od_tva(e) is attendu


def test_807_filtres_societe_date_brouillon_et_od_mixte(application):
 def lignes(*valeurs):return [{'compte':c,'debit':d,'credit':cr} for c,d,cr in valeurs]
 with closing(client(application)) as api,closing(client(application)) as autre:
  poster(api,'VT','2025-01-10',lignes(('5141',200,0),('4455',0,200)),'OPERATION')
  poster(api,'OD','2025-01-31',lignes(('4455',200,0),('4456',0,200)),'REFERENCE-SANS-TVA')
  poster(api,'OD','2025-02-01',lignes(('4455',30,0),('6583',0,30)),'TVA-DECLARATION-FAUSSE')
  poster(api,'OD','2025-02-28',lignes(('4455',99,0),('4456',0,99)),'BROUILLON',False)
  poster(api,'OD','2026-01-31',lignes(('4455',700,0),('4456',0,700)),'AUTRE-ANNEE')
  poster(autre,'OD','2025-01-31',lignes(('4455',1000,0),('4456',0,1000)),'AUTRE-SOCIETE')
  avant=ok(api.get('/api/ecritures',params={'exercice':2025}));a=b14(api)['automatique']['lignes'][0]
  assert [D(str(a[k])) for k in ['operations','declarations','solde_fin']]==list(map(D,['170','200','-30'])),a
  assert ok(api.get('/api/ecritures',params={'exercice':2025}))==avant


def test_807_an_et_journal_tv_conservent_leur_traitement(application):
 def lignes(*valeurs):return [{'compte':c,'debit':d,'credit':cr} for c,d,cr in valeurs]
 with closing(client(application)) as api:
  poster(api,'AN','2025-01-01',lignes(('34552',10,0),('1111',0,10)),'OUVERTURE-FICTIVE')
  poster(api,'VT','2025-01-15',lignes(('5141',100,0),('4455',0,100)),'OPERATION')
  poster(api,'TV','2025-01-31',lignes(('4455',100,0),('4456',0,100)),'LIQUIDATION-TV')
  poster(api,'TV','2025-01-31',lignes(('4456',10,0),('34552',0,10)),'DEDUCTION-TV')
  s=b14(api);a,b=s['automatique']['lignes'][:2]
  assert [D(str(a[k])) for k in ['solde_debut','operations','declarations','solde_fin']]==list(map(D,['0','100','100','0']))
  assert [D(str(b[k])) for k in ['solde_debut','operations','declarations','solde_fin']]==list(map(D,['10','0','10','0']))
