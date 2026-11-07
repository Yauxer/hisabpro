"""TVA stable pendant le calcul réel de clôture, aucun calcul métier simulé."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor,TimeoutError
from datetime import date
import pytest
from sqlalchemy import text
from test_tva_trace_concurrente_isole import (
    application,application093,application092,application091,application090,
    application089,application087,migration,resultat,TRACE,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou
from test_avances_salaries_isole import originaux
from recette_restauration_consolidee_084 import empreintes_tables


def dossier(api):
    annee=date.today().year-1;sid=ok(api.get('/api/societe/moi'))['id']
    ok(api.post('/api/exercices',json={'annee':annee,'date_debut':f'{annee}-01-01','date_fin':f'{annee}-12-31'}),201)
    e=ok(api.post('/api/ecritures',json={'date':f'{annee}-12-31','journal':'BQ','reference':'CAPITAL-FICTIF488',
        'libelle':'Capital fictif488','est_validee':True,'lignes':[{'compte':'5141','debit':1000},{'compte':'1111','credit':1000}]}),201)
    ok(api.put(f'/api/tva/parametres/{annee}',json={'credit_ouverture':20,'prorata_deduction_pct':80}))
    return {'s':sid,'a':annee},e['id']


def test_tva_en_cours_refuse_cloture_avant_calcul_et_sans_mutation(application):
    with closing(client(application)[0]) as api:
        api.timeout=15;p,_=dossier(api);avant=empreintes_tables(application['engine'])
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('UPDATE tva_parametres_exercice SET credit_ouverture=30 WHERE societe_id=:s AND exercice=:a'),p)
            db.execute(text('LOCK TABLE immobilisations IN ACCESS EXCLUSIVE MODE'))
            f=pool.submit(api.post,f"/api/cloture/cloturer?exercice={p['a']}")
            try:r=f.result(timeout=3)
            except TimeoutError:pytest.fail('La clôture a commencé ses calculs au lieu de refuser le conflit initial.')
            assert r.status_code==409,r.text
            tx.rollback()  # Libérer aussi le verrou de table avant le contrôle de conservation.
            apres=empreintes_tables(application['engine'])
            assert {k:v for k,v in apres.items() if k!='audit_actions'}=={k:v for k,v in avant.items() if k!='audit_actions'}
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        assert ok(api.get(f"/api/tva/parametres/{p['a']}"))['credit_ouverture']==20


def test_cloture_en_calcul_refuse_tva_et_seconde_cloture_puis_termine(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        api.timeout=20;p,eid=dossier(api);avant=originaux(application,p['s'])
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE immobilisations IN ACCESS EXCLUSIVE MODE'))
            f=pool.submit(api.post,f"/api/cloture/cloturer?exercice={p['a']}")
            attendre_verrou(application,f,table='immobilisations')
            r=api.put(f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':30,'prorata_deduction_pct':80})
            assert r.status_code==409,r.text
            assert resultat(application['engine'],TRACE,p)=='40001'
            assert api.post(f"/api/cloture/cloturer?exercice={p['a']}").status_code==409
            # Les périmètres indépendants restent disponibles pendant le calcul.
            for a,annee in [(autre,p['a']),(api,p['a']-1)]:
                ok(a.put(f'/api/tva/parametres/{annee}',json={'credit_ouverture':12,'prorata_deduction_pct':80}))
            tx.rollback();r=f.result(timeout=20)
            assert r.status_code==200,r.text
            # Jeu IS par défaut sans exonération consignée : la CM existante
            # de3000 est comptabilisée automatiquement. Ne pas la neutraliser
            # pour ce test de concurrence ; résultat0 avant impôt puis-3000.
            assert r.json()['resultat_net']==-3000 and r.json()['a_nouveaux_sur']==p['a']+1
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        apres=originaux(application,p['s'])
        for table,lignes in avant.items():assert all(l in apres[table] for l in lignes),table
        with application['engine'].connect() as c:
            impot=c.execute(text("SELECT l.compte,l.debit,l.credit FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s AND e.reference=:r ORDER BY l.compte"),
                {'s':p['s'],'r':f"CALCUL-IS-{p['a']}"}).all()
            assert impot==[('4453',0,3000),('6705',3000,0)]
        assert ok(api.get(f"/api/tva/parametres/{p['a']}"))['credit_ouverture']==20
        assert api.put(f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':30,'prorata_deduction_pct':80}).status_code==409
        r=api.get('/api/fec/export',params={'exercice':p['a']})
        assert r.status_code==200,r.text


def test_refus_metier_cloture_libere_verrou_et_conserve_brouillon(application):
    with closing(client(application)[0]) as api:
        p,_=dossier(api)
        ok(api.post('/api/ecritures',json={'date':f"{p['a']}-12-31",'journal':'OD','reference':'BROUILLON-FICTIF488',
            'libelle':'Brouillon fictif488','lignes':[{'compte':'5141','debit':10},{'compte':'1111','credit':10}]}),201)
        avant=originaux(application,p['s'])
        r=api.post(f"/api/cloture/cloturer?exercice={p['a']}")
        assert r.status_code==400 and 'brouillon' in r.text.lower(),r.text
        ok(api.put(f"/api/tva/parametres/{p['a']}",json={'credit_ouverture':30,'prorata_deduction_pct':80}))
        assert originaux(application,p['s'])==avant
