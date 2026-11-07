"""Fin des JWT non révocables, uniquement clés synthétiques et PostgreSQL nonce."""
from pathlib import Path
from contextlib import closing
import json
import pytest
from jose import jwt
from passlib.hash import bcrypt
from sqlalchemy import text
from test_factures_conservation923_isole import (
 application,application104,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,creer_facture,path,demande,comptabilite)
from postgres_isole import verifier_cible_isolee

R=Path(__file__).resolve().parents[1]

def jeton_synthetique(app,api,*,supprimer_version=True,**claims):
 c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']) and app['api_url'].startswith('http://127.0.0.1:')
 # Clé de la fixture e2e_isole_support, jamais une variable ou clé utilisateur.
 cle='secret-prive-synthetique-e2e-'+c['nonce'];courant=api.headers['Authorization'].split(' ',1)[1]
 contenu=jwt.decode(courant,cle,algorithms=['HS256']);assert 'pwd_version' in contenu
 if supprimer_version:contenu.pop('pwd_version')
 contenu.update(claims)
 return jwt.encode(contenu,cle,algorithm='HS256')

def test_925_ancien_jwt_refuse_en_lecture_ecriture_et_telechargement(application):
 with closing(client(application)[0]) as api:
  u=ok(api.get('/api/auth/me'));f=creer_facture(api);ok(api.post(path(f),json=demande()),201);avant=comptabilite(application,u['societe_id']);h={'Authorization':'Bearer '+jeton_synthetique(application,api)}
  for url in ['/api/auth/me','/api/factures?exercice=2026','/api/ecritures?exercice=2026',path(f),path(f)+'/pdf']:
   r=api.get(url,headers=h);assert r.status_code==401 and r.json()['detail']=='Session ancienne : reconnectez-vous'
  r=api.post('/api/ecritures',headers=h,json={'date':'2026-01-20','journal':'BQ','libelle':'Refus ancien JWT FICTIF925','lignes':[{'compte':'5141','debit':1},{'compte':'1111','credit':1}]});assert r.status_code==401
  assert api.get('/api/auth/me').status_code==200 and api.get(path(f)+'/pdf').status_code==200 and comptabilite(application,u['societe_id'])==avant
  (R/'.codex-tests/jwt925_chaine.json').write_text(json.dumps({'ancien_jwt_signe':401,'lectures_ecriture_pdf_refuses':True,'jeton_versionne_actif':200,'comptabilite_inchangee':True,'cle_synthetique_seulement':True,'aucune_base_reelle':True},indent=2),encoding='utf8')

def test_925_reconnexion_et_changement_mot_de_passe_toutes_societes(application):
 api,email,secret=client(application)
 with closing(api):
  me=ok(api.get('/api/auth/me'));principal=dict(api.headers);ancien=jeton_synthetique(application,api);autre=ok(api.post('/api/societes/nouvelle',json={'raison_sociale':'Deuxième société FICTIVE925'}),201)
  token=ok(api.post(f'/api/societes/switcher/{autre["id"]}'))['access_token'];assert 'pwd_version' in jwt.get_unverified_claims(token);secondaire={'Authorization':'Bearer '+token};avant=comptabilite(application,me['societe_id'])
  nouveau='NouveauSecretFictif925!';assert api.post('/api/auth/mot-de-passe',json={'mot_de_passe_actuel':secret,'nouveau_mot_de_passe':nouveau}).status_code==204
  for h in [principal,secondaire,{'Authorization':'Bearer '+ancien}]:assert api.get('/api/auth/me',headers=h).status_code==401
  assert api.post('/api/auth/login',json={'email':email,'password':secret}).status_code==401
  n=ok(api.post('/api/auth/login',json={'email':email,'password':nouveau}));assert 'pwd_version' in jwt.get_unverified_claims(n['access_token']);api.headers['Authorization']='Bearer '+n['access_token'];assert ok(api.get('/api/auth/me'))['id']==me['id'];assert len(ok(api.get('/api/societes/mes-societes')))==2
  assert comptabilite(application,me['societe_id'])==avant

def test_925_connexion_hash_bcrypt_historique_sans_recriture(application):
 api,email,secret=client(application)
 with closing(api):
  me=ok(api.get('/api/auth/me'));c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);historique=bcrypt.hash(secret)
  # Précondition exclusivement sur ce nouveau compte fictif ;jamais un compte réel.
  with application['engine'].begin() as db:db.execute(text('UPDATE utilisateurs SET hashed_password=:h WHERE id=:u AND societe_id=:s'),{'h':historique,'u':me['id'],'s':me['societe_id']})
  n=ok(api.post('/api/auth/login',json={'email':email,'password':secret}));payload=jwt.get_unverified_claims(n['access_token']);assert 'pwd_version' in payload and historique not in json.dumps(payload)
  api.headers['Authorization']='Bearer '+n['access_token'];assert ok(api.get('/api/auth/me'))['id']==me['id']
  with application['engine'].connect() as db:assert db.scalar(text('SELECT hashed_password FROM utilisateurs WHERE id=:u'),{'u':me['id']})==historique

@pytest.mark.parametrize('version',[None,123,'','a'*64])
def test_925_version_absente_ou_fausse_ne_peut_pas_etre_substituee(application,version):
 with closing(client(application)[0]) as api:
  token=jeton_synthetique(application,api,supprimer_version=False,pwd_version=version)
  assert api.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code==401
  assert api.get('/api/auth/me').status_code==200
