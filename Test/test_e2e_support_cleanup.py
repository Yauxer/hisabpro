from pathlib import Path
import tempfile

import pytest

import e2e_isole_support as support


@pytest.mark.parametrize('verrou_permanent', [False, True])
def test_nettoyage_verrou_transitoire_reessaie_et_permanent_echoue(monkeypatch, verrou_permanent):
    espace = support.ROOT / '.codex-tests'
    espace.mkdir(exist_ok=True)
    dossier = support.DossierE2E(prefix='hisabpro_e2e_', dir=espace)
    cible = Path(dossier.name)
    (cible / 'api.log').write_text('Fictif', encoding='utf-8')
    nettoyage = tempfile.TemporaryDirectory.cleanup
    appels = []
    pauses = []
    def simuler_verrou(obj):
        appels.append(obj.name)
        if verrou_permanent or len(appels) < 3:
            raise PermissionError('Verrou fichier synthétique')
        return nettoyage(obj)
    monkeypatch.setattr(tempfile.TemporaryDirectory, 'cleanup', simuler_verrou)
    monkeypatch.setattr(support.time, 'sleep', pauses.append)
    try:
        if verrou_permanent:
            with pytest.raises(PermissionError):
                dossier.cleanup()
            assert len(appels) == 20 and len(pauses) == 19
            assert cible.exists()
        else:
            dossier.cleanup()
            assert len(appels) == 3 and pauses == [0.1, 0.1]
            assert not cible.exists()
    finally:
        nettoyage(dossier)


def test_nettoyage_refuse_dossier_hors_prefixe(monkeypatch):
    espace = support.ROOT / '.codex-tests'
    espace.mkdir(exist_ok=True)
    dossier = support.DossierE2E(prefix='autre_test_', dir=espace)
    nettoyage = tempfile.TemporaryDirectory.cleanup
    try:
        with pytest.raises(RuntimeError, match='refusé'):
            dossier.cleanup()
        assert Path(dossier.name).exists()
    finally:
        nettoyage(dossier)
