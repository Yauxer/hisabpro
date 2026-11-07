"""Recette commerciale avant IS avec navigation terminée, sans changer les oracles."""
import pytest
from navigation823_support import navigations_completes823
from test_e2e_cahier_avant_is817_isole import (
 test_817_cahier_connecte_balance_et_grand_livre_avant_is as parcours_complet,
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_823_avant_is_connecte_navigation_complete(application,largeur,tmp_path,navigations_completes823):
 parcours_complet(application,largeur,tmp_path)
