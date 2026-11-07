from contextlib import closing
import pytest
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ajustements_inventaire_isole import exercice, donnees
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier


@pytest.mark.parametrize('lien',['ecriture_id','contrepassation_id'])
def test_613_journal_ne_detache_pas_une_piece_inventaire(application,lien):
    with closing(client(application)[0]) as api:
        exercice(api)
        a=ok(api.post('/api/cloture/ajustements?exercice=2025',json=donnees()))
        avant=donnees_metier(application)
        r=api.delete(f"/api/ecritures/{a[lien]}")
        assert r.status_code==409,r.text
        assert 'Clôture' in r.json()['detail']
        assert donnees_metier(application)==avant
        assert ok(api.get('/api/cloture/contrepassations?exercice=2026'))['total']==1
        # La suppression métier ordinaire retire le dossier et ses deux brouillons.
        ok(api.delete(f"/api/cloture/ajustements/{a['id']}"))
        assert ok(api.get('/api/cloture/ajustements?exercice=2025'))==[]
        assert ok(api.get('/api/cloture/contrepassations?exercice=2026'))['total']==0
        assert api.delete(f"/api/ecritures/{a[lien]}").status_code==404
        manuel=ok(api.post('/api/ecritures',json={'date':'2025-02-01','journal':'BQ',
            'libelle':'Brouillon manuel fictif613','reference':'MANUEL-FICTIF613',
            'lignes':[{'compte':'5141','debit':1},{'compte':'1111','credit':1}]}),201)
        assert api.delete(f"/api/ecritures/{manuel['id']}").status_code==204
