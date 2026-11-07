from datetime import date
from decimal import Decimal
import pytest
import models
from services import etic_service as etic
from test_patch125_etic_requetes_orm import db, facture_source, ecriture_source


@pytest.mark.parametrize('type_', ['vente', 'achat'])
@pytest.mark.parametrize('defaut', [None, 'montant', 'sens', 'tiers', 'compte', 'double'])
def test_ras_exige_contrepartie_exacte_et_tiers_compatible(db, type_, defaut):
    f, _ = facture_source(db, type_=type_)
    f.ras_taux = 10
    compte = '3421' if type_ == 'vente' else '4411'
    etat = '3453' if type_ == 'vente' else '4457'
    e = ecriture_source(db, f, date(2026, 7, 1), -Decimal(10), journal='OD', compte=compte)
    contre = models.LigneEcriture(compte=etat, debit=10 if type_ == 'vente' else 0,
                                  credit=10 if type_ == 'achat' else 0)
    e.lignes.append(contre)
    if defaut == 'montant':
        contre.debit = 9 if type_ == 'vente' else 0
        contre.credit = 9 if type_ == 'achat' else 0
    if defaut == 'sens': contre.debit, contre.credit = contre.credit, contre.debit
    if defaut == 'tiers': e.lignes[0].tiers_id = 99
    if defaut == 'compte': contre.compte = '9999'
    if defaut == 'double':
        ecriture_source(db, f, e.date, -Decimal(10), journal='OD', compte=compte).lignes.append(
            models.LigneEcriture(compte=etat, debit=contre.debit, credit=contre.credit))
    db.flush()
    got = etic._ventilation_factures_par_compte(db, 3, 2026, type_)[compte]
    assert got['total_source'] == 110
    assert got['echues'] == (110 if defaut is None else 0)
    assert bool(got['anomalies_sources']) == (defaut is not None)
