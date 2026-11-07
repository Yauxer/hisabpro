"""Référentiels exacts du cahier via Edge/API/PostgreSQL natif isolé."""
import pytest
from cahier_formulaires773_support import laboratoire,referentiels
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_773_sept_tiers_et_trois_articles_cahier_interface(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path) as (api,page,sid,preuve):referentiels(api,page,application,sid,preuve)
