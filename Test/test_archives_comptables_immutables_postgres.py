"""Archives et préparations immuables, uniquement PostgreSQL éphémère."""
from contextlib import contextmanager
import hashlib

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.exercices_service import ensure_exercice
from test_archives_permissions_postgres import cible_archive, refuser

TABLES = ('livres_inventaire_archives', 'liasse_balances_preparation')


def instantane(engine):
    with engine.connect() as db:
        return tuple(db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).all() for table in TABLES)


@contextmanager
def dossier_archives(role_present=True):
    with cible_archive(role_present=role_present) as cible:
        for nom in ('009_livre_inventaire.sql', '011_livre_inventaire_v2.sql', '071_liasse_balances_preparation.sql'):
            cible['migration'](nom)
        cible['garde']()
        with Session(cible['owner']) as db:
            exercice = ensure_exercice(db, cible['sid'], 2025)
            db.commit()
            eid = exercice.id
        with cible['owner'].begin() as db:
            for version in (1, 2):
                contenu = '{"fictif":true,"version":' + str(version) + '}'
                sha = hashlib.sha256(contenu.encode()).hexdigest()
                db.execute(text('INSERT INTO livres_inventaire_archives(societe_id,exercice,version,contenu_json,empreinte_sha256) '
                                'VALUES(:sid,2025,:v,:contenu,:sha)'), {'sid': cible['sid'], 'v': version, 'contenu': contenu, 'sha': sha})
                db.execute(text('INSERT INTO liasse_balances_preparation(societe_id,exercice,exercice_id,version,contenu,empreinte_sha256) '
                                'VALUES(:sid,2025,:eid,:v,:contenu,:sha)'), {'sid': cible['sid'], 'eid': eid, 'v': version, 'contenu': contenu, 'sha': sha})
            if role_present:
                db.execute(text('CREATE ROLE anciennes_comptables NOLOGIN'))
                db.execute(text('GRANT anciennes_comptables TO hisabpro'))
                for table in TABLES:
                    db.execute(text(f'GRANT UPDATE, DELETE, TRUNCATE ON {table} TO anciennes_comptables'))
                    db.execute(text(f'GRANT UPDATE, DELETE, TRUNCATE ON {table} TO PUBLIC, hisabpro'))
        cible['eid'] = eid
        yield cible


@pytest.fixture(scope='module')
def cible():
    with dossier_archives() as dossier:
        dossier['avant'] = instantane(dossier['owner'])
        for _ in range(2):
            dossier['migration']('074_archives_comptables_immutables.sql')
            assert instantane(dossier['owner']) == dossier['avant']
        yield dossier


@pytest.mark.parametrize('table,sql', [
    ('livres_inventaire_archives', 'UPDATE livres_inventaire_archives SET contenu_json=\'interdit\''),
    ('livres_inventaire_archives', 'DELETE FROM livres_inventaire_archives'),
    ('livres_inventaire_archives', 'TRUNCATE livres_inventaire_archives'),
    ('liasse_balances_preparation', 'TRUNCATE liasse_balances_preparation'),
])
def test_archive_owner_refuse_mutation_et_conserve_snapshot(cible, table, sql):
    avant = instantane(cible['owner'])
    cible['garde']()
    refuser(cible['owner'], sql, 'P0001')
    assert instantane(cible['owner']) == avant


@pytest.mark.parametrize('table', TABLES)
@pytest.mark.parametrize('operation', ['UPDATE', 'DELETE', 'TRUNCATE'])
def test_runtime_heritage_groupe_ne_contourne_pas_archive(cible, table, operation):
    avant = instantane(cible['owner'])
    with cible['runtime'].connect() as db:
        assert db.scalar(text("SELECT current_user")) == 'hisabpro'
        assert db.scalar(text('SELECT has_table_privilege(current_user,:table,:op)'), {'table': table, 'op': operation})
    commande = {'UPDATE': f'UPDATE {table} SET version=version+1',
                'DELETE': f'DELETE FROM {table}', 'TRUNCATE': f'TRUNCATE {table}'}[operation]
    cible['garde']()
    refuser(cible['runtime'], commande, 'P0001')
    assert instantane(cible['owner']) == avant


def test_revoke_acl_directes_public_sans_masquer_heritage(cible):
    with cible['owner'].connect() as db:
        for table in TABLES:
            privileges = db.execute(text("SELECT r.rolname,a.privilege_type FROM pg_class c "
                "CROSS JOIN LATERAL aclexplode(c.relacl) a LEFT JOIN pg_roles r ON r.oid=a.grantee "
                "WHERE c.oid=to_regclass(:table) AND (a.grantee=0 OR r.rolname='hisabpro')"), {'table': table}).all()
            assert not any(privilege in {'UPDATE', 'DELETE', 'TRUNCATE'} for _, privilege in privileges)
    with cible['runtime'].connect() as db:
        for table in TABLES:
            assert db.scalar(text('SELECT has_table_privilege(current_user,:table,\'SELECT\')'), {'table': table})
            assert db.scalar(text('SELECT has_table_privilege(current_user,:table,\'INSERT\')'), {'table': table})


def test_nouvelles_versions_runtime_autorisees_originaux_preserves(cible):
    avant = instantane(cible['owner'])
    contenu = '{"fictif":true,"version":3}'
    sha = hashlib.sha256(contenu.encode()).hexdigest()
    cible['garde']()
    with cible['runtime'].begin() as db:
        db.execute(text('INSERT INTO livres_inventaire_archives(societe_id,exercice,version,contenu_json,empreinte_sha256) '
                        'VALUES(:sid,2025,3,:contenu,:sha)'), {'sid': cible['sid'], 'contenu': contenu, 'sha': sha})
        db.execute(text('INSERT INTO liasse_balances_preparation(societe_id,exercice,exercice_id,version,contenu,empreinte_sha256) '
                        'VALUES(:sid,2025,:eid,3,:contenu,:sha)'), {'sid': cible['sid'], 'eid': cible['eid'], 'contenu': contenu, 'sha': sha})
    apres = instantane(cible['owner'])
    assert all(rows[:len(original)] == original and len(rows) == len(original)+1 for original, rows in zip(avant, apres))


def test074_rejouable_sans_role_applicatif():
    with dossier_archives(role_present=False) as cible:
        avant = instantane(cible['owner'])
        for _ in range(2):
            cible['migration']('074_archives_comptables_immutables.sql')
        for table in TABLES:
            cible['garde']()
            refuser(cible['owner'], f'TRUNCATE {table}', 'P0001')
        assert instantane(cible['owner']) == avant
