"""Edge → main:app → LOGIN SQL limité, sur PostgreSQL nonce consolidé087.

Réutilise les vrais parcours et leurs oracles ; aucun endpoint métier remplacé.
"""
from pathlib import Path
import hashlib

import pytest
from sqlalchemy import text

from e2e_isole_support import application_isolee
from postgres_isole import verifier_cible_isolee
from recette_installation_vierge import BACK, candidats, tables_vides
from recette_installation_vierge_consolidee import COMPLEMENTS
from recette_installation_vierge_084 import catalogue

# Les fonctions gardent leurs assertions et paramétrages d'origine, avec le
# fixture local qui lance désormais le vrai serveur sous LOGIN hisabpro.
from test_e2e_facturation_isole import (
    test_facture_validation_reglements_et_lettrage_ui_reels as test_runtime_facture_journal_lettrage,
)
from test_e2e_rapprochement_isole import (
    test_csv_credit_pointage_soldes_rechargement_et_doublon_ui_reels as test_runtime_import_csv_pointage,
)
from test_e2e_rapprochement_propositions_isole import (
    test_selection_confirmation_rechargement_et_origines_preservees as test_runtime_propositions_simple_et_lot,
)

EXTENSIONS = ('083_ras_reglements.sql', '084_rapprochement_ventilations.sql',
              '085_permissions_documents_commerciaux.sql',
              '086_permissions_acomptes_avoirs.sql', '087_permissions_banque_releves.sql')


@pytest.fixture(scope='module')
def application():
    executions = []
    def preparer(engine, cluster):
        def garde():
            assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        garde()
        with engine.begin() as db:
            db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB '
                            'NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
        for fichier in (*candidats(), *(BACK / n for n in (*COMPLEMENTS, *EXTENSIONS))):
            garde()
            tables_vides(engine, cluster)
            raw = engine.raw_connection()
            try:
                raw.autocommit = True
                with raw.cursor() as cursor:
                    cursor.execute(fichier.read_text(encoding='utf-8'))
            finally:
                raw.close()
            tables_vides(engine, cluster)
            executions.append((fichier.name, hashlib.sha256(fichier.read_bytes()).hexdigest()))
        assert len(executions) == 78 and len(set(n for n, _ in executions)) == 78
        catalogue(engine)
    with application_isolee(preparer_runtime=preparer) as app:
        assert app['role_sql'] == 'hisabpro'
        app['migrations_runtime'] = executions
        yield app
        # L'API doit effectivement avoir ouvert des connexions avec le rôle
        # attendu, sans connexion du migrateur depuis son processus serveur.
        with app['engine'].connect() as db:
            assert db.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND usename='hisabpro'")) > 0
        assert all(hashlib.sha256((BACK / n).read_bytes()).hexdigest() == sha for n, sha in executions)
    assert all(process.poll() is not None for process in app['processus'])
    assert not app['web_thread'].is_alive()
    assert not app['cluster']['directory'].exists() and not app['directory'].exists()


@pytest.fixture(scope='module')
def migration(application):
    """Précondition084 réellement installée ; aucune migration après les pièces."""
    assert '084_rapprochement_ventilations.sql' in dict(application['migrations_runtime'])
    return catalogue(application['engine'])
