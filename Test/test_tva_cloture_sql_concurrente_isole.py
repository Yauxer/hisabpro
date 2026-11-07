"""Courses TVA/statut SQL : uniquement PG nonce, vrais verrous observés."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
import uuid
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from test_avances_salaries_isole import (
    application as application095,application093,application092,application091,
    application090,application089,application087,migration,appliquer,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou,autres_donnees_inchangees
from test_permissions_tva_runtime_isole import donnees_metier
from recette_restauration_consolidee_084 import empreintes_tables
from test_restauration_runtime_acl_089 import catalogue_acl
from recette_installation_vierge import BACK

SQL='096_verrou_parametres_tva.sql'


@pytest.fixture(scope='module')
def application(application095):
    app=application095
    if (BACK/SQL).exists():
        avant=empreintes_tables(app['engine']);droits=catalogue_acl(app['engine'])
        appliquer(app,SQL);assert empreintes_tables(app['engine'])==avant
        assert catalogue_acl(app['engine'])==droits
        appliquer(app,SQL);assert empreintes_tables(app['engine'])==avant
        assert catalogue_acl(app['engine'])==droits
    yield app


def preparer(app,api,operation):
    sid=ok(api.get('/api/societe/moi'))['id'];annee=date.today().year
    if operation!='insert':
        ok(api.put(f'/api/tva/parametres/{annee}',json={'credit_ouverture':20,'prorata_deduction_pct':80}))
    return {'s':sid,'a':annee},donnees_metier(app)


REQUETES={
    'update':"UPDATE tva_parametres_exercice SET credit_ouverture=30,prorata_deduction_pct=85 WHERE societe_id=:s AND exercice=:a",
    'insert':"INSERT INTO tva_parametres_exercice(societe_id,exercice,credit_ouverture,prorata_deduction_pct) VALUES(:s,:a,30,85)",
    'delete':"DELETE FROM tva_parametres_exercice WHERE societe_id=:s AND exercice=:a",
}


def moteur(app,operation):
    return create_engine(app['cluster']['url'] if operation=='delete' else make_url(app['cluster']['url']).set(username='hisabpro'))


def executer(engine,operation,p,nom):
    try:
        with engine.begin() as db:
            db.execute(text("SELECT set_config('application_name',:n,true)"),{'n':nom})
            db.execute(text("SET LOCAL statement_timeout='12s'"))
            assert db.execute(text(REQUETES[operation]),p).rowcount==1
        return 'ok'
    except DBAPIError as exc:return exc.orig.pgcode


@pytest.mark.parametrize('operation',['update','insert','delete'])
@pytest.mark.parametrize('decision',['confirmer','annuler'])
def test_sql_attend_statut_et_relit_apres_commit_ou_rollback(application,operation,decision):
    with closing(client(application)[0]) as api:
        p,avant=preparer(application,api,operation)
        engine=moteur(application,operation);pool=ThreadPoolExecutor(1)
        db=application['engine'].connect();tx=db.begin();nom='sql485-'+uuid.uuid4().hex[:8]
        try:
            assert db.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:s AND annee=:a"),p).rowcount==1
            f=pool.submit(executer,engine,operation,p,nom)
            attendre_verrou(application,f,nom=nom)
            if decision=='confirmer':tx.commit()
            else:tx.rollback()
            assert f.result(timeout=20)==('23514' if decision=='confirmer' else 'ok')
            with application['engine'].connect() as lecture:
                r=lecture.execute(text('SELECT credit_ouverture,prorata_deduction_pct FROM tva_parametres_exercice WHERE societe_id=:s AND exercice=:a'),p).first()
            attendu=(None if operation=='insert' else (20,80)) if decision=='confirmer' else (None if operation=='delete' else (30,85))
            assert (tuple(r) if r else None)==attendu
            autres_donnees_inchangees(application,avant)
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True);engine.dispose()


@pytest.mark.parametrize('operation',['update','insert','delete'])
def test_statut_attend_fin_transaction_sql_parametres(application,operation):
    with closing(client(application)[0]) as api:
        p,avant=preparer(application,api,operation);engine=moteur(application,operation)
        db=engine.connect();tx=db.begin();pool=ThreadPoolExecutor(1);nom='fermeture485-'+uuid.uuid4().hex[:8]
        try:
            db.execute(text(REQUETES[operation]),p)
            def fermer():
                with application['engine'].begin() as c:
                    c.execute(text("SELECT set_config('application_name',:n,true)"),{'n':nom})
                    c.execute(text("SET LOCAL statement_timeout='12s'"))
                    assert c.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:s AND annee=:a"),p).rowcount==1
                return 'ok'
            f=pool.submit(fermer)
            attendre_verrou(application,f,nom=nom)
            tx.commit();assert f.result(timeout=20)=='ok'
            assert executer(engine,'insert' if operation=='delete' else 'update',p,nom+'-clos')=='23514'
            autres_donnees_inchangees(application,avant)
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True);engine.dispose()


def test_sql_et_api_sur_meme_parametre_sans_interblocage(application):
    with closing(client(application)[0]) as api:
        p,avant=preparer(application,api,'update');engine=moteur(application,'update')
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        nom='mixte485-'+uuid.uuid4().hex[:8]
        try:
            db.execute(text('SELECT id FROM tva_parametres_exercice WHERE societe_id=:s AND exercice=:a FOR UPDATE'),p).one()
            sql=pool.submit(executer,engine,'update',p,nom)
            attendre_verrou(application,sql,nom=nom)
            http=pool.submit(api.put,f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':40,'prorata_deduction_pct':90})
            attendre_verrou(application,http,table='tva_parametres_exercice')
            # L'API possède alors son verrou d'exercice et attend la même ligne.
            # Le contrôle SQL doit pouvoir prendre un verrou compatible.
            tx.rollback()
            resultat_sql=sql.result(timeout=20);r=http.result(timeout=20)
            assert (resultat_sql,r.status_code)==('ok',200),(resultat_sql,r.status_code,r.text)
            assert ok(api.get(f"/api/tva/parametres/{p['a']}"))['credit_ouverture']==40
            autres_donnees_inchangees(application,avant)
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True);engine.dispose()
