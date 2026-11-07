"""CGI2026 : cas117-V-b explicitement qualifié, aucune inférence comptable."""
from decimal import Decimal
import pytest
from pydantic import ValidationError
from services.ras_tva_simulation_service import SimulationRasTvaIn, simuler


def donnees(**kw):
    d = {'date_paiement': '2026-10-18', 'payeur': 'pm_privee_assujettie',
        'prestataire': 'pp_assujettie', 'prestation_liste_b': True,
        'exclusion': 'aucune_apres_controle', 'attestation': 'presentee',
        'date_attestation': '2026-09-01', 'reference_attestation': 'FICTIF-REGULARITE-559',
        'montant_paiement_ttc': '600', 'tva_paiement': '100'}
    d.update(kw)
    return d


def calcul(**kw):
    return simuler(SimulationRasTvaIn.model_validate(donnees(**kw)))


@pytest.mark.parametrize('payeur', ['pm_privee_assujettie', 'pp_rnr_rns_assujettie'])
def test_attestation_montant_partiel_sur_tva_seule(payeur):
    r = calcul(payeur=payeur)
    assert (r['statut'], r['base_tva'], r['taux_retenue_tva'], r['retenue_tva'],
        r['net_apres_cette_ras_tva'], r['mois_reversement']) == ('calcule', '100.00', '75', '75.00', '525.00', '2026-11')


def test_absence_attestation_tva_entierement_retenue():
    r = calcul(attestation='absente', date_attestation=None, reference_attestation=None)
    assert r['retenue_tva'] == '100.00' and r['net_apres_cette_ras_tva'] == '500.00'


def test_fin_annee_arrondi_et_tva_nulle_explicite():
    r = calcul(date_paiement='2026-12-31', date_attestation='2026-11-01',
               montant_paiement_ttc='0.02', tva_paiement='0.01')
    assert r['retenue_tva'] == '0.01' and r['net_apres_cette_ras_tva'] == '0.01'
    assert r['mois_reversement'] == '2027-01'
    r = calcul(tva_paiement='0')
    assert r['statut'] == 'calcule' and r['retenue_tva'] == '0.00'


@pytest.mark.parametrize('kw', [
    {'date_paiement': None}, {'payeur': 'a_qualifier'}, {'prestataire': 'a_qualifier'},
    {'prestation_liste_b': None}, {'exclusion': 'a_qualifier'}, {'attestation': 'a_qualifier'},
    {'date_attestation': None}, {'reference_attestation': '  '},
    {'date_attestation': '2026-10-19'}, {'date_attestation': '2026-04-18'},
    {'tva_paiement': None}, {'montant_paiement_ttc': None},
    {'montant_paiement_ttc': '0', 'tva_paiement': '0'},
])
def test_manquant_ou_incoherent_reste_inconnu(kw):
    r = calcul(**kw)
    assert r['statut'] == 'a_completer' and r['motifs']
    assert r['retenue_tva'] is None and r['net_apres_cette_ras_tva'] is None
    assert r['taux_retenue_tva'] is None


@pytest.mark.parametrize('kw', [{'payeur': 'autre'}, {'prestataire': 'autre'},
    {'prestation_liste_b': False}, {'date_paiement': '2025-12-31'}, {'date_paiement': '2027-01-01'}])
def test_hors_perimetre_ne_signifie_pas_absence_de_ras(kw):
    r = calcul(**kw)
    assert r['statut'] == 'non_couvert' and r['retenue_tva'] is None


@pytest.mark.parametrize('motif', ['energie_eau_reseaux', 'assainissement_compteurs',
    'telecommunications', 'courtier_assurances', 'petites_prestations_justifiees'])
def test_exclusion_exige_reference_et_ne_presume_aucun_seuil(motif):
    assert calcul(exclusion=motif)['retenue_tva'] is None
    r = calcul(exclusion=motif, reference_exclusion='JUSTIFICATION-FICTIVE-559')
    assert r['statut'] == 'exclu' and r['retenue_tva'] == '0.00'


@pytest.mark.parametrize('champ', ['montant_paiement_ttc', 'tva_paiement'])
@pytest.mark.parametrize('valeur', ['NaN', 'Infinity', '-Infinity', True, -1, '1e100', '1.001'])
def test_nombres_invalides_refuses(champ, valeur):
    with pytest.raises(ValidationError):
        SimulationRasTvaIn.model_validate(donnees(**{champ: valeur}))


def test_coherence_tva_et_champs_non_prevus():
    with pytest.raises(ValidationError):
        SimulationRasTvaIn.model_validate(donnees(tva_paiement='601'))
    with pytest.raises(ValidationError):
        SimulationRasTvaIn.model_validate(donnees(prestation_liste_b='true'))
    with pytest.raises(ValidationError):
        SimulationRasTvaIn.model_validate(donnees(taux=0))
    with pytest.raises(ValidationError):
        SimulationRasTvaIn.model_validate(donnees(attestation='absente'))


def test_moins_de_six_mois_et_jour_anniversaire():
    assert calcul(date_paiement='2026-07-30', date_attestation='2026-01-31')['statut'] == 'calcule'
    assert calcul(date_paiement='2026-07-31', date_attestation='2026-01-31')['statut'] == 'a_completer'


def test_grands_montants_centimes_preserves():
    r = calcul(montant_paiement_ttc='9999999999999999.99', tva_paiement='1000000000000000.01')
    assert r['retenue_tva'] == '750000000000000.01'
    assert Decimal(r['net_apres_cette_ras_tva']) + Decimal(r['retenue_tva']) == Decimal('9999999999999999.99')
