"""Deux mouvements ordinaires coexistent ; photographies/clôture exclusives."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import time
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_inventaire_cloture_concurrente_isole import dossier
from test_mouvements_stock_cloture_isole import mouvement
from test_stock_comptabilisation_concurrente_isole import generer
from test_e2e_inventaire_nombres_isole import photo
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou


def test_deux_mouvements_coexistent_et_refusent_photographie_generation_cloture(application):
    with closing(client(application)[0]) as api:
        api.timeout=30;p=dossier(api)
        aid=ok(api.post('/api/articles',json={'code':'AUTRE-FICTIF524',
            'designation':'Autre stock fictif524','stock_actuel':0,'is_stockable':True,
            'cmup':20,'prix_achat_ht':20}),201)['id']
        q={**p,'article':aid}
        payload={'date':f"{p['a']}-12-31",'reference':'PHYSIQUE-FICTIF524',
            'lignes':[{'article_id':p['article'],'quantite_reelle':5},
                      {'article_id':q['article'],'quantite_reelle':7}]}
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE mouvements_stock IN SHARE MODE'))
            f=pool.submit(mouvement,api,p,5);attendre_verrou(application,f,table='mouvements_stock')
            g=pool.submit(mouvement,api,q,7)
            fin=time.monotonic()+8
            while True:
                with application['engine'].connect() as c:
                    nb=c.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE usename='hisabpro' AND wait_event_type='Lock' AND query ILIKE '%INSERT INTO mouvements_stock%'"))
                if nb==2:break
                assert not g.done(),f"Deuxième mouvement refusé : {g.result().status_code} {g.result().text}" if g.done() else ''
                assert time.monotonic()<fin,'Deux mouvements simultanés non observés dans PostgreSQL.'
                time.sleep(.05)
            avant=photo(application,p['s'])
            assert api.post('/api/inventaire/valider',json=payload).status_code==409
            assert generer(api,p).status_code==409
            assert api.post('/api/cloture/cloturer',params={'exercice':p['a']}).status_code==409
            assert photo(application,p['s'])==avant
            tx.rollback();r1=f.result(timeout=30);r2=g.result(timeout=30)
            assert r1.status_code==r2.status_code==200,(r1.text,r2.text)
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        with application['engine'].connect() as c:
            assert c.execute(text('SELECT article_id,stock_avant,stock_apres FROM mouvements_stock WHERE societe_id=:s ORDER BY article_id'),{'s':p['s']}).all()==[(p['article'],0,5),(q['article'],0,7)]
        assert ok(api.post('/api/inventaire/valider',json=payload))['total_valeur']==240
        eid=ok(generer(api,p))['ecriture_id'];ok(api.post(f'/api/ecritures/{eid}/valider'))
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-2760
        assert api.get('/api/fec/export',params={'exercice':p['a']}).status_code==200
