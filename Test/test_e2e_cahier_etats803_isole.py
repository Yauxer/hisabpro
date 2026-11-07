"""Du cahier annuel à la clôture et au snapshot fiscal, en PostgreSQL temporaire."""
import pytest
from cahier_formulaires773_support import laboratoire,referentiels,DATA,ok
from test_e2e_cahier_immobilisation785_isole import capital,acquisition
from cahier_semestre789_support import semestre
from cahier_annuel791_support import annuel
from cahier_cloture793_support import cloturer_cahier
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

from cahier_etats803_support import verifier_etats

@pytest.mark.parametrize('largeur',[1440,390])
def test_803_etats_livre_inventaire_fec_annuel_cloture(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'etats803f') as (api,page,sid,preuve):
  tiers,articles=referentiels(api,page,application,sid,preuve);b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  capital(page,application,sid,preuve);immo=acquisition(api,page,application,sid,tiers['F-IMMO'],preuve);semestre(api,page,application,sid,tiers,articles,banque,preuve,tmp_path);annuel(api,page,application,sid,tiers,articles,banque,immo,preuve);cloturer_cahier(api,page,application,sid,preuve)

  verifier_etats(api,page,application,sid,preuve,tmp_path)
