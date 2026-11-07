"""Registre stable pendant clôture : HTTP et PostgreSQL nonce, calcul réel."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import pytest
from sqlalchemy import text
from test_immobilisations_mutations_concurrentes_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,autre_immo,
)
from test_tva_calcul_cloture_isole import dossier
from test_dotations_concurrentes_isole import generer
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_avances_salaries_isole import originaux
from test_tva_verrou_exercice_isole import attendre_verrou
from recette_restauration_consolidee_084 import empreintes_tables

VERROU="SELECT pg_advisory_xact_lock(hashtextextended(:cle,0))"


def acquisition(annee):
    return {'designation':'Matériel fictif497','categorie':'Matériel informatique','date_acquisition':f'{annee}-01-01',
        'prix_acquisition_ht':10000,'duree_amort':5,'methode':'lineaire','compte_immo':'2355','compte_amort':'28355','compte_dotation':'61935'}


def dossier_complet(api):
    p,_=dossier(api);immo=autre_immo(api,p['a'])
    dot=ok(generer(api,'unitaire',p['a'],immo['id']))
    for eid in [immo['ecriture_acquisition_id'],dot['ecriture_id']]:
        ok(api.post(f'/api/ecritures/{eid}/valider'))
    return p,immo


def test_cloture_en_calcul_refuse_modification_registre_puis_termine(application):
    with closing(client(application)[0]) as api:
        api.timeout=25;p,immo=dossier_complet(api);avant=originaux(application,p['s'])
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE fiscal_parametres_exercice IN ACCESS EXCLUSIVE MODE'))
            f=pool.submit(api.post,f"/api/cloture/cloturer?exercice={p['a']}")
            attendre_verrou(application,f,table='fiscal_parametres_exercice')
            r=api.patch(f"/api/immobilisations/{immo['id']}",json={'notes':'Modification pendant clôture fictive497'})
            lecture=api.get(f"/api/immobilisations/{immo['id']}/tableau")
            tx.rollback();cloture=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert lecture.status_code==200,lecture.text
            assert cloture.status_code==200 and cloture.json()['resultat_net']==-5000,cloture.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        apres=originaux(application,p['s'])
        for t,lignes in avant.items():assert all(l in apres[t] for l in lignes)
        assert ok(api.get(f"/api/immobilisations/{immo['id']}/tableau"))['immobilisation']['notes']!= 'Modification pendant clôture fictive497'
        assert api.get('/api/fec/export',params={'exercice':p['a']}).status_code==200


def test_mutation_registre_en_cours_refuse_cloture_puis_reprise(application):
    with closing(client(application)[0]) as api:
        api.timeout=25;p,immo=dossier_complet(api)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE immobilisations IN SHARE MODE'))
            f=pool.submit(api.patch,f"/api/immobilisations/{immo['id']}",json={'notes':'Modification confirmée fictive497'})
            attendre_verrou(application,f,table='immobilisations')
            r=api.post(f"/api/cloture/cloturer?exercice={p['a']}")
            tx.rollback();mutation=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert mutation.status_code==200,mutation.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        r=api.post(f"/api/cloture/cloturer?exercice={p['a']}")
        assert r.status_code==200 and r.json()['resultat_net']==-5000,r.text


@pytest.mark.parametrize('operation',['creation','patch','delete','payer','sortie','unitaire','lot','preparation','reclasser','reconstituer','corriger'])
def test_toutes_mutations_http_et_preparation_respectent_verrou_registre(application,operation):
    with closing(client(application)[0]) as api:
        p,immo=dossier_complet(api);iid=immo['id'];a=p['a'];avant=empreintes_tables(application['engine'])
        with application['engine'].connect() as c:
            tx=c.begin()
            try:
                c.execute(text(VERROU),{'cle':f"hisabpro:registre-immobilisations:{p['s']}"})
                if operation=='creation':r=api.post('/api/immobilisations',params={'generer_ecriture':False},json=acquisition(a))
                elif operation=='patch':r=api.patch(f'/api/immobilisations/{iid}',json={'notes':'Refus497'})
                elif operation=='delete':r=api.delete(f'/api/immobilisations/{iid}')
                elif operation=='payer':r=api.post(f'/api/immobilisations/{iid}/payer',json={'date_paiement':f'{a}-12-31'})
                elif operation=='sortie':r=api.post(f'/api/immobilisations/{iid}/sortie',json={'date_sortie':f'{a}-12-31','type_sortie':'rebut'})
                elif operation in {'unitaire','lot'}:r=generer(api,operation,a,iid)
                elif operation=='preparation':r=api.post('/api/cloture/generer-dotations',params={'exercice':a})
                else:
                    suffixe={'reclasser':'reclasser','reconstituer':'reconstituer-acquisitions','corriger':'corriger-amortissements'}[operation]
                    payload={'exercice':a,**({'immo_ids':[iid]} if operation=='corriger' else {'items':[]})}
                    r=api.post('/api/immobilisations/reconciliation-historique/'+suffixe,json=payload)
                assert r.status_code==409 and "clôture ou d'immobilisations" in r.text,r.text
                assert api.get(f'/api/immobilisations/{iid}/tableau').status_code==200
                apres=empreintes_tables(application['engine'])
                assert {k:v for k,v in apres.items() if k!='audit_actions'}=={k:v for k,v in avant.items() if k!='audit_actions'}
            finally:tx.rollback()
        assert api.patch(f'/api/immobilisations/{iid}',json={'notes':'Après libération497'}).status_code==200


def test_autre_societe_disponible_et_creations_autre_exercice_aussi_protegees(application):
    with closing(client(application)[0]) as a,closing(client(application)[0]) as b:
        p,immo=dossier_complet(a);q,autre=dossier_complet(b)
        with application['engine'].connect() as c:
            tx=c.begin()
            try:
                c.execute(text(VERROU),{'cle':f"hisabpro:registre-immobilisations:{p['s']}"})
                assert a.post('/api/immobilisations',json=acquisition(date.today().year)).status_code==409
                assert b.patch(f"/api/immobilisations/{autre['id']}",json={'notes':'Société indépendante497'}).status_code==200
                r=b.post(f"/api/cloture/cloturer?exercice={q['a']}")
                assert r.status_code==200 and r.json()['resultat_net']==-5000,r.text
            finally:tx.rollback()


def test_creation_sur_registre_vide_refuse_cloture_et_refus_metier_libere_verrou(application):
    with closing(client(application)[0]) as api:
        api.timeout=25;p,_=dossier(api)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE immobilisations IN SHARE MODE'))
            f=pool.submit(api.post,'/api/immobilisations',json=acquisition(p['a']))
            attendre_verrou(application,f,table='immobilisations')
            r=api.post(f"/api/cloture/cloturer?exercice={p['a']}")
            tx.rollback();creation=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert creation.status_code==201,creation.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        r=api.post(f"/api/cloture/cloturer?exercice={p['a']}")
        assert r.status_code==400 and 'brouillon' in r.text.lower(),r.text
        assert api.patch(f"/api/immobilisations/{creation.json()['id']}",json={'notes':'Reprise après refus497'}).status_code==200
