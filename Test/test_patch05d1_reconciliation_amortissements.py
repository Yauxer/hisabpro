# -*- coding: utf-8 -*-
"""Tests purs Patch 05D.1 — prise en compte des écritures correctrices."""
from decimal import Decimal
from types import SimpleNamespace
from services.immobilisations_reconciliation_service import (
    _references_amortissement_patterns,
    _montants_par_compte,
)


def ligne(compte, debit='0', credit='0'):
    return SimpleNamespace(compte=compte, debit=Decimal(debit), credit=Decimal(credit))


def test_patterns_incluent_am_et_corrections():
    assert _references_amortissement_patterns(42) == ('AM-%-42', 'RECON-AMORT-%-42')


def test_correction_debit_28_reduit_amortissement_cumule():
    lignes = [
        ligne('28355', credit='2000.00'),
        ligne('28355', debit='861.11'),
    ]
    d = _montants_par_compte(lignes, '28', 'credit')
    assert d['28355'] == Decimal('1138.89')


def test_correction_credit_6_reduit_dotation_exercice():
    lignes = [
        ligne('61935', debit='2000.00'),
        ligne('61935', credit='861.11'),
    ]
    d = _montants_par_compte(lignes, '6', 'debit')
    assert d['61935'] == Decimal('1138.89')


if __name__ == '__main__':
    test_patterns_incluent_am_et_corrections()
    test_correction_debit_28_reduit_amortissement_cumule()
    test_correction_credit_6_reduit_dotation_exercice()
    print('OK — 3 tests Patch 05D.1 rapprochement amortissements')
