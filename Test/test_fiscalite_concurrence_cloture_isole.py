"""IS figé pendant clôture/confirmation : API et transactions PG nonce réelles."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from decimal import Decimal
import pytest
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_tva_calcul_cloture_isole import dossier
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou
from recette_restauration_consolidee_084 import empreintes_tables
from test_avances_salaries_isole import originaux


def parametres(api,p,reference=10000,**changements):
    # Hypothèses documentaires fictives de laboratoire, jamais régime réel supposé.
    return api.put(f"/api/fiscalite/is/{p['a']}/parametres",json={
        'acomptes_reference_forcee':reference,
        'acomptes_justification_reference_forcee':'Référence fictive explicite512',**changements})


def confirmation(api,p):
    return api.post(f"/api/fiscalite/is/{p['a']}/liquidation/confirmer")


def hors_audit(tables):return {k:v for k,v in tables.items() if k!='audit_actions'}


def test_parametres_refuses_pendant_cloture_apres_lecture_du_calcul(application):
    with closing(client(application)[0]) as api:
        api.timeout=25;p,_=dossier(api);ok(parametres(api,p))
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE fiscal_retraitements IN ACCESS EXCLUSIVE MODE'))
            f=pool.submit(api.post,'/api/cloture/cloturer',params={'exercice':p['a']})
            attendre_verrou(application,f,table='fiscal_retraitements')
            r=parametres(api,p,cm_minimum_3000_exonere=True,
                cm_justification_minimum_exonere='Entrée fictive pour reproduire une course, sans qualification fiscale')
            tx.rollback();cloture=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert cloture.status_code==200 and cloture.json()['resultat_net']==-3000,cloture.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        situation=ok(api.get(f"/api/fiscalite/is/{p['a']}"))
        assert not situation['parametres']['cm_minimum_3000_exonere']
        assert situation['comptabilisation_is']['coherente']


def test_parametres_en_cours_refusent_cloture_puis_reprise(application):
    with closing(client(application)[0]) as api:
        api.timeout=25;p,_=dossier(api)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE fiscal_parametres_exercice IN SHARE MODE'))
            f=pool.submit(parametres,api,p)
            attendre_verrou(application,f,table='fiscal_parametres_exercice')
            r=api.post('/api/cloture/cloturer',params={'exercice':p['a']})
            tx.rollback();params=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert params.status_code==200,params.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-3000


@pytest.mark.parametrize('operation',['ajouter','modifier','supprimer'])
def test_retraitements_refuses_pendant_cloture(application,operation):
    with closing(client(application)[0]) as api:
        api.timeout=25;p,_=dossier(api)
        corps={'type':'reintegration','libelle':'Retraitement fictif512','montant':1000}
        rid=ok(api.post(f"/api/fiscalite/is/{p['a']}/retraitements",json=corps))['id']
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE fiscal_deficits IN ACCESS EXCLUSIVE MODE'))
            f=pool.submit(api.post,'/api/cloture/cloturer',params={'exercice':p['a']})
            attendre_verrou(application,f,table='fiscal_deficits')
            if operation=='ajouter':r=api.post(f"/api/fiscalite/is/{p['a']}/retraitements",json=corps)
            elif operation=='modifier':r=api.patch(f'/api/fiscalite/is/retraitements/{rid}',json={**corps,'montant':2000})
            else:r=api.delete(f'/api/fiscalite/is/retraitements/{rid}')
            tx.rollback();cloture=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert cloture.status_code==200,cloture.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        with application['engine'].connect() as c:
            assert c.execute(text('SELECT id,montant FROM fiscal_retraitements WHERE societe_id=:s ORDER BY id'),{'s':p['s']}).all()==[(rid,1000)]


@pytest.mark.parametrize('premiere,seconde',[
    ('confirmation','parametres'),('parametres','confirmation'),('confirmation','confirmation'),
])
def test_confirmation_et_mutation_ne_se_croisent_pas(application,premiere,seconde):
    with closing(client(application)[0]) as api:
        api.timeout=25;p,_=dossier(api);ok(parametres(api,p))
        ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))
        sources=originaux(application,p['s'])
        def executer(nom):return confirmation(api,p) if nom=='confirmation' else parametres(api,p,reference=20000)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            table='fiscal_liquidations_is' if premiere=='confirmation' else 'fiscal_parametres_exercice'
            db.execute(text(f'LOCK TABLE {table} IN SHARE MODE'))
            f=pool.submit(executer,premiere);attendre_verrou(application,f,table=table)
            g=pool.submit(executer,seconde)
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=25)
            if r2 is None:r2=g.result(timeout=25)
            assert r1.status_code==200,r1.text
            assert r2.status_code==409,r2.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        if premiere=='parametres':ok(confirmation(api,p))
        assert parametres(api,p,reference=30000).status_code==409
        with application['engine'].connect() as c:
            assert c.scalar(text('SELECT count(*) FROM fiscal_liquidations_is WHERE societe_id=:s AND exercice=:a'),p)==1
            assert c.scalar(text('SELECT acomptes_reference_forcee FROM fiscal_parametres_exercice WHERE societe_id=:s AND exercice=:a'),p)==(20000 if premiere=='parametres' else 10000)
            snapshot=c.scalar(text('SELECT snapshot_detail FROM fiscal_liquidations_is WHERE societe_id=:s AND exercice=:a'),p)
            assert Decimal(snapshot['parametres_fiscaux']['acomptes_reference_forcee'])==(20000 if premiere=='parametres' else 10000)
        assert originaux(application,p['s'])==sources


def test_parametres_autres_perimetres_disponibles(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        api.timeout=25;p,_=dossier(api);q,_=dossier(autre)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE fiscal_retraitements IN ACCESS EXCLUSIVE MODE'))
            f=pool.submit(api.post,'/api/cloture/cloturer',params={'exercice':p['a']})
            attendre_verrou(application,f,table='fiscal_retraitements')
            assert parametres(autre,q).status_code==200
            assert parametres(api,{**p,'a':p['a']-1}).status_code==200
            tx.rollback();r=f.result(timeout=25)
            assert r.status_code==200,r.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)


def test_reference_et_paiement_restent_completables_apres_cloture(application):
    with closing(client(application)[0]) as api:
        p,_=dossier(api);ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))
        sources=originaux(application,p['s']);ok(parametres(api,p))
        ok(api.put(f"/api/fiscalite/is/{p['a']}/acomptes/1",json={
            'montant_verse':1000,'date_versement':f"{p['a']+1}-03-31",'reference_paiement':'Paiement fiscal fictif postcloture512'}))
        assert parametres(api,p,cm_minimum_3000_exonere=True,cm_justification_minimum_exonere='Fictif').status_code==409
        assert originaux(application,p['s'])==sources
        assert ok(api.get(f"/api/fiscalite/is/{p['a']}"))['comptabilisation_is']['coherente']


def test_echec_parametrage_libere_verrou_et_preserve_donnees(application):
    with closing(client(application)[0]) as api:
        p,_=dossier(api);avant=empreintes_tables(application['engine'])
        r=parametres(api,p,cm_base_exclue=1,cm_justification_base_exclue='Base fictive impossible512')
        assert r.status_code==400,r.text
        assert hors_audit(empreintes_tables(application['engine']))==hors_audit(avant)
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-3000
