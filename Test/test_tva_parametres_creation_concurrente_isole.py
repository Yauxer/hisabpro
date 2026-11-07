"""Deux initialisations TVA simultanées, sans remplacer les réponses HTTP."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import time
from sqlalchemy import text
from test_tva_cloture_sql_concurrente_isole import (
    application,application095,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_tva_verrou_exercice_isole import autres_donnees_inchangees


def test_deux_initialisations_http_concurrentes_reussissent_sans_doublon(application):
    with closing(client(application)[0]) as api:
        sid=ok(api.get('/api/societe/moi'))['id'];annee=date.today().year
        avant=donnees_metier(application);db=application['engine'].connect();tx=db.begin()
        pool=ThreadPoolExecutor(2)
        try:
            # Le verrou de table du laboratoire autorise les SELECT préalables,
            # mais retient les deux INSERT pour reproduire la fenêtre de course.
            db.execute(text('LOCK TABLE tva_parametres_exercice IN SHARE MODE'))
            futures=[pool.submit(api.put,f'/api/tva/parametres/{annee}',
                json={'credit_ouverture':v,'prorata_deduction_pct':80}) for v in (30,40)]
            limite=time.monotonic()+8
            while True:
                with application['engine'].connect() as c:
                    n=c.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE usename='hisabpro' AND wait_event_type='Lock' AND query ILIKE '%INSERT%tva_parametres_exercice%'"))
                if n==2:break
                assert time.monotonic()<limite, 'Deux INSERT concurrents non observés'
                time.sleep(.05)
            tx.rollback()
            resultats=[f.result(timeout=20) for f in futures]
            assert [r.status_code for r in resultats]==[200,200],[r.text for r in resultats]
            assert sorted(r.json()['credit_ouverture'] for r in resultats)==[30,40]
            with application['engine'].connect() as c:
                rows=c.execute(text('SELECT credit_ouverture,prorata_deduction_pct FROM tva_parametres_exercice WHERE societe_id=:s AND exercice=:a'),{'s':sid,'a':annee}).all()
            assert len(rows)==1 and rows[0][0] in (30,40) and rows[0][1]==80
            autres_donnees_inchangees(application,avant)
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
