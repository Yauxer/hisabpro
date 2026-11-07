"""Concurrence native paramètres TVA / statut d'un exercice fictif existant."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date
import time,uuid
import pytest
from sqlalchemy import text
from test_permissions_tva_runtime_isole import (
    application,application092,application091,application090,application089,application087,migration,
    donnees_metier,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok


def attendre_verrou(app,futur,*,table=None,nom=None):
    fin=time.monotonic()+8
    while time.monotonic()<fin:
        with app['engine'].connect() as db:
            if nom:
                attente=db.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE application_name=:n AND wait_event_type='Lock'"),{'n':nom})
            else:
                attente=db.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE usename='hisabpro' AND wait_event_type='Lock' AND query ILIKE :q"),{'q':f'%{table}%'})
        if attente:return
        if futur.done():
            r=futur.result()
            pytest.fail(f'Opération terminée avant le verrou attendu : {getattr(r,"status_code",r)}')
        time.sleep(.05)
    pytest.fail('Attente native de verrou non observée dans pg_stat_activity.')


def preparer(app,api):
    annee=date.today().year;sid=ok(api.get('/api/societe/moi'))['id']
    path=f'/api/tva/parametres/{annee}'
    ok(api.put(path,json={'credit_ouverture':20,'prorata_deduction_pct':80}))
    with app['engine'].connect() as db:
        assert db.scalar(text('SELECT count(*) FROM exercices_comptables WHERE societe_id=:s AND annee=:a'),{'s':sid,'a':annee})==1
    return sid,annee,path,donnees_metier(app)


def autres_donnees_inchangees(app,avant):
    apres=donnees_metier(app)
    for nom in ('exercices_comptables','tva_parametres_exercice'):
        avant.pop(nom,None);apres.pop(nom,None)
    assert apres==avant


@pytest.mark.parametrize('decision',['confirmer','annuler'])
def test_parametres_attendent_confirmation_ou_annulation_du_statut(application,decision):
    with closing(client(application)[0]) as api:
        sid,annee,path,avant=preparer(application,api)
        pool=ThreadPoolExecutor(max_workers=1)
        db=application['engine'].connect();transaction=db.begin()
        try:
            # Une décision de statut non encore confirmée, dans le seul cluster nonce.
            assert db.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:s AND annee=:a"),{'s':sid,'a':annee}).rowcount==1
            futur=pool.submit(api.put,path,json={'credit_ouverture':30,'prorata_deduction_pct':85})
            attendre_verrou(application,futur,table='exercices_comptables')
            if decision=='confirmer':transaction.commit()
            else:transaction.rollback()
            r=futur.result(timeout=20)
            assert r.status_code==(409 if decision=='confirmer' else 200),r.text
            p=ok(api.get(path))
            assert (p['credit_ouverture'],p['prorata_deduction_pct'])==((20,80) if decision=='confirmer' else (30,85))
            autres_donnees_inchangees(application,avant)
        finally:
            if transaction.is_active:transaction.rollback()
            db.close();pool.shutdown(wait=True)


def test_statut_attend_fin_de_sauvegarde_parametres_deja_en_cours(application):
    with closing(client(application)[0]) as api:
        sid,annee,path,avant=preparer(application,api)
        pool=ThreadPoolExecutor(max_workers=2)
        db=application['engine'].connect();transaction=db.begin()
        nom='cloture477-'+uuid.uuid4().hex[:10]
        try:
            # Bloquer uniquement le paramètre pour observer le verrou d'exercice
            # détenu par l'API après son contrôle, avant son UPDATE/commit.
            db.execute(text('SELECT id FROM tva_parametres_exercice WHERE societe_id=:s AND exercice=:a FOR UPDATE'),{'s':sid,'a':annee}).one()
            sauvegarde=pool.submit(api.put,path,json={'credit_ouverture':30,'prorata_deduction_pct':85})
            attendre_verrou(application,sauvegarde,table='tva_parametres_exercice')
            def confirmer():
                with application['engine'].begin() as fermeture:
                    fermeture.execute(text("SELECT set_config('application_name',:n,true)"),{'n':nom})
                    assert fermeture.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:s AND annee=:a"),{'s':sid,'a':annee}).rowcount==1
                return 'statut confirme'
            cloture=pool.submit(confirmer)
            attendre_verrou(application,cloture,nom=nom)
            transaction.rollback()
            assert sauvegarde.result(timeout=20).status_code==200
            assert cloture.result(timeout=20)=='statut confirme'
            assert api.put(path,json={'credit_ouverture':999,'prorata_deduction_pct':10}).status_code==409
            p=ok(api.get(path));assert (p['credit_ouverture'],p['prorata_deduction_pct'])==(30,85)
            autres_donnees_inchangees(application,avant)
        finally:
            if transaction.is_active:transaction.rollback()
            db.close();pool.shutdown(wait=True)
