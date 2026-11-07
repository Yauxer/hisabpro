"""Installation entière avec migrations explicites, sans adresse DB externe."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def rapport_data(p):
    return json.loads(p.read_text(encoding='utf-8').split('```json\n')[1].split('```')[0])


def lancer(script, rapport):
    env = dict(os.environ, PYTHON_DOTENV_DISABLED='1', PYTHONUTF8='1')
    commande = [sys.executable, '-X', 'utf8', *script, str(rapport)]
    r = subprocess.run(commande, cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding='utf-8', timeout=180)
    assert r.returncode == 0, (r.stdout[-7000:], r.stderr[-3000:])
    data = rapport_data(rapport)
    assert data['erreur'] is None and data['cluster_supprime'] is True
    return data


def test_installation_084_rejeux_droits_refus_et_tables_vides(tmp_path):
    data = lancer(['Test/recette_installation_vierge_084.py','--rapport'], tmp_path/'084.md')
    assert data['statut'] == '75_SQL_et_11_rejeux_valides_installation_runtime_incomplete'
    assert len(data['appliquees']) == 86
    assert len({x['fichier'] for x in data['appliquees']}) == 75
    assert data['extensions_absentes_avant_application'] and data['extension_identique_apres_rejeu']
    assert len(data['zero_final']) == 25 and not any(data['zero_final'].values())
    assert len(data['refus_extension']) == 17
    assert data['role_runtime'] == ['hisabpro','hisabpro',True,False,False,False,False,False]
    assert data['runtime_create_public'] is False
    for row in data['appliquees']:
        assert row['sha256'] == hashlib.sha256((ROOT/'hisabpro-backend'/row['fichier']).read_bytes()).hexdigest()
    assert [r['fichier'] for r in data['appliquees'][-4:]] == [
        '083_ras_reglements.sql','084_rapprochement_ventilations.sql']*2


def test_socle_082_default_preserve_sans_extensions(tmp_path):
    script = "import sys;from pathlib import Path;sys.path.insert(0,'Test');" \
             "from recette_installation_vierge_consolidee import executer;" \
             "raise SystemExit(executer(rapport=Path(sys.argv[1])))"
    data = lancer(['-c',script],tmp_path/'082.md')
    assert data['statut'] == '73_SQL_et_9_rejeux_valides_installation_runtime_incomplete'
    assert len(data['appliquees']) == 82 and len(data['zero_final']) == 22
    assert not any(r['fichier'].startswith(('083_','084_')) for r in data['appliquees'])
    assert 'extensions_absentes_avant_application' not in data
