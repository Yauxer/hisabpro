"""Contrats de l'assistant d'inventaire, sans données ni connexion externes."""
from decimal import Decimal
import pytest

from services.cloture_service import construire_ajustement, TYPES_AJUSTEMENT


@pytest.mark.parametrize('montant', ['NaN', 'Infinity', '-Infinity', 'invalide',
                                    '10000000000000000', '1e1000', True])
def test_montant_invalide_refuse_par_erreur_metier(montant):
    with pytest.raises(ValueError, match='montant|Montant'):
        construire_ajustement('cca', montant, '6125')


@pytest.mark.parametrize('type_', ['cca', 'pca', 'fnp', 'fae'])
def test_compte_fixe_ne_peut_devenir_un_compte_de_capital(type_):
    activite = '7124' if type_ in ('pca', 'fae') else '6125'
    with pytest.raises(ValueError, match='contrepartie'):
        construire_ajustement(type_, '1200', activite, '1111')


@pytest.mark.parametrize('compte', ['6inconnu', '6125;DROP', '61250000000', '6 125'])
def test_compte_malforme_refuse(compte):
    with pytest.raises(ValueError, match='Compte'):
        construire_ajustement('cca', '1200', compte)


@pytest.mark.parametrize('type_', TYPES_AJUSTEMENT)
def test_modeles_existants_equilibres_et_contrepassation_explicite(type_):
    activite = '7124' if type_ in ('pca', 'fae') else '6125'
    lignes, auto, comptes = construire_ajustement(type_, '1200.125', activite)
    assert sum(l['debit'] for l in lignes) == sum(l['credit'] for l in lignes) == Decimal('1200.13')
    assert auto == (type_ in ('cca', 'pca', 'fnp', 'fae'))
    assert comptes['compte_contrepartie'] == TYPES_AJUSTEMENT[type_]['compte_contrepartie']


def test_subdivision_du_compte_de_regularisation_conservee():
    lignes, _, _ = construire_ajustement('cca', '9999999999999999.99', '6125', '349101')
    assert lignes[0]['compte'] == '349101'
    assert lignes[0]['debit'] == Decimal('9999999999999999.99')
