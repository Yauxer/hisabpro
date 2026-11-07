"""Parcours annuels existants avec vraie application sous LOGIN SQL limité."""
from pathlib import Path

import pytest
from sqlalchemy import text, create_engine

from postgres_isole import verifier_cible_isolee, cluster_isole
from recette_installation_vierge import BACK
from test_complements_structure_postgres import refuser
from test_permissions_documents_commerciaux_postgres import acl
from test_e2e_runtime_consolide_isole import application as application087, migration
from test_e2e_annee_rapprochement_ventilation_isole import (
    test_annee_banque_1000_ventilations240_cloture_an_paiements120 as scenario_annee_banque,
)
from test_e2e_annee_ventilation_inter_exercices_isole import (
    test_oracle_independant_ventilations_soldes_et_an as test_oracle_annee_independant,
)
from test_e2e_immobilisations_degressif_isole import (
    test_edge_cinq_dotations_degressives_et_acquisition_definitive_conservee as test_runtime_immo_degressif,
    test_oracle_degressif_bascule_lineaire_independant as test_oracle_degressif_independant,
)

ROOT = Path(__file__).resolve().parents[1]
SQL = '088_permissions_cycle_annuel.sql'
SQL_IDENTITE = '089_lettrage_identite_auxiliaire.sql'
TABLES = ('clotures_exercice', 'bareme_ir', 'taux_cotisations', 'deductions_ir')


@pytest.fixture(scope='module')
def application(application087):
    app = application087
    cluster = app['cluster']
    assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
    app['avant088'] = acl(app['engine'])
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    runtime = create_engine(make_url(cluster['url']).set(username='hisabpro'))
    try:
        refuser(runtime, 'INSERT INTO public.clotures_exercice DEFAULT VALUES', '42501')
        for t in TABLES[1:]:
            refuser(runtime, f'SELECT id FROM public.{t}', '42501')
        for _ in range(2):
            assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
            raw = app['engine'].raw_connection()
            try:
                raw.autocommit = True
                with raw.cursor() as cursor:
                    cursor.execute((BACK / SQL).read_text(encoding='utf-8'))
            finally:
                raw.close()
        assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        raw = app['engine'].raw_connection()
        try:
            raw.autocommit = True
            with raw.cursor() as cursor:
                for _ in range(2):
                    cursor.execute((BACK / SQL_IDENTITE).read_text(encoding='utf-8'))
        finally:
            raw.close()
        app['runtime088'] = runtime
        yield app
    finally:
        runtime.dispose()
        # Conserver l'erreur SQL réelle avant le nettoyage normal du serveur.
        assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        preuve = ROOT/'.codex-tests'/f"runtime444_api_{cluster['nonce']}.log"
        preuve.write_text(app['api_log'].read_text(encoding='utf-8', errors='replace'), encoding='utf-8')


@pytest.fixture(scope='module')
def annee_banque(application, migration, tmp_path_factory):
    scenario_annee_banque(application, migration, tmp_path_factory.mktemp('annee-runtime089'))
    return application


def test_runtime_annee_banque(annee_banque):
    with annee_banque['engine'].connect() as db:
        assert db.scalar(text('SELECT count(*) FROM clotures_exercice')) >= 1


def test088_acl_rejeu_et_traces_definitives_preservees(annee_banque):
    app = annee_banque
    before, seq_before = app['avant088']
    after, seq_after = acl(app['engine'])
    assert seq_after == seq_before
    assert all(after[t] == before[t] for t in before if t not in TABLES)
    for t in TABLES:
        assert after[t] == {'SELECT': True, 'INSERT': t == 'clotures_exercice',
                            'UPDATE': False, 'DELETE': False, 'TRUNCATE': False}
        for op in ('UPDATE', 'DELETE', 'TRUNCATE'):
            sql = f'UPDATE public.{t} SET id=id' if op == 'UPDATE' else f'{op} {"FROM " if op == "DELETE" else ""}public.{t}'
            refuser(app['runtime088'], sql, '42501')
    from recette_restauration_consolidee_084 import empreintes_tables
    before_data = empreintes_tables(app['engine'])
    raw = app['engine'].raw_connection()
    try:
        raw.autocommit = True
        with raw.cursor() as cursor:
            cursor.execute((BACK / SQL).read_text(encoding='utf-8'))
    finally:
        raw.close()
    assert empreintes_tables(app['engine']) == before_data
    assert acl(app['engine']) == (after, seq_after)
    # Les traces réelles des scénarios précédents restent protégées même owner.
    with app['engine'].connect() as db:
        assert db.scalar(text('SELECT count(*) FROM clotures_exercice')) >= 1
    refuser(app['engine'], 'UPDATE clotures_exercice SET resultat_net=resultat_net', '23514')
    refuser(app['engine'], 'DELETE FROM clotures_exercice', '23514')


def test088_lecture_referentiel_et_cloture_interdite_au_lecteur(application):
    from test_ras_lecture_conservation import client
    import httpx
    import uuid
    api, _, _ = client(application)
    try:
        r = api.get('/api/employes/referentiel', params={'annee': 2025})
        assert r.status_code == 200, r.text
        email = 'lecture088-' + uuid.uuid4().hex[:8] + '@example.com'
        password = 'Lecture088!Fictive'
        r = api.post('/api/utilisateurs', json={'nom': 'Lecture fictive088', 'email': email,
                     'mot_de_passe': password, 'role': 'lecture'})
        assert r.status_code == 201, r.text
        with httpx.Client(base_url=application['api_url']) as lecteur:
            r = lecteur.post('/api/auth/login', json={'email': email, 'password': password})
            assert r.status_code == 200, r.text
            lecteur.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
            assert lecteur.get('/api/employes/referentiel', params={'annee':2025}).status_code == 200
            assert lecteur.post('/api/cloture/cloturer',params={'exercice':2025}).status_code == 403
    finally:
        api.close()


def test088_role_absent_ne_cree_aucun_objet():
    with cluster_isole() as c:
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        engine = create_engine(c['url'])
        try:
            for _ in range(2):
                raw = engine.raw_connection()
                try:
                    raw.autocommit = True
                    with raw.cursor() as cursor:
                        cursor.execute((BACK / SQL).read_text(encoding='utf-8'))
                finally:
                    raw.close()
            with engine.connect() as db:
                assert not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro')"))
                assert not db.scalar(text("SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace"))
        finally:
            engine.dispose()
    assert not c['directory'].exists()
