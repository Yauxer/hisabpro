"""Assistants historiques : choix explicites, HTTP/PG nonce, sources conservées."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor,TimeoutError
from datetime import date
import pytest
from sqlalchemy import text
from test_registre_immobilisations_cloture_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,acquisition,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_dotations_concurrentes_isole import generer
from test_avances_salaries_isole import originaux
from test_tva_verrou_exercice_isole import attendre_verrou


def preparer(api,operation):
    annee=date.today().year-2
    ok(api.post('/api/exercices',json={'annee':annee,'date_debut':f'{annee}-01-01','date_fin':f'{annee}-12-31'}),201)
    immo=ok(api.post('/api/immobilisations',params={'generer_ecriture':operation!='reconstituer'},json=acquisition(annee)),201)
    if immo['ecriture_acquisition_id']:ok(api.post(f"/api/ecritures/{immo['ecriture_acquisition_id']}/valider"))
    return annee,immo,ok(api.get('/api/societe/moi'))['id']


def reconcilier(api,operation,annee,iid):
    if operation=='reclasser':suffixe='reclasser';p={'exercice':annee,'items':[{'immo_id':iid,'categorie_cible':'Matériel de bureau'}]}
    elif operation=='reconstituer':suffixe='reconstituer-acquisitions';p={'exercice':annee,'items':[{'immo_id':iid,'mode':'dette_acquisition','compte_contrepartie':'4481'}]}
    else:suffixe='corriger-amortissements';p={'exercice':annee,'immo_ids':[iid]}
    return api.post('/api/immobilisations/reconciliation-historique/'+suffixe,json=p)


@pytest.mark.parametrize('operation',['reclasser','reconstituer','corriger'])
def test_deux_assistants_simultanes_ne_dupliquent_pas_lecriture(application,operation):
    with closing(client(application)[0]) as api:
        api.timeout=25;annee,immo,sid=preparer(api,operation);iid=immo['id'];avant=originaux(application,sid)
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE lignes_ecriture IN SHARE MODE'))
            f=pool.submit(reconcilier,api,operation,annee,iid);attendre_verrou(application,f,table='lignes_ecriture')
            g=pool.submit(reconcilier,api,operation,annee,iid)
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=25)
            if r2 is None:r2=g.result(timeout=25)
            assert r1.status_code==200,r1.text
            assert r2.status_code==409,r2.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        prefixe={'reclasser':'RECLASS-IMMO','reconstituer':'RECON-ACQ','corriger':'RECON-AMORT'}[operation]
        with application['engine'].connect() as c:
            ids=c.execute(text('SELECT id FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':sid,'r':f'{prefixe}-{annee}-{iid}'}).scalars().all()
            assert len(ids)==1
            lignes=c.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:id ORDER BY compte'),{'id':ids[0]}).all()
            attendu={'reclasser':[('2352',10000,0),('2355',0,10000)],
                'reconstituer':[('2355',10000,0),('34551',2000,0),('4481',0,12000)],
                'corriger':[('28355',0,2000),('61935',2000,0)]}[operation]
            assert lignes==attendu
        apres=originaux(application,sid)
        for t,lignes in avant.items():assert all(l in apres[t] for l in lignes)
        r=reconcilier(api,operation,annee,iid)
        assert r.status_code==(200 if operation=='corriger' else 409),r.text
        if operation=='corriger':assert r.json()['nb_ecritures']==0
        assert originaux(application,sid)==apres


@pytest.mark.parametrize('action',['plan','generation'])
def test_correction_presente_gele_plan_et_refuse_dotation_automatique_en_double(application,action):
    with closing(client(application)[0]) as api:
        annee,immo,sid=preparer(api,'corriger');iid=immo['id']
        ok(reconcilier(api,'corriger',annee,iid));avant=originaux(application,sid)
        r=(api.patch(f'/api/immobilisations/{iid}',json={'duree_amort':10}) if action=='plan'
           else generer(api,'unitaire',annee,iid))
        assert r.status_code==409,r.text
        assert originaux(application,sid)==avant
        # Une correction de N ne doit pas interdire une dotation indépendante de N+1.
        ok(api.post('/api/exercices',json={'annee':annee+1,'date_debut':f'{annee+1}-01-01','date_fin':f'{annee+1}-12-31'}),201)
        assert ok(generer(api,'unitaire',annee+1,iid))['dotation']==2000


@pytest.mark.parametrize('operation',['reclasser','reconstituer','corriger'])
@pytest.mark.parametrize('premier',['assistant','mutation'])
def test_assistant_et_modification_courante_se_refusent_mutuellement(application,operation,premier):
    with closing(client(application)[0]) as api:
        api.timeout=25;annee,immo,sid=preparer(api,operation);iid=immo['id']
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(1)
        try:
            table='lignes_ecriture' if premier=='assistant' else 'immobilisations'
            db.execute(text(f'LOCK TABLE {table} IN SHARE MODE'))
            if premier=='assistant':f=pool.submit(reconcilier,api,operation,annee,iid)
            else:f=pool.submit(api.patch,f'/api/immobilisations/{iid}',json={'notes':'Modification fictive499'})
            attendre_verrou(application,f,table=table)
            r=(api.patch(f'/api/immobilisations/{iid}',json={'notes':'Refus fictif499'}) if premier=='assistant'
               else reconcilier(api,operation,annee,iid))
            tx.rollback();r1=f.result(timeout=25)
            assert r.status_code==409,r.text
            assert r1.status_code==200,r1.text
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        if premier=='assistant':assert api.patch(f'/api/immobilisations/{iid}',json={'notes':'Reprise499'}).status_code==200
        else:assert reconcilier(api,operation,annee,iid).status_code==200


@pytest.mark.parametrize('operation',['reclasser','reconstituer'])
def test_selection_dupliquee_refusee_sans_effet(application,operation):
    with closing(client(application)[0]) as api:
        annee,immo,sid=preparer(api,operation);avant=originaux(application,sid)
        if operation=='reclasser':suffixe='reclasser';item={'immo_id':immo['id'],'categorie_cible':'Matériel de bureau'}
        else:suffixe='reconstituer-acquisitions';item={'immo_id':immo['id'],'mode':'dette_acquisition','compte_contrepartie':'4481'}
        r=api.post('/api/immobilisations/reconciliation-historique/'+suffixe,json={'exercice':annee,'items':[item,item]})
        assert r.status_code==400 and 'une seule fois' in r.text,r.text
        assert originaux(application,sid)==avant
        assert ok(api.get(f"/api/immobilisations/{immo['id']}/tableau"))['immobilisation']['compte_immo']=='2355'


def test_conflit_tardif_annule_tout_le_lot_de_reclassement(application):
    with closing(client(application)[0]) as api:
        annee,immo,sid=preparer(api,'reclasser')
        autre=ok(api.post('/api/immobilisations',json=acquisition(annee)),201)
        ok(api.post(f"/api/ecritures/{autre['ecriture_acquisition_id']}/valider"))
        avant=originaux(application,sid)
        payload={'exercice':annee,'items':[{'immo_id':i,'categorie_cible':'Matériel de bureau'} for i in [immo['id'],autre['id']]]}
        with application['engine'].connect() as c:
            tx=c.begin()
            try:
                c.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:cle,0))'),{'cle':f"hisabpro:immobilisation:{sid}:{autre['id']}"})
                r=api.post('/api/immobilisations/reconciliation-historique/reclasser',json=payload)
                assert r.status_code==409,r.text
                assert originaux(application,sid)==avant
                for i in [immo['id'],autre['id']]:
                    assert ok(api.get(f'/api/immobilisations/{i}/tableau'))['immobilisation']['compte_immo']=='2355'
            finally:tx.rollback()
        r=ok(api.post('/api/immobilisations/reconciliation-historique/reclasser',json=payload))
        assert r['nb_ecritures']==2
