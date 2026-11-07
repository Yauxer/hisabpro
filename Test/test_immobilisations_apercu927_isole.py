"""Aperçu de sortie réel, calcul partagé et lecture seule sur PostgreSQL nonce."""
from pathlib import Path
from contextlib import closing
from types import SimpleNamespace
from decimal import Decimal as D
from datetime import date
import json,pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
import schemas
from routers.immobilisations import apercu_sortie_immobilisation,_proteger_mutation_registre
from test_factures_conservation923_isole import (
 application,application104,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok)
from postgres_isole import verifier_cible_isolee

R=Path(__file__).resolve().parents[1]
def url(i):return f'/api/immobilisations/{i["id"]}/sortie'
def demande(**kw):return {'type_sortie':'cession','date_sortie':'2026-01-01','prix_cession_ht':20000,'taux_tva_cession':20,'encaissement_immediat':False,**kw}

def preparer(api,methode='lineaire',amortissable=True):
 if not any(e['annee']==2025 for e in ok(api.get('/api/exercices'))):ok(api.post('/api/exercices',json={'annee':2025,'date_debut':'2025-01-01','date_fin':'2025-12-31'}),201)
 f=ok(api.post('/api/tiers',json={'nom':'Fournisseur FICTIF927','type':'fournisseur'}),201)
 i=ok(api.post('/api/immobilisations',json={'designation':'Immobilisation FICTIVE927','categorie':'Matériel informatique' if amortissable else 'Terrain','date_acquisition':'2025-01-01','date_mise_en_service':'2025-01-01','prix_acquisition_ht':24000,'duree_amort':5,'methode':methode,'amortissable':amortissable,'valeur_residuelle':0,'fournisseur_tiers_id':f['id'],'compte_immo':'2355' if amortissable else '2311','compte_amort':'28355','compte_dotation':'61935'}),201)
 ok(api.post(f'/api/ecritures/{i["ecriture_acquisition_id"]}/valider'))
 if amortissable:
  e=ok(api.post(f'/api/immobilisations/{i["id"]}/generer-ecriture',params={'annee':2025}));ok(api.post(f'/api/ecritures/{e["ecriture_id"]}/valider'))
 return i

def photo(app,sid):
 with app['engine'].connect() as db:
  r={t:list(db.scalars(text(f'SELECT row_to_json(t)::text FROM {t} t WHERE societe_id=:s ORDER BY id'),{'s':sid})) for t in ['immobilisations','ecritures','exercices_comptables']}
  for t,parent,fk in [('lignes_ecriture','ecritures','ecriture_id'),('periodes_comptables','exercices_comptables','exercice_id')]:r[t]=list(db.scalars(text(f'SELECT row_to_json(t)::text FROM {t} t JOIN {parent} p ON p.id=t.{fk} WHERE p.societe_id=:s ORDER BY t.id'),{'s':sid}))
  r['sequences']={t:db.scalar(text(f'SELECT last_value FROM {t}_id_seq')) for t in ['immobilisations','ecritures','lignes_ecriture','exercices_comptables','periodes_comptables']}
  return r

@pytest.mark.parametrize('methode,cumul,vnc,gain,annuite',[('lineaire','4813.33','19186.67','813.33','13.33'),('degressif','10080.00','13920.00','6080.00','480.00')])
def test_927_apercu_sans_mutation_et_montants_identiques_enregistrement(application,methode,cumul,vnc,gain,annuite):
 with closing(client(application)[0]) as api:
  i=preparer(api,methode);u=ok(api.get('/api/auth/me'));avant=photo(application,u['societe_id']);body=demande();a=ok(api.post(url(i)+'/apercu',json=body));assert photo(application,u['societe_id'])==avant
  assert [D(str(a[k])) for k in ['cumul_amortissement','vnc','resultat_cession']]==list(map(D,[cumul,vnc,gain]));assert a['dotations'][-1]['annee']==2026 and D(str(a['dotations'][-1]['dotation']))==D(annuite) and a['dotations'][-1]['etat']=='à comptabiliser';assert a['dotations'][0]['etat']=='déjà comptabilisée'
  assert ok(api.post(url(i)+'/apercu',json=body))==a and photo(application,u['societe_id'])==avant
  r=ok(api.post(url(i),json={**body,'empreinte_apercu':a['empreinte_apercu']}));assert all(D(str(r[k]))==D(str(a[k])) for k in ['vnc','cumul_amortissement','prix_cession_ht','tva_cession','ttc_cession','resultat_cession'])
  apres=photo(application,u['societe_id']);assert all(x in apres['ecritures'] for x in avant['ecritures']) and len(apres['ecritures'])==len(avant['ecritures'])+3
  assert api.post(url(i)+'/apercu',json=body).status_code==409
  if methode=='lineaire':(R/'.codex-tests/immo927_chaine.json').write_text(json.dumps({'apercu':a,'sortie':r,'comptabilite_et_calendrier_inchanges_par_apercu':True,'trois_ecritures_nouvelles_sans_encaissement':True,'aucune_base_reelle':True},ensure_ascii=False,indent=2),encoding='utf8')

def test_927_lecture_seule_sql_meme_avec_dependance_et_aucun_exercice_cree(application):
 with closing(client(application)[0]) as api:
  i=preparer(api);u=ok(api.get('/api/auth/me'));a=ok(api.post(url(i)+'/apercu',json=demande()));avant=photo(application,u['societe_id'])
  with Session(application['runtime088']) as db:
   db.execute(text('SET TRANSACTION READ ONLY'));_proteger_mutation_registre(SimpleNamespace(method='POST'),u,db)
   b=apercu_sortie_immobilisation(i['id'],schemas.ImmobilisationSortieIn.model_validate(demande()),u,db);assert jsonable_encoder(b)==a and db.scalar(text('SHOW transaction_read_only'))=='on'
  assert photo(application,u['societe_id'])==avant
  c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
  # Calendrier supprimé seulement dans cette nouvelle société fictive isolée.
  with application['engine'].begin() as db:
   ex=db.scalar(text('SELECT id FROM exercices_comptables WHERE societe_id=:s AND annee=2026'),{'s':u['societe_id']});db.execute(text('DELETE FROM periodes_comptables WHERE exercice_id=:e'),{'e':ex});db.execute(text('DELETE FROM exercices_comptables WHERE id=:e'),{'e':ex})
  apres=photo(application,u['societe_id']);assert api.post(url(i)+'/apercu',json=demande()).status_code==409 and photo(application,u['societe_id'])==apres

def test_927_changement_demande_ou_dotation_rend_apercu_perime(application):
 with closing(client(application)[0]) as api:
  i=preparer(api);u=ok(api.get('/api/auth/me'));body=demande();a=ok(api.post(url(i)+'/apercu',json=body));avant=photo(application,u['societe_id'])
  r=api.post(url(i),json={**body,'prix_cession_ht':21000,'empreinte_apercu':a['empreinte_apercu']});assert r.status_code==409 and photo(application,u['societe_id'])==avant
  e=ok(api.post('/api/ecritures',json={'date':'2026-01-01','journal':'AM','reference':f'AM-2026-{i["id"]}','libelle':'Dotation FICTIVE927 antérieure à la sortie','lignes':[{'compte':'61935','debit':13.33},{'compte':'28355','credit':13.33}]}),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'));avant=photo(application,u['societe_id'])
  r=api.post(url(i),json={**body,'empreinte_apercu':a['empreinte_apercu']});assert r.status_code==409 and 'aperçu' in r.text and photo(application,u['societe_id'])==avant
  b=ok(api.post(url(i)+'/apercu',json=body));assert b['empreinte_apercu']!=a['empreinte_apercu'] and b['dotations'][-1]['etat']=='déjà comptabilisée';ok(api.post(url(i),json={**body,'empreinte_apercu':b['empreinte_apercu']}));assert len(photo(application,u['societe_id'])['ecritures'])==len(avant['ecritures'])+2

def test_927_incoherence_dotation_refusee_avant_toute_ecriture(application):
 with closing(client(application)[0]) as api:
  i=preparer(api);u=ok(api.get('/api/auth/me'));ok(api.post('/api/ecritures',json={'date':'2026-01-01','journal':'AM','reference':f'AM-2026-{i["id"]}','libelle':'Écart FICTIF927 à examiner','lignes':[{'compte':'61935','debit':4800},{'compte':'28355','credit':4800}]}),201);avant=photo(application,u['societe_id'])
  for suffixe in ['/apercu','']:
   r=api.post(url(i)+suffixe,json=demande());assert r.status_code==409 and '13.33' in r.text and photo(application,u['societe_id'])==avant

def test_927_roles_societes_dates_et_montants_non_finis(application):
 with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
  i=preparer(api);u=ok(api.get('/api/auth/me'));ub=ok(autre.get('/api/auth/me'));assert autre.post(url(i)+'/apercu',json=demande()).status_code==404
  ok(api.post(f'/api/societes/{u["societe_id"]}/inviter',params={'email':ub['email'],'role':'lecture'}));autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{u["societe_id"]}'))['access_token'];assert autre.post(url(i)+'/apercu',json=demande()).status_code==200 and autre.post(url(i),json=demande()).status_code==403
  avant=photo(application,u['societe_id'])
  for kw,statut in [({'date_sortie':'2024-12-31'},400),({'date_sortie':f'{date.today().year+1}-01-01'},400),({'prix_cession_ht':'NaN'},422),({'prix_cession_ht':'Infinity'},422),({'empreinte_apercu':'faux'},422)]:assert api.post(url(i)+'/apercu',json=demande(**kw)).status_code==statut
  assert photo(application,u['societe_id'])==avant

def test_927_bien_non_amortissable_et_rebut(application):
 with closing(client(application)[0]) as api:
  i=preparer(api,amortissable=False);a=ok(api.post(url(i)+'/apercu',json=demande(type_sortie='rebut')));assert a['dotations']==[] and D(str(a['cumul_amortissement']))==0 and D(str(a['vnc']))==24000 and D(str(a['resultat_cession']))==-24000 and D(str(a['tva_cession']))==0
  r=ok(api.post(url(i),json={**demande(type_sortie='rebut'),'empreinte_apercu':a['empreinte_apercu']}));assert D(str(r['resultat_cession']))==-24000
