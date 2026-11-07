"""API authentifiée et LOGIN PostgreSQL réels, exclusivement cluster nonce."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from database import Base, get_db
import models
from postgres_isole import cluster_isole, verifier_cible_isolee
from routers import auth, employes, utilisateurs

MIGRATION = Path(__file__).resolve().parents[1] / 'hisabpro-backend/082_paie_referentiels.sql'


@pytest.fixture(scope='module')
def laboratoire():
    with cluster_isole() as cible:
        verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        owner = create_engine(cible['url'])
        runtime = None
        try:
            Base.metadata.create_all(owner)
            with Session(owner) as db:
                db.add(models.CompteCGNCReference(numero='1111', libelle='Capital social', classe=1, type_compte='SP'))
                db.add(models.TauxCotisation(annee=2087, code='historique-fictif', taux_sal=0.0123, taux_pat=0.0456, plafond=None))
                db.commit()
            with owner.connect() as c:
                historique = c.exec_driver_sql('SELECT row_to_json(t)::text FROM taux_cotisations t ORDER BY id').all()
            with owner.begin() as c:
                c.exec_driver_sql('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS')
                c.exec_driver_sql('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
                c.exec_driver_sql('GRANT USAGE ON SCHEMA public TO hisabpro')
                c.exec_driver_sql('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hisabpro')
                c.exec_driver_sql('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hisabpro')
            with owner.connect() as c:
                c.exec_driver_sql(MIGRATION.read_text(encoding='utf-8'))
                c.exec_driver_sql(MIGRATION.read_text(encoding='utf-8'))
                c.commit()
                assert c.exec_driver_sql('SELECT row_to_json(t)::text FROM taux_cotisations t ORDER BY id').all() == historique
            runtime = create_engine(make_url(cible['url']).set(username='hisabpro'))
            with runtime.begin() as c:
                assert c.exec_driver_sql('SELECT current_user,session_user').one() == ('hisabpro', 'hisabpro')
                assert not c.exec_driver_sql("SELECT has_schema_privilege(current_user,'public','CREATE')").scalar()
            app = FastAPI()
            app.include_router(auth.router)
            app.include_router(employes.router)
            app.include_router(utilisateurs.router)
            def db_runtime():
                with Session(runtime) as db:
                    yield db
            app.dependency_overrides[get_db] = db_runtime  # DB uniquement ; sécurité métier réelle.
            yield {'app': app, 'owner': owner, 'runtime': runtime}
        finally:
            if runtime is not None:
                runtime.dispose()
            owner.dispose()
    assert not cible['directory'].exists()


def administrateur(laboratoire):
    api = TestClient(laboratoire['app'])
    suffix = uuid.uuid4().hex[:10]
    response = api.post('/api/auth/register', json={'nom': 'Admin fictif',
        'email': f'referentiel-{suffix}@example.com', 'password': 'Referentiel2026!',
        'raison_sociale': f'Référentiel fictif {suffix}'})
    assert response.status_code == 200, response.text
    api.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
    return api


def lire(api, annee):
    response = api.get(f'/api/employes/referentiel?annee={annee}')
    assert response.status_code == 200, response.text
    return response.json()


def consigner(api, annee, empreinte, sources=None):
    return api.post(f'/api/employes/referentiel?annee={annee}', json={
        'empreinte_attendue': empreinte, 'sources': sources or [], 'regime': 'Laboratoire non réglementaire'})


def test_api_versions_sources_scope_identique_et_annee(laboratoire):
    with administrateur(laboratoire) as a, administrateur(laboratoire) as b:
        debut = lire(a, 2091)
        assert debut['statut'] == 'non_verifie' and debut['historique'] == []
        assert debut['peut_consigner'] and not debut['paie_definitive_autorisee']
        autre = lire(b, 2091)
        assert debut['parametres_actuels'] == autre['parametres_actuels']
        assert debut['empreinte_actuelle'] != autre['empreinte_actuelle']
        assert consigner(b, 2091, debut['empreinte_actuelle']).status_code == 409
        assert consigner(a, 2092, debut['empreinte_actuelle']).status_code == 409
        assert lire(b, 2091)['historique'] == []
        assert lire(a, 2092)['historique'] == []
        response = consigner(a, 2091, debut['empreinte_actuelle'])
        assert response.status_code == 201, response.text
        source = {'titre': 'Pièce partielle fictive', 'url': None, 'article': '',
                  'date_effet': None, 'date_consultation': '', 'perimetre': 'À vérifier', 'limite': 'Non validée'}
        response = consigner(a, 2091, debut['empreinte_actuelle'], [source])
        assert response.status_code == 201, response.text
        actuel = response.json()
        assert actuel['statut'] == 'preuves_partielles'
        assert [v['version'] for v in actuel['historique']] == [2, 1]
        assert actuel['historique'][1]['sources'] == []
        assert actuel['version_courante']['sources'][0]['date_effet'] is None
        assert actuel['parametres_actuels'] == debut['parametres_actuels']
        assert not actuel['paie_definitive_autorisee']


def test_api_capture_reelle_perime_et_parametres_intacts(laboratoire):
    with Session(laboratoire['owner']) as db:
        db.add(models.TauxCotisation(annee=2093, code='laboratoire', libelle='NON REGLEMENTAIRE', taux_sal=0.02, taux_pat=0.03))
        db.add(models.BaremeIR(annee=2093, tranche_min=0, tranche_max=None, taux=0.1, deduction=0))
        db.add(models.DeductionIR(annee=2093, code='laboratoire', montant_an=100, max_beneficiaires=2))
        db.commit()
    with administrateur(laboratoire) as api:
        initial = lire(api, 2093)
        with laboratoire['owner'].connect() as c:
            comptes = c.exec_driver_sql('SELECT count(*) FROM comptes_societe').scalar()
            ecritures = c.exec_driver_sql('SELECT count(*) FROM ecritures').scalar()
        r = consigner(api, 2093, initial['empreinte_actuelle'])
        assert r.status_code == 201, r.text
        snapshot = r.json()['version_courante']
        assert snapshot['parametres'] == initial['parametres_actuels']
        with laboratoire['owner'].begin() as c:
            assert c.exec_driver_sql('SELECT count(*) FROM comptes_societe').scalar() == comptes
            assert c.exec_driver_sql('SELECT count(*) FROM ecritures').scalar() == ecritures
            # Modification volontaire d'un paramètre fictif dans le seul laboratoire.
            c.exec_driver_sql('UPDATE taux_cotisations SET taux_pat=0.04 WHERE annee=2093')
        perime = lire(api, 2093)
        assert perime['statut'] == 'perime'
        assert perime['version_courante'] == snapshot
        assert consigner(api, 2093, initial['empreinte_actuelle']).status_code == 409
        assert consigner(api, 2093, perime['empreinte_actuelle']).status_code == 201
        with laboratoire['owner'].connect() as c:
            assert c.exec_driver_sql('SELECT taux_pat FROM taux_cotisations WHERE annee=2093').scalar() == 0.04


@pytest.mark.parametrize('valeur', ['NaN', 'Infinity', '-Infinity'])
def test_api_historiques_non_finis_lisibles_capture_refusee(laboratoire, valeur):
    annee = {'NaN': 2094, 'Infinity': 2095, '-Infinity': 2096}[valeur]
    with laboratoire['owner'].begin() as c:
        c.execute(text('INSERT INTO taux_cotisations(annee,code,taux_sal,taux_pat) VALUES(:annee,:code,CAST(:valeur AS double precision),0)'),
                  {'annee': annee, 'code': 'historique-fictif', 'valeur': valeur})
    with administrateur(laboratoire) as api:
        lecture = lire(api, annee)
        assert lecture['diagnostics']
        assert lecture['parametres_actuels']['taux_cotisations'][0]['taux_sal'] == valeur
        response = consigner(api, annee, lecture['empreinte_actuelle'])
        assert response.status_code == 409, response.text
        assert lire(api, annee)['historique'] == []
    with laboratoire['owner'].connect() as c:
        assert c.execute(text('SELECT taux_sal::text FROM taux_cotisations WHERE annee=:annee'), {'annee': annee}).scalar() == valeur


def test_api_concurrence_versions_sans_collision(laboratoire):
    with administrateur(laboratoire) as api:
        empreinte = lire(api, 2097)['empreinte_actuelle']
        headers = dict(api.headers)
        barrier = Barrier(2)
        def envoyer(index):
            with TestClient(laboratoire['app'], headers=headers) as client:
                barrier.wait(timeout=10)
                return consigner(client, 2097, empreinte, [{'titre': f'Pièce fictive {index}'}])
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(envoyer, [1, 2]))
        assert [r.status_code for r in responses] == [201, 201], [r.text for r in responses]
        historique = lire(api, 2097)['historique']
        assert [v['version'] for v in historique] == [2, 1]
        assert {v['sources'][0]['titre'] for v in historique} == {'Pièce fictive 1', 'Pièce fictive 2'}


@pytest.mark.parametrize('role', ['lecture', 'comptable'])
def test_api_permissions_reelles_et_corps_borne(laboratoire, role):
    with administrateur(laboratoire) as api:
        email = f'lecture-{uuid.uuid4().hex[:10]}@example.com'
        response = api.post('/api/utilisateurs', json={'nom': 'Profil fictif', 'email': email,
            'mot_de_passe': 'Referentiel2026!', 'role': role})
        assert response.status_code == 201, response.text
        api.headers.clear()
        response = api.post('/api/auth/login', json={'email': email, 'password': 'Referentiel2026!'})
        assert response.status_code == 200, response.text
        api.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
        lecture = lire(api, 2098)
        assert not lecture['peut_consigner']
        assert consigner(api, 2098, lecture['empreinte_actuelle']).status_code == 403
        assert lecture['historique'] == []


def test_api_extra_client_refuse_et_annee_explicite(laboratoire):
    with administrateur(laboratoire) as api:
        assert api.get('/api/employes/referentiel').status_code == 422
        assert api.get('/api/employes/referentiel?annee=2024').status_code == 422
        empreinte = lire(api, 2099)['empreinte_actuelle']
        for champ in ('societe_id', 'parametres', 'statut', 'version'):
            r = api.post('/api/employes/referentiel?annee=2099', json={
                'empreinte_attendue': empreinte, champ: 1})
            assert r.status_code == 422, r.text
        assert lire(api, 2099)['historique'] == []


def test_082_rejeu_versions_preservees_et_appendonly_runtime_owner(laboratoire):
    with administrateur(laboratoire) as api:
        empreinte = lire(api, 2100)['empreinte_actuelle']
        assert consigner(api, 2100, empreinte).status_code == 201
    with laboratoire['owner'].connect() as c:
        avant = c.exec_driver_sql('SELECT row_to_json(v)::text FROM paie_referentiel_versions v ORDER BY id').all()
        tables = ('taux_cotisations', 'bareme_ir', 'deductions_ir', 'comptes_societe', 'ecritures')
        avant_autres = {t: c.exec_driver_sql(f'SELECT row_to_json(v)::text FROM {t} v ORDER BY id').all() for t in tables}
        c.exec_driver_sql(MIGRATION.read_text(encoding='utf-8'))
        c.exec_driver_sql(MIGRATION.read_text(encoding='utf-8'))
        c.commit()
        assert c.exec_driver_sql('SELECT row_to_json(v)::text FROM paie_referentiel_versions v ORDER BY id').all() == avant
        assert {t: c.exec_driver_sql(f'SELECT row_to_json(v)::text FROM {t} v ORDER BY id').all() for t in tables} == avant_autres
    for moteur, sqlstate in [(laboratoire['runtime'], '42501'), (laboratoire['owner'], '23514')]:
        for sql in ['UPDATE paie_referentiel_versions SET commentaire=\'Altéré\'',
                    'DELETE FROM paie_referentiel_versions', 'TRUNCATE paie_referentiel_versions']:
            with pytest.raises(DBAPIError) as erreur:
                with moteur.begin() as c:
                    c.exec_driver_sql(sql)
            assert erreur.value.orig.pgcode == sqlstate
    with laboratoire['owner'].connect() as c:
        assert c.exec_driver_sql('SELECT row_to_json(v)::text FROM paie_referentiel_versions v ORDER BY id').all() == avant
