"""Continuation du cahier dans une même société :aucun journal attendu injecté."""
import pytest
from cahier_formulaires773_support import laboratoire,referentiels
from cahier_cycle775_support import cycle
from cahier_suite777_support import suite
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_777_cahier_cheque_avoir_credit_vente_stock60(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'suite777') as (api,page,sid,preuve):
  tiers,articles=referentiels(api,page,application,sid,preuve);cycle(api,page,application,sid,tiers,articles,preuve,tmp_path);suite(api,page,application,sid,tiers,articles,preuve)
