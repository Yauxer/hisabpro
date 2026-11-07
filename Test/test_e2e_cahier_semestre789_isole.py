"""Parcours connecté du cahier jusqu'au30/06/2025, Edge et PostgreSQL nonce réels."""
import pytest
from cahier_formulaires773_support import laboratoire,referentiels,DATA,ok
from test_e2e_cahier_immobilisation785_isole import capital,acquisition
from cahier_semestre789_support import semestre
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_789_semestre_connecte_capital_actif_marchandises_services_effets_tva(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'semestre789') as (api,page,sid,preuve):
  tiers,articles=referentiels(api,page,application,sid,preuve);b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  capital(page,application,sid,preuve);acquisition(api,page,application,sid,tiers['F-IMMO'],preuve);semestre(api,page,application,sid,tiers,articles,banque,preuve,tmp_path)
