"""Stock global de déficits : concurrence native API/PG isolé, aucun calcul simulé."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor, TimeoutError
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
from test_fiscalite_concurrence_cloture_isole import parametres, confirmation, hors_audit
from recette_restauration_consolidee_084 import empreintes_tables
from test_avances_salaries_isole import originaux


def corps(p, montant=1000):
    return {'exercice_origine': p['a']-2, 'montant_ordinaire': montant,
        'commentaire': 'Déficit historique fictif514, montant fourni explicitement'}


def ajouter(api,p):
    return ok(api.post('/api/fiscalite/deficits',json=corps(p)))['id']


def modifier(api,p,did,operation):
    if operation=='ajouter':
        return api.post('/api/fiscalite/deficits',json={**corps(p), 'exercice_origine':p['a']-1})
    if operation=='modifier':
        return api.patch(f'/api/fiscalite/deficits/{did}',json=corps(p,2000))
    return api.delete(f'/api/fiscalite/deficits/{did}')


def photo(app,sid):
    with app['engine'].connect() as c:
        return c.execute(text('SELECT id,exercice_origine,montant_ordinaire,montant_amortissements FROM fiscal_deficits WHERE societe_id=:s ORDER BY id'),{'s':sid}).all()


@pytest.mark.parametrize('operation',['ajouter','modifier','supprimer'])
@pytest.mark.parametrize('premiere',['cloture','confirmation'])
def test_sources_deficits_refusees_pendant_calcul_fige(application,operation,premiere):
    with closing(client(application)[0]) as api:
        api.timeout=25;p,_=dossier(api);did=ajouter(api,p);ok(parametres(api,p))
        if premiere=='confirmation':ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))
        avant=photo(application,p['s']);sources=originaux(application,p['s'])
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            # Après lecture du stock déficitaire ; les CRUD ne lisent pas cette table.
            table='fiscal_liquidations_is'
            mode='ACCESS EXCLUSIVE' if premiere=='cloture' else 'SHARE'
            db.execute(text(f'LOCK TABLE {table} IN {mode} MODE'))
            f=pool.submit(api.post,'/api/cloture/cloturer',params={'exercice':p['a']}) if premiere=='cloture' else pool.submit(confirmation,api,p)
            attendre_verrou(application,f,table=table)
            r=modifier(api,p,did,operation)
            tx.rollback();r1=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert r1.status_code==200,r1.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        assert photo(application,p['s'])==avant
        if premiere=='confirmation':assert originaux(application,p['s'])==sources
        assert ok(api.get(f"/api/fiscalite/is/{p['a']}"))['comptabilisation_is']['coherente']


@pytest.mark.parametrize('seconde',['cloture','confirmation'])
def test_mutation_deficit_en_cours_refuse_calcul_puis_reprise(application,seconde):
    with closing(client(application)[0]) as api:
        api.timeout=25;p,_=dossier(api);ok(parametres(api,p))
        if seconde=='confirmation':ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE fiscal_deficits IN SHARE MODE'))
            f=pool.submit(api.post,'/api/fiscalite/deficits',json=corps(p))
            attendre_verrou(application,f,table='fiscal_deficits')
            def calcul():
                return api.post('/api/cloture/cloturer',params={'exercice':p['a']}) if seconde=='cloture' else confirmation(api,p)
            g=pool.submit(calcul)
            try:r=g.result(timeout=2)
            except TimeoutError:r=None
            tx.rollback();r1=f.result(timeout=25)
            if r is None:r=g.result(timeout=25)
            assert r1.status_code==200,r1.text
            assert r.status_code==409,r.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        ok(calcul())
        assert photo(application,p['s'])[0][2]==1000


def produit(api,annee,montant=20000):
    return ok(api.post('/api/ecritures',json={'date':f'{annee}-12-31','journal':'BQ',
        'reference':f'PRODUIT-FICTIF514-{annee}','libelle':'Produit fictif514',
        'est_validee':True,'lignes':[{'compte':'5141','debit':montant},{'compte':'7111','credit':montant}]}),201)


def test_imputations_deux_exercices_ne_consomment_pas_le_meme_solde(application):
    with closing(client(application)[0]) as api:
        api.timeout=25;p,_=dossier(api);did=ajouter(api,p)
        anterieur=p['a']-1
        ok(api.post('/api/exercices',json={'annee':anterieur,'date_debut':f'{anterieur}-01-01','date_fin':f'{anterieur}-12-31'}),201)
        for a in (anterieur,p['a']):produit(api,a)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        def imputer(a):return api.post(f'/api/fiscalite/is/{a}/deficits/confirmer-imputation')
        try:
            db.execute(text('LOCK TABLE fiscal_deficit_imputations IN SHARE MODE'))
            f=pool.submit(imputer,anterieur);attendre_verrou(application,f,table='fiscal_deficit_imputations')
            g=pool.submit(imputer,p['a'])
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=25)
            if r2 is None:r2=g.result(timeout=25)
            assert r1.status_code==200 and r1.json()['montant_confirme']==1000,r1.text
            assert r2.status_code==409,r2.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        assert ok(imputer(p['a']))['montant_confirme']==0
        with application['engine'].connect() as c:
            assert c.execute(text('SELECT exercice_cible,montant_ordinaire FROM fiscal_deficit_imputations WHERE societe_id=:s AND deficit_id=:d ORDER BY exercice_cible'),{'s':p['s'],'d':did}).all()==[(anterieur,1000)]
        assert api.patch(f'/api/fiscalite/deficits/{did}',json=corps(p,2000)).status_code==409
        assert api.delete(f'/api/fiscalite/deficits/{did}').status_code==409


def test_stock_deficits_isole_par_societe_et_echec_libere_verrou(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        p,_=dossier(api);q,_=dossier(autre)
        db=application['engine'].connect();tx=db.begin()
        try:
            db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:cle,0))"),{'cle':f"hisabpro:deficits-fiscaux:{p['s']}"})
            assert api.post('/api/fiscalite/deficits',json=corps(p)).status_code==409
            assert autre.post('/api/fiscalite/deficits',json=corps(q)).status_code==200
        finally:tx.rollback();db.close()
        ajouter(api,p);avant=empreintes_tables(application['engine'])
        assert api.post('/api/fiscalite/deficits',json=corps(p)).status_code==409
        assert hors_audit(empreintes_tables(application['engine']))==hors_audit(avant)
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-3000


def test_deficit_calcule_et_annulation_imputation_restent_possibles(application):
    with closing(client(application)[0]) as api:
        p,_=dossier(api)
        ok(api.post('/api/ecritures',json={'date':f"{p['a']}-12-31",'journal':'BQ',
            'reference':'CHARGE-FICTIVE514','libelle':'Charge fictive514','est_validee':True,
            'lignes':[{'compte':'6121','debit':2000},{'compte':'5141','credit':2000}]}),201)
        d=ok(api.post(f"/api/fiscalite/is/{p['a']}/deficits/enregistrer-genere"))
        assert d['montant_ordinaire']==2000 and d['source']=='calcul'
        assert api.delete(f"/api/fiscalite/is/{p['a']}/deficits/imputation").status_code==204
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-5000
