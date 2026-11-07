"""1A.1 : droits réellement persistés sous LOGIN PG non propriétaire et HTTP réel."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date
from pathlib import Path
from uuid import uuid4
import time

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_permissions_tva_runtime_isole import (
    application as application093, application092, application091,
    application090, application089, application087, migration)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_paie_grh_postgres import dossier
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R = Path(__file__).resolve().parents[1]
P = '/api/employes/securite'
IDENTITE = 'personnel.lire_identite'
REMUNERATION = 'personnel.lire_remuneration'
SENSIBLE = 'personnel.lire_identifiants_sensibles'
AUDIT = 'personnel.audit_lire'


@pytest.fixture(scope='module')
def application(application093):
    app = application093
    c = app['cluster']
    assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    for nom in ['094_protection_parametres_tva_clotures.sql', '095_registre_avances_salaries.sql']:
        raw = app['engine'].raw_connection()
        try:
            raw.autocommit = True
            with raw.cursor() as cursor: cursor.execute((R/'hisabpro-backend'/nom).read_text(encoding='utf8'))
        finally: raw.close()
    avant = empreintes_tables(app['engine'])
    for _ in range(2):
        raw = app['engine'].raw_connection()
        try:
            raw.autocommit = True
            with raw.cursor() as cursor: cursor.execute((R/'hisabpro-backend/105_personnel_habilitations.sql').read_text(encoding='utf8'))
        finally: raw.close()
    apres = empreintes_tables(app['engine'])
    assert all(apres[t] == h for t, h in avant.items())
    runtime = create_engine(make_url(c['url']).set(username='hisabpro'))
    with runtime.connect() as db:
        assert db.execute(text('SELECT current_user,session_user')).one() == ('hisabpro','hisabpro')
        assert not db.scalar(text("SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls FROM pg_roles WHERE rolname=current_user"))
        assert not db.scalar(text("SELECT count(*) FROM pg_class WHERE relname LIKE 'personnel_%' AND relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)"))
    app = dict(app, personnel_runtime=runtime)
    yield app
    runtime.dispose()


def employee(api):
    return ok(api.post('/api/employes', json=dossier(numero_cnss='CNSS-FICTIF-PRIVE-873')),201)


def role_client(app, api, role='lecture'):
    email = f'personnel873-{uuid4().hex[:8]}@hisabpro-recette.example'
    secret = 'PersonnelFictif873!'
    u = ok(api.post('/api/utilisateurs', json={'nom':'Compte Personnel fictif873','email':email,
               'mot_de_passe':secret,'role':role}),201)
    lecteur = httpx.Client(base_url=app['api_url'], timeout=30)
    r = lecteur.post('/api/auth/login',json={'email':email,'password':secret})
    assert r.status_code == 200
    lecteur.headers['Authorization'] = 'Bearer '+r.json()['access_token']
    return lecteur, u, email, secret


def grant(api, uid, cap, status=201):
    return ok(api.post(P+'/habilitations',json={'utilisateur_id':uid,'capacite':cap,'motif':'Délégation fictive contrôlée873'}),status)


def activer(api, status=201):
    return ok(api.post(P+'/activation',json={'confirmation':'PROTEGER_PERSONNEL','motif':'Activation fictive contrôlée873'}),status)


def originaux(app, sid):
    with app['engine'].connect() as db:
        return {t: db.execute(text(f'SELECT row_to_json(t)::text FROM {t} t WHERE societe_id=:s ORDER BY id'),
                              {'s':sid}).scalars().all() for t in ['employes','ecritures','grh_absences','paie_referentiel_versions']}


def test_873_installation_sans_activation_et_admin_sans_droit_implicite(application):
    with closing(client(application)[0]) as api:
        e = employee(api);sid = ok(api.get('/api/auth/me'))['societe_id'];avant = originaux(application,sid)
        c = ok(api.get(P+'/acces'));assert c['schema_installe'] and c['mode']=='historique' and c['modification_historique_autorisee']
        activer(api);c = ok(api.get(P+'/acces'));assert c['mode']=='protege' and c['capacites']==[] and not c['modification_historique_autorisee']
        assert api.get('/api/employes').status_code==403
        activer(api,409)
        assert originaux(application,sid)==avant


def test_873_masques_sur_liste_simulation_et_anciens_exports(application):
    with closing(client(application)[0]) as api:
        e=employee(api);sid=ok(api.get('/api/auth/me'))['societe_id'];avant=originaux(application,sid)
        lecteur,u,_,_=role_client(application,api)
        with closing(lecteur):
            grant(api,u['id'],IDENTITE);activer(api)
            r=lecteur.get('/api/employes');assert r.status_code==200 and r.headers['cache-control']=='no-store'
            row=r.json()[0];assert row['id']==e['id'] and all(row[k] is None for k in ['salaire_brut','numero_cnss','situation_familiale','nb_enfants','personnes_charge_ir'])
            for path in ['/api/employes/cotisations?annee=2026&mois=1','/api/employes/conges','/api/employes/conges/export/pdf','/api/employes/avances','/api/employes/referentiel?annee=2026']:
                assert lecteur.get(path).status_code==403,path
            grant(api,u['id'],REMUNERATION)
            r=lecteur.get('/api/employes/cotisations',params={'annee':2026,'mois':1});assert r.status_code==200
            row=r.json()['employes'][0]['employe'];assert row['salaire_brut']==e['salaire_brut'] and row['numero_cnss'] is None
            assert 'CNSS-FICTIF-PRIVE-873' not in r.text
            assert lecteur.get('/api/employes/avances').status_code==200
            grant(api,u['id'],SENSIBLE);assert lecteur.get('/api/employes').json()[0]['numero_cnss']==e['numero_cnss']
            assert lecteur.get('/api/employes/conges').status_code==200
            r=lecteur.get('/api/employes/conges/export/pdf');assert r.status_code==200 and r.headers['cache-control']=='no-store'
            grant(api,u['id'],AUDIT);assert lecteur.get('/api/employes/referentiel?annee=2026').json()['peut_consigner'] is False
            assert ok(lecteur.get('/api/auth/me'))['role']=='lecture'
            assert lecteur.post('/api/ecritures',json={'date':date.today().isoformat(),'journal':'BQ','libelle':'Refus hors Personnel','lignes':[{'compte':'5141','debit':1},{'compte':'1111','credit':1}]}).status_code==403
        assert originaux(application,sid)==avant


def test_873_revocation_immediate_meme_session_et_historique(application):
    with closing(client(application)[0]) as api:
        employee(api);lecteur,u,_,_=role_client(application,api)
        with closing(lecteur):
            grant(api,u['id'],IDENTITE);h=grant(api,u['id'],REMUNERATION);grant(api,u['id'],REMUNERATION,409);activer(api)
            assert lecteur.get('/api/employes').json()[0]['salaire_brut'] is not None
            ok(api.post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Retrait fictif873'}))
            assert lecteur.get('/api/employes').json()[0]['salaire_brut'] is None
            assert lecteur.get('/api/employes/cotisations?annee=2026').status_code==403
            assert api.post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Doublon'}).status_code==409
            nouveau=grant(api,u['id'],REMUNERATION);assert nouveau['id']!=h['id']
            rows=ok(api.get(P+'/habilitations'));old=next(x for x in rows if x['id']==h['id']);assert old['revoquee_at'] and old['motif_revocation']=='Retrait fictif873'


@pytest.mark.parametrize('role',['lecture','comptable'])
def test_873_administration_reservee_admin(application,role):
    with closing(client(application)[0]) as api:
        lecteur,u,_,_=role_client(application,api,role)
        with closing(lecteur):
            assert lecteur.get(P+'/habilitations').status_code==403
            assert lecteur.post(P+'/habilitations',json={'utilisateur_id':u['id'],'capacite':IDENTITE,'motif':'Refus'}).status_code==403
            assert lecteur.post(P+'/activation',json={'confirmation':'PROTEGER_PERSONNEL','motif':'Refus'}).status_code==403


@pytest.mark.parametrize('payload',[{}, {'utilisateur_id':True,'capacite':IDENTITE,'motif':'x'},
    {'utilisateur_id':1,'capacite':'paie.payer','motif':'x'}, {'utilisateur_id':1,'capacite':IDENTITE,'motif':' '},
    {'utilisateur_id':1,'capacite':IDENTITE,'motif':'x'*501},
    {'utilisateur_id':1,'capacite':IDENTITE,'motif':'x','societe_id':2}])
def test_873_payload_habilitation_strict(application,payload):
    with closing(client(application)[0]) as api:
        assert api.post(P+'/habilitations',json=payload).status_code==422


def test_873_societes_invite_et_module_desactive(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        employee(api);me=ok(api.get('/api/auth/me'));b=ok(autre.get('/api/auth/me'))
        grant(api,b['id'],IDENTITE,404)
        email=ok(autre.get('/api/utilisateurs'))[0]['email']
        ok(api.post(f'/api/societes/{me["societe_id"]}/inviter',params={'email':email,'role':'lecture'}))
        h=grant(api,b['id'],IDENTITE);activer(api)
        sw=ok(autre.post(f'/api/societes/switcher/{me["societe_id"]}'));headers={'Authorization':'Bearer '+sw['access_token']}
        assert autre.get('/api/employes',headers=headers).status_code==200
        # Une nouvelle invitation ne reprend pas les anciennes capacités sensibles.
        assert api.delete(f'/api/utilisateurs/{b["id"]}').status_code==204
        assert autre.get('/api/employes',headers=headers).status_code==403
        ok(api.post(f'/api/societes/{me["societe_id"]}/inviter',params={'email':email,'role':'lecture'}))
        assert autre.get('/api/employes',headers=headers).status_code==403
        ok(api.post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Nouvelle invitation : réattribution explicite'}))
        grant(api,b['id'],IDENTITE)
        assert autre.get('/api/employes',headers=headers).status_code==200
        assert autre.post(P+f'/habilitations/{h["id"]}/revoquer',headers=headers,json={'motif':'Refus invité lecture'}).status_code==403
        assert autre.get(P+'/acces').json()['mode']=='historique'
        ok(api.patch('/api/societe/modules',json={'module':'paie_grh','actif':False}))
        assert autre.get('/api/employes',headers=headers).status_code==403
        ok(api.patch('/api/societe/modules',json={'module':'paie_grh','actif':True}))
        assert autre.get('/api/employes',headers=headers).status_code==200


@pytest.mark.parametrize('cas',['creation','edition','archive','absence','decision','referentiel','avance','annulation_avance'])
def test_873_anciennes_mutations_interdites_sans_alterer_donnees(application,cas):
    with closing(client(application)[0]) as api:
        e=employee(api);sid=ok(api.get('/api/auth/me'))['societe_id'];avant=originaux(application,sid);activer(api)
        method,path,payload={
            'creation':('POST','/api/employes',dossier()),
            'edition':('PUT',f'/api/employes/{e["id"]}',dossier(salaire_brut=12345)),
            'archive':('DELETE',f'/api/employes/{e["id"]}',None),
            'absence':('POST','/api/employes/conges',{'employe_id':e['id'],'date_debut':'2026-10-01','date_fin':'2026-10-02'}),
            'decision':('PATCH','/api/employes/conges/1',{'statut':'approuve'}),
            'referentiel':('POST','/api/employes/referentiel?annee=2026',{'empreinte_attendue':'0'*64}),
            'avance':('POST','/api/employes/avances',{'employe_id':e['id'],'ligne_id':1,'motif':'Refus'}),
            'annulation_avance':('POST','/api/employes/avances/1/annuler',{'motif':'Refus'})}[cas]
        r=api.request(method,path,**({'json':payload} if payload is not None else {}));assert r.status_code==409,r.text
        assert originaux(application,sid)==avant


def test_873_double_delegation_concurrente_unique(application):
    with closing(client(application)[0]) as api:
        uid=ok(api.get('/api/auth/me'))['id']
        def envoyer(_):
            with httpx.Client(base_url=application['api_url'],headers=dict(api.headers),timeout=30) as a:
                return a.post(P+'/habilitations',json={'utilisateur_id':uid,'capacite':IDENTITE,'motif':'Concurrence fictive873'}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(envoyer,range(2)))==[201,409]
        assert len(ok(api.get(P+'/habilitations')))==1


def test_873_compte_reference_ne_peut_pas_etre_supprime(application):
    with closing(client(application)[0]) as api:
        lecteur,u,_,_=role_client(application,api);lecteur.close()
        grant(api,u['id'],IDENTITE)
        r=api.delete(f'/api/utilisateurs/{u["id"]}');assert r.status_code==409
        assert any(x['id']==u['id'] for x in ok(api.get('/api/utilisateurs')))
        ok(api.patch(f'/api/utilisateurs/{u["id"]}',json={'actif':False}))
        assert any(x['id']==u['id'] and x['actif'] is False for x in ok(api.get('/api/utilisateurs')))


def test_873_securite_sans_authentification(application):
    with httpx.Client(base_url=application['api_url']) as api:
        for path in ['/acces','/habilitations']:
            assert api.get(P+path).status_code==401
        assert api.post(P+'/activation',json={'confirmation':'PROTEGER_PERSONNEL','motif':'Refus'}).status_code==401


def test_873_sql_historique_et_activation_immutables(application):
    with closing(client(application)[0]) as api:
        me=ok(api.get('/api/auth/me'));h=grant(api,me['id'],IDENTITE);activer(api)
        for engine in [application['personnel_runtime'],application['engine']]:
            for sql in [f"DELETE FROM personnel_habilitations WHERE id={h['id']}",
                        'TRUNCATE personnel_habilitations',
                        f"UPDATE personnel_acces_societes SET motif='x' WHERE societe_id={me['societe_id']}"]:
                with engine.connect() as db:
                    with pytest.raises(DBAPIError):db.execute(text(sql))
                    db.rollback()
        assert len(ok(api.get(P+'/habilitations')))==1 and ok(api.get(P+'/acces'))['mode']=='protege'


def test_873_activation_attend_operation_historique(application):
    from services.personnel_acces_service import exiger_mutation_historique
    with closing(client(application)[0]) as api:
        me=ok(api.get('/api/auth/me'))
        with Session(application['personnel_runtime']) as db,ThreadPoolExecutor(max_workers=1) as pool:
            exiger_mutation_historique(db,me)
            future=pool.submit(activer,api)
            try:
                limite=time.monotonic()+10;bloque=False
                while time.monotonic()<limite:
                    with application['engine'].connect() as owner:
                        bloque=bool(owner.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE usename='hisabpro' AND wait_event_type='Lock' AND wait_event='advisory'")))
                    if bloque:break
                    assert not future.done();time.sleep(.02)
                assert bloque
            finally:db.rollback()
            assert future.result(timeout=20)['mode']=='protege'


def test_873_rejeu105_avec_historique_et_activation_preserves(application):
    from test_restauration_runtime_acl_089 import catalogue_acl
    with closing(client(application)[0]) as api:
        me=ok(api.get('/api/auth/me'));h=grant(api,me['id'],IDENTITE);activer(api)
        ok(api.post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Historique avant rejeu'}))
        grant(api,me['id'],IDENTITE)
        avant=empreintes_tables(application['engine']);droits=catalogue_acl(application['engine'])
        raw=application['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/105_personnel_habilitations.sql').read_text(encoding='utf8'))
        finally:raw.close()
        assert empreintes_tables(application['engine'])==avant and catalogue_acl(application['engine'])==droits
        assert ok(api.get(P+'/acces'))['mode']=='protege' and len(ok(api.get(P+'/habilitations')))==2
