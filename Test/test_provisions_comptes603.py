from decimal import Decimal
import pytest
from services.cloture_service import construire_ajustement


@pytest.mark.parametrize('type_,compte',[
    ('depreciation_stock','3942'),('depreciation_stock','1518'),('depreciation_stock','4501'),('depreciation_stock','3950'),
    ('depreciation_client','3911'),('depreciation_client','3941'),('depreciation_client','3943'),('depreciation_client','1518'),
    ('provision_risque','3911'),('provision_risque','3942'),
])
def test_603_refuse_compte_d_une_autre_famille(type_,compte):
    with pytest.raises(ValueError,match='contrepartie|provision'):
        construire_ajustement(type_,'123.45',compte_contrepartie=compte)


@pytest.mark.parametrize('type_,compte',[
    ('depreciation_stock','3911'),('depreciation_stock','3915'),('depreciation_stock','391101'),
    ('depreciation_client','3942'),('depreciation_client','394201'),
    ('provision_risque','1511'),('provision_risque','1558'),('provision_risque','4501'),('provision_risque','450801'),
])
def test_603_conserve_familles_subdivisions_et_montant(type_,compte):
    lignes,auto,comptes=construire_ajustement(type_,'123.45',compte_contrepartie=compte)
    assert not auto and comptes['compte_contrepartie']==compte
    assert lignes[1]['compte']==compte and lignes[1]['credit']==Decimal('123.45')
    assert sum(l['debit'] for l in lignes)==sum(l['credit'] for l in lignes)
