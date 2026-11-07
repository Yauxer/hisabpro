"""CHECK historiques manquants après create_all, uniquement PG éphémère."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from test_archives_permissions_postgres import cible_archive


@pytest.fixture(scope='module')
def cible():
    with cible_archive() as dossier:
        dossier['migration']('026_etic_exercice.sql')
        dossier['garde']()
        with dossier['owner'].begin() as db:
            db.execute(text("INSERT INTO etic_sections_exercice(societe_id,exercice,code,contenu) VALUES(:sid,2025,'Z9','{}')"), {'sid': dossier['sid']})
            db.execute(text("INSERT INTO liasses_fiscales_archives(societe_id,exercice,version,contenu_json,empreinte_sha256) "
                            "VALUES(:sid,2025,3,'{}','ancien_format_fictif')"), {'sid': dossier['sid']})
        dossier['avant'] = instantane(dossier['owner'])
        for _ in range(2):
            dossier['migration']('076_contraintes_etic_archives.sql')
            assert instantane(dossier['owner']) == dossier['avant']
        yield dossier


def instantane(engine):
    with engine.connect() as db:
        return tuple(db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).all()
                     for table in ('etic_sections_exercice', 'liasses_fiscales_archives'))


@pytest.mark.parametrize('nature,valeur', [('etic', 'Z9'), ('etic', 'b2bis'),
    ('archive', 'a'*63), ('archive', 'A'*64), ('archive', 'x'*64)])
def test_nouveaux_codes_etic_et_hash_invalides_refuses(cible, nature, valeur):
    cible['garde']()
    with cible['owner'].connect() as db:
        with pytest.raises(DBAPIError) as erreur:
            if nature == 'etic':
                db.execute(text("INSERT INTO etic_sections_exercice(societe_id,exercice,code,contenu) VALUES(:sid,2025,:v,'{}')"), {'sid': cible['sid'], 'v': valeur})
            else:
                db.execute(text("INSERT INTO liasses_fiscales_archives(societe_id,exercice,version,contenu_json,empreinte_sha256) "
                    "VALUES(:sid,2025,3,'{}',:v)"), {'sid': cible['sid'], 'v': valeur})
        assert erreur.value.orig.pgcode == '23514'
        assert erreur.value.orig.diag.constraint_name == ('ck_etic_section_code' if nature == 'etic' else 'ck_liasse_archive_sha256')
        db.rollback()


def test076_preserve_anciens_cas_invalides_et_indique_nonvalidation(cible):
    with cible['owner'].connect() as db:
        for table, nom in [('etic_sections_exercice', 'ck_etic_section_code'),
                           ('liasses_fiscales_archives', 'ck_liasse_archive_sha256')]:
            assert db.scalar(text('SELECT convalidated FROM pg_constraint WHERE conname=:n AND conrelid=to_regclass(:t)'),
                             {'n': nom, 't': table}) is False
    assert instantane(cible['owner']) == cible['avant']


def test076_autorise_codes_et_sha_valides_existants(cible):
    cible['garde']()
    with cible['owner'].begin() as db:
        db.execute(text("INSERT INTO etic_sections_exercice(societe_id,exercice,code,contenu) VALUES(:sid,2025,'B2bis','{}')"), {'sid': cible['sid']})
        db.execute(text("INSERT INTO liasses_fiscales_archives(societe_id,exercice,version,contenu_json,empreinte_sha256) "
                        "VALUES(:sid,2025,4,'{}',:sha)"), {'sid': cible['sid'], 'sha': 'a'*64})
    apres = instantane(cible['owner'])
    assert all(rows[:len(avant)] == avant and len(rows) == len(avant)+1 for avant, rows in zip(cible['avant'], apres))


def test076_sans_role_applicatif_ne_touche_pas_permissions_ou_archives():
    with cible_archive(role_present=False) as dossier:
        avant = instantane(dossier['owner'])
        for _ in range(2):
            dossier['migration']('076_contraintes_etic_archives.sql')
        assert instantane(dossier['owner']) == avant
