"""Restauration conjointe091 : PG natif+ACL+pièces, deux main:app non propriétaires.

La source est mise au repos en arrêtant son seul processus API créé par le banc.
Aucun dump, processus, fichier ou PostgreSQL utilisateur n'est utilisé.
"""
from contextlib import closing
from datetime import date
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from e2e_isole_support import application_isolee, arreter_processus_cree, attendre_http, port_loopback_libre
from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_installation_vierge import BACK, candidats, tables_vides
from recette_installation_vierge_consolidee import COMPLEMENTS
from recette_installation_vierge_084 import catalogue
from recette_restauration_consolidee_084 import schema, verifier_schema, empreintes_tables, sha
from test_e2e_runtime_consolide_isole import EXTENSIONS
from test_e2e_runtime_annuel_isole import scenario_annee_banque
from test_e2e_runtime_session_isole import _affecter_perte_fictive
from test_justificatifs_modeles_runtime_isole import ecriture, pdf_fictif, original
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_sauvegarde_pieces_documents_isole import manifeste
from test_restauration_runtime_acl_089 import catalogue_acl, lignes_tables
from test_complements_structure_postgres import refuser

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ops.postgres_sauvegarde import sauvegarder, restaurer_isole


def preparer091(engine,c):
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    with engine.begin() as db:
        db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
    ajouts=('088_permissions_cycle_annuel.sql','089_lettrage_identite_auxiliaire.sql',
            '090_permissions_multi_societes.sql','091_permissions_affectation_resultat.sql')
    migrations=[*candidats(),*(BACK/n for n in (*COMPLEMENTS,*EXTENSIONS,*ajouts))]
    assert len(migrations)==82 and len({p.name for p in migrations})==82
    for p in migrations:
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        tables_vides(engine,c)
        raw=engine.raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute(p.read_text(encoding='utf-8'))
        finally:raw.close()
        tables_vides(engine,c)


def lancer_cible(c,uploads):
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    assert uploads.resolve().is_relative_to(c['directory'].resolve())
    port=port_loopback_libre();url=f'http://127.0.0.1:{port}'
    log=c['directory']/'api452.log'
    env=os.environ.copy()
    env.update(DATABASE_URL=make_url(c['url']).set(username='hisabpro').render_as_string(hide_password=False),
        APP_ENV='test',HISABPRO_CREATE_TABLES='false',PYTHON_DOTENV_DISABLED='1',PYTHONUTF8='1',
        SECRET_KEY='secret-fictif-restore452-'+c['nonce'],ALGORITHM='HS256',
        HISABPRO_UPLOAD_DIR=str(uploads),CORS_ORIGINS='http://127.0.0.1:1')
    with log.open('w',encoding='utf-8') as out:
        proc=subprocess.Popen([sys.executable,'-X','utf8','-m','uvicorn','main:app',
            '--host','127.0.0.1','--port',str(port),'--log-level','warning'],cwd=BACK,env=env,
            stdout=out,stderr=subprocess.STDOUT,
            **({'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {'start_new_session':True}))
    try:attendre_http(url+'/api/health',proc,log)
    except BaseException:
        arreter_processus_cree(proc);raise
    return proc,url,log


def connecter(api,email,password='RasLecture2026!'):
    token=ok(api.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
    api.headers['Authorization']='Bearer '+token


def test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path, fichiers_supplementaires=None):
    preuve={'erreur':None,'cibles_supprimees':False}
    try:
        with application_isolee(preparer_runtime=preparer091) as source,cluster_isole() as cible:
            def garde():
                assert verifier_cible_isolee(source['cluster']['url'],source['cluster']['directory'],source['cluster']['nonce'])
                assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
                assert cible['nonce']!=source['cluster']['nonce'] and cible['port']!=source['cluster']['port']
            garde();assert source['role_sql']=='hisabpro'
            # Scénarios existants réutilisés avec leurs vrais oracles, sans
            # changer les calculs ni fabriquer une décision sur une base réelle.
            dossier_annuel=tmp_path/'annee452';dossier_annuel.mkdir()
            scenario_annee_banque(source,catalogue(source['engine']),dossier_annuel)
            _affecter_perte_fictive(source)
            api,email,password=client(source)
            with closing(api):
                sid=ok(api.get('/api/auth/me'))['societe_id']
                eid=ecriture(api,reference='ORIGINE-FICTIVE452')
                brouillon=ecriture(api,validee=False,reference='BROUILLON-FICTIF452')
                ok(api.post(f'/api/ecritures/{eid}/justificatifs',json={'reference':'REFERENCE-FICTIVE452'}),201)
                fichiers=[]
                for docid,contenu in ((eid,pdf_fictif()),(eid,pdf_fictif()+b'\n% variante fictive452'),(brouillon,pdf_fictif())):
                    f=ok(api.post(f'/api/attachments/ecriture/{docid}',files={'file':('preuve452.pdf',contenu,'application/pdf')}))
                    fichiers.append((docid,f['nom'],contenu))
                lecteur=email.replace('@','-lecture@')
                ok(api.post('/api/utilisateurs',json={'nom':'Lecteur fictif452','email':lecteur,'mot_de_passe':password,'role':'lecture'}),201)
                autre,autre_email,_=client(source);autre.close()
                fec_source=api.get('/api/fec/export',params={'exercice':date.today().year})
                assert fec_source.status_code==409,fec_source.text
                assert 'ECRITURES_BROUILLON' in fec_source.text
                doc_source=ok(api.get(f'/api/ecritures/{eid}/justificatifs'))
            with source['engine'].connect() as db:
                decision=db.execute(text('SELECT d.ecriture_id,u.email,d.societe_id FROM decisions_affectation_resultat d '
                                         'JOIN utilisateurs u ON u.id=d.created_by')).one()
            with httpx.Client(base_url=source['api_url']) as annuel:
                connecter(annuel,decision.email)
                f=ok(annuel.post(f'/api/attachments/ecriture/{decision.ecriture_id}',
                    files={'file':('PV-FICTIF452.pdf',pdf_fictif(),'application/pdf')}))
                fichier_pv=f['nom']
                etat_source=ok(annuel.get('/api/cloture/etat',params={'exercice':2025}))
                fec_annuel=annuel.get('/api/fec/export',params={'exercice':2025})
                assert fec_annuel.status_code==200,fec_annuel.text
            uploads=Path(source['uploads_dir']).resolve()
            assert uploads.is_relative_to(source['directory'].resolve())
            assert not uploads.is_relative_to((BACK/'uploads').resolve())
            # Plus d'auteur de mutation : seul le serveur créé ici est arrêté.
            arreter_processus_cree(source['processus'][0])
            assert source['processus'][0].poll() is not None
            avant_schema=schema(source['engine']);avant=empreintes_tables(source['engine'])
            avant_acl=catalogue_acl(source['engine']);avant_lignes=lignes_tables(source['engine'])
            avant_fichiers=manifeste(uploads)
            supplements=fichiers_supplementaires or {}
            assert len(avant_fichiers)==4+len(supplements)
            assert all(avant_fichiers.get(p)==empreinte for p,empreinte in supplements.items())
            originaux=original(source,eid)
            backup=source['directory']/'backup452';backup.mkdir()
            shutil.copytree(uploads,backup/'pieces')
            assert manifeste(backup/'pieces')==avant_fichiers
            dump=sauvegarder(source['cluster']['url'],backup/'database.dump',source['cluster']['bin'],inclure_droits=True)
            with pytest.raises(FileExistsError):
                sauvegarder(source['cluster']['url'],dump,source['cluster']['bin'],inclure_droits=True)
            assert empreintes_tables(source['engine'])==avant
            restored=create_engine(cible['url']);runtime=None;proc=None
            try:
                garde()
                with restored.begin() as db:
                    db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
                restaurer_isole(cible['url'],dump,cible['bin'],cible['directory'],cible['nonce'],inclure_droits=True)
                verifier_schema(schema(restored),avant_schema)
                assert empreintes_tables(restored)==avant and catalogue_acl(restored)==avant_acl
                fichiers_cible=cible['directory']/'pieces452'
                shutil.copytree(backup/'pieces',fichiers_cible)
                assert manifeste(fichiers_cible)==avant_fichiers
                with pytest.raises(FileExistsError):shutil.copytree(backup/'pieces',fichiers_cible)
                runtime=create_engine(make_url(cible['url']).set(username='hisabpro'))
                with runtime.connect() as db:
                    role=db.execute(text('SELECT current_user,session_user,rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls '
                                         'FROM pg_roles WHERE rolname=current_user')).one()
                    assert tuple(role)==('hisabpro','hisabpro',True,False,False,False,False,False)
                    assert not db.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
                    assert not db.scalar(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)'))
                proc,url,log=lancer_cible(cible,fichiers_cible)
                with httpx.Client(base_url=url) as api:
                    connecter(api,email,password)
                    assert ok(api.get('/api/societe/moi'))['id']==sid
                    assert ok(api.get(f'/api/ecritures/{eid}/justificatifs'))==doc_source
                    refus_fec=api.get('/api/fec/export',params={'exercice':date.today().year})
                    assert refus_fec.status_code==409 and refus_fec.json()==fec_source.json()
                    assert ok(api.get('/api/modeles'))
                    for docid,nom,contenu in fichiers:
                        r=api.get(f'/api/attachments/ecriture/{docid}/download/{nom}')
                        assert r.status_code==200 and r.content==contenu
                    assert api.delete(f'/api/attachments/ecriture/{eid}/{fichiers[0][1]}').status_code==409
                    connecter(api,lecteur,password)
                    assert api.get(f'/api/attachments/ecriture/{eid}/download/{fichiers[0][1]}').content==fichiers[0][2]
                    assert api.post(f'/api/attachments/ecriture/{eid}',files={'file':('interdit.pdf',pdf_fictif(),'application/pdf')}).status_code==403
                    assert api.post(f'/api/ecritures/{eid}/justificatifs',json={'reference':'INTERDIT'}).status_code==403
                    connecter(api,autre_email,password)
                    assert api.get(f'/api/ecritures/{eid}/justificatifs').status_code==404
                    assert api.get(f'/api/attachments/ecriture/{eid}/download/{fichiers[0][1]}').status_code==404
                    connecter(api,decision.email)
                    assert ok(api.get('/api/cloture/etat',params={'exercice':2025}))==etat_source
                    fec_restaure=api.get('/api/fec/export',params={'exercice':2025})
                    assert fec_restaure.status_code==200 and fec_restaure.content==fec_annuel.content
                    r=api.get(f'/api/attachments/ecriture/{decision.ecriture_id}/download/{fichier_pv}')
                    assert r.status_code==200 and r.content==pdf_fictif()
                    connecter(api,email,password)
                    ok(api.post(f'/api/ecritures/{eid}/justificatifs',json={'reference':'APRES-RESTORE-FICTIF452'}),201)
                    nouveau=ok(api.post(f'/api/attachments/ecriture/{eid}',files={'file':('nouvelle452.pdf',pdf_fictif(),'application/pdf')}))
                    assert api.get(nouveau['url']).content==pdf_fictif()
                    assert ok(api.get(f'/api/ecritures/{eid}/justificatifs'))['reference_fec']=='APRES-RESTORE-FICTIF452'
                    assert api.delete(f'/api/attachments/ecriture/{brouillon}/{fichiers[2][1]}').status_code==204
                    assert api.get(f'/api/attachments/ecriture/{brouillon}/download/{fichiers[2][1]}').status_code==404
                assert original({'engine':restored},eid)==originaux
                for table in ('ecritures','lignes_ecriture','clotures_exercice','decisions_affectation_resultat'):
                    assert lignes_tables(restored)[table]==avant_lignes[table]
                assert empreintes_tables(source['engine'])==avant
                assert manifeste(uploads)==avant_fichiers and catalogue_acl(source['engine'])==avant_acl
                refuser(runtime,'DELETE FROM decisions_affectation_resultat','42501')
                refuser(runtime,"DELETE FROM ecriture_justificatifs WHERE ecriture_id="+str(eid),'P0001')
                with pytest.raises(ValueError,match='doit être vide'):
                    restaurer_isole(cible['url'],dump,cible['bin'],cible['directory'],cible['nonce'],inclure_droits=True)
                with restored.connect() as db:
                    assert db.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND usename='hisabpro'"))>0
                    assert db.scalar(text('SELECT count(*) FROM decisions_affectation_resultat'))==1
                preuve.update(tables=len(avant),fichiers=avant_fichiers,
                    acl={k:{'nombre':len(v),'sha256':sha(v)} for k,v in avant_acl.items()},
                    schema_donnees_acl_sequences_identiques=True,fec2025_octets_identiques=True,
                    refus_fec_brouillon_identique=True,
                    decision091_et_pv_restitues=True,reprise_ecriture_append_only=True,
                    role_runtime=list(role),source_preservee=True,
                    dump_sha256=hashlib.sha256(dump.read_bytes()).hexdigest())
            finally:
                if proc is not None:arreter_processus_cree(proc)
                if runtime is not None:runtime.dispose()
                restored.dispose()
            assert proc.poll() is not None
        assert not cible['directory'].exists() and not source['cluster']['directory'].exists()
        assert not source['directory'].exists() and not source['web_thread'].is_alive()
        preuve['cibles_supprimees']=True
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        if 'source' in locals() and 'cible' in locals():
            preuve['cibles_supprimees']=not source['directory'].exists() and not source['cluster']['directory'].exists() and not cible['directory'].exists()
        (ROOT/'.codex-tests/restauration452_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf-8')
