"""SQL100 et API réelle sous LOGIN non propriétaire ; exclusivement nonce."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4
import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_ras_tva_capture_isole import (
    application as application099,application098,application097,application093,
    application092,application091,application090,application089,application087,migration)
from test_avances_salaries_isole import appliquer
from recette_restauration_consolidee_084 import empreintes_tables
from test_restauration_runtime_acl_089 import catalogue_acl
from test_ras_lecture_conservation import client
from test_ajustements_inventaire_isole import exercice,donnees
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_journal_cloture_concurrente_isole import moteur
from test_e2e_annee_connectee_isole import ORACLE as PROFIL
from test_e2e_prorata_inventaire_isole import ecriture,photo

PATH='/api/cloture/reprises-provisions'


@pytest.fixture(scope='module')
def application(application099):
    app=application099
    with closing(client(app)[0]) as api:
        r=api.get(PATH);assert r.status_code==503 and '100' in r.text
    avant=empreintes_tables(app['engine']);acl=catalogue_acl(app['engine'])
    appliquer(app,'100_reprises_provisions.sql')
    apres=empreintes_tables(app['engine']);droits=catalogue_acl(app['engine'])
    assert all(apres[k]==v for k,v in avant.items())
    assert all(all(v in droits[k] for v in vs) for k,vs in acl.items())
    appliquer(app,'100_reprises_provisions.sql')
    assert empreintes_tables(app['engine'])==apres and catalogue_acl(app['engine'])==droits
    yield app


def dotation(api,type_='provision_risque',charge='6195',provision='1518',valider=True):
    if not any(e['annee']==2025 for e in ok(api.get('/api/exercices'))):exercice(api)
    a=ok(api.post('/api/cloture/ajustements?exercice=2025',json=donnees(type_,charge,provision,montant='1000',libelle='Dotation fictive615')))
    if valider:ok(api.post(f"/api/ecritures/{a['ecriture_id']}/valider"))
    return a


def demande(montant='400.00',**kw):
    return {'date':'2026-02-01','montant':montant,'justification':'Risque fictif partiellement sans objet',**kw}


def corps(api,aid,data=None):
    data=data or demande()
    a=ok(api.post(f'{PATH}/{aid}/apercu',json=data))
    return {**data,'cle':str(uuid4()),'empreinte':a['empreinte'],'mouvements_verifies':True}


def creer(api,aid,data=None):
    return ok(api.post(f'{PATH}/{aid}',json=corps(api,aid,data)))


def test_615_partiels_reservations_validation_annulation_idempotence(application):
    with closing(client(application)[0]) as api:
        a=dotation(api);aid=a['id'];avant=donnees_metier(application)
        c=corps(api,aid)
        assert donnees_metier(application)==avant
        s=ok(api.post(f'{PATH}/{aid}',json=c));r=s['reprises'][0]
        assert (s['disponible'],s['reservations_brouillons'],s['reprises_validees'])==('600.00','400.00','0.00')
        assert ok(api.post(f'{PATH}/{aid}',json=c))==s
        assert api.post(f'{PATH}/{aid}',json={**c,'montant':'200'}).status_code==409
        ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider"))
        s=creer(api,aid,demande('200'));r2=s['reprises'][0]
        assert (s['disponible'],s['reservations_brouillons'],s['reprises_validees'])==('400.00','200.00','400.00')
        ann={'date':'2026-02-02','motif':'Justificatif fictif corrigé'}
        s=ok(api.post(f"{PATH}/{aid}/{r['id']}/annuler",json=ann));n=next(x for x in s['reprises'] if x['id']==r['id'])
        assert s['disponible']=='400.00' and n['inverse_id']
        assert ok(api.post(f"{PATH}/{aid}/{r['id']}/annuler",json=ann))==s
        assert api.post(f"{PATH}/{aid}/{r['id']}/annuler",json={**ann,'motif':'Autre'}).status_code==409
        # Chronologie OD : valider le second brouillon du 01 avant l'inverse du 02.
        ok(api.post(f"/api/ecritures/{r2['ecriture_id']}/valider"))
        ok(api.post(f"/api/ecritures/{n['inverse_id']}/valider"))
        s=ok(api.get(f'{PATH}/{aid}'))
        assert (s['disponible'],s['reprises_validees'],s['reservations_brouillons'])==('800.00','200.00','0.00')
        assert api.post(f'{PATH}/{aid}/apercu',json=demande('800.01')).status_code==409
        with application['engine'].connect() as db:
            ls=db.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:e ORDER BY compte'),{'e':r2['ecriture_id']}).all()
            assert ls==[('1518',Decimal(200),Decimal(0)),('7195',Decimal(0),Decimal(200))]
            assert db.scalar(text('SELECT montant FROM ajustements_inventaire WHERE id=:a'),{'a':aid})==Decimal(1000)


@pytest.mark.parametrize('valeur',[True,'NaN','Infinity','-Infinity','0','-1','0.001','10000000000000000'])
def test_615_montants_refuses_sans_mutation(application,valeur):
    with closing(client(application)[0]) as api:
        a=dotation(api);avant=donnees_metier(application)
        assert api.post(f"{PATH}/{a['id']}/apercu",json=demande(valeur)).status_code==422
        assert donnees_metier(application)==avant


@pytest.mark.parametrize('type_,charge,provision,produit',[
    ('provision_risque','6393','1518','7393'),('provision_risque','6595','4501','7595'),
    ('depreciation_client','61964','3942','7196'),('depreciation_client','65963','3942','7596'),
    ('depreciation_stock','61961','3911','7196')])
def test_615_natures_qualifiees(application,type_,charge,provision,produit):
    with closing(client(application)[0]) as api:
        a=dotation(api,type_,charge,provision)
        s=creer(api,a['id']);assert s['compte_reprise']==produit


def test_615_sources_non_qualifiees_et_apercu_perime(application):
    with closing(client(application)[0]) as api:
        a=dotation(api,valider=False)
        assert 'validée' in ok(api.get(f"{PATH}/{a['id']}"))['diagnostic']
        assert api.post(f"{PATH}/{a['id']}/apercu",json=demande()).status_code==409
        a=dotation(api,charge='6125')
        assert 'qualifiée' in ok(api.get(f"{PATH}/{a['id']}"))['diagnostic']
        assert api.post(f"{PATH}/{a['id']}/apercu",json=demande()).status_code==409
        a=dotation(api);aid=a['id'];c=corps(api,aid)
        creer(api,aid,demande('100'))
        assert api.post(f'{PATH}/{aid}',json=c).status_code==409
        assert api.post(f'{PATH}/{aid}/apercu',json=demande(date='2025-01-01')).status_code==422
        assert api.post(f'{PATH}/{aid}/apercu',json=demande(date='2027-01-01')).status_code==404


def test_615_journal_ne_modifie_ni_ne_detruit_le_registre(application):
    with closing(client(application)[0]) as api:
        a=dotation(api);s=creer(api,a['id']);r=s['reprises'][0]
        s=ok(api.post(f"{PATH}/{a['id']}/{r['id']}/annuler",json={'date':'2026-02-02','motif':'Fictif'}))
        for eid in [a['ecriture_id'],r['ecriture_id'],s['reprises'][0]['inverse_id']]:
            avant=donnees_metier(application)
            assert api.patch(f'/api/ecritures/{eid}',json={'libelle':'Interdit'}).status_code==409
            assert api.delete(f'/api/ecritures/{eid}').status_code==409
            assert api.post(f'/api/ecritures/{eid}/contrepasser',json={'date_correction':'2026-02-03','motif':'Interdit'}).status_code==409
            assert donnees_metier(application)==avant
        # Les deux brouillons doivent être validés avant de libérer leur réservation.
        inv=s['reprises'][0]['inverse_id']
        assert api.post(f'/api/ecritures/{inv}/valider').status_code==409
        assert ok(api.get(f"{PATH}/{a['id']}"))['disponible']=='600.00'
        lot=ok(api.post('/api/ecritures/valider-lot',json={'ids':[inv,r['ecriture_id']]}))
        assert lot['nb_validees']==2 and lot['nb_refusees']==0
        assert ok(api.get(f"{PATH}/{a['id']}"))['disponible']=='1000.00'


def test_615_concurrence_capacite_et_meme_cle(application):
    with closing(client(application)[0]) as api:
        a=dotation(api);aid=a['id'];c1=corps(api,aid,demande('600'));c2=corps(api,aid,demande('600'))
        url=api.base_url;headers=dict(api.headers)
        def poster(c):
            with httpx.Client(base_url=url,headers=headers,timeout=25) as c_api:return c_api.post(f'{PATH}/{aid}',json=c)
        with ThreadPoolExecutor(2) as pool:rs=list(pool.map(poster,[c1,c2]))
        assert sorted(r.status_code for r in rs)==[200,409],[(r.status_code,r.text) for r in rs]
        assert ok(api.get(f'{PATH}/{aid}'))['disponible']=='400.00'
        a=dotation(api);aid=a['id'];c1=corps(api,aid)
        with ThreadPoolExecutor(2) as pool:rs=list(pool.map(poster,[c1,c1]))
        assert [r.status_code for r in rs]==[200,200],[(r.status_code,r.text) for r in rs]
        assert len(ok(api.get(f'{PATH}/{aid}'))['reprises'])==1


def test_615_societes_et_lecture(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        a=dotation(api);aid=a['id'];c=corps(api,aid)
        assert autre.get(f'{PATH}/{aid}').status_code==404
        assert autre.post(f'{PATH}/{aid}',json=c).status_code==404
        email='lecture615-'+uuid4().hex[:8]+'@example.com';password='Fictif615!Motdepasse'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecture615','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        with httpx.Client(base_url=application['api_url']) as lecteur:
            token=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
            lecteur.headers['Authorization']='Bearer '+token
            assert lecteur.get(PATH).status_code==200
            assert lecteur.post(f'{PATH}/{aid}/apercu',json=demande()).status_code==200
            assert lecteur.post(f'{PATH}/{aid}',json=c).status_code==403


def test_615_droits_sql_immutabilite_rejeu(application):
    with closing(client(application)[0]) as api:
        a=dotation(api);s=creer(api,a['id']);r=s['reprises'][0];engine=moteur(application)
        try:
            for sql in ['UPDATE reprises_provisions SET montant=1 WHERE id=:r',
                'DELETE FROM reprises_provisions WHERE id=:r','TRUNCATE reprises_provisions CASCADE',
                'UPDATE ecritures SET libelle=\'Interdit\' WHERE id=:e',
                'DELETE FROM lignes_ecriture WHERE ecriture_id=:e',
                'UPDATE ajustements_inventaire SET montant=2 WHERE id=:a']:
                with engine.connect() as db:
                    tx=db.begin()
                    try:
                        with pytest.raises(DBAPIError):db.execute(text(sql),{'r':r['id'],'e':r['ecriture_id'],'a':a['id']})
                    finally:tx.rollback()
        finally:engine.dispose()
        avant=donnees_metier(application)
        appliquer(application,'100_reprises_provisions.sql')
        assert donnees_metier(application)==avant


def test_615_source_close_reprise_et_annulation_en_periode_ouverte(application):
    with closing(client(application)[0]) as api:
        exercice(api)
        ok(api.patch('/api/societe/moi',json={'forme_juridique':'SARL','regime_fiscal':'is','exercice_debut':2020,'capital_social':20000}))
        ok(api.put('/api/fiscalite/is/2025/parametres',json=PROFIL['profil']['parametres_is']))
        ecriture(api,'2025-01-02',[('5141','20000',0),('1111',0,'20000')],'CAPITAL-FICTIF615')
        a=dotation(api);source=photo(application,[a['ecriture_id']])
        clos=ok(api.post('/api/cloture/cloturer?exercice=2025'))
        assert Decimal(str(clos['resultat_net']))==Decimal('-4000')
        assert api.post(f"{PATH}/{a['id']}/apercu",json=demande(date='2025-12-31')).status_code==423
        s=creer(api,a['id']);r=s['reprises'][0]
        ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider"))
        s=ok(api.post(f"{PATH}/{a['id']}/{r['id']}/annuler",json={'date':'2026-02-02','motif':'Fictif après clôture source'}))
        ok(api.post(f"/api/ecritures/{s['reprises'][0]['inverse_id']}/valider"))
        assert ok(api.get(f"{PATH}/{a['id']}"))['disponible']=='1000.00'
        assert photo(application,[a['ecriture_id']])==source
        etats=ok(api.get('/api/etats/liasse/2026'))['etats']
        assert etats['bilan']['equilibre'] and Decimal(str(etats['cpc']['resultat_net']))==0


def test_615_periode_fermee_aucune_mutation(application):
    with closing(client(application)[0]) as api:
        a=dotation(api);aid=a['id'];c=corps(api,aid)
        ok(api.patch('/api/exercices/2026/periodes/2',json={'statut':'fermee'}))
        avant=donnees_metier(application)
        assert api.post(f'{PATH}/{aid}/apercu',json=demande()).status_code==423
        assert api.post(f'{PATH}/{aid}',json=c).status_code==423
        assert donnees_metier(application)==avant
        ok(api.patch('/api/exercices/2026/periodes/2',json={'statut':'ouverte'}))
        s=creer(api,aid);r=s['reprises'][0]
        ok(api.patch('/api/exercices/2026/periodes/3',json={'statut':'fermee'}))
        avant=donnees_metier(application)
        assert api.post(f"{PATH}/{aid}/{r['id']}/annuler",json={'date':'2026-03-01','motif':'Fictif'}).status_code==423
        assert donnees_metier(application)==avant


@pytest.mark.parametrize('operation',['creation','annulation'])
def test_615_cloture_concurrente_refus409_et_reprise(application,operation):
    with closing(client(application)[0]) as api:
        a=dotation(api);aid=a['id'];c=corps(api,aid)
        if operation=='annulation':
            s=ok(api.post(f'{PATH}/{aid}',json=c));r=s['reprises'][0]
        sid=ok(api.get('/api/societe/moi'))['id'];avant=donnees_metier(application)
        with application['engine'].connect() as db:
            tx=db.begin()
            try:
                db.execute(text('SELECT public.hisabpro_verrou_tva_cloture(:s,2026,true)'),{'s':sid})
                if operation=='creation':refus=api.post(f'{PATH}/{aid}',json=c)
                else:refus=api.post(f"{PATH}/{aid}/{r['id']}/annuler",json={'date':'2026-02-02','motif':'Fictif'})
                assert refus.status_code==409,refus.text
                assert donnees_metier(application)==avant
            finally:tx.rollback()
        if operation=='creation':ok(api.post(f'{PATH}/{aid}',json=c))
        else:ok(api.post(f"{PATH}/{aid}/{r['id']}/annuler",json={'date':'2026-02-02','motif':'Fictif'}))


@pytest.mark.parametrize('anomalie',['orpheline','montant_nan','montant_contradictoire','deja_contrepassable'])
def test_615_anomalie_historique_visible_sans_bloquer_les_autres_sources(application,anomalie):
    with closing(client(application)[0]) as api:
        saine=dotation(api);a=dotation(api)
        if anomalie=='deja_contrepassable':
            ok(api.post(f"/api/ecritures/{a['ecriture_id']}/contrepasser",json={'date_correction':'2026-02-01','motif':'Inverse fictif historique'}))
        else:
            # Injection du seul dossier historique fictif, jamais d'une pièce définitive.
            with application['engine'].begin() as db:
                if anomalie=='orpheline':sql='UPDATE ajustements_inventaire SET ecriture_id=NULL WHERE id=:a'
                elif anomalie=='montant_nan':sql="UPDATE ajustements_inventaire SET montant='NaN'::numeric WHERE id=:a"
                else:sql='UPDATE ajustements_inventaire SET montant=900 WHERE id=:a'
                db.execute(text(sql),{'a':a['id']})
        avant=donnees_metier(application)
        s=ok(api.get(PATH));d=next(x for x in s['items'] if x['id']==a['id'])
        assert d['diagnostic'] and d['compte_reprise'] is None
        if anomalie=='montant_nan':assert d['disponible'] is None and d['dotation'] is None
        assert api.post(f"{PATH}/{a['id']}/apercu",json=demande()).status_code==409
        assert donnees_metier(application)==avant
        assert ok(api.post(f"{PATH}/{saine['id']}/apercu",json=demande()))['lignes'][1]['compte']=='7195'
