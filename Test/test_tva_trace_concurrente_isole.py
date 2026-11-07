"""Trace seule et exercice absent : vraie concurrence PG nonce, sans écriture."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from test_permissions_tva_runtime_isole import (
    application as application093,application092,application091,application090,
    application089,application087,migration,
)
from test_avances_salaries_isole import appliquer
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_restauration_runtime_acl_089 import catalogue_acl
from recette_restauration_consolidee_084 import empreintes_tables
from recette_installation_vierge import BACK
from test_tva_verrou_exercice_isole import attendre_verrou

SQL='097_verrou_tva_trace_cloture.sql'
TRACE='INSERT INTO clotures_exercice(societe_id,exercice,resultat_net) VALUES(:s,:a,0)'
PARAM={
    'insert':'INSERT INTO tva_parametres_exercice(societe_id,exercice,credit_ouverture,prorata_deduction_pct) VALUES(:s,:a,30,80)',
    'update':'UPDATE tva_parametres_exercice SET credit_ouverture=30 WHERE societe_id=:s AND exercice=:a',
    'delete':'DELETE FROM tva_parametres_exercice WHERE societe_id=:s AND exercice=:a',
}


@pytest.fixture(scope='module')
def application(application093):
    app=application093
    for nom in ['094_protection_parametres_tva_clotures.sql','095_registre_avances_salaries.sql','096_verrou_parametres_tva.sql']:
        appliquer(app,nom)
    if (BACK/SQL).exists():
        avant=empreintes_tables(app['engine']);acl=catalogue_acl(app['engine'])
        appliquer(app,SQL)
        assert empreintes_tables(app['engine'])==avant
        nouveaux=catalogue_acl(app['engine'])
        assert all(all(v in nouveaux[k] for v in vs) for k,vs in acl.items())
        appliquer(app,SQL)
        assert empreintes_tables(app['engine'])==avant and catalogue_acl(app['engine'])==nouveaux
    yield app


def scope(api,present=False):return {'s':ok(api.get('/api/societe/moi'))['id'],'a':date.today().year-(0 if present else 1)}


def moteur(app,operation='insert'):
    return create_engine(app['cluster']['url'] if operation=='delete' else make_url(app['cluster']['url']).set(username='hisabpro'))


def resultat(engine,sql,p):
    try:
        with engine.begin() as db:db.execute(text(sql),p)
        return 'ok'
    except DBAPIError as exc:return exc.orig.pgcode


def aucun_exercice(app,p):
    with app['engine'].connect() as db:
        assert db.scalar(text('SELECT count(*) FROM exercices_comptables WHERE societe_id=:s AND annee=:a'),p)==0


@pytest.mark.parametrize('operation',['insert','update','delete','api'])
@pytest.mark.parametrize('decision',['confirmer','annuler'])
@pytest.mark.parametrize('present',[False,True])
def test_trace_en_cours_refuse_parametre_sans_ligne_et_reprise(application,operation,decision,present):
    with closing(client(application)[0]) as api:
        p=scope(api,present)
        if not present:aucun_exercice(application,p)
        if operation!='insert':ok(api.put(f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':20,'prorata_deduction_pct':80}))
        avant=empreintes_tables(application['engine'])
        trace_engine=moteur(application)
        db=trace_engine.connect();tx=db.begin();engine=moteur(application,operation)
        try:
            db.execute(text(TRACE),p)
            if operation=='api':
                r=api.put(f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':30,'prorata_deduction_pct':80})
                assert r.status_code==409,r.text
            else:assert resultat(engine,PARAM[operation],p)=='40001'
            if decision=='confirmer':tx.commit()
            else:tx.rollback()
            if operation=='api':
                r=api.put(f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':30,'prorata_deduction_pct':80})
                assert r.status_code==(409 if decision=='confirmer' else 200),r.text
            else:assert resultat(engine,PARAM[operation],p)==('23514' if decision=='confirmer' else 'ok')
            if not present:aucun_exercice(application,p)
            apres=empreintes_tables(application['engine'])
            assert {k:v for k,v in avant.items() if k not in {'audit_actions','clotures_exercice','tva_parametres_exercice'}}=={
                k:v for k,v in apres.items() if k not in {'audit_actions','clotures_exercice','tva_parametres_exercice'}}
        finally:
            if tx.is_active:tx.rollback()
            db.close();engine.dispose();trace_engine.dispose()


@pytest.mark.parametrize('operation',['insert','update','delete'])
@pytest.mark.parametrize('present',[False,True])
@pytest.mark.parametrize('decision',['confirmer','annuler'])
def test_parametre_en_cours_refuse_trace_puis_reprise(application,operation,present,decision):
    with closing(client(application)[0]) as api:
        p=scope(api,present)
        if operation!='insert':ok(api.put(f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':20,'prorata_deduction_pct':80}))
        engine=moteur(application,operation);db=engine.connect();tx=db.begin()
        try:
            db.execute(text(PARAM[operation]),p)
            assert resultat(application['engine'],TRACE,p)=='40001'
            if decision=='confirmer':tx.commit()
            else:tx.rollback()
            assert resultat(application['engine'],TRACE,p)=='ok'
            assert resultat(engine,PARAM['insert'],p)=='23514'
            if not present:aucun_exercice(application,p)
        finally:
            if tx.is_active:tx.rollback()
            db.close();engine.dispose()


def test_societe_et_annee_differentes_ne_sont_pas_bloquees(application):
    with closing(client(application)[0]) as a,closing(client(application)[0]) as b:
        p=scope(a);db=application['engine'].connect();tx=db.begin()
        try:
            db.execute(text(TRACE),p)
            for api,annee in [(b,p['a']),(a,p['a']-1)]:
                ok(api.put(f'/api/tva/parametres/{annee}',json={'credit_ouverture':12,'prorata_deduction_pct':80}))
            tx.rollback();aucun_exercice(application,p)
        finally:
            if tx.is_active:tx.rollback()
            db.close()


def test_creation_exercice_clos_refusee_pendant_parametre_absent(application):
    with closing(client(application)[0]) as api:
        p=scope(api);db=application['engine'].connect();tx=db.begin()
        sql="INSERT INTO exercices_comptables(societe_id,annee,date_debut,date_fin,statut) VALUES(:s,:a,:d,:f,'cloture')"
        valeurs={**p,'d':date(p['a'],1,1),'f':date(p['a'],12,31)}
        try:
            db.execute(text(PARAM['insert']),p)
            assert resultat(application['engine'],sql,valeurs)=='40001'
            tx.commit();aucun_exercice(application,p)
            assert resultat(application['engine'],sql,valeurs)=='ok'
        finally:
            if tx.is_active:tx.rollback()
            db.close()


@pytest.mark.parametrize('decision',['confirmer','annuler'])
def test_creation_exercice_en_cours_refuse_parametre_puis_reprise(application,decision):
    with closing(client(application)[0]) as api:
        p=scope(api);db=application['engine'].connect();tx=db.begin()
        try:
            db.execute(text("INSERT INTO exercices_comptables(societe_id,annee,date_debut,date_fin,statut) VALUES(:s,:a,:d,:f,'cloture')"),
                       {**p,'d':date(p['a'],1,1),'f':date(p['a'],12,31)})
            r=api.put(f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':30,'prorata_deduction_pct':80})
            assert r.status_code==409,r.text
            if decision=='confirmer':tx.commit()
            else:tx.rollback()
            r=api.put(f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':30,'prorata_deduction_pct':80})
            assert r.status_code==(409 if decision=='confirmer' else 200),r.text
            if decision=='annuler':aucun_exercice(application,p)
        finally:
            if tx.is_active:tx.rollback()
            db.close()


def test_fonctions097_invoker_et_droits_execution_explicites(application):
    with application['engine'].connect() as db:
        for nom in ['hisabpro_verrou_tva_cloture','hisabpro_verrou_trace_tva','hisabpro_verrou_statut_tva']:
            assert db.scalar(text("SELECT count(*) FROM information_schema.routine_privileges WHERE routine_schema='public' AND routine_name=:n AND grantee='hisabpro' AND privilege_type='EXECUTE'"),{'n':nom})==1
            assert db.scalar(text("SELECT prosecdef FROM pg_proc WHERE oid=(SELECT oid FROM pg_proc WHERE proname=:n)"),{'n':nom}) is False


def test_trace_confirmee_apres_controle_api_retourne409_et_aucune_ligne(application):
    with closing(client(application)[0]) as api:
        p=scope(api);db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE tva_parametres_exercice IN SHARE MODE'))
            f=pool.submit(api.put,f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':30,'prorata_deduction_pct':80})
            attendre_verrou(application,f,table='tva_parametres_exercice')
            # Le contrôle HTTP a lu l'absence de clôture, mais le trigger n'a
            # pas encore acquis le verrou de périmètre : vraie course résiduelle.
            assert resultat(application['engine'],TRACE,p)=='ok'
            tx.rollback();r=f.result(timeout=20)
            assert r.status_code==409 and 'SQL' not in r.text,r.text
            with application['engine'].connect() as c:
                assert c.scalar(text('SELECT count(*) FROM tva_parametres_exercice WHERE societe_id=:s AND exercice=:a'),p)==0
            aucun_exercice(application,p)
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)


def test_creation_exercice_api_concurrente_annulee_sans_periode_partielle(application):
    with closing(client(application)[0]) as api:
        p=scope(api);db=application['engine'].connect();tx=db.begin()
        body={'annee':p['a'],'date_debut':f"{p['a']}-01-01",'date_fin':f"{p['a']}-12-31"}
        try:
            db.execute(text(PARAM['insert']),p)
            r=api.post('/api/exercices',json=body)
            assert r.status_code==409,r.text
            aucun_exercice(application,p)
            tx.rollback();ok(api.post('/api/exercices',json=body),201)
            with application['engine'].connect() as c:
                assert c.scalar(text('SELECT count(*) FROM periodes_comptables p JOIN exercices_comptables e ON e.id=p.exercice_id WHERE e.societe_id=:s AND e.annee=:a'),p)==12
        finally:
            if tx.is_active:tx.rollback()
            db.close()
