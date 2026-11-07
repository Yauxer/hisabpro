"""L'extension runtime refuse les rôles privilégiés et nettoie son bac en erreur."""
import pytest
from sqlalchemy import text

from e2e_isole_support import application_isolee
from postgres_isole import verifier_cible_isolee


@pytest.mark.parametrize('cas', ['superuser', 'membre_migrateur', 'preparation_interrompue'])
def test_preparation_runtime_refuse_privileges_et_nettoie(cas):
    captures = []
    def preparer(engine, cluster):
        assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        captures.append(cluster['directory'])
        if cas == 'preparation_interrompue':
            raise RuntimeError('Échec de préparation fictif442')
        with engine.begin() as db:
            db.execute(text('CREATE ROLE hisabpro LOGIN ' +
                ('SUPERUSER' if cas == 'superuser' else
                 'NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS')))
            if cas == 'membre_migrateur':
                db.execute(text('GRANT hisabpro_recette TO hisabpro'))
    attendu = RuntimeError if cas == 'preparation_interrompue' else AssertionError
    with pytest.raises(attendu):
        with application_isolee(preparer_runtime=preparer):
            pytest.fail('Le serveur ne doit pas être exposé avec cette préparation.')
    assert len(captures) == 1 and not captures[0].exists()
