"""Dotations concurrentes : API et PostgreSQL nonce, aucun calcul métier simulé."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import date
import time
import pytest
from sqlalchemy import text
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_avances_salaries_isole import originaux
from test_tva_verrou_exercice_isole import attendre_verrou


def dossier(api,annee=None):
    annee=annee or date.today().year-1
    ok(api.post('/api/exercices',json={'annee':annee,'date_debut':f'{annee}-01-01','date_fin':f'{annee}-12-31'}),201)
    immo=ok(api.post('/api/immobilisations',json={'designation':'Matériel fictif493','categorie':'Matériel informatique',
        'date_acquisition':f'{annee}-01-01','date_mise_en_service':f'{annee}-01-01','prix_acquisition_ht':10000,
        'duree_amort':5,'methode':'lineaire','compte_immo':'2355','compte_amort':'28355','compte_dotation':'61935'}),201)
    return annee,immo,ok(api.get('/api/societe/moi'))['id']


def generer(api,route,annee,iid):
    if route=='unitaire':return api.post(f'/api/immobilisations/{iid}/generer-ecriture',params={'annee':annee})
    if route=='lot':return api.post('/api/immobilisations/generer-dotations-annee',params={'annee':annee})
    return api.post('/api/cloture/generer-dotations',params={'exercice':annee})


@pytest.mark.parametrize('premiere,seconde', [('unitaire','unitaire'),('unitaire','lot'),('lot','unitaire'),('lot','lot'),('cloture','unitaire'),('unitaire','cloture')])
def test_generation_simultanee_ne_cree_quune_dotation(application,premiere,seconde):
    with closing(client(application)[0]) as api:
        api.timeout=25;annee,immo,sid=dossier(api);iid=immo['id'];avant=originaux(application,sid)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE lignes_ecriture IN SHARE MODE'))
            f=pool.submit(generer,api,premiere,annee,iid)
            attendre_verrou(application,f,table='lignes_ecriture')
            g=pool.submit(generer,api,seconde,annee,iid)
            try:second=g.result(timeout=2)
            except TimeoutError:
                # Avant correction les deux INSERT de lignes attendent : les
                # deux contrôles de référence ont déjà laissé passer la course.
                fin=time.monotonic()+5
                while time.monotonic()<fin:
                    with application['engine'].connect() as c:
                        n=c.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE usename='hisabpro' AND wait_event_type='Lock' AND query ILIKE '%INSERT INTO lignes_ecriture%'"))
                    if n>=2:break
                    time.sleep(.05)
                assert n>=2,'La seconde requête ne participe pas à la course attendue.'
                second=None
            tx.rollback();r=f.result(timeout=25)
            if second is None:second=g.result(timeout=25)
            assert r.status_code==200,r.text
            assert second.status_code==409,second.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        with application['engine'].connect() as c:
            ids=c.execute(text('SELECT id FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':sid,'r':f'AM-{annee}-{iid}'}).scalars().all()
            assert len(ids)==1
            lignes=c.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:id ORDER BY compte'),{'id':ids[0]}).all()
            assert lignes==[('28355',0,2000),('61935',2000,0)]
        apres=originaux(application,sid)
        for table,lignes in avant.items():assert all(l in apres[table] for l in lignes)
        # Rejouer ne duplique rien : unité409, lots200 avec une ligne ignorée.
        r=generer(api,seconde,annee,iid)
        assert r.status_code==(409 if seconde=='unitaire' else 200),r.text
        if seconde!='unitaire':assert r.json()['nb_generees']==0 and r.json()['nb_ignorees']==1
        assert originaux(application,sid)==apres


def test_verrou_limite_a_societe_immobilisation_exercice_et_libere(application):
    with closing(client(application)[0]) as a,closing(client(application)[0]) as b:
        annee,immo,sid=dossier(a,date.today().year-2)
        _,autre,_=dossier(b,annee)
        ok(a.post('/api/exercices',json={'annee':annee+1,'date_debut':f'{annee+1}-01-01','date_fin':f'{annee+1}-12-31'}),201)
        payload={'designation':'Autre matériel fictif493','categorie':'Matériel informatique','date_acquisition':f'{annee}-01-01',
            'prix_acquisition_ht':10000,'duree_amort':5,'methode':'lineaire','compte_immo':'2355','compte_amort':'28355','compte_dotation':'61935'}
        immo2=ok(a.post('/api/immobilisations',json=payload),201)
        with application['engine'].connect() as db:
            tx=db.begin()
            try:
                db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:cle,0))'),{'cle':f"hisabpro:dotation:{sid}:{immo['id']}:{annee}"})
                assert generer(a,'unitaire',annee,immo['id']).status_code==409
                for api,iid,an in [(a,immo2['id'],annee),(a,immo['id'],annee+1),(b,autre['id'],annee)]:
                    assert ok(generer(api,'unitaire',an,iid))['dotation']==2000
            finally:tx.rollback()
        assert ok(generer(a,'unitaire',annee,immo['id']))['dotation']==2000


def test_refus_cloture_annule_creation_et_libere_verrou_dotation(application):
    with closing(client(application)[0]) as api:
        annee,immo,sid=dossier(api);avant=originaux(application,sid)
        with application['engine'].connect() as db:
            tx=db.begin()
            try:
                db.execute(text('SELECT hisabpro_verrou_tva_cloture(:s,:a,true)'),{'s':sid,'a':annee})
                r=generer(api,'unitaire',annee,immo['id']);assert r.status_code==409,r.text
                assert originaux(application,sid)==avant
            finally:tx.rollback()
        assert ok(generer(api,'unitaire',annee,immo['id']))['dotation']==2000
