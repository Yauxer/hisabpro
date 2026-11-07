"""Base sans migration 129 : la TVA reste calculée, le gel est signalé indisponible. PG nonce."""
from contextlib import closing

from test_compensations_tva953_isole import (  # noqa: F401
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, dossier, ok,
)


def test_959_sans_migration129_calcul_disponible_et_depot_refuse(application):
    with closing(client(application)[0]) as api:
        dossier(api, application)
        r = ok(api.get('/api/tva/declaration', params={'exercice': 2025, 'mois': 1}))
        assert r['declaration_deposee'] is None
        assert any('migration 129' in a for a in r['alertes'])
        assert api.get('/api/tva/declarations-deposees', params={'exercice': 2025}).status_code == 503
        assert api.post('/api/tva/declarations-deposees', json={'exercice': 2025, 'mois': 1,
            'date_depot': '2025-02-15', 'reference_depot': 'X'}).status_code == 503
