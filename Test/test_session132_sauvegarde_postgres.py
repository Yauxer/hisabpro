"""pg_dump/pg_restore réels, uniquement PostgreSQL éphémère marqué."""
from pathlib import Path
import sys
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from postgres_isole import cluster_isole, verifier_cible_isolee, _run

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ops.postgres_sauvegarde import connexion_pg, sauvegarder, restaurer_isole


def test_identifiants_restent_hors_arguments_et_pas_d_url_affichee():
    env = connexion_pg('postgresql://recette:secret%40test@127.0.0.1:5555/recette')
    assert env['PGPASSWORD'] == 'secret@test' and env['PGPORT'] == '5555'
    with pytest.raises(ValueError, match='PostgreSQL explicite'):
        connexion_pg('sqlite://')


def test_variables_heritees_ne_peuvent_pas_changer_cible(monkeypatch):
    for key in ['PGHOSTADDR', 'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS', 'PGPASSWORD']:
        monkeypatch.setenv(key, 'cible_exterieure')
    env = connexion_pg('postgresql://hisabpro_recette@127.0.0.1:5555/hisabpro_recette_isole')
    assert env['PGHOST'] == '127.0.0.1' and env['PGPORT'] == '5555'
    assert not any(key in env for key in ['PGHOSTADDR', 'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS', 'PGPASSWORD'])


def test_sauvegarde_existante_ne_peut_pas_etre_ecrasee(tmp_path):
    destination = tmp_path / 'existant.dump'; destination.write_bytes(b'preuve')
    with pytest.raises(FileExistsError):
        sauvegarder('postgresql://test@localhost/test', destination, tmp_path)
    assert destination.read_bytes() == b'preuve'


def test_restauration_hors_bac_refusee_avant_connexion(tmp_path):
    with pytest.raises((ValueError, FileNotFoundError)):
        restaurer_isole('postgresql://test@localhost:5432/reel', tmp_path / 'archive', tmp_path, tmp_path, 'nonce')


def test_sauvegarde_restauration_vraies_postgresql():
    with cluster_isole() as cluster:
        verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        source = create_engine(cluster['url'])
        destination = None
        try:
            with source.begin() as connection:
                connection.execute(text('CREATE TABLE recette_ecritures (id integer PRIMARY KEY, societe integer NOT NULL, debit numeric(18,2), credit numeric(18,2))'))
                connection.execute(text('INSERT INTO recette_ecritures VALUES (1,1,100000,0),(2,1,0,100000),(3,2,700.25,0),(4,2,0,700.25)'))
            archive = sauvegarder(cluster['url'], cluster['directory'] / 'sauvegarde.dump', cluster['bin'])
            name = make_url(cluster['url']).database + '_restauration'
            _run([cluster['bin'] / ('createdb' + cluster['suffix']), '-h', '127.0.0.1', '-p', cluster['port'], '-U', 'hisabpro_recette', name])
            restored_url = make_url(cluster['url']).set(database=name).render_as_string(hide_password=False)
            restaurer_isole(restored_url, archive, cluster['bin'], cluster['directory'], cluster['nonce'])
            destination = create_engine(restored_url)
            query = text('SELECT societe,count(*),sum(debit),sum(credit) FROM recette_ecritures GROUP BY societe ORDER BY societe')
            with source.connect() as a, destination.connect() as b:
                assert a.execute(query).all() == b.execute(query).all() == [(1,2,100000,100000),(2,2,700.25,700.25)]
            with pytest.raises(ValueError, match='doit être vide'):
                restaurer_isole(restored_url, archive, cluster['bin'], cluster['directory'], cluster['nonce'])
        finally:
            source.dispose()
            if destination:
                destination.dispose()
