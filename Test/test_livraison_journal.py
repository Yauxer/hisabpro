import json
from zipfile import ZipFile
import pytest
import livrer_session132 as livraison
from journal_codex import consigner, etapes


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    baseline = tmp_path / 'baseline.json'; baseline.write_text('{}', encoding='utf-8')
    manifest = tmp_path / 'docs/manifest.json'
    journal = tmp_path / 'CODEX_PROGRESS.md'
    code = tmp_path / 'correction.py'; code.write_text('CORRECTION = True\n', encoding='utf-8')
    monkeypatch.setattr(livraison, 'ROOT', tmp_path)
    monkeypatch.setattr(livraison, 'BASELINE', baseline)
    monkeypatch.setattr(livraison, 'MANIFEST', manifest)
    consigner('debut', 'LOT-01', objectif='Correction', prochaine='Tester', path=journal)
    return tmp_path, journal, manifest


def test_recu_final_present_dans_zip_et_manifest(workspace):
    root, journal, manifest = workspace
    livraison.livrer('lot.zip', ['correction.py'], 'Correction validée', '2 tests réussis',
                     etape='LOT-01', prochaine='Recette navigateur')
    assert etapes(journal)['LOT-01']['statut'] == 'termine'
    with ZipFile(root / 'lot.zip') as z:
        assert z.testzip() is None and len(z.namelist()) == len(set(z.namelist()))
        assert z.read('CODEX_PROGRESS.md') == journal.read_bytes()
        assert '"statut": "termine"' in z.read('CODEX_PROGRESS.md').decode('utf-8')
    assert json.loads(manifest.read_text(encoding='utf-8'))[0]['zip'] == 'lot.zip'


def test_echec_avant_archive_ne_termine_pas_etape(workspace):
    root, journal, manifest = workspace
    avant = journal.read_bytes()
    with pytest.raises(ValueError):
        livraison.livrer('lot.zip', ['absent.py'], 'Correction', 'Non exécutés', etape='LOT-01')
    assert journal.read_bytes() == avant and not (root / 'lot.zip').exists()
    assert not manifest.exists()


def test_etape_inexistante_refusee_avant_livraison(workspace):
    root, journal, _ = workspace
    with pytest.raises(ValueError, match='active'):
        livraison.livrer('lot.zip', ['correction.py'], 'Correction', '2 tests', etape='INCONNUE')
    assert etapes(journal)['LOT-01']['statut'] == 'en_cours'
