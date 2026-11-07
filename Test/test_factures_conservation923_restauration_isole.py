"""Une copie conservée reste identique après pg_dump/pg_restore natifs."""
from pathlib import Path
from contextlib import closing
import hashlib,json
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from test_factures_conservation923_isole import (
 application,application104,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,creer_facture,path,demande)
from services.factures_conservation_service import consulter,telecharger
from postgres_isole import cluster_isole,verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables,schema,verifier_schema
from test_restauration_runtime_acl_089 import catalogue_acl
from ops.postgres_sauvegarde import sauvegarder,restaurer_isole

R=Path(__file__).resolve().parents[1]

def test_923_restauration_native_copie_et_droits(application):
 app=application;s=app['cluster'];assert verifier_cible_isolee(s['url'],s['directory'],s['nonce'])
 with closing(client(app)[0]) as api:
  f=creer_facture(api);a=ok(api.post(path(f),json=demande()),201);user=ok(api.get('/api/auth/me'));raw=api.get(path(f)+'/pdf').content
 avant=empreintes_tables(app['engine']);structure=schema(app['engine']);droits=catalogue_acl(app['engine']);archive=sauvegarder(s['url'],s['directory']/'copie923.dump',s['bin'],inclure_droits=True)
 with cluster_isole() as cible:
  assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce']) and cible['nonce']!=s['nonce'];owner=create_engine(cible['url']);runtime=None
  try:
   with owner.begin() as db:db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
   restaurer_isole(cible['url'],archive,cible['bin'],cible['directory'],cible['nonce'],inclure_droits=True)
   verifier_schema(schema(owner),structure);assert empreintes_tables(owner)==avant and catalogue_acl(owner)==droits
   runtime=create_engine(make_url(cible['url']).set(username='hisabpro'))
   with Session(runtime) as db:
    assert db.scalar(text('SELECT current_user'))=='hisabpro';r=consulter(db,user,f['id'])['copie'];assert jsonable_encoder(r)==a;assert telecharger(db,user,f['id']).body==raw
   assert empreintes_tables(owner)==avant and empreintes_tables(app['engine'])==avant
  finally:
   if runtime is not None:runtime.dispose()
   owner.dispose()
 assert not cible['directory'].exists()
 (R/'.codex-tests/conservation923_restauration.json').write_text(json.dumps({'tables':len(avant),'schema_donnees_sequences_acl_identiques':True,'pdf_octets_identiques':True,'metadata_identiques':True,'role_limite':True,'source_inchangee':True,'cible_nonce_supprimee':True,'aucune_base_reelle':True,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2),encoding='utf8')
