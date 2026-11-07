"""Installation antérieure : lecture explicite, aucune DDL automatique."""
from contextlib import closing
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier


def test_593_preparation_absente_sans_migration_ni_zero_presume(application):
    with closing(client(application)[0]) as api:
        avant=donnees_metier(application)
        d=ok(api.get('/api/tva/ras/preparation/2026/11'))
        assert d['disponible'] is False and d['migration_requise']=='099_ras_tva_details.sql'
        assert d['totaux'] is None and d['lignes']==[]
        r=api.get('/api/tva/ras/preparation/2026/11/export/pdf',params={'empreinte':d['empreinte_sha256']})
        assert r.status_code==409 and '099' in r.text
        assert donnees_metier(application)==avant
