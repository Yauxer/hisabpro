"""Validation avant mutation des montants d'acompte et d'imputation."""
import pytest
from pydantic import ValidationError

from acomptes import AcompteCreate, ImputerIn


@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), -float('inf'), 'NaN', 'Infinity', True, False, {}, [], 'invalide'])
@pytest.mark.parametrize('schema,champ', [(AcompteCreate, 'montant'), (AcompteCreate, 'taux_tva'), (ImputerIn, 'montant')])
def test_acompte_refuse_nombre_non_fini_ou_booleen(schema, champ, valeur):
    payload = {'facture_id': 1} if schema is ImputerIn else {'tiers': 'Fictif', 'date': '2026-05-01', 'montant': 400}
    with pytest.raises(ValidationError):
        schema(**{**payload, champ: valeur})


def test_imputation_automatique_et_valeurs_finies_restent_disponibles():
    assert ImputerIn(facture_id=1).montant is None
    assert ImputerIn(facture_id=1, montant=None).montant is None
    assert ImputerIn(facture_id=1, montant='400.25').montant == 400.25
    create = AcompteCreate(tiers='Fictif', date='2026-05-01', montant='400.25', taux_tva='20')
    assert create.montant == 400.25 and create.taux_tva == 20
