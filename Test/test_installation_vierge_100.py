"""Installation100 : vrai CLI nonce, pas une substitution SQLite."""
from test_installation_vierge_084 import lancer
from pathlib import Path
import subprocess
import sys


def test_installation100_preserve099_rejoue_schema_acl_et_sequences(tmp_path):
    d=lancer(['Test/recette_installation_vierge_100.py','--rapport'],tmp_path/'100.md')
    assert d['statut']=='91_SQL_et_27_rejeux_valides_chaine100_runtime_partiel'
    assert len(d['appliquees'])==118 and len({r['fichier'] for r in d['appliquees']})==91
    assert [r['fichier'] for r in d['appliquees'][-2:]]==['100_reprises_provisions.sql']*2
    assert len(d['zero_final'])==40 and not any(d['zero_final'].values())
    assert d['100_tables_anterieures_preservees']==75
    assert d['100_rejeu_schema_acl_donnees_sequences_identiques']
    assert d['100_acl_runtime_et_public_controlees'] and d['100_triggers_actifs']==9
    assert d['099_rejeu_schema_acl_donnees_sequences_identiques'] and d['cluster_supprime']


def test_cli100_refuse_adresse_externe_avant_creation_cluster():
    r=subprocess.run([sys.executable,'-X','utf8','Test/recette_installation_vierge_100.py',
        '--url','postgresql://externe.invalid/interdit'],cwd=Path(__file__).resolve().parents[1],
        text=True,encoding='utf8',capture_output=True,timeout=20)
    assert r.returncode==2 and 'unrecognized arguments' in r.stderr
