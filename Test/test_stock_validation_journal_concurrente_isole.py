"""Régénération de brouillon contre validation Journal, API et PG nonce réels."""
from concurrent.futures import ThreadPoolExecutor,TimeoutError
from contextlib import closing
import pytest
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_stock_comptabilisation_concurrente_isole import preparer,generer
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou


def lignes(app,eid):
    with app['engine'].connect() as c:
        return c.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l WHERE ecriture_id=:i ORDER BY id'),{'i':eid}).scalars().all()


def audit(app,eid):
    with app['engine'].connect() as c:
        return c.execute(text('SELECT row_to_json(a)::text FROM audit_ecritures a WHERE ecriture_id=:i ORDER BY id'),{'i':eid}).scalars().all()


def validation(api,eid,lot):
    return api.post('/api/ecritures/valider-lot',json={'ids':[eid]}) if lot else api.post(f'/api/ecritures/{eid}/valider')


def est_validee(r,lot):
    return r.status_code==200 and (not lot or r.json()['nb_validees']==1)


@pytest.mark.parametrize('lot',[False,True])
@pytest.mark.parametrize('premiere',['validation','regeneration'])
def test_validation_et_regeneration_ne_changent_pas_une_definitive(application,lot,premiere):
    with closing(client(application)[0]) as api:
        api.timeout=30;p=preparer(api);eid=ok(generer(api,p))['ecriture_id']
        avant=lignes(application,eid);audit_avant=audit(application,eid)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            if premiere=='validation':
                # Bloque le compteur du trigger après prise du verrou d'en-tête.
                db.execute(text('LOCK TABLE ecriture_sequences IN SHARE MODE'))
                f=pool.submit(validation,api,eid,lot)
                attendre_verrou(application,f,table='ecritures')
                g=pool.submit(generer,api,p)
            else:
                # Bloque la suppression des lignes, sans bloquer leur lecture.
                db.execute(text('SELECT id FROM lignes_ecriture WHERE ecriture_id=:i ORDER BY id LIMIT 1 FOR UPDATE'),{'i':eid})
                f=pool.submit(generer,api,p)
                attendre_verrou(application,f,table='lignes_ecriture')
                g=pool.submit(validation,api,eid,lot)
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=30)
            if r2 is None:r2=g.result(timeout=30)
            rv,rg=(r1,r2) if premiere=='validation' else (r2,r1)
            assert r1.status_code==200,r1.text
            if premiere=='validation':
                assert est_validee(rv,lot),rv.text
                assert rg.status_code==409,rg.text
                courant=eid
                assert lignes(application,eid)==avant
            else:
                assert not est_validee(rv,lot),rv.text
                if lot:
                    assert rv.status_code==200 and rv.json()['nb_validees']==0,rv.text
                    assert rv.json()['refusees'][0]['motif']=='introuvable',rv.text
                else:assert rv.status_code in (404,409),rv.text
                courant=rg.json()['ecriture_id'];assert courant!=eid
                ok(api.post(f'/api/ecritures/{courant}/valider'))
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        with application['engine'].connect() as c:
            rows=c.execute(text('SELECT id,est_validee,numero_ecriture,date_validation FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':p['s'],'r':f"STOCK-CLOTURE-{p['a']}"}).all()
            assert len(rows)==1 and rows[0][0]==courant and rows[0][1] and rows[0][2] and rows[0][3],rows
            assert c.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:i ORDER BY compte'),{'i':courant}).all()==[('3111',160,0),('6114',0,160)]
            assert c.scalar(text('SELECT count(*) FROM audit_ecritures WHERE ecriture_id=:i'),{'i':eid})>0
            assert c.scalar(text("SELECT count(*) FROM audit_ecritures WHERE ecriture_id=:i AND action IN ('validation','validation_lot') AND nouveau->>'est_validee'='true'"),{'i':courant})==1
        assert set(audit_avant).issubset(audit(application,eid))
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-2840
        assert api.get('/api/fec/export',params={'exercice':p['a']}).status_code==200


@pytest.mark.parametrize('premier_lot',[False,True])
@pytest.mark.parametrize('second_lot',[False,True])
def test_deux_validations_ne_modifient_pas_audit_ni_numero(application,premier_lot,second_lot):
    with closing(client(application)[0]) as api:
        api.timeout=30;p=preparer(api);eid=ok(generer(api,p))['ecriture_id']
        avant=lignes(application,eid)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE ecriture_sequences IN SHARE MODE'))
            f=pool.submit(validation,api,eid,premier_lot)
            attendre_verrou(application,f,table='ecritures')
            g=pool.submit(validation,api,eid,second_lot)
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=30)
            if r2 is None:r2=g.result(timeout=30)
            assert est_validee(r1,premier_lot),r1.text
            assert not est_validee(r2,second_lot),r2.text
            if second_lot:assert r2.status_code==200 and r2.json()['nb_refusees']==1,r2.text
            else:assert r2.status_code==400,r2.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        assert lignes(application,eid)==avant
        with application['engine'].connect() as c:
            assert c.scalar(text("SELECT count(*) FROM audit_ecritures WHERE ecriture_id=:i AND action IN ('validation','validation_lot') AND nouveau->>'est_validee'='true'"),{'i':eid})==1
            assert c.scalar(text("SELECT dernier_numero FROM ecriture_sequences WHERE societe_id=:s AND exercice=:a AND journal='OD'"),p)==1


def test_lots_recoupants_en_ordre_inverse_restent_chronologiques(application):
    with closing(client(application)[0]) as api:
        api.timeout=30;p=preparer(api);eid=ok(generer(api,p))['ecriture_id']
        autre=ok(api.post('/api/ecritures',json={'date':f"{p['a']}-12-31",'journal':'OD',
            'reference':'AUTRE-FICTIVE520','libelle':'Autre brouillon fictif520',
            'lignes':[{'compte':'5141','debit':10},{'compte':'4481','credit':10}]}),201)['id']
        avant={i:lignes(application,i) for i in (eid,autre)}
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE ecriture_sequences IN SHARE MODE'))
            f=pool.submit(api.post,'/api/ecritures/valider-lot',json={'ids':[autre,eid]})
            attendre_verrou(application,f,table='ecritures')
            g=pool.submit(api.post,'/api/ecritures/valider-lot',json={'ids':[eid,autre]})
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=30)
            if r2 is None:r2=g.result(timeout=30)
            assert r1.status_code==200 and r1.json()['nb_validees']==2,r1.text
            assert r2.status_code==200 and r2.json()['nb_validees']==0 and r2.json()['nb_refusees']==2,r2.text
            assert r1.json()['validees']==[eid,autre]
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        for i in (eid,autre):assert lignes(application,i)==avant[i]
        with application['engine'].connect() as c:
            assert c.scalar(text("SELECT dernier_numero FROM ecriture_sequences WHERE societe_id=:s AND exercice=:a AND journal='OD'"),p)==2
            assert c.scalar(text('SELECT count(DISTINCT numero_ecriture) FROM ecritures WHERE id IN (:i,:j)'),{'i':eid,'j':autre})==2
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-2840
        assert api.get('/api/fec/export',params={'exercice':p['a']}).status_code==200
