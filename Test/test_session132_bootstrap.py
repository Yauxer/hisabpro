from pathlib import Path
import pytest
from services.production_bootstrap_service import creation_schema_au_demarrage


@pytest.mark.parametrize('env,expected', [({}, True), ({'APP_ENV': 'dev'}, True),
    ({'APP_ENV': 'prod'}, False), ({'APP_ENV': 'production'}, False),
    ({'APP_ENV': 'PROD'}, False), ({'APP_ENV': 'production', 'HISABPRO_CREATE_TABLES': '1'}, True),
    ({'HISABPRO_CREATE_TABLES': '0'}, False), ({'HISABPRO_CREATE_TABLES': 'false'}, False)])
def test_creation_schema_est_explicitement_controlee(env, expected):
    assert creation_schema_au_demarrage(env) is expected


def test_configuration_ambigue_ne_cree_pas_le_schema():
    with pytest.raises(ValueError):
        creation_schema_au_demarrage({'HISABPRO_CREATE_TABLES': 'auto'})


def test_bootstrap_ne_reintroduit_pas_grant_global_sur_archives():
    source = (Path(__file__).resolve().parents[1] / 'hisabpro-backend/database.py').read_text(encoding='utf-8')
    assert 'GRANT ALL PRIVILEGES ON ALL TABLES' not in source
    assert 'GRANT ALL PRIVILEGES ON ALL SEQUENCES' not in source
