"""pg_dump/restore natifs avec ACL, année089 et reprise API sous LOGIN limité."""
from collections import Counter
from datetime import date
from pathlib import Path
import hashlib
import json
import sys

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from database import get_db
import lettrage
from routers import auth, societe, tiers, factures, commercial, ecritures, fec
from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_restauration_consolidee_084 import schema, verifier_schema, empreintes_tables, sha
from test_complements_structure_postgres import refuser
from test_e2e_runtime_annuel_isole import application, application087, migration, annee_banque
from test_permissions_acomptes_avoirs_postgres import dossier, valider, originaux, bilan

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ops.postgres_sauvegarde import sauvegarder, restaurer_isole


def catalogue_acl(engine):
    """ACL effectives par défaut + explicites,triées et identifiées sans OID local."""
    acteur="CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END"
    queries={
        'relations':f"SELECT c.relkind::text,c.relname,pg_get_userbyid(c.relowner),"
            f"pg_get_userbyid(a.grantor),{acteur},a.privilege_type,a.is_grantable "
            "FROM pg_class c CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl,"
            "acldefault(CASE WHEN c.relkind='S' THEN 'S'::\"char\" ELSE 'r'::\"char\" END,c.relowner))) a "
            "WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','p','S') ORDER BY 1,2,3,4,5,6,7",
        'colonnes':f"SELECT c.relname,col.attname,pg_get_userbyid(a.grantor),{acteur},"
            "a.privilege_type,a.is_grantable FROM pg_attribute col JOIN pg_class c ON c.oid=col.attrelid "
            "CROSS JOIN LATERAL aclexplode(col.attacl) a WHERE c.relnamespace='public'::regnamespace "
            "AND col.attnum>0 AND NOT col.attisdropped ORDER BY 1,2,3,4,5,6",
        'fonctions':f"SELECT p.proname,pg_get_function_identity_arguments(p.oid),pg_get_userbyid(p.proowner),"
            f"pg_get_userbyid(a.grantor),{acteur},a.privilege_type,a.is_grantable FROM pg_proc p "
            "CROSS JOIN LATERAL aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) a "
            "WHERE p.pronamespace='public'::regnamespace AND p.prokind IN ('f','p') ORDER BY 1,2,3,4,5,6,7",
        'schemas':f"SELECT n.nspname,pg_get_userbyid(n.nspowner),pg_get_userbyid(a.grantor),{acteur},"
            "a.privilege_type,a.is_grantable FROM pg_namespace n "
            "CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl,acldefault('n',n.nspowner))) a "
            "WHERE n.nspname='public' ORDER BY 1,2,3,4,5,6",
        'defauts':f"SELECT d.defaclobjtype::text,COALESCE(n.nspname,'GLOBAL'),"
            f"pg_get_userbyid(d.defaclrole),pg_get_userbyid(a.grantor),{acteur},a.privilege_type,a.is_grantable "
            "FROM pg_default_acl d LEFT JOIN pg_namespace n ON n.oid=d.defaclnamespace "
            "CROSS JOIN LATERAL aclexplode(d.defaclacl) a ORDER BY 1,2,3,4,5,6,7",
    }
    with engine.connect() as db:
        return {k:[list(r) for r in db.execute(text(q))] for k,q in queries.items()}


def lignes_tables(engine):
    with engine.connect() as db:
        tables=db.execute(text("SELECT relname FROM pg_class WHERE relnamespace='public'::regnamespace "
                               "AND relkind IN ('r','p') ORDER BY relname")).scalars().all()
        return {t:db.execute(text(f'SELECT row_to_json(t)::text FROM public."{t}" t ORDER BY 1')).scalars().all()
                for t in tables}


def vide(engine):
    with engine.connect() as db:
        return db.scalar(text("SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace "
                              "AND relkind IN ('r','p','v','m','S')"))==0


def api_restauree(runtime,garde):
    app=FastAPI()
    for router in (auth.router,societe.router,tiers.router,factures.router,
                   commercial.router_regl,ecritures.router,lettrage.router,fec.router):
        app.include_router(router)
    def connexion():
        garde()
        with Session(runtime) as db:
            assert db.scalar(text('SELECT current_user'))=='hisabpro'
            yield db
    app.dependency_overrides[get_db]=connexion
    return TestClient(app)


def test089_restore_acl_colonnes_fonctions_annee_et_nouveau_cycle_api(annee_banque):
    source_app=annee_banque
    source_cible=source_app['cluster'];source=source_app['engine']
    def garde_source():
        assert verifier_cible_isolee(source_cible['url'],source_cible['directory'],source_cible['nonce'])
    garde_source()
    with source.connect() as db:
        email=db.scalar(text('SELECT u.email FROM utilisateurs u JOIN clotures_exercice c '
                             'ON c.societe_id=u.societe_id ORDER BY u.id LIMIT 1'))
    assert email
    with httpx.Client(base_url=source_app['api_url']) as api_source:
        r=api_source.post('/api/auth/login',json={'email':email,'password':'RasLecture2026!'})
        assert r.status_code==200,r.text
        api_source.headers['Authorization']='Bearer '+r.json()['access_token']
        r=api_source.get('/api/fec/export',params={'exercice':2025})
        assert r.status_code==200,r.text
        fec_source=r.content
    avant_schema=schema(source);avant_donnees=empreintes_tables(source)
    avant_acl=catalogue_acl(source);avant_lignes=lignes_tables(source)
    assert avant_acl['colonnes'] and avant_acl['fonctions'] and len(avant_donnees)==73
    preuve={'source_schema':{k:{'nombre':len(v),'sha256':sha(v)} for k,v in avant_schema.items()
                             if k!='checks_reparses'},
            'acl':{k:{'nombre':len(v),'sha256':sha(v)} for k,v in avant_acl.items()},
            'tables':avant_donnees,'erreur':None,'cible_supprimee':False}
    try:
        with cluster_isole() as cible:
            def garde():
                garde_source()
                assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
            garde()
            assert cible['nonce']!=source_cible['nonce'] and cible['port']!=source_cible['port']
            archive=sauvegarder(source_cible['url'],source_cible['directory']/'annuelle089_acl.dump',
                                source_cible['bin'],inclure_droits=True)
            preuve['dump_taille']=archive.stat().st_size
            preuve['dump_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
            restored=create_engine(cible['url']);runtime=None
            try:
                assert vide(restored)
                acl_vide=catalogue_acl(restored)
                # Les rôles ne sont pas dans un pg_dump :l'erreur reste atomique.
                with pytest.raises(RuntimeError,match='pg_restore a échoué'):
                    restaurer_isole(cible['url'],archive,cible['bin'],cible['directory'],
                                   cible['nonce'],inclure_droits=True)
                assert vide(restored) and catalogue_acl(restored)==acl_vide
                preuve['role_absent_rollback_complet']=True
                garde()
                with restored.begin() as db:
                    assert not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro')"))
                    db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB '
                                    'NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
                garde()
                restaurer_isole(cible['url'],archive,cible['bin'],cible['directory'],
                               cible['nonce'],inclure_droits=True)
                verifier_schema(schema(restored),avant_schema)
                assert empreintes_tables(restored)==avant_donnees
                assert catalogue_acl(restored)==avant_acl
                preuve['schema_donnees_acl_sequences_identiques']=True
                runtime=create_engine(make_url(cible['url']).set(username='hisabpro'))
                with runtime.connect() as db:
                    role=db.execute(text('SELECT current_user,session_user,rolcanlogin,rolsuper,rolcreatedb,'
                        'rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user')).one()
                    assert tuple(role)==('hisabpro','hisabpro',True,False,False,False,False,False)
                    assert not db.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
                    assert not db.scalar(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)'))
                    assert db.scalar(text("SELECT has_column_privilege(current_user,'employes','nom','UPDATE')"))
                    assert not db.scalar(text("SELECT has_column_privilege(current_user,'employes','societe_id','UPDATE')"))
                    assert db.scalar(text("SELECT has_column_privilege(current_user,'grh_absences','statut','UPDATE')"))
                    assert not db.scalar(text("SELECT has_column_privilege(current_user,'grh_absences','employe_id','UPDATE')"))
                    preuve['role_runtime']=list(role)
                with api_restauree(runtime,garde) as api:
                    r=api.post('/api/auth/login',json={'email':email,'password':'RasLecture2026!'})
                    assert r.status_code==200,r.text
                    api.headers['Authorization']='Bearer '+r.json()['access_token']
                    r=api.get('/api/fec/export',params={'exercice':2025})
                    assert r.status_code==200 and r.content==fec_source,r.text
                    preuve['fec2025_octets_identiques']=True
                    # Nouvelle société fictive :prouve aussi la reprise des séquences.
                    api,user,tier,fs=dossier({'client':api},'vente')
                    r=api.post('/api/reglements',json={'facture_id':fs[0]['id'],'tiers':tier['nom'],
                        'tiers_id':tier['id'],'date':date.today().isoformat(),
                        'mode':'virement','montant':120,'comptabiliser':True})
                    assert r.status_code==201,r.text
                    paiement=r.json();valider(api)
                    with runtime.connect() as db:
                        lids=db.execute(text("SELECT l.id FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id "
                            "WHERE e.societe_id=:sid AND l.compte='3421' AND "
                            "((e.source='facture' AND e.reference=(SELECT numero FROM factures WHERE id=:fid)) "
                            "OR e.id=:pid) ORDER BY l.id"),
                            {'sid':user['societe_id'],'fid':fs[0]['id'],'pid':paiement['ecriture_id']}).scalars().all()
                    assert len(lids)==2
                    before=originaux({'owner':restored},user['societe_id'])
                    r=api.post('/api/lettrage/comptable/lettrer',json={'ligne_ids':lids,'code':'RES'})
                    assert r.status_code==200 and r.json()['nb']==2,r.text
                    assert originaux({'owner':restored},user['societe_id'])==before
                    bilan({'runtime':runtime},user['societe_id'],[120,120,120])
                    preuve['nouveau_cycle_runtime_debit_credit']=360
                for sql,code in (
                    ("UPDATE ecritures SET libelle=libelle||' INTERDIT-TEST' WHERE est_validee",'23514'),
                    ('UPDATE lignes_ecriture SET debit=debit+1','23514'),
                    ('DELETE FROM clotures_exercice','42501'),
                    ('UPDATE taux_cotisations SET id=id','42501'),
                    ('UPDATE employes SET societe_id=societe_id','42501'),
                    ('TRUNCATE rapprochement_ventilations','42501'),
                    ("SELECT setval('ras_reglement_captures_id_seq',1,false)",'42501'),
                    ('CREATE TABLE public.interdit_restore089(id integer)','42501')):
                    garde();refuser(runtime,sql,code)
                preuve['huit_refus_runtime_preserves']=True
                apres_lignes=lignes_tables(restored)
                assert all(not (Counter(rows)-Counter(apres_lignes[t])) for t,rows in avant_lignes.items())
                assert empreintes_tables(source)==avant_donnees and catalogue_acl(source)==avant_acl
                verifier_schema(schema(source),avant_schema)
                with pytest.raises(ValueError,match='doit être vide'):
                    restaurer_isole(cible['url'],archive,cible['bin'],cible['directory'],
                                   cible['nonce'],inclure_droits=True)
                preuve['cible_non_vide_refusee']=True
                preuve['source_et_originaux_restaures_preserves']=True
            finally:
                if runtime is not None:runtime.dispose()
                restored.dispose()
        preuve['cible_supprimee']=not cible['directory'].exists()
        assert preuve['cible_supprimee']
    except BaseException as exc:
        preuve['erreur']=repr(exc)
        raise
    finally:
        if 'cible' in locals():
            preuve['cible_supprimee']=not cible['directory'].exists()
        (ROOT/'.codex-tests/restauration446_preuve.json').write_text(
            json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf-8')
