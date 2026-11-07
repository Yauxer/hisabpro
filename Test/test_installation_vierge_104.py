from pathlib import Path
import subprocess,sys
from test_installation_vierge_084 import lancer


def test_104_installation_rejeu_acl_et_aucune_base_reelle(tmp_path):
    d=lancer(['Test/recette_installation_vierge_104.py','--rapport'],tmp_path/'104.md')
    assert d['statut']=='95_SQL_et_31_rejeux_valides_chaine104_runtime_partiel'
    assert len(d['appliquees'])==126 and len({r['fichier'] for r in d['appliquees']})==95
    assert [r['fichier'] for r in d['appliquees'][-2:]]==['104_liasse_balance_documents.sql']*2
    assert d['104_tables_anterieures_preservees']==82 and d['104_triggers_actifs']==3
    assert len(d['zero_final'])==46 and not any(d['zero_final'].values())
    assert d['104_rejeu_schema_acl_donnees_sequences_identiques'] and d['cluster_supprime']


def test_104_cli_refuse_url_externe_avant_cluster():
    r=subprocess.run([sys.executable,'-X','utf8','Test/recette_installation_vierge_104.py','--url','postgresql://externe.invalid/interdit'],
        cwd=Path(__file__).resolve().parents[1],text=True,encoding='utf8',capture_output=True,timeout=20)
    assert r.returncode==2 and 'unrecognized arguments' in r.stderr
