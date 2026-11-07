"""Recette CLI087 réelle ;ordre, conservation, droits et refus sur cluster nonce."""
import hashlib

from test_installation_vierge_084 import ROOT, lancer


def test_installation_087_permissions_rejeux_donnees_et_schema_conserves(tmp_path):
    data = lancer(['Test/recette_installation_vierge_087.py', '--rapport'], tmp_path / '087.md')
    assert data['statut'] == '78_SQL_et_14_rejeux_valides_runtime_cible_non_exhaustif'
    assert len(data['appliquees']) == 92 and len({r['fichier'] for r in data['appliquees']}) == 78
    assert len(data['zero_final']) == 36 and not any(data['zero_final'].values())
    for champ in ('permissions_087_absentes_avant', 'schema_donnees_sequences_inchanges',
                  'acl_hors_onze_tables_inchangees', 'update_sequences_inchanges',
                  'permissions_087_identiques_apres_rejeu'):
        assert data[champ] is True
    assert len(data['droits_087']) == len(data['sequences_087_usage_select']) == 11
    assert len(data['refus_permissions_087']) == 17
    assert len(data['refus_extension']) == 17
    assert data['role_runtime'] == ['hisabpro', 'hisabpro', True, False, False, False, False, False]
    assert data['runtime_create_public'] is False
    assert [r['fichier'] for r in data['appliquees'][-6:]] == [
        '085_permissions_documents_commerciaux.sql', '086_permissions_acomptes_avoirs.sql',
        '087_permissions_banque_releves.sql'] * 2
    for row in data['appliquees']:
        assert hashlib.sha256((ROOT/'hisabpro-backend'/row['fichier']).read_bytes()).hexdigest() == row['sha256']
    droits_finaux = {r['relname']: r for r in data['droits_tables']}
    assert droits_finaux['devis']['insertion'] is True
    assert droits_finaux['comptes_bancaires']['suppression'] is False
    assert droits_finaux['rapprochement_lignes']['suppression'] is True
