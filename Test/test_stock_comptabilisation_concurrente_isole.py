"""Une seule régularisation de stock par photographie, HTTP/PG nonce réels."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import pytest
from sqlalchemy import text
from test_inventaire_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration, dossier, compter,
)
from test_tva_calcul_cloture_isole import dossier as dossier_capital
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou
from recette_restauration_consolidee_084 import empreintes_tables
from test_avances_salaries_isole import originaux


def preparer(api):
    p=dossier(api)
    assert ok(compter(api,p,8,'FINAL510'))['total_valeur']==160
    return p


def generer(api,p):
    return api.post('/api/inventaire/comptabiliser-stock',params={'exercice':p['a']})


def operation(api,p,nom):
    return generer(api,p) if nom=='comptabiliser' else compter(api,p,10,'RECOMPTAGE510')


@pytest.mark.parametrize('premiere,seconde',[
    ('comptabiliser','comptabiliser'),('comptabiliser','compter'),('compter','comptabiliser'),
])
def test_comptabilisation_et_comptage_se_serialisent_puis_reprise(application,premiere,seconde):
    with closing(client(application)[0]) as api:
        api.timeout=25;p=preparer(api)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            table='lignes_ecriture' if premiere=='comptabiliser' else 'inventaires_stock'
            db.execute(text(f'LOCK TABLE {table} IN SHARE MODE'))
            f=pool.submit(operation,api,p,premiere);attendre_verrou(application,f,table=table)
            g=pool.submit(operation,api,p,seconde)
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=25)
            if r2 is None:r2=g.result(timeout=25)
            assert r1.status_code==200,r1.text
            if premiere==seconde=='comptabiliser':
                with application['engine'].connect() as c:
                    pieces=c.execute(text('SELECT e.id,sum(l.debit),sum(l.credit) FROM ecritures e JOIN lignes_ecriture l ON l.ecriture_id=e.id WHERE e.societe_id=:s AND e.reference=:r GROUP BY e.id ORDER BY e.id'),
                        {'s':p['s'],'r':f"STOCK-CLOTURE-{p['a']}"}).all()
                    assert len(pieces)==1,pieces
            assert r2.status_code==409,r2.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        valeur=160 if premiere=='comptabiliser' else 200
        eid=r1.json()['ecriture_id'] if premiere=='comptabiliser' else ok(generer(api,p))['ecriture_id']
        with application['engine'].connect() as c:
            ids=c.execute(text('SELECT id FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':p['s'],'r':f"STOCK-CLOTURE-{p['a']}"}).scalars().all()
            assert ids==[eid]
            assert c.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:id ORDER BY compte'),{'id':eid}).all()==[('3111',valeur,0),('6114',0,valeur)]
        ok(api.post(f'/api/ecritures/{eid}/valider'))
        etat=ok(api.get('/api/inventaire/stock/cloture',params={'exercice':p['a']}))
        assert etat['valeur_physique_brute']==etat['valeur_comptable_brute']==valeur and etat['stock_rapproche']
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==valeur-3000
        assert api.get('/api/fec/export',params={'exercice':p['a']}).status_code==200


def test_generation_limitee_a_societe_et_exercice(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        p=preparer(api);q=preparer(autre)
        ok(api.post('/api/exercices',json={'annee':p['a']-1,'date_debut':f"{p['a']-1}-01-01",'date_fin':f"{p['a']-1}-12-31"}),201)
        ancien={**p,'a':p['a']-1};ok(compter(api,ancien,8,'ANCIEN510'))
        with application['engine'].connect() as db:
            tx=db.begin()
            try:
                db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:cle,0))'),{'cle':f"hisabpro:inventaire-stock:{p['s']}:{p['a']}"})
                assert generer(api,p).status_code==409
                assert generer(autre,q).status_code==200
                assert generer(api,ancien).status_code==200
            finally:tx.rollback()
        assert generer(api,p).status_code==200


def test_generation_refusee_libere_verrou_et_preserve_donnees(application):
    with closing(client(application)[0]) as api:
        p,_=dossier_capital(api);avant=empreintes_tables(application['engine'])
        r=generer(api,p)
        assert r.status_code==409 and 'Aucun inventaire' in r.text,r.text
        assert {k:v for k,v in avant.items() if k!='audit_actions'}=={k:v for k,v in empreintes_tables(application['engine']).items() if k!='audit_actions'}
        aid=ok(api.post('/api/articles',json={'code':'SANSINV510','designation':'Stock fictif510',
            'is_stockable':True,'stock_actuel':0,'cmup':20,'prix_achat_ht':20}),201)['id']
        p['article']=aid;ok(compter(api,p,8,'APRESREFUS510'))
        assert generer(api,p).status_code==200


def test_regeneration_explicite_brouillon_reste_possible_definitive_preservee(application):
    with closing(client(application)[0]) as api:
        p=preparer(api);e1=ok(generer(api,p))['ecriture_id'];e2=ok(generer(api,p))['ecriture_id']
        assert e1!=e2
        with application['engine'].connect() as c:
            ids=c.execute(text('SELECT id FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':p['s'],'r':f"STOCK-CLOTURE-{p['a']}"}).scalars().all()
            assert ids==[e2]
        ok(api.post(f'/api/ecritures/{e2}/valider'));avant=originaux(application,p['s'])
        r=generer(api,p)
        assert r.status_code==409 and 'définitive' in r.text,r.text
        assert originaux(application,p['s'])==avant
