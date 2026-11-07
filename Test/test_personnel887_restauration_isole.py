"""pg_dump/pg_restore réels :coffre,banque,ACL et clés gardées séparément."""
from contextlib import closing
from pathlib import Path
import json,tempfile,hashlib
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from fastapi import HTTPException
from test_personnel887_banque_isole import (
    application,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,preparer,banque,soumettre,approuver_banque,ok,depot,PDF,SECRET)
from postgres_isole import cluster_isole,verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables,schema,verifier_schema
from test_restauration_runtime_acl_089 import catalogue_acl
from ops.postgres_sauvegarde import sauvegarder,restaurer_isole
from services.personnel_coffre_service import telecharger,reveler_banque

R=Path(__file__).resolve().parents[1]

def test_887_restauration_native_coffre_banque_et_cle_separee(application,equipe):
    app=application;eq=equipe;s=app['cluster'];assert verifier_cible_isolee(s['url'],s['directory'],s['nonce'])
    eid=preparer(eq);piece=ok(depot(eq['a'],eid,categorie='banque'),201)['id']
    ident=ok(banque(eq,eid,piece_id=piece),201)['id'];soumettre(eq['a'],ident,1);approuver_banque(eq,eid,ident,1)
    avant=empreintes_tables(app['engine']);structure=schema(app['engine']);droits=catalogue_acl(app['engine'])
    keys=app['cles885']['path'];copie=keys.read_bytes();preuve={'donnees_reelles':False,'erreur':None}
    with tempfile.TemporaryDirectory(prefix='hisabpro_restaure_cles887_') as td:
        sauvegarde_cles=Path(td)/'cles_separees.json';sauvegarde_cles.write_bytes(copie);sauvegarde_cles.chmod(0o600)
        with cluster_isole() as cible:
            assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce']) and cible['nonce']!=s['nonce']
            archive=sauvegarder(s['url'],s['directory']/'coffre887.dump',s['bin'],inclure_droits=True)
            brut=archive.read_bytes();assert SECRET.encode() not in brut and PDF not in brut
            for valeur in json.loads(copie)['cles'].values():assert valeur.encode() not in brut
            restored=create_engine(cible['url']);runtime=None
            try:
                with restored.begin() as db:db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
                restaurer_isole(cible['url'],archive,cible['bin'],cible['directory'],cible['nonce'],inclure_droits=True)
                verifier_schema(schema(restored),structure)
                assert empreintes_tables(restored)==avant and catalogue_acl(restored)==droits
                runtime=create_engine(make_url(cible['url']).set(username='hisabpro'))
                with runtime.connect() as db:
                    assert db.scalar(text('SELECT current_user'))=='hisabpro'
                    assert not db.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
                user={'id':eq['uid'],'societe_id':eq['sid'],'role':'admin'}
                with Session(runtime) as db:
                    assert telecharger(db,user,eid,piece)==(PDF,'application/pdf')
                    assert reveler_banque(db,user,eid,ident)['rib_iban']==SECRET
                keys.write_text('{}',encoding='utf8')
                try:
                    with Session(runtime) as db:
                        with pytest.raises(HTTPException) as e:reveler_banque(db,user,eid,ident)
                        assert e.value.status_code==503 and SECRET not in str(e.value.detail)
                finally:keys.write_bytes(sauvegarde_cles.read_bytes())
                with Session(runtime) as db:assert reveler_banque(db,user,eid,ident)['rib_iban']==SECRET
                apres=empreintes_tables(restored)
                assert all(apres[t]==avant[t] for t in ('ecritures','lignes_ecriture','personnel_banque_versions','personnel_coffre_pieces'))
                assert empreintes_tables(app['engine'])==avant
                preuve.update(schema_acl_donnees_sequences_identiques=True,role_runtime_limite=True,cles_absentes_archive=True,
                  pieces_banque_restituees=True,cle_absente_refusee=True,recuperation_cle_reussie=True,tables=len(avant),dump_sha256=hashlib.sha256(brut).hexdigest())
            finally:
                keys.write_bytes(copie)
                if runtime is not None:runtime.dispose()
                restored.dispose()
        assert not cible['directory'].exists();preuve['cible_temporaire_supprimee']=True
    (R/'.codex-tests/personnel887_restauration_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
