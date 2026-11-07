from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.stock_utils import construire_lignes_rapprochement, money


def _dc(lignes):
    d = sum((money(x['debit']) for x in lignes), Decimal('0.00'))
    c = sum((money(x['credit']) for x in lignes), Decimal('0.00'))
    return d, c


def test_premier_stock_final():
    lignes = construire_lignes_rapprochement(
        {'3111': {'valeur': Decimal('44626.00'), 'variations': {'6114'}}},
        {'3111': Decimal('0.00')},
    )
    assert lignes == [
        {'compte': '3111', 'libelle': 'Stock final', 'debit': Decimal('44626.00'), 'credit': Decimal('0.00')},
        {'compte': '6114', 'libelle': 'Variation de stock', 'debit': Decimal('0.00'), 'credit': Decimal('44626.00')},
    ]
    assert _dc(lignes) == (Decimal('44626.00'), Decimal('44626.00'))


def test_baisse_stock_exercice_suivant():
    lignes = construire_lignes_rapprochement(
        {'3111': {'valeur': Decimal('43000.00'), 'variations': {'6114'}}},
        {'3111': Decimal('44626.00')},
    )
    assert lignes[0]['compte'] == '6114' and lignes[0]['debit'] == Decimal('1626.00')
    assert lignes[1]['compte'] == '3111' and lignes[1]['credit'] == Decimal('1626.00')
    assert _dc(lignes) == (Decimal('1626.00'), Decimal('1626.00'))


def test_deja_rapproche_aucune_ligne():
    lignes = construire_lignes_rapprochement(
        {'3111': {'valeur': Decimal('44626.00'), 'variations': {'6114'}}},
        {'3111': Decimal('44626.00')},
    )
    assert lignes == []


def test_mapping_ambigu_refuse():
    try:
        construire_lignes_rapprochement(
            {'3111': {'valeur': Decimal('100.00'), 'variations': {'6114', '6124'}}},
            {'3111': Decimal('0.00')},
        )
    except ValueError as exc:
        assert 'plusieurs comptes de variation' in str(exc)
    else:
        raise AssertionError('Un mapping ambigu doit être refusé')


if __name__ == '__main__':
    test_premier_stock_final()
    test_baisse_stock_exercice_suivant()
    test_deja_rapproche_aucune_ligne()
    test_mapping_ambigu_refuse()
    print('OK — 4 tests Patch 06A stock de clôture')
