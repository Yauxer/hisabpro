from datetime import date
from decimal import Decimal
import pytest
import models
from services import etic_service as etic
from test_patch125_etic_requetes_orm import db, facture_source, ecriture_source


def source_reglement(db, lie=False):
    f, _ = facture_source(db)
    r = models.Reglement(societe_id=3, facture_id=f.id, tiers_id=1, tiers='Test',
                        date=date(2026, 7, 1), montant=30, statut='complet')
    db.add(r)
    db.flush()
    e = ecriture_source(db, f, r.date, -Decimal(30), reference=f'REG-{r.id}')
    e.lignes.append(models.LigneEcriture(compte='5141', debit=30, credit=0))
    if lie:
        r.ecriture_id = e.id
    db.flush()
    return f, r, e


@pytest.mark.parametrize('lie', [True, False])
def test_reference_technique_exacte_et_lien_non_modifie(db, lie):
    f, r, e = source_reglement(db, lie)
    original = r.ecriture_id
    got = etic._ventilation_factures_par_compte(db, 3, 2026, 'vente')['3421']
    assert got['total_source'] == got['echues'] == 90
    assert got['anomalies_sources'] == []
    assert r.ecriture_id == original


@pytest.mark.parametrize('defaut', ['tiers', 'date', 'montant', 'journal', 'desequilibre', 'reference', 'lien_invalide', 'double', 'tiers_absent'])
def test_historique_conflit_reste_non_qualifie(db, defaut):
    f, r, e = source_reglement(db)
    if defaut == 'tiers': e.lignes[0].tiers_id = 99
    if defaut == 'date': e.date = date(2026, 7, 2)
    if defaut == 'montant': e.lignes[0].credit = 31
    if defaut == 'journal': e.journal = 'OD'
    if defaut == 'desequilibre': e.lignes[1].debit = 29
    if defaut == 'reference': e.reference = f'REG-0{r.id}'
    if defaut == 'lien_invalide': r.ecriture_id = 999
    if defaut == 'tiers_absent': r.tiers_id = f.tiers_id = None
    if defaut == 'double': ecriture_source(db, f, date(2026, 7, 2), -Decimal(31), reference=e.reference)
    db.flush()
    got = etic._ventilation_factures_par_compte(db, 3, 2026, 'vente')['3421']
    assert got['total_source'] == 90
    assert got['echues'] == 0
    assert got['anomalies_sources']
    assert r.ecriture_id == (999 if defaut == 'lien_invalide' else None)
