"""077 sur installation consolidee ; auth JWT reelle et role PG non owner."""
from contextlib import contextmanager
from datetime import date
import hashlib

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

import models
from database import get_db
from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_installation_vierge import BACK, candidats, tables_vides
from recette_installation_vierge_consolidee import COMPLEMENTS
from routers import auth, societe, tiers, articles, factures, commercial, ecritures
from test_complements_structure_postgres import refuser


def catalogue_phase077(engine):
    """Contrôles de la phase074–076, distincte de l'installation consolidée."""
    checks_attendus = {
        'etic_sections_exercice': ('ck_etic_section_code',),
        'liasses_fiscales_archives': ('ck_liasse_archive_sha256',),
        'ligne_auxiliaire_complements': ('ck_ligne_aux_complement_nature',
            'ck_ligne_aux_complement_compte_non_vide', 'ck_ligne_aux_complement_libelle_non_vide'),
    }
    triggers_attendus = {
        'livres_inventaire_archives': ('trg_livre_inventaire_immutable', 'trg_livre_inventaire_truncate'),
        'liasse_balances_preparation': ('trg_balance_preparation_immuable', 'trg_balance_preparation_truncate'),
        'ligne_auxiliaire_complements': ('trg_ligne_aux_complements_append_only', 'trg_ligne_aux_complements_no_truncate'),
    }
    with engine.connect() as db:
        checks = {table: [dict(row._mapping) for row in db.execute(text(
            'SELECT conname,convalidated,pg_get_constraintdef(oid) AS definition FROM pg_constraint '
            "WHERE conrelid=to_regclass(:table) AND contype='c' ORDER BY conname"), {'table': table})]
            for table in checks_attendus}
        triggers = {table: [dict(row._mapping) for row in db.execute(text(
            'SELECT tgname,tgenabled,pg_get_triggerdef(oid) AS definition FROM pg_trigger '
            'WHERE tgrelid=to_regclass(:table) AND NOT tgisinternal ORDER BY tgname'), {'table': table})]
            for table in triggers_attendus}
    for table, names in checks_attendus.items():
        assert set(names) <= {x['conname'] for x in checks[table]}, (table, checks[table])
    for table, names in triggers_attendus.items():
        assert set(names) <= {x['tgname'] for x in triggers[table]}, (table, triggers[table])
        assert all(x['tgenabled'] == 'O' for x in triggers[table])
    return {'checks': checks, 'triggers': triggers}


@contextmanager
def installation(role_present=True):
    with cluster_isole() as cluster:
        def garde():
            assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        garde()
        owner = create_engine(cluster['url'])
        runtime = None
        def migration(nom):
            garde()
            raw = owner.raw_connection()
            try:
                raw.autocommit = True
                with raw.cursor() as cursor:
                    cursor.execute((BACK / nom).read_text(encoding='utf-8'))
            finally:
                raw.close()
        try:
            garde()
            if role_present:
                with owner.begin() as db:
                    db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
            garde()
            models.Base.metadata.create_all(owner)
            for fichier in candidats():
                tables_vides(owner, cluster)
                migration(fichier.name)
                tables_vides(owner, cluster)
            for nom in COMPLEMENTS:
                # Ce banc vérifie précisément la transition avant/après077.
                # La recette consolidée évolue ; ses lots077+ doivent rester
                # hors du socle, sinon le rôle dispose déjà des droits testés.
                if int(nom.split('_', 1)[0]) < 77:
                    migration(nom)
            avant = catalogue_phase077(owner)
            if role_present:
                runtime = create_engine(make_url(cluster['url']).set(username='hisabpro'))
                garde()
                refuser(runtime, 'SELECT id FROM societes', '42501')
                with owner.connect() as db:
                    legacy_update = {row[0]: row[1] for row in db.execute(text(
                        "SELECT c.oid::regclass::text,has_sequence_privilege('hisabpro',c.oid,'UPDATE') "
                        "FROM pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relkind='S'"))}
            else:
                legacy_update = {}
            for _ in range(2):
                migration('077_permissions_cycle_facturation.sql')
                assert catalogue_phase077(owner) == avant
                tables_vides(owner, cluster)
            yield {'owner': owner, 'runtime': runtime, 'garde': garde, 'migration': migration,
                   'legacy_sequence_update': legacy_update}
        finally:
            if runtime is not None:
                runtime.dispose()
            owner.dispose()
    assert not cluster['directory'].exists()


@pytest.fixture(scope='module')
def cible():
    with installation() as cible:
        app = FastAPI()
        for route in (auth.router, societe.router, tiers.router, articles.router,
                      articles.router_familles, factures.router, commercial.router_regl, ecritures.router):
            app.include_router(route)
        def db_runtime():
            cible['garde']()
            with Session(cible['runtime']) as db:
                assert db.scalar(text('SELECT current_user')) == 'hisabpro'
                yield db
        # Seule la connexion est injectee ; aucune auth/permission remplacee.
        app.dependency_overrides[get_db] = db_runtime
        with TestClient(app) as client:
            cible['client'] = client
            yield cible


def ok(reponse, statut=200):
    assert reponse.status_code == statut, (reponse.status_code, reponse.text)
    return reponse.json() if reponse.content else None


@pytest.fixture(scope='module')
def cycle(cible):
    client = cible['client']
    annee = date.today().year
    jour = f'{annee}-05-15'
    credentials = {'email': 'cycle077@example.invalid', 'password': 'Recette077!Sure'}
    inscription = ok(client.post('/api/auth/register', json={**credentials, 'nom': 'Administrateur fictif',
        'raison_sociale': 'HisabPro077 fictive', 'ice': '001234567890123', 'identifiant_fiscal': '12345678'}))
    assert inscription['role'] == 'admin'
    login = ok(client.post('/api/auth/login', json=credentials))
    client.headers['Authorization'] = 'Bearer ' + login['access_token']
    utilisateur = ok(client.get('/api/auth/me'))
    sid = ok(client.get('/api/societe/moi'))['id']
    ok(client.patch('/api/societe/moi', json={'adresse': '1 rue fictive', 'ville': 'Casablanca',
        'rc': '123456', 'forme_juridique': 'SARL', 'regime_tva': 'encaissement'}))
    tier = ok(client.post('/api/tiers', json={'type': 'client', 'nom': 'Client particulier fictif',
        'categorie_fiscale': 'particulier', 'adresse': '2 rue fictive', 'delai_paiement': 30}), 201)
    article = ok(client.post('/api/articles', json={'code': 'S077', 'designation': 'Prestation fictive',
        'prix_vente_ht': 100, 'is_stockable': False, 'tva': 20, 'compte_vente': '7121'}), 201)
    facture = ok(client.post('/api/factures', json={'type': 'vente', 'date': jour,
        'tiers': tier['nom'], 'tiers_id': tier['id'], 'reference': 'PIECE-FICTIVE077',
        'lignes': [{'article_id': article['id'], 'description': article['designation'],
            'quantite': 1, 'prix_unitaire': 100, 'tva': 20}]}), 201)
    validation = ok(client.post(f"/api/factures/{facture['id']}/valider"))
    assert validation['est_validee']
    comptabilisation = ok(client.post(f"/api/factures/{facture['id']}/comptabiliser"))
    reglement = ok(client.post('/api/reglements', json={'facture_id': facture['id'],
        'date': jour, 'tiers': tier['nom'], 'montant': 120, 'mode': 'virement',
        'reference': 'VIR-FICTIF077', 'comptabiliser': True}), 201)
    assert reglement['est_comptabilisee']
    liste = ok(client.get('/api/factures', params={'exercice': annee}))
    payee = next(f for f in liste if f['id'] == facture['id'])
    assert payee['statut'] == 'payee'
    with cible['runtime'].connect() as db:
        lignes = db.execute(text('SELECT l.compte,sum(l.debit),sum(l.credit) FROM lignes_ecriture l '
            'JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:sid GROUP BY l.compte ORDER BY l.compte'), {'sid': sid}).all()
        valeurs = {compte: (float(debit), float(credit)) for compte, debit, credit in lignes}
        assert valeurs == {'3421': (120, 120), '4455': (0, 20), '5141': (120, 0), '7121': (0, 100)}
        traces = db.scalar(text('SELECT count(*) FROM audit_ecritures WHERE societe_id=:sid'), {'sid': sid})
        assert traces > 0
        # La comptabilisation genere des brouillons : validation explicite du journal.
        eids = db.execute(text('SELECT id FROM ecritures WHERE societe_id=:sid ORDER BY id'), {'sid': sid}).scalars().all()
    for eid in eids:
        ok(client.post(f'/api/ecritures/{eid}/valider'))
    return {'sid': sid, 'uid': utilisateur['id'], 'fid': facture['id'], 'eids': eids,
            'comptabilisation': comptabilisation}


def test077_auth_reelle_cycle_facture_reglement_equilibre(cycle):
    assert len(cycle['eids']) == 2


def test077_runtime_nonowner_sans_create_truncate_ni_nouveau_droit_setval(cible, cycle):
    with cible['runtime'].connect() as db:
        assert db.execute(text('SELECT current_user,session_user')).one() == ('hisabpro', 'hisabpro')
        assert not db.scalar(text("SELECT has_schema_privilege(current_user,'public','CREATE')"))
        assert not db.scalar(text('SELECT rolsuper FROM pg_roles WHERE rolname=current_user'))
        assert not db.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
        assert db.scalar(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)')) == 0
        for table in ('societes', 'utilisateurs', 'tiers', 'articles', 'factures', 'lignes_facture', 'reglements'):
            seq = db.scalar(text("SELECT pg_get_serial_sequence(:table,'id')"), {'table': table})
            assert db.scalar(text("SELECT has_sequence_privilege(current_user,:seq,'USAGE')"), {'seq': seq})
            # 005/008 donnent deja UPDATE sur des sequences : aucune normalisation
            # globale dans077. Prouver qu'il ne cree pas ce droit supplementaire.
            assert db.scalar(text("SELECT has_sequence_privilege(current_user,:seq,'UPDATE')"), {'seq': seq}) == cible['legacy_sequence_update'][seq.removeprefix('public.')]
            assert not db.scalar(text("SELECT has_table_privilege(current_user,:table,'TRUNCATE')"), {'table': table})
    cible['garde']()
    refuser(cible['runtime'], 'CREATE TABLE public.contournement077(id integer)', '42501')
    with cible['owner'].connect() as db:
        apres = {row[0]: row[1] for row in db.execute(text(
            "SELECT c.oid::regclass::text,has_sequence_privilege('hisabpro',c.oid,'UPDATE') "
            "FROM pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relkind='S'"))}
    assert apres == cible['legacy_sequence_update']


@pytest.mark.parametrize('sql,code', [("UPDATE ecritures SET libelle='interdit'", '23514'),
    ('DELETE FROM ecritures', '23514'), ('UPDATE lignes_ecriture SET debit=debit+1', '23514'),
    ('DELETE FROM lignes_ecriture', '23514'),
    ("UPDATE lignes_facture SET description='interdit'", 'P0001'), ('DELETE FROM factures', '23503')])
def test077_droits_metier_preservent_definitives(cible, cycle, sql, code):
    cible['garde']()
    refuser(cible['runtime'], sql, code)


@pytest.mark.parametrize('table', ['audit_ecritures', 'audit_actions', 'audit_periodes_comptables',
    'liasses_fiscales_archives', 'livres_inventaire_archives', 'liasse_balances_preparation',
    'ligne_auxiliaire_complements'])
def test077_audits_archives_acl_preservees(cible, cycle, table):
    cible['garde']()
    for sql in (f'UPDATE {table} SET id=id', f'DELETE FROM {table}', f'TRUNCATE {table}'):
        refuser(cible['runtime'], sql, '42501')
    if table.startswith('audit_'):
        with cible['runtime'].connect() as db:
            assert not db.scalar(text("SELECT has_table_privilege(current_user,:table,'INSERT')"), {'table': table})
    else:
        with cible['runtime'].connect() as db:
            for op in ('SELECT', 'INSERT'):
                assert db.scalar(text('SELECT has_table_privilege(current_user,:table,:op)'), {'table': table, 'op': op})


def test077_auth_jwt_et_isolation_societes_reelles(cible, cycle):
    client = cible['client']
    ok(client.post('/api/auth/login', json={'email': 'cycle077@example.invalid', 'password': 'incorrect'}), 401)
    # Bearer invalide ne passe pas la dependance d'authentification reelle.
    ok(client.get('/api/factures', params={'exercice': date.today().year},
        headers={'Authorization': 'Bearer invalide'}), 401)
    token = ok(client.post('/api/auth/register', json={'email': 'autre077@example.invalid',
        'password': 'Autre077!Sure', 'nom': 'Autre administrateur fictif',
        'raison_sociale': 'Autre societe fictive'}))['access_token']
    entete = {'Authorization': 'Bearer ' + token}
    assert ok(client.get('/api/factures', params={'exercice': date.today().year}, headers=entete)) == []
    ok(client.post(f"/api/factures/{cycle['fid']}/valider", headers=entete), 404)


def test077_archive_insert_autorise_snapshot_preserve_apres_rejeu(cible, cycle):
    contenu = '{"fictif":true}'
    sha = hashlib.sha256(contenu.encode()).hexdigest()
    cible['garde']()
    with cible['runtime'].begin() as db:
        db.execute(text('INSERT INTO liasses_fiscales_archives(societe_id,exercice,version,contenu_json,empreinte_sha256) '
            'VALUES(:sid,:annee,1,:contenu,:sha)'), {'sid': cycle['sid'], 'annee': date.today().year, 'contenu': contenu, 'sha': sha})
    cible['migration']('077_permissions_cycle_facturation.sql')
    with cible['runtime'].connect() as db:
        assert db.execute(text('SELECT contenu_json,empreinte_sha256 FROM liasses_fiscales_archives WHERE societe_id=:sid'), {'sid': cycle['sid']}).one() == (contenu, sha)
    ok(cible['client'].delete(f"/api/factures/{cycle['fid']}"), 409)


def test077_rejouable_role_absent():
    # Les migrations historiques (012 notamment) exigent le role bootstrap.
    # Ce cas prouve uniquement le contrat conditionnel du nouveau077.
    with cluster_isole() as cluster:
        assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        engine = create_engine(cluster['url'])
        try:
            for _ in range(2):
                assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
                raw = engine.raw_connection()
                try:
                    raw.autocommit = True
                    with raw.cursor() as cursor:
                        cursor.execute((BACK / '077_permissions_cycle_facturation.sql').read_text(encoding='utf-8'))
                finally:
                    raw.close()
            with engine.connect() as db:
                assert not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro')"))
        finally:
            engine.dispose()
    assert not cluster['directory'].exists()
