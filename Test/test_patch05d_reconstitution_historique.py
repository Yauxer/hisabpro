# -*- coding: utf-8 -*-
"""Tests purs Patch 05D — reconstitution contrôlée des immobilisations."""
from decimal import Decimal
from services.immobilisations_reconciliation_service import (
    construire_lignes_acquisition_reconstituee,
    construire_lignes_reprise_ouverture,
    construire_lignes_correction_dotation,
)


def totals(lignes):
    d = sum((Decimal(str(x[1])) for x in lignes), Decimal('0'))
    c = sum((Decimal(str(x[2])) for x in lignes), Decimal('0'))
    return d, c


def test_acquisition_2026_tva_recuperable():
    l = construire_lignes_acquisition_reconstituee(
        '10000', '2000', '12000', '2355', '34551', '4481'
    )
    assert l[0][0] == '2355' and l[0][1] == Decimal('10000.00')
    assert l[1][0] == '34551' and l[1][1] == Decimal('2000.00')
    assert l[2][0] == '4481' and l[2][2] == Decimal('12000.00')
    assert totals(l) == (Decimal('12000.00'), Decimal('12000.00'))


def test_reprise_anterieure_ne_touche_pas_au_resultat():
    l = construire_lignes_reprise_ouverture(
        '10000', '3138.89', '2355', '28355', '1160'
    )
    assert l[0][:3] == ('2355', Decimal('10000.00'), Decimal('0.00'))
    assert l[1][:3] == ('28355', Decimal('0.00'), Decimal('3138.89'))
    assert l[2][:3] == ('1160', Decimal('0.00'), Decimal('6861.11'))
    assert all(not x[0].startswith(('6','7')) for x in l)
    assert totals(l) == (Decimal('10000.00'), Decimal('10000.00'))


def test_correction_dotation_insuffisante():
    l = construire_lignes_correction_dotation('861.11', '28355', '61935')
    assert l[0][:3] == ('61935', Decimal('861.11'), Decimal('0.00'))
    assert l[1][:3] == ('28355', Decimal('0.00'), Decimal('861.11'))
    assert totals(l) == (Decimal('861.11'), Decimal('861.11'))


def test_correction_dotation_excessive():
    l = construire_lignes_correction_dotation('-2083.33', '28355', '61935')
    assert l[0][:3] == ('28355', Decimal('2083.33'), Decimal('0.00'))
    assert l[1][:3] == ('61935', Decimal('0.00'), Decimal('2083.33'))
    assert totals(l) == (Decimal('2083.33'), Decimal('2083.33'))


if __name__ == '__main__':
    test_acquisition_2026_tva_recuperable()
    test_reprise_anterieure_ne_touche_pas_au_resultat()
    test_correction_dotation_insuffisante()
    test_correction_dotation_excessive()
    print('OK — 4 tests Patch 05D reconstitution historique')
