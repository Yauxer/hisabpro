from pathlib import Path
import pytest
from postgres_isole import verifier_cible_isolee


@pytest.mark.parametrize('url', ['postgresql://real@localhost:5432/hisabpro',
    'postgresql://hisabpro_recette@127.0.0.1:5432/hisabpro_recette_abc', 'sqlite://'])
def test_cible_reelle_ou_non_identifiee_est_refusee(url, tmp_path):
    with pytest.raises((ValueError, FileNotFoundError)):
        verifier_cible_isolee(url, tmp_path, 'nonce')
