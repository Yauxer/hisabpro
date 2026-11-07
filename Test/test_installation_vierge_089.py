"""089 sur vrai PostgreSQLnonce :une fonction attendue,aucune mutation de données."""
from test_installation_vierge_084 import lancer


def test_installation089_ordre_rejeu_acl_et_difference_fonction_limitee(tmp_path):
    d=lancer(['Test/recette_installation_vierge_089.py','--rapport'],tmp_path/'089.md')
    assert d['statut']=='80_SQL_et_16_rejeux_valides_runtime_annuel_partiel'
    assert len(d['appliquees'])==96 and len({r['fichier'] for r in d['appliquees']})==80
    assert len(d['zero_final'])==36 and not any(d['zero_final'].values())
    assert len(d['refus_088_089'])==17
    assert len(d['refus_extension'])+len(d['refus_permissions_087'])+len(d['refus_088_089'])==51
    assert d['fonction_089_seule_difference_schema']==[['hisabpro_guard_lettrage_comptable','']]
    for key in ('proprietaire_fonction_089_inchange','donnees_et_sequences_088_089_inchangees',
                'acl_hors_quatre_tables_088_inchangees','rejeu_088_089_identique'):
        assert d[key] is True
    assert [r['fichier'] for r in d['appliquees'][-4:]]==[
        '088_permissions_cycle_annuel.sql','089_lettrage_identite_auxiliaire.sql']*2
    assert d['droits_088']['clotures_exercice']['INSERT'] is True
    assert d['droits_088']['taux_cotisations']['UPDATE'] is False
