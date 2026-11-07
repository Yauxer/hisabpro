"""Format de montants serveur sous Node, sans conversion en flottant."""
import json
from pathlib import Path
import subprocess


def test_format_exact_pour_petits_grands_et_invalides():
    root = Path(__file__).resolve().parents[1]
    script = """
import {montantDecimalExact as f} from './src/utils/montantDecimalExact.js';
console.log(JSON.stringify(['0.00','1200.13','9249999999999999.98','-750000000000000.01',null,'NaN','1e6',100,'800','350.5','9999999999999999','1.001'].map(f)));
"""
    r = subprocess.run(['node', '--input-type=module', '-e', script], cwd=root,
        text=True, encoding='utf8', capture_output=True, timeout=20)
    assert r.returncode == 0, r.stderr
    valeurs = json.loads(r.stdout)
    assert valeurs[:4] == ['0,00', '1.200,13', '9.249.999.999.999.999,98', '-750.000.000.000.000,01']
    assert valeurs[4:8] == ['À vérifier'] * 4
    assert valeurs[8:] == ['800,00','350,50','9.999.999.999.999.999,00','À vérifier']
