"""Mouvements directs et photographies stables : API et concurrence PG nonce."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor,TimeoutError
import pytest
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_inventaire_cloture_concurrente_isole import dossier,compter
from test_stock_comptabilisation_concurrente_isole import generer
from test_e2e_inventaire_nombres_isole import photo
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou
from recette_restauration_consolidee_084 import empreintes_tables


def mouvement(api,p,quantite=5,jour=None):
    return api.patch(f"/api/articles/{p['article']}/stock",json={
        'stock_actuel':quantite,'date':jour or f"{p['a']}-12-31",
        'reference':'CORRECTION-FICTIVE518','note':'Laboratoire isolé518'})


def terminer(api,p,quantite=5):
    assert ok(compter(api,p,quantite,'FINAL518'))['total_valeur']==quantite*20
    eid=ok(generer(api,p))['ecriture_id'];assert eid
    ok(api.post(f'/api/ecritures/{eid}/valider'))
    assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==quantite*20-3000
    assert api.get('/api/fec/export',params={'exercice':p['a']}).status_code==200


def test_cloture_en_cours_refuse_correction_stock_et_preserve_sources(application):
    with closing(client(application)[0]) as api:
        api.timeout=25;p=dossier(api)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE fiscal_parametres_exercice IN ACCESS EXCLUSIVE MODE'))
            f=pool.submit(api.post,'/api/cloture/cloturer',params={'exercice':p['a']})
            attendre_verrou(application,f,table='fiscal_parametres_exercice')
            avant=photo(application,p['s']);r=mouvement(api,p)
            apres=photo(application,p['s'])
            tx.rollback();r1=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert apres==avant
            assert r1.status_code==200 and r1.json()['resultat_net']==-3000,r1.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        avant=empreintes_tables(application['engine'])
        assert mouvement(api,p).status_code==409
        assert {k:v for k,v in empreintes_tables(application['engine']).items() if k!='audit_actions'}=={k:v for k,v in avant.items() if k!='audit_actions'}


@pytest.mark.parametrize('seconde',['cloture','comptage','comptabilisation'])
def test_mouvement_en_cours_refuse_autre_operation_puis_reprise(application,seconde):
    with closing(client(application)[0]) as api:
        api.timeout=25;p=dossier(api)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE mouvements_stock IN SHARE MODE'))
            f=pool.submit(mouvement,api,p);attendre_verrou(application,f,table='mouvements_stock')
            def executer():
                if seconde=='cloture':return api.post('/api/cloture/cloturer',params={'exercice':p['a']})
                return compter(api,p,10,'CONCURRENT518') if seconde=='comptage' else generer(api,p)
            g=pool.submit(executer)
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=25)
            if r2 is None:r2=g.result(timeout=25)
            assert r1.status_code==200,r1.text
            assert r2.status_code==409,r2.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        terminer(api,p)


def test_generation_en_cours_refuse_mouvement(application):
    with closing(client(application)[0]) as api:
        api.timeout=25;p=dossier(api);ok(compter(api,p,5,'PHYSIQUE518'))
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE lignes_ecriture IN SHARE MODE'))
            f=pool.submit(generer,api,p);attendre_verrou(application,f,table='lignes_ecriture')
            r=mouvement(api,p,10)
            tx.rollback();r1=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert r1.status_code==200,r1.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        ok(api.post(f"/api/ecritures/{r1.json()['ecriture_id']}/valider"))
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-2900


def test_mouvement_utilise_exercice_decale_et_isole_societe(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        q=dossier(autre);s=ok(api.get('/api/societe/moi'))['id'];a=q['a']
        ok(api.post('/api/exercices',json={'annee':a,'date_debut':f'{a-1}-07-01','date_fin':f'{a}-06-30'}),201)
        aid=ok(api.post('/api/articles',json={'code':'DECALE518','designation':'Article fictif décalé518','stock_actuel':0,'cmup':20,'prix_achat_ht':20}),201)['id']
        p={'s':s,'a':a,'article':aid};jour=f'{a-1}-12-31'
        with application['engine'].connect() as db:
            tx=db.begin()
            try:
                db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:cle,0))'),{'cle':f'hisabpro:inventaire-stock:{s}:{a}'})
                assert mouvement(api,p,1,jour).status_code==409
                assert mouvement(autre,q,1).status_code==200
            finally:tx.rollback()
            tx=db.begin()
            try:
                db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:cle,0))'),{'cle':f'hisabpro:inventaire-stock:{s}:{a-1}'})
                assert mouvement(api,p,1,jour).status_code==200
            finally:tx.rollback()


def test_chronologie_invalide_preserve_et_libere_verrou(application):
    with closing(client(application)[0]) as api:
        p=dossier(api);ok(mouvement(api,p,2));avant=empreintes_tables(application['engine'])
        assert mouvement(api,p,3,f"{p['a']}-12-30").status_code==409
        assert {k:v for k,v in empreintes_tables(application['engine']).items() if k!='audit_actions'}=={k:v for k,v in avant.items() if k!='audit_actions'}
        assert mouvement(api,p,3).status_code==200
