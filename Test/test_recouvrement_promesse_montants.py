"""Une promesse de paiement ne peut contenir NaN, infini ou booléen."""
import pytest
from pydantic import ValidationError
from routers.recouvrement import RelanceCreate, RelanceUpdate


@pytest.mark.parametrize('schema', [RelanceCreate, RelanceUpdate])
@pytest.mark.parametrize('valeur', ['NaN', 'Infinity', '-Infinity', '1e999', True, False])
def test_promesse_invalides_refusees(schema, valeur):
    with pytest.raises(ValidationError):
        schema(facture_id=1, montant_promis=valeur)


@pytest.mark.parametrize('schema', [RelanceCreate, RelanceUpdate])
def test_promesse_facultative_ou_positive(schema):
    assert schema(facture_id=1, montant_promis=None).montant_promis is None
    assert schema(facture_id=1, montant_promis='400.25').montant_promis == 400.25
