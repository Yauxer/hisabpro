"""Un taux n'est pas un montant : combinaison HT/TVA refusée même si RAS arrondie0."""
from contextlib import closing
import pytest
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    preparer, demande,
)
from test_ras_lecture_conservation import client
from test_permissions_tva_runtime_isole import donnees_metier


@pytest.mark.parametrize('taux',[0, 0.00000001, 0.0001, 0.001, 10])
def test_577_taux_ht_non_nul_jamais_arrondi_a_zero(application,taux):
    with closing(client(application)[0]) as api:
        _,r=preparer(api,taux_ht=taux)
        avant=donnees_metier(application)
        reponse=api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=demande())
        assert reponse.status_code==(200 if taux==0 else 409),reponse.text
        if taux!=0:assert 'HT' in reponse.text
        else:assert reponse.json()['dossier']['simulation']['retenue_tva']=='75.00'
        assert donnees_metier(application)==avant
