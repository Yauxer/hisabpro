"""Journal : modification/suppression et validation concurrentes, API/PG nonce."""
from concurrent.futures import ThreadPoolExecutor,TimeoutError
from contextlib import closing
import pytest
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_tva_calcul_cloture_isole import dossier
from test_stock_validation_journal_concurrente_isole import lignes,audit,validation,est_validee
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou


def preparer(api):
    p,_=dossier(api)
    eid=ok(api.post('/api/ecritures',json={'date':f"{p['a']}-12-31",'journal':'OD',
        'reference':'BROUILLON-FICTIF522','libelle':'Brouillon original fictif522',
        'lignes':[{'compte':'5141','debit':100},{'compte':'4481','credit':100}]}),201)['id']
    return p,eid


def mutation(api,eid,operation):
    if operation=='supprimer':return api.delete(f'/api/ecritures/{eid}')
    return api.patch(f'/api/ecritures/{eid}',json={'libelle':'Modification fictive522',
        'lignes':[{'compte':'5141','debit':200},{'compte':'4481','credit':200}]})


def terminer(api,p):
    assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-3000
    assert api.get('/api/fec/export',params={'exercice':p['a']}).status_code==200


@pytest.mark.parametrize('operation',['modifier','supprimer'])
@pytest.mark.parametrize('lot',[False,True])
def test_validation_en_cours_refuse_mutation_puis_preserve_definitive(application,operation,lot):
    with closing(client(application)[0]) as api:
        api.timeout=30;p,eid=preparer(api);avant=lignes(application,eid);audit_avant=audit(application,eid)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE ecriture_sequences IN SHARE MODE'))
            f=pool.submit(validation,api,eid,lot);attendre_verrou(application,f,table='ecritures')
            g=pool.submit(mutation,api,eid,operation)
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=30)
            if r2 is None:r2=g.result(timeout=30)
            assert est_validee(r1,lot),r1.text
            assert r2.status_code==423 and 'contrepassation' in r2.text,r2.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        assert lignes(application,eid)==avant
        assert set(audit_avant).issubset(audit(application,eid))
        detail=ok(api.get(f'/api/ecritures/{eid}'))
        assert detail['est_validee'] and detail['numero_ecriture'] and detail['date_validation']
        assert detail['reference']=='BROUILLON-FICTIF522' and detail['libelle']=='Brouillon original fictif522'
        with application['engine'].connect() as c:
            assert c.scalar(text("SELECT count(*) FROM audit_ecritures WHERE ecriture_id=:i AND action IN ('validation','validation_lot') AND nouveau->>'est_validee'='true'"),{'i':eid})==1
            assert c.scalar(text("SELECT count(*) FROM audit_ecritures WHERE ecriture_id=:i AND action IN ('modification','suppression_brouillon')"),{'i':eid})==0
        terminer(api,p)


@pytest.mark.parametrize('operation',['modifier','supprimer'])
def test_mutation_en_cours_puis_validation_relit_ses_sources(application,operation):
    with closing(client(application)[0]) as api:
        api.timeout=30;p,eid=preparer(api);audit_avant=audit(application,eid)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            table='lignes_ecriture' if operation=='modifier' else 'audit_ecritures'
            db.execute(text(f'LOCK TABLE {table} IN SHARE MODE'))
            f=pool.submit(mutation,api,eid,operation)
            attendre_verrou(application,f,table='lignes_ecriture' if operation=='modifier' else 'ecriture')
            g=pool.submit(validation,api,eid,False)
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=30)
            if r2 is None:r2=g.result(timeout=30)
            assert r1.status_code==(200 if operation=='modifier' else 204),r1.text
            if operation=='modifier':
                assert est_validee(r2,False),r2.text
                detail=ok(api.get(f'/api/ecritures/{eid}'))
                assert detail['libelle']=='Modification fictive522'
                assert sum(l['debit'] for l in detail['lignes'])==sum(l['credit'] for l in detail['lignes'])==200
            else:
                assert r2.status_code==404,r2.text
                assert api.get(f'/api/ecritures/{eid}').status_code==404
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        assert set(audit_avant).issubset(audit(application,eid))
        terminer(api,p)
