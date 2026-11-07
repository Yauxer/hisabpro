"""Chaîne existante098 : ordre, rejet des privilèges et rejeu natif isolé."""
from recette_installation_vierge_098 import EXTENSIONS
from test_installation_vierge_084 import lancer


def test_installation098_ordre_rejeu_acl_et_reference_seule(tmp_path):
    d = lancer(['Test/recette_installation_vierge_098.py', '--rapport'], tmp_path/'098.md')
    assert d['statut'] == '89_SQL_et_25_rejeux_valides_chaine098_runtime_partiel'
    assert len(d['appliquees']) == 114 and len({r['fichier'] for r in d['appliquees']}) == 89
    assert [r['fichier'] for r in d['appliquees'][-16:]] == list(EXTENSIONS)*2
    assert len(d['zero_final']) == 37 and not any(d['zero_final'].values())
    assert d['098_rejeu_schema_acl_donnees_sequences_identiques']
    assert d['098_historiques_et_modeles_existants_preserves']
    assert d['098_acl_runtime_controlees']
    assert d['098_ajouts_reference_092'] == {'modeles_ecritures': 5, 'lignes_modele': 10}
    assert d['098_tables_hors_references_inchangees'] >= 60
