"""La recette E2E ne peut initialiser ou lancer un serveur sur une cible réelle."""
from contextlib import contextmanager
import pytest
import e2e_isole_support as support


def test_cible_non_isolee_refusee_avant_moteur_ddl_et_processus(monkeypatch, tmp_path):
    appels = []

    @contextmanager
    def cible_non_isolee():
        yield {"url": "postgresql+psycopg2://recette@127.0.0.1:5432/base_fictive",
               "directory": tmp_path, "nonce": "fictif"}

    monkeypatch.setattr(support, "cluster_isole", cible_non_isolee)
    monkeypatch.setattr(support, "create_engine", lambda *args, **kwargs: appels.append("moteur"))
    monkeypatch.setattr(support.subprocess, "Popen", lambda *args, **kwargs: appels.append("serveur"))
    with pytest.raises(ValueError, match="hors PostgreSQL isolé"):
        with support.application_isolee():
            pytest.fail("Une cible non isolée ne doit jamais être démarrée.")
    assert not appels
