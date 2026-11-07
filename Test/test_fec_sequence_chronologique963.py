"""Contrôle FEC : numérotation chronologique selon la date comptable (963)."""
from datetime import date, datetime
from types import SimpleNamespace

from services.fec_service import controler_fec
from test_patch053_comptabilite_auxiliaire_fec_avis24 import _ligne, _ecriture


def _bq(id_, seq, jour, cree):
    ec = _ecriture([_ligne('5141', debit=100), _ligne('7111', credit=100)])
    ec.id, ec.numero_ecriture, ec.journal, ec.date, ec.date_piece = id_, f'BQ-2027-{seq:04d}', 'BQ', jour, jour
    ec.created_at, ec.reference = cree, f'REF-{seq}'
    return ec


def _codes(ecritures):
    return {b['code'] for b in controler_fec(ecritures, 2027)['bloquants']}


def test_963_meme_jour_valide_dans_un_autre_ordre_que_la_creation_accepte():
    # Brouillons créés avant (id 141) mais validés après des écritures du même jour.
    ecritures = [_bq(147, 1, date(2027, 1, 1), datetime(2026, 9, 2)),
                 _bq(148, 2, date(2027, 1, 1), datetime(2026, 9, 2, 1)),
                 _bq(141, 3, date(2027, 1, 1), datetime(2026, 8, 1)),
                 _bq(140, 4, date(2027, 1, 2), datetime(2026, 8, 1))]
    assert 'SEQUENCE_NON_CHRONOLOGIQUE' not in _codes(ecritures)


def test_963_date_qui_recule_dans_la_numerotation_toujours_refusee():
    ecritures = [_bq(1, 1, date(2027, 1, 5), datetime(2027, 1, 5)),
                 _bq(2, 2, date(2027, 1, 3), datetime(2027, 1, 3))]
    assert 'SEQUENCE_NON_CHRONOLOGIQUE' in _codes(ecritures)
