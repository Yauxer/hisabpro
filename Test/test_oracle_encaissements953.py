"""Arithmétique indépendante du moteur fiscal, jeu fictif fourni à la recette."""
from collections import defaultdict
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def variante():
    return json.loads((ROOT / 'docs/recette/DONNEES_ENCAISSEMENTS_953.json').read_text(encoding='utf8'))


def test_953_oracle_mensuel_independant_des_encaissements():
    x = variante()
    # Cumul par facture pour répartir l'arrondi de centime entre les mois.
    cent = lambda v: v.quantize(D('.01'), rounding=ROUND_HALF_UP)
    jan = cent(D(10000) / 6)
    fev = D(27000) / 6 - jan
    mars = cent(D(5000 + 3000) / 6)
    mai = D(18000) / 6 - mars
    juin = D(24000 + 120000) / 6
    collectee = [jan, fev, mars, D(0), mai, juin] + [D(0)] * 6
    recup = [D(6800), D(2400), D(2400)] + [D(0)] * 9
    credit = D(0)
    for m, c, r in zip(x['tva_mois'], collectee, recup, strict=True):
        net = c - r - credit
        assert list(map(D, [m[k] for k in ['collectee', 'recuperable', 'credit_ouverture', 'due', 'credit_fin']])) == [c, r, credit, max(net, D(0)), max(-net, D(0))]
        credit = max(-net, D(0))
    assert sum(collectee) == D('31500') and sum(recup) == D('11600')
    assert sum(D(m['due']) for m in x['tva_mois']) == D('19900')


def test_953_oracle_journal_bilan_et_tva_non_exigible():
    x = variante(); solde = defaultdict(lambda: D(0))
    assert len(x['operations']) == 50 and sum(len(o['lignes']) for o in x['operations']) == 118
    assert len({o['reference_recette'] for o in x['operations']}) == 50
    for o in x['operations']:
        assert sum(D(l['debit']) for l in o['lignes']) == sum(D(l['credit']) for l in o['lignes'])
        for l in o['lignes']: solde[l['compte']] += D(l['debit']) - D(l['credit'])
    assert solde['4455'] == -D(2400) and solde['4456'] == 0
    assert solde['5141'] == D('287730')
    assert -sum(v for k, v in solde.items() if k.startswith(('6', '7'))) == D('106409.75')


def test_953_jeu_debit_original_conserve_et_contextes_restaures():
    original = json.loads((ROOT / 'docs/recette/jeu_donnees_recette.json').read_text(encoding='utf8'))
    x = variante()
    assert original['societe']['regime_tva'] == 'debit' and x['societe']['regime_tva'] == 'encaissement'
    refs = lambda data: {o['reference_recette']: o for o in data['operations']}
    a, b = refs(original), refs(x)
    assert set(a) - set(b) == {'TVA-12'} and set(b) - set(a) == {'TVA-05'}
    for ref in set(a) & set(b) - {'TVA-01', 'TVA-02', 'TVA-03'}:
        assert a[ref] == b[ref], ref
