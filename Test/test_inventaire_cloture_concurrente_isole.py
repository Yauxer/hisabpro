"""Comptage et clôture : transactions concurrentes natives, aucun mock métier."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_tva_calcul_cloture_isole import dossier as dossier_capital
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou
from recette_restauration_consolidee_084 import empreintes_tables
from test_e2e_inventaire_nombres_isole import photo


def compter(api,p,quantite,reference):
    return api.post('/api/inventaire/valider',json={'date':f"{p['a']}-12-31",'reference':reference,
        'lignes':[{'article_id':p['article'],'quantite_reelle':quantite}]})


def dossier(api):
    p,_=dossier_capital(api)
    article=ok(api.post('/api/articles',json={'code':'FICTIF508','designation':'Stock fictif508',
        'is_stockable':True,'stock_actuel':0,'cmup':20,'prix_achat_ht':20}),201)
    p['article']=article['id']
    assert ok(compter(api,p,0,'INITIAL508'))['total_valeur']==0
    assert ok(api.get('/api/inventaire/stock/cloture',params={'exercice':p['a']}))['stock_rapproche']
    return p


def hors_audit(tables):
    return {k:v for k,v in tables.items() if k!='audit_actions'}


def test_cloture_en_calcul_refuse_nouveau_comptage_et_conserve_stock(application):
    with closing(client(application)[0]) as api:
        api.timeout=25;p=dossier(api)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE fiscal_parametres_exercice IN ACCESS EXCLUSIVE MODE'))
            f=pool.submit(api.post,'/api/cloture/cloturer',params={'exercice':p['a']})
            attendre_verrou(application,f,table='fiscal_parametres_exercice')
            avant=photo(application,p['s'])
            r=compter(api,p,5,'PENDANT508')
            apres=photo(application,p['s'])
            tx.rollback();cloture=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert apres==avant
            assert cloture.status_code==200 and cloture.json()['resultat_net']==-3000,cloture.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        etat=ok(api.get('/api/inventaire/stock/cloture',params={'exercice':p['a']}))
        assert etat['valeur_physique_brute']==0 and etat['stock_rapproche']
        assert api.get('/api/fec/export',params={'exercice':p['a']}).status_code==200
        tables=empreintes_tables(application['engine'])
        refus=compter(api,p,0,'APRES508')
        assert refus.status_code==409 and 'clôturé' in refus.text,refus.text
        assert hors_audit(empreintes_tables(application['engine']))==hors_audit(tables)


def test_comptage_en_cours_refuse_cloture_puis_reprise(application):
    with closing(client(application)[0]) as api:
        api.timeout=25;p=dossier(api)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE inventaires_stock IN SHARE MODE'))
            f=pool.submit(compter,api,p,0,'ENCOURS508')
            attendre_verrou(application,f,table='inventaires_stock')
            r=api.post('/api/cloture/cloturer',params={'exercice':p['a']})
            tx.rollback();inventaire=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert inventaire.status_code==200,inventaire.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-3000


def test_verrou_comptage_limite_societe_et_exercice(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        api.timeout=25;p=dossier(api);q=dossier(autre)
        ok(api.post('/api/exercices',json={'annee':p['a']-1,'date_debut':f"{p['a']-1}-01-01",'date_fin':f"{p['a']-1}-12-31"}),201)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE fiscal_parametres_exercice IN ACCESS EXCLUSIVE MODE'))
            f=pool.submit(api.post,'/api/cloture/cloturer',params={'exercice':p['a']})
            attendre_verrou(application,f,table='fiscal_parametres_exercice')
            assert compter(autre,q,0,'AUTRESOCIETE508').status_code==200
            assert compter(api,{**p,'a':p['a']-1},0,'AUTREEXERCICE508').status_code==200
            tx.rollback();r=f.result(timeout=25)
            assert r.status_code==200,r.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)


def test_echec_comptage_libere_verrou_sans_modifier_inventaire(application):
    with closing(client(application)[0]) as api:
        p=dossier(api);avant=empreintes_tables(application['engine'])
        r=api.post('/api/inventaire/valider',json={'date':f"{p['a']}-12-31",'reference':'REFUS508','lignes':[]})
        assert r.status_code==409,r.text
        assert hors_audit(empreintes_tables(application['engine']))==hors_audit(avant)
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-3000
