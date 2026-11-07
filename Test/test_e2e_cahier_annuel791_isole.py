"""Exercice complet produit par les formulaires, pas par injection de journal attendu."""
import pytest
from cahier_formulaires773_support import laboratoire,referentiels,DATA,ok
from test_e2e_cahier_immobilisation785_isole import capital,acquisition
from cahier_semestre789_support import semestre
from cahier_annuel791_support import annuel
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_791_cinquante_operations_formulaires_balance_etats_annuels(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'annuel791') as (api,page,sid,preuve):
  tiers,articles=referentiels(api,page,application,sid,preuve);b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  capital(page,application,sid,preuve);immo=acquisition(api,page,application,sid,tiers['F-IMMO'],preuve);semestre(api,page,application,sid,tiers,articles,banque,preuve,tmp_path);annuel(api,page,application,sid,tiers,articles,banque,immo,preuve)
