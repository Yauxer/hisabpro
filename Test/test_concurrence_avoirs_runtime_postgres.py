"""Courses contrôlées : deux JWT/API concurrents sur PG nonce, sans mock métier."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import time

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from test_permissions_acomptes_avoirs_postgres import (
    cible, cible_documents, dossier, valider, originaux, conserver, ok,
)


def attendre_bloques(cible,n,futures):
    limite=time.monotonic()+10
    while time.monotonic()<limite:
        cible['garde']()
        with cible['owner'].connect() as db:
            count=db.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() "
                "AND usename='hisabpro' AND wait_event_type='Lock' AND query ILIKE '%avoirs%'"))
        if count>=n:
            return
        for f in futures:
            if f.done():
                r=f.result()
                raise AssertionError(('Requête terminée avant le verrou attendu',r.status_code,r.text))
        time.sleep(0.025)
    raise AssertionError(f'{n}attentes SQL nonobservées')


def course(cible,aid,premier,second):
    app=cible['client'].app
    token=cible['client'].headers['Authorization']
    def poster(operation):
        chemin,body=operation
        with TestClient(app) as api:
            return api.post(chemin,json=body,headers={'Authorization':token})
    cible['garde']()
    with cible['owner'].connect() as verrou:
        transaction=verrou.begin()
        verrou.execute(text('SELECT id FROM avoirs WHERE id=:id FOR UPDATE'),{'id':aid})
        with ThreadPoolExecutor(max_workers=2) as pool:
            try:
                un=pool.submit(poster,premier)
                attendre_bloques(cible,1,[un])
                deux=pool.submit(poster,second)
                attendre_bloques(cible,2,[un,deux])
            finally:
                # Libérer avant la sortie du pool, même si une assertion échoue.
                transaction.rollback()
            return un.result(timeout=30),deux.result(timeout=30)


@pytest.mark.parametrize('sens',['vente','achat'])
@pytest.mark.parametrize('cas',['double_comptabilisation','double_annulation',
    'consommation_puis_annulation','annulation_puis_consommation'])
def test_avoir_concurrent_unique_coherent_et_origines_conservees(cible,sens,cas):
    api,user,tier,fs=dossier(cible,sens)
    jour=date.today().isoformat();sid=user['societe_id']
    ok(api.post('/api/reglements',json={'facture_id':fs[0]['id'],'tiers':tier['nom'],
        'date':jour,'montant':120,'mode':'virement','comptabiliser':True}),201)
    valider(api)
    a=ok(api.post('/api/avoirs',json={'facture_id':fs[0]['id'],'date':jour,
        'motif':'Concurrence fictive438','retour_stock':False,
        'lignes':[{'facture_ligne_id':fs[0]['lignes'][0]['id'],'quantite':0.5}]}),201)
    aid=a['id']
    comptabiliser=(f'/api/avoirs/{aid}/comptabiliser',None)
    annuler=(f'/api/avoirs/{aid}/annuler',None)
    consommer=(f'/api/avoirs/{aid}/utiliser',{'type_utilisation':'imputation',
        'facture_id':fs[1]['id'],'date_utilisation':jour,'montant':30})
    if cas!='double_comptabilisation':
        ok(api.post(comptabiliser[0]));valider(api)
    avant=originaux(cible,sid)
    premier,second={'double_comptabilisation':(comptabiliser,comptabiliser),
        'double_annulation':(annuler,annuler),
        'consommation_puis_annulation':(consommer,annuler),
        'annulation_puis_consommation':(annuler,consommer)}[cas]
    rs=course(cible,aid,premier,second)
    with cible['runtime'].connect() as db:
        diagnostic={
            'statut':db.scalar(text('SELECT statut FROM avoirs WHERE id=:id'),{'id':aid}),
            'av':db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid AND reference=:ref'),
                {'sid':sid,'ref':a['numero']}),
            'ann':db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid AND reference=:ref'),
                {'sid':sid,'ref':'ANN-'+a['numero']}),
            'usages_actifs':db.scalar(text("SELECT count(*) FROM utilisations_avoirs WHERE avoir_id=:id AND statut='active'"),{'id':aid}),
        }
    codes=[r.status_code for r in rs]
    assert codes==([200,200] if cas=='double_annulation' else [200,409]),(codes,diagnostic)
    assert diagnostic['av']==1,diagnostic
    if cas=='double_annulation':
        assert rs[0].json()['ecriture_annulation_id']==rs[1].json()['ecriture_annulation_id'],diagnostic
    if cas in {'double_annulation','annulation_puis_consommation'}:
        assert diagnostic['ann']==1 and diagnostic['statut']=='annule',diagnostic
    else:
        assert diagnostic['ann']==0 and diagnostic['statut']!='annule',diagnostic
    assert diagnostic['usages_actifs']==(1 if cas=='consommation_puis_annulation' else 0),diagnostic
    conserver(cible,sid,avant)
    valider(api);conserver(cible,sid,avant)
    if cas=='consommation_puis_annulation':
        row=next(r for r in ok(api.get('/api/avoirs',params={'exercice':date.today().year})) if r['id']==aid)
        assert row['montant_disponible']==30 and row['montant_utilise']==30
