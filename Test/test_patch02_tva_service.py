# -*- coding: utf-8 -*-
"""Tests autonomes du moteur TVA Patch 02A (sans base de données)."""
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.tva_service import (
    allouer_paiement, date_paiement_effective, total_ventilation, ventilation_facture
)


def ligne(ht, taux, remise=0, remise2=0, rabais=0):
    return SimpleNamespace(
        quantite=1, prix_unitaire=ht, tva=taux,
        remise=remise, remise2=remise2, rabais=rabais,
    )


def facture(lignes, **kwargs):
    valeurs = dict(
        lignes=lignes,
        remise_globale=0, ristourne=0, escompte=0,
        frais_transport_ht=0, frais_transport_tva=20,
        frais_emballage_ht=0, frais_emballage_tva=20,
    )
    valeurs.update(kwargs)
    return SimpleNamespace(**valeurs)


def test_facture_simple_20():
    v = ventilation_facture(facture([ligne(1000, 20)]))
    assert v[Decimal('20')]['base'] == Decimal('1000.00')
    assert v[Decimal('20')]['tva'] == Decimal('200.00')
    assert v[Decimal('20')]['ttc'] == Decimal('1200.00')


def test_paiement_partiel_50_pourcent():
    v = ventilation_facture(facture([ligne(1000, 20)]))
    p = allouer_paiement(v, Decimal('600'))
    assert p[Decimal('20')]['base'] == Decimal('500.00')
    assert p[Decimal('20')]['tva'] == Decimal('100.00')


def test_facture_multi_taux():
    v = ventilation_facture(facture([ligne(1000, 20), ligne(500, 10)]))
    t = total_ventilation(v)
    assert t['base'] == Decimal('1500.00')
    assert t['tva'] == Decimal('250.00')
    assert t['ttc'] == Decimal('1750.00')
    p = allouer_paiement(v, Decimal('875'))
    assert p[Decimal('20')]['tva'] == Decimal('100.00')
    assert p[Decimal('10')]['tva'] == Decimal('25.00')


def test_remises_et_escompte():
    f = facture(
        [ligne(1000, 20, remise=10)],
        remise_globale=10,
        ristourne=0,
        escompte=2,
        frais_transport_ht=100,
        frais_transport_tva=20,
    )
    v = ventilation_facture(f)
    avant_escompte = ventilation_facture(f, appliquer_escompte=False)
    # Ligne : 1000 * 90% * 90% = 810 ; + transport 100 ; puis escompte 2% = 891,80
    assert avant_escompte[Decimal('20')]['base'] == Decimal('910.00')
    assert v[Decimal('20')]['base'] == Decimal('891.80')
    assert v[Decimal('20')]['tva'] == Decimal('178.36')


def test_date_effective_reglement():
    direct = SimpleNamespace(mode='virement', statut='complet', date=date(2026, 8, 10), date_encaissement=None)
    cheque = SimpleNamespace(mode='cheque', statut='encaisse', date=date(2026, 8, 10), date_encaissement=date(2026, 8, 14))
    attente = SimpleNamespace(mode='cheque', statut='portefeuille', date=date(2026, 8, 10), date_encaissement=None)
    assert date_paiement_effective(direct) == date(2026, 8, 10)
    assert date_paiement_effective(cheque) == date(2026, 8, 14)
    assert date_paiement_effective(attente) is None


if __name__ == '__main__':
    tests = [v for k, v in globals().copy().items() if k.startswith('test_') and callable(v)]
    for test in tests:
        test()
    print(f'OK — {len(tests)} tests TVA Patch 02A')
