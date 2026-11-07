"""Vrai CLI102 nonce, droits applicatifs et refus de cible externe."""
from pathlib import Path
import subprocess,sys
from test_installation_vierge_084 import lancer


def test_installation102_preserve100_rejoue_et_verifie_droits(tmp_path):
    d=lancer(['Test/recette_installation_vierge_102.py','--rapport'],tmp_path/'102.md')
    assert d['statut']=='93_SQL_et_29_rejeux_valides_chaine102_runtime_partiel'
    assert len(d['appliquees'])==122 and len({r['fichier'] for r in d['appliquees']})==93
    assert [r['fichier'] for r in d['appliquees'][-4:]]==['101_societes_liees.sql','102_factures_correspondantes.sql']*2
    assert len(d['zero_final'])==43 and not any(d['zero_final'].values())
    assert d['102_tables_anterieures_preservees']==77 and d['102_triggers_actifs']==9
    assert d['102_rejeu_schema_acl_donnees_sequences_identiques'] and d['102_acl_runtime_public_sequences_controlees']
    assert d['100_rejeu_schema_acl_donnees_sequences_identiques'] and d['cluster_supprime']


def test_cli102_refuse_url_externe_avant_creation_cluster():
    r=subprocess.run([sys.executable,'-X','utf8','Test/recette_installation_vierge_102.py','--url','postgresql://externe.invalid/interdit'],cwd=Path(__file__).resolve().parents[1],text=True,encoding='utf8',capture_output=True,timeout=20)
    assert r.returncode==2 and 'unrecognized arguments' in r.stderr
