"""Courses plan/sortie : vrais HTTP/PG nonce et barrières SQL, aucun mock métier."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor,TimeoutError
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
import models
from routers.immobilisations import _get_immo
from test_dotations_concurrentes_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,dossier,generer,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_avances_salaries_isole import originaux
from test_tva_verrou_exercice_isole import attendre_verrou


def sortie(api,iid,annee,nature='rebut'):
    return api.post(f'/api/immobilisations/{iid}/sortie',json={'date_sortie':f'{annee}-12-31',
        'type_sortie':nature,'prix_cession_ht':7500 if nature=='cession' else 0,'encaissement_immediat':False})


@pytest.mark.parametrize('nature',['rebut','cession','encaissement','paiement'])
def test_deux_sorties_ou_encaissements_ne_creent_quune_operation(application,nature):
    with closing(client(application)[0]) as api:
        api.timeout=25;annee,immo,sid=dossier(api);iid=immo['id']
        ok(generer(api,'unitaire',annee,iid))
        if nature=='encaissement':ok(sortie(api,iid,annee,'cession'))
        avant=originaux(application,sid)
        def appel():
            if nature=='paiement':return api.post(f'/api/immobilisations/{iid}/payer',json={'date_paiement':f'{annee}-12-31','compte_reglement':'5141'})
            if nature=='encaissement':return api.post(f'/api/immobilisations/{iid}/encaisser-cession',json={'date_encaissement':f'{annee}-12-31','compte_tresorerie':'5141'})
            return sortie(api,iid,annee,nature)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE lignes_ecriture IN SHARE MODE'))
            f=pool.submit(appel);attendre_verrou(application,f,table='lignes_ecriture')
            g=pool.submit(appel)
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=25)
            if r2 is None:r2=g.result(timeout=25)
            assert r1.status_code==200,r1.text
            assert r2.status_code==409,r2.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        prefixe={'encaissement':'ENC-CESSION','paiement':'PAY-IMMO'}.get(nature,'SORTIE-IMMO')
        reference=f'{prefixe}-{iid}'
        with application['engine'].connect() as c:
            assert c.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':sid,'r':reference})==1
        apres=originaux(application,sid)
        for table,lignes in avant.items():assert all(l in apres[table] for l in lignes)
        assert appel().status_code==409
        assert originaux(application,sid)==apres


@pytest.mark.parametrize('route',['unitaire','lot','cloture'])
def test_dotation_en_cours_refuse_changement_du_plan(application,route):
    with closing(client(application)[0]) as api:
        api.timeout=25;annee,immo,sid=dossier(api);iid=immo['id']
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE lignes_ecriture IN SHARE MODE'))
            f=pool.submit(generer,api,route,annee,iid);attendre_verrou(application,f,table='lignes_ecriture')
            r=api.patch(f'/api/immobilisations/{iid}',json={'duree_amort':10})
            tx.rollback();r1=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert r1.status_code==200,r1.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        assert api.patch(f'/api/immobilisations/{iid}',json={'duree_amort':10}).status_code==409
        assert ok(api.get(f'/api/immobilisations/{iid}/tableau'))['immobilisation']['duree_amort']==5


@pytest.mark.parametrize('route',['unitaire','lot','cloture'])
def test_plan_en_cours_refuse_generation_puis_utilise_plan_confirme(application,route):
    with closing(client(application)[0]) as api:
        api.timeout=25;annee,immo,sid=dossier(api);iid=immo['id']
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE immobilisations IN SHARE MODE'))
            f=pool.submit(api.patch,f'/api/immobilisations/{iid}',json={'duree_amort':10})
            attendre_verrou(application,f,table='immobilisations')
            r=generer(api,route,annee,iid)
            tx.rollback();r1=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert r1.status_code==200,r1.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        r=ok(generer(api,route,annee,iid))
        assert r.get('dotation',r.get('total_dotation'))==1000


def autre_immo(api,annee):
    return ok(api.post('/api/immobilisations',json={'designation':'Autre matériel fictif495','categorie':'Matériel informatique',
        'date_acquisition':f'{annee}-01-01','prix_acquisition_ht':10000,'duree_amort':5,'methode':'lineaire',
        'compte_immo':'2355','compte_amort':'28355','compte_dotation':'61935'}),201)


def test_conflit_asset_ne_bloque_pas_lecture_autres_assets_ni_autres_societes(application):
    with closing(client(application)[0]) as a,closing(client(application)[0]) as b:
        annee,immo,sid=dossier(a);_,etranger,_=dossier(b);autre=autre_immo(a,annee)
        with application['engine'].connect() as c:
            tx=c.begin()
            try:
                c.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:cle,0))'),{'cle':f"hisabpro:immobilisation:{sid}:{immo['id']}"})
                assert a.patch(f"/api/immobilisations/{immo['id']}",json={'notes':'Conflit fictif'}).status_code==409
                assert a.get(f"/api/immobilisations/{immo['id']}/tableau").status_code==200
                assert b.patch(f"/api/immobilisations/{immo['id']}",json={'notes':'Interdit'}).status_code==404
                for api,iid in [(a,autre['id']),(b,etranger['id'])]:
                    assert api.patch(f'/api/immobilisations/{iid}',json={'notes':'Indépendant fictif495'}).status_code==200
            finally:tx.rollback()
        assert a.patch(f"/api/immobilisations/{immo['id']}",json={'notes':'Après libération'}).status_code==200


def test_refus_metier_libere_verrou_sans_mutation(application):
    with closing(client(application)[0]) as api:
        annee,immo,sid=dossier(api);avant=originaux(application,sid)
        assert api.patch(f"/api/immobilisations/{immo['id']}",json={'valeur_residuelle':11000}).status_code==400
        r=ok(api.get(f"/api/immobilisations/{immo['id']}/tableau"))
        assert r['immobilisation']['valeur_residuelle']==0 and originaux(application,sid)==avant
        assert generer(api,'unitaire',annee,immo['id']).status_code==200


def test_conflit_tardif_lot_annule_toutes_les_dotations_et_permet_reprise(application):
    with closing(client(application)[0]) as api:
        annee,immo,sid=dossier(api);autre=autre_immo(api,annee);avant=originaux(application,sid)
        with application['engine'].connect() as c:
            tx=c.begin()
            try:
                c.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:cle,0))'),{'cle':f"hisabpro:immobilisation:{sid}:{autre['id']}"})
                r=generer(api,'lot',annee,immo['id']);assert r.status_code==409,r.text
                assert originaux(application,sid)==avant
            finally:tx.rollback()
        r=ok(generer(api,'lot',annee,immo['id']))
        assert r['nb_generees']==2 and r['total_dotation']==4000


def test_relecture_du_plan_precharge_dans_session_reelle(application):
    with closing(client(application)[0]) as api:
        _,immo,sid=dossier(api)
        with Session(application['engine']) as db:
            ancien=db.get(models.Immobilisation,immo['id']);assert ancien.duree_amort==5
            ok(api.patch(f"/api/immobilisations/{immo['id']}",json={'duree_amort':10}))
            assert ancien.duree_amort==5  # Cache ORM effectivement ancien.
            actuel=_get_immo(db,sid,immo['id'],ecriture=True)
            assert actuel is ancien and actuel.duree_amort==10
