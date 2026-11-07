from pathlib import Path
import subprocess,sys
from test_installation_vierge_084 import lancer


def test_103_installation_vide_rejeu_acl_et_aucune_migration_reelle(tmp_path):
    d=lancer(['Test/recette_installation_vierge_103.py','--rapport'],tmp_path/'103.md')
    assert d['statut']=='94_SQL_et_30_rejeux_valides_chaine103_runtime_partiel'
    assert len(d['appliquees'])==124 and len({r['fichier'] for r in d['appliquees']})==94
    assert [r['fichier'] for r in d['appliquees'][-2:]]==['103_ras_rapprochements_versement.sql']*2
    assert d['103_tables_anterieures_preservees']==80 and d['103_triggers_actifs']==6
    assert len(d['zero_final'])==45 and not any(d['zero_final'].values())
    assert d['103_rejeu_schema_acl_donnees_sequences_identiques'] and d['cluster_supprime']


def test_103_cli_refuse_url_externe_avant_cluster():
    r=subprocess.run([sys.executable,'-X','utf8','Test/recette_installation_vierge_103.py','--url','postgresql://externe.invalid/interdit'],
        cwd=Path(__file__).resolve().parents[1],text=True,encoding='utf8',capture_output=True,timeout=20)
    assert r.returncode==2 and 'unrecognized arguments' in r.stderr
