from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import sys

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.immobilisations_service import (  # noqa: E402
    ventilation_acquisition, calculer_tableau_amortissement,
    coefficient_degressif, resultat_cession,
)


def immo(**kw):
    base = dict(
        valeur_brute=Decimal('100000'), valeur_residuelle=Decimal('0'),
        amortissable=True, duree_amort=5, methode='lineaire', taux_degressif=None,
        date_acquisition=date(2026, 6, 15), date_mise_en_service=date(2026, 7, 1),
        date_sortie=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def run():
    v = ventilation_acquisition(100000, 20, 100)
    assert v['tva_recuperable'] == Decimal('20000.00')
    assert v['cout_entree'] == Decimal('100000.00')
    assert v['ttc'] == Decimal('120000.00')

    v = ventilation_acquisition(100000, 20, 50)
    assert v['tva_recuperable'] == Decimal('10000.00')
    assert v['tva_non_recuperable'] == Decimal('10000.00')
    assert v['cout_entree'] == Decimal('110000.00')
    assert v['ttc'] == Decimal('120000.00')

    p = calculer_tableau_amortissement(immo())
    assert p[0]['annee'] == 2026 and p[0]['dotation'] == Decimal('10000.00'), p
    assert p[1]['dotation'] == Decimal('20000.00')
    assert p[-1]['annee'] == 2031 and p[-1]['dotation'] == Decimal('10000.00')
    assert p[-1]['cumul'] == Decimal('100000.00')
    assert p[-1]['valeur_nette'] == Decimal('0.00')

    assert coefficient_degressif(4) == Decimal('1.5')
    assert coefficient_degressif(5) == Decimal('2')
    assert coefficient_degressif(7) == Decimal('3')
    pd = calculer_tableau_amortissement(immo(
        methode='degressif', taux_degressif=Decimal('2'),
        date_acquisition=date(2026, 4, 18), date_mise_en_service=date(2026, 5, 1)
    ))
    assert pd[0]['debut_periode'] == date(2026, 4, 1)
    assert pd[-1]['cumul'] == Decimal('100000.00'), pd

    c = resultat_cession(immo(), date(2028, 6, 30), 70000)
    assert c['vnc'] > Decimal('0')
    assert c['resultat_cession'] == Decimal('70000.00') - c['vnc']

    terrain = immo(amortissable=False, duree_amort=None)
    assert calculer_tableau_amortissement(terrain) == []

    print('OK — 6 tests Immobilisations Patch 03')


if __name__ == '__main__':
    run()
