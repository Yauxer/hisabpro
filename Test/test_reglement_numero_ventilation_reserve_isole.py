"""Le numéro technique de lot ne doit pas provenir d'un règlement manuel."""
from contextlib import closing
import pytest
from test_e2e_facturation_isole import application
from test_reglements_par_tiers_isole import dossier
from test_ras_lecture_conservation import client
from test_lecture_reglements_historiques import photo

@pytest.mark.parametrize('sens',['vente','achat'])
def test_numero_technique_refuse_avant_toute_mutation(application,sens):
    with closing(client(application)[0]) as api:
        _,ids,p=dossier(api,sens)
        avant=photo(application)
        r=api.post('/api/reglements',json={'facture_id':ids[0],'tiers_id':p['tiers_id'],
            'tiers':'Tiers fictif','date':p['date'],'montant':20,'mode':'virement',
            'numero':'VT-'+p['operation_id'].replace('-','')+'-01'})
        assert r.status_code==422,r.text
        assert photo(application)==avant

def test_numero_commercial_VT_habituel_reste_disponible(application):
    with closing(client(application)[0]) as api:
        _,ids,p=dossier(api)
        r=api.post('/api/reglements',json={'facture_id':ids[0],'tiers_id':p['tiers_id'],
            'tiers':'Tiers fictif','date':p['date'],'montant':20,'mode':'virement',
            'numero':'VT-2026-RECETTE-001'})
        assert r.status_code==201,r.text
        assert r.json()['numero']=='VT-2026-RECETTE-001'
