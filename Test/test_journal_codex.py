from zipfile import ZipFile
import pytest
from journal_codex import consigner, etapes


def test_reprise_persistante_et_historique_preserve(tmp_path):
    journal = tmp_path / 'suivi.md'
    journal.write_text('Historique utilisateur\n', encoding='utf-8')
    consigner('debut', 'LOT-01', objectif='Contrôle', prochaine='Analyser', path=journal)
    consigner('point', 'LOT-01', fait='Correction enregistrée', tests='Tests pas encore exécutés',
              prochaine='Lancer les tests ciblés', path=journal)
    consigner('interruption', 'LOT-01', prochaine='Reprendre les tests ciblés', path=journal)
    r = etapes(journal)['LOT-01']
    assert r['statut'] == 'interrompu' and r['fait'] == 'Correction enregistrée'
    assert r['prochaine'] == 'Reprendre les tests ciblés'
    assert journal.read_text(encoding='utf-8').startswith('Historique utilisateur\n')
    assert journal.read_text(encoding='utf-8').count('<!-- CODEX_STEP') == 3


def test_fin_exige_archive_verifiee(tmp_path):
    journal = tmp_path / 'suivi.md'
    consigner('debut', 'LOT-01', objectif='Correction', prochaine='Tester', path=journal)
    avant = journal.read_bytes()
    for archive in [tmp_path / 'absent.zip', tmp_path / 'incorrect.zip']:
        if archive.name == 'incorrect.zip':
            archive.write_bytes(b'pas un zip')
        with pytest.raises(ValueError):
            consigner('fin', 'LOT-01', zip_path=archive, prochaine='Lot suivant', path=journal)
        assert journal.read_bytes() == avant
    archive = tmp_path / 'livraison.zip'
    with ZipFile(archive, 'w') as z:
        z.writestr('src/correction.txt', 'Correction')
    consigner('fin', 'LOT-01', tests='3 tests ciblés réussis', zip_path=archive,
              prochaine='Recette utilisateur', path=journal)
    assert etapes(journal)['LOT-01']['statut'] == 'termine'


def test_transitions_invalides_ne_perdent_pas_le_point_de_reprise(tmp_path):
    journal = tmp_path / 'suivi.md'
    with pytest.raises(ValueError):
        consigner('point', 'LOT-01', path=journal)
    assert not journal.exists()
    consigner('debut', 'LOT-01', objectif='Correction', prochaine='Tester', path=journal)
    avant = journal.read_bytes()
    with pytest.raises(ValueError):
        consigner('debut', 'LOT-01', objectif='Écraser', prochaine='Autre', path=journal)
    assert journal.read_bytes() == avant


def test_etapes_independantes_et_accents_relus(tmp_path):
    journal = tmp_path / 'suivi.md'
    for id in ['LOT-01', 'LOT-02']:
        consigner('debut', id, objectif='Échéances à contrôler', prochaine='Vérifier', path=journal)
    consigner('interruption', 'LOT-01', prochaine='Attendre justificatif', path=journal)
    assert etapes(journal)['LOT-02']['statut'] == 'en_cours'
    assert etapes(journal)['LOT-01']['objectif'] == 'Échéances à contrôler'
    assert list(etapes(journal))[-1] == 'LOT-01'
