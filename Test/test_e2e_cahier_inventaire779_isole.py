"""Le stock60 est produit par le cycle commercial,puis compté etcomptabilisé viaUI."""
import pytest
from cahier_formulaires773_support import laboratoire,referentiels
from cahier_cycle775_support import cycle
from cahier_suite777_support import suite
from cahier_inventaire779_support import inventaire
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_779_cahier_cycle_inventaire_stock6600_etats_provisoires(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'inventaire779') as (api,page,sid,preuve):
  tiers,articles=referentiels(api,page,application,sid,preuve);cycle(api,page,application,sid,tiers,articles,preuve,tmp_path);suite(api,page,application,sid,tiers,articles,preuve);inventaire(api,page,application,sid,articles,preuve)
