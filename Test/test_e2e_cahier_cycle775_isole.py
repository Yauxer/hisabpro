"""Cycle commercial du cahier, valeurs exactes2025,aucune donnée réelle."""
import pytest
from cahier_formulaires773_support import laboratoire,referentiels
from cahier_cycle775_support import cycle
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_775_achats_acompte_lettrage_devis_bc_bl_facture_reglement_cahier(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'cycle775') as (api,page,sid,preuve):
  tiers,articles=referentiels(api,page,application,sid,preuve);cycle(api,page,application,sid,tiers,articles,preuve,tmp_path)
