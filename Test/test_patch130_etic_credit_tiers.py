from datetime import date
from decimal import Decimal
import pytest
import models
from services import etic_service as etic
from test_patch125_etic_requetes_orm import db, facture_source, ecriture_source


@pytest.mark.parametrize('tiers_cas', ['identique', 'absent', 'different', 'ecriture_avoir_incompatible'])
def test_nom_identique_ne_prouve_pas_identite_des_tiers(db, tiers_cas):
    origine, _ = facture_source(db, numero='FA-ORIGINE')
    cible, principale = facture_source(db, numero='FA-CIBLE')
    if tiers_cas == 'absent': origine.tiers_id = cible.tiers_id = None
    if tiers_cas == 'different':
        cible.tiers_id = principale.lignes[0].tiers_id = 2
    av = models.Avoir(societe_id=3, facture_id=origine.id, type='vente', numero='AV-EXCEDENT',
        date=date(2026, 7, 1), exercice=2026, tiers=origine.tiers, est_comptabilisee=True,
        lignes=[models.LigneAvoir(description='Crédit synthétique', quantite=1, prix_unitaire=125, tva=20)])
    db.add(av)
    e = ecriture_source(db, origine, av.date, -Decimal(150), journal='AV', reference=av.numero)
    if tiers_cas == 'ecriture_avoir_incompatible': e.lignes[0].tiers_id = 99
    db.flush()
    db.add(models.UtilisationAvoir(societe_id=3, avoir_id=av.id, facture_id=cible.id,
        date_utilisation=date(2026, 8, 1), montant=30, type_utilisation='imputation', statut='active'))
    db.flush()
    got = etic._ventilation_factures_par_compte(db, 3, 2026, 'vente')['3421']
    assert got['total_source'] == 90
    assert got['echues'] == (90 if tiers_cas == 'identique' else 0)
    assert bool(got['anomalies_sources']) == (tiers_cas != 'identique')
