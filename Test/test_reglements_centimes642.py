from decimal import Decimal
import pytest
from pydantic import ValidationError
import schemas


@pytest.mark.parametrize('v',[0.005,0.001,1.001,'12.345',Decimal('0.005'),'1e-3',0.300000000001])
@pytest.mark.parametrize('schema',[schemas.ReglementCreate,schemas.ReglementUpdate])
def test_642_reglement_refuse_sous_centime_sans_arrondir(schema,v):
    d={'montant':v}
    if schema is schemas.ReglementCreate:d.update(date='2026-10-19',tiers='Tiers fictif642')
    with pytest.raises(ValidationError,match='centime'):schema(**d)


@pytest.mark.parametrize('v',[0.01,'0.10',400.25,Decimal('12.34'),'100.000','1e2',0.1+0.2])
def test_642_reglement_centimes_exacts_et_patch_notes_preserves(v):
    assert Decimal(str(schemas.ReglementCreate(date='2026-10-19',tiers='Tiers fictif642',montant=v).montant))==Decimal(str(v))
    assert schemas.ReglementUpdate(montant=v).montant==float(v)
    assert schemas.ReglementUpdate(notes='Note seule').montant is None
