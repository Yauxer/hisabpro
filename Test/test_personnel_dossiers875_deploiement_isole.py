"""Préflight avant105/106 et migration sans dépendances, cibles nonce seulement."""
from pathlib import Path
import httpx
import pytest
from sqlalchemy import text
from test_paie_grh_postgres import app_paie,application,compte,dossier
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

P='/api/employes/securite/preflight-dossiers'
R=Path(__file__).resolve().parents[1]


def test_875_preflight_avant_migrations_sans_reprise(app_paie):
    app=app_paie
    with httpx.Client(base_url=app['api_url'],timeout=30) as api:
        compte(api);r=api.post('/api/employes',json=dossier(matricule=None,date_embauche=None));assert r.status_code==201
        me=api.get('/api/auth/me').json();avant=empreintes_tables(app['engine'])
        r=api.get(P);assert r.status_code==200 and r.headers['cache-control']=='no-store'
        q=r.json();assert q['schema_versions']=='absent' and q['nombre_employes']==1
        assert q['matricules_manquants']['nombre']==1 and q['dates_entree_inconnues']['nombre']==1
        assert not q['historique_atteste'] and not q['activation_paie_autorisee']
        assert empreintes_tables(app['engine'])==avant


def test_875_migration_sans105_refuse_atomiquement(app_paie):
    app=app_paie;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    avant=empreintes_tables(app['engine']);raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:
            with pytest.raises(Exception) as exc:cur.execute((R/'hisabpro-backend/106_personnel_dossiers_versions.sql').read_text(encoding='utf8'))
            assert exc.value.pgcode=='23514'
            cur.execute('ROLLBACK')
    finally:raw.close()
    assert empreintes_tables(app['engine'])==avant
    with app['engine'].connect() as db:assert not db.scalar(text("SELECT to_regclass('personnel_dossiers') IS NOT NULL"))


def test_875_detection_installation_partielle_sans_ecriture(app_paie):
    app=app_paie;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    with httpx.Client(base_url=app['api_url'],timeout=30) as api:
        compte(api)
        with app['engine'].begin() as db:db.execute(text('CREATE TABLE personnel_dossiers(employe_id integer)'))
        try:
            r=api.get(P);assert r.status_code==200
            assert r.json()['schema_versions']=='partiel'
            assert r.json()['controles_schema']['colonnes_attendues_manquantes']['personnel_dossiers']
            assert not r.json()['activation_paie_autorisee']
        finally:
            # Exclusivement la table vide de ce test dans son cluster marqué.
            assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
            with app['engine'].begin() as db:db.execute(text('DROP TABLE personnel_dossiers'))
