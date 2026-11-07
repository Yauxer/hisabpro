"""Profil exclusivement Personnel, PostgreSQL natif nonce et vrais appels HTTP."""
from contextlib import closing
from pathlib import Path
import pytest,httpx
from sqlalchemy import text
from test_personnel_workflow877_isole import (
    application875,application873,application093,application092,application091,application090,application089,
    application087,migration,client,ok,role_client,grant,activer,CAPS,W,P,creation,decision,soumettre,comptabilite)
from test_personnel879_donnees_isole import application as application108,application107
from recette_restauration_consolidee_084 import empreintes_tables
from postgres_isole import verifier_cible_isolee

R=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def application(application108):
    app=application108;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    # Aucun profil nouveau attribuable avant le contrôle de migration.
    with closing(client(app)[0]) as api:
        r=api.post('/api/utilisateurs',json={'nom':'Profil avant migration fictif','email':'avant881@example.com','mot_de_passe':'Mot-Fictif-881!','role':'personnel'})
        assert r.status_code==503,r.text
    avant=empreintes_tables(app['engine'])
    for _ in range(2):
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/109_personnel_profil_cloisonne.sql').read_text(encoding='utf8'))
        finally:raw.close()
    assert empreintes_tables(app['engine'])==avant
    yield app

@pytest.fixture
def equipe881(application):
    with closing(client(application)[0]) as admin:
        perso,u,email,secret=role_client(application,admin,'personnel')
        with closing(perso):
            yield {'a':admin,'p':perso,'uid':u['id'],'email':email,'secret':secret}

def autoriser(eq):
    for cap in CAPS:grant(eq['a'],eq['uid'],cap)
    if ok(eq['a'].get(P+'/acces'))['mode']!='protege':activer(eq['a'])

def test_881_profil_sans_droit_implicite_et_contexte_minimal(application,equipe881):
    eq=equipe881;p=eq['p']
    assert ok(p.get('/api/auth/me'))['role']=='personnel'
    ctx=ok(p.get(W+'/contexte'));assert set(ctx)=={'societe','module_actif'} and set(ctx['societe'])=={'id','raison_sociale'}
    assert p.get(W).status_code==409
    activer(eq['a'])
    assert ok(p.get(P+'/acces'))['capacites']==[]
    assert p.get(W).status_code==403 and p.post(W,json=creation()).status_code==403
    autoriser(eq)
    avant=comptabilite(application,ctx['societe']['id'])
    e=ok(p.post(W,json=creation('FICTIF881')),201);i=e['demande']['id']
    soumettre(p,i,0)
    assert p.post(f'{W}/demandes/{i}/approuver',json=decision(0)).status_code==403
    aid=ok(eq['a'].get('/api/auth/me'))['id']
    for cap in CAPS:grant(eq['a'],aid,cap)
    ok(eq['a'].post(f'{W}/demandes/{i}/approuver',json=decision(0)))
    assert ok(p.get(f'{W}/{e["employe_id"]}'))['statut']=='ACTIF'
    assert comptabilite(application,ctx['societe']['id'])==avant

@pytest.mark.parametrize('methode,chemin',[
 ('GET','/api/factures?exercice=2026'),('GET','/api/ecritures?exercice=2026'),('POST','/api/ecritures'),
 ('GET','/api/tiers'),('GET','/api/articles'),('GET','/api/plan-comptable'),('GET','/api/exercices'),
 ('GET','/api/societe/moi'),('PATCH','/api/societe/moi'),('GET','/api/societe/modules'),
 ('GET','/api/utilisateurs'),('POST','/api/utilisateurs'),('GET','/api/production/controle'),
 ('GET','/api/employes'),('GET','/api/employes/avances'),('POST','/api/employes'),
 ('GET',P+'/habilitations'),('POST',P+'/habilitations'),('POST','/api/societes/nouvelle')])
def test_881_refus_direct_autres_modules(equipe881,methode,chemin):
    r=equipe881['p'].request(methode,chemin,json={} if methode!='GET' else None)
    assert r.status_code==403,(chemin,r.status_code,r.text)

def test_881_role_modifie_relu_sans_attendre_jwt(application,equipe881):
    eq=equipe881;p=eq['p'];a=eq['a']
    ok(a.patch(f'/api/utilisateurs/{eq["uid"]}',json={'role':'comptable'}))
    assert p.get('/api/factures?exercice=2026').status_code==200
    ok(a.patch(f'/api/utilisateurs/{eq["uid"]}',json={'role':'personnel'}))
    assert p.get('/api/factures').status_code==403
    assert ok(p.get('/api/auth/me'))['role']=='personnel'
    ok(a.patch(f'/api/utilisateurs/{eq["uid"]}',json={'actif':False}))
    assert p.get('/api/auth/me').status_code==401

def test_881_societe_secondaire_role_propre_et_revocation(application,equipe881):
    eq=equipe881;a=eq['a'];p=eq['p'];sid=ok(a.get('/api/auth/me'))['societe_id']
    with closing(client(application)[0]) as autre:
        uid=ok(autre.get('/api/auth/me'))['id']
        ok(a.post(f'/api/societes/{sid}/inviter',params={'email':ok(autre.get('/api/auth/me'))['email'],'role':'personnel'}))
        bascule=ok(autre.post(f'/api/societes/switcher/{sid}'))
        with httpx.Client(base_url=application['api_url'],headers={'Authorization':'Bearer '+bascule['access_token']},timeout=30) as invite:
            assert ok(invite.get('/api/auth/me'))['role']=='personnel'
            assert invite.get('/api/factures').status_code==403
            ok(a.patch(f'/api/utilisateurs/{uid}',json={'actif':False}))
            assert invite.get('/api/auth/me').status_code==403
        # Son rôle principal indépendant n'a pas été diminué.
        assert ok(autre.get('/api/auth/me'))['role']=='admin'

def test_881_habilitation_revoquee_et_module_desactive_effectifs(equipe881):
    eq=equipe881;autoriser(eq);p=eq['p'];a=eq['a']
    assert p.get(W).status_code==200
    caps=ok(a.get(P+'/habilitations'))
    h=next(x for x in caps if x['utilisateur_id']==eq['uid'] and x['capacite']=='personnel.proposer')
    ok(a.post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Révocation fictive881'}))
    assert p.post(W,json=creation()).status_code==403 and p.get(W).status_code==200
    ok(a.patch('/api/societe/modules',json={'module':'paie_grh','actif':False}))
    assert p.get(W).status_code==403 and not ok(p.get(W+'/contexte'))['module_actif']

def test_881_mot_de_passe_personnel_et_jeton_revoque(application,equipe881):
    eq=equipe881;p=eq['p'];nouveau='Secret-Fictif-Renouvele-881!'
    r=p.post('/api/auth/mot-de-passe',json={'mot_de_passe_actuel':eq['secret'],'nouveau_mot_de_passe':nouveau})
    assert r.status_code==204,r.text
    assert p.get('/api/auth/me').status_code==401
    with httpx.Client(base_url=application['api_url'],timeout=30) as api:
        assert api.post('/api/auth/login',json={'email':eq['email'],'password':eq['secret']}).status_code==401
        data=ok(api.post('/api/auth/login',json={'email':eq['email'],'password':nouveau}))
        api.headers['Authorization']='Bearer '+data['access_token']
        assert ok(api.get('/api/auth/me'))['role']=='personnel' and api.get('/api/ecritures?exercice=2026').status_code==403

