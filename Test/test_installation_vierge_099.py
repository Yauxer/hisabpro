"""Installation099 : aucun DDL sur base utilisateur, ordre/rejeu et ACL natifs."""
from test_installation_vierge_084 import lancer


def test_installation099_preserve098_rejoue_et_verifie_acl(tmp_path):
    d=lancer(['Test/recette_installation_vierge_099.py','--rapport'],tmp_path/'099.md')
    assert d['statut']=='90_SQL_et_26_rejeux_valides_chaine099_runtime_partiel'
    assert len(d['appliquees'])==116 and len({r['fichier'] for r in d['appliquees']})==90
    assert [r['fichier'] for r in d['appliquees'][-2:]]==['099_ras_tva_details.sql']*2
    assert len(d['zero_final'])==38 and not any(d['zero_final'].values())
    assert d['099_tables_anterieures_preservees']==74
    assert d['099_rejeu_schema_acl_donnees_sequences_identiques']
    assert d['099_acl_runtime_controlees'] and d['098_historiques_et_modeles_existants_preserves']
