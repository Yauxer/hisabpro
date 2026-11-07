"""Déclarations TVA déposées figées (959). PostgreSQL nonce, données fictives."""
from contextlib import closing
from decimal import Decimal as D
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from test_compensations_tva953_isole import (  # noqa: F401
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, dossier, ok,
)

ROOT = Path(__file__).resolve().parents[1]


def _appliquer_129(app):
    raw = app['engine'].raw_connection()
    try:
        raw.autocommit = True
        with raw.cursor() as cur:
            cur.execute((ROOT / 'hisabpro-backend/129_declarations_tva_deposees.sql').read_text(encoding='utf8'))
    finally:
        raw.close()


def decl(api, mois):
    return ok(api.get('/api/tva/declaration', params={'exercice': 2025, 'mois': mois}))


def operation(api, tiers, banque, nature, jour, pu=1000):
    f = ok(api.post('/api/factures', json={'type': nature, 'tiers': tiers['nom'], 'tiers_id': tiers['id'],
        'date': jour, 'reference': 'DEP959-' + jour + str(pu), 'lignes': [{'description': 'S959', 'quantite': 1,
        'prix_unitaire': pu, 'tva': 20}]}), 201)
    ok(api.post(f'/api/factures/{f["id"]}/valider'))
    e = ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'))
    ok(api.post(f'/api/ecritures/{e["ecriture_id"]}/valider'))
    ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': tiers['nom'], 'date': jour,
        'montant': pu * 1.2, 'mode': 'virement', 'compte_bancaire_id': banque['id'], 'comptabiliser': True}), 201)


def deposer(api, mois=1, **kw):
    return api.post('/api/tva/declarations-deposees', json={'exercice': 2025, 'mois': mois,
        'date_depot': '2025-02-15', 'reference_depot': 'DGI-FICTIF-959', **kw})


def test_959_depot_fige_ecart_signale_et_credit_reporte(application):
    _appliquer_129(application)
    with closing(client(application)[0]) as api:
        _, fournisseur, banque = dossier(api, application, 'encaissement', 'fournisseur')
        operation(api, fournisseur, banque, 'achat', '2025-01-10')
        jan = decl(api, 1)
        assert D(str(jan['credit_tva'])) == 200 and jan['declaration_deposee'] is None
        d = ok(deposer(api), 201)
        assert (d['credit_tva'], d['tva_due'], d['reference_depot']) == (200, 0, 'DGI-FICTIF-959')
        jan = decl(api, 1)
        assert jan['declaration_deposee']['id'] == d['id'] and jan['ecarts_depot'] is None
        # Achat de janvier saisi après le dépôt : le recalcul change, le déposé non.
        operation(api, fournisseur, banque, 'achat', '2025-01-20', pu=500)
        jan = decl(api, 1)
        assert jan['ecarts_depot'] == {'recuperable': 100.0, 'credit_tva': 100.0}
        assert jan['declaration_deposee']['credit_tva'] == 200
        assert any('montants déposés restent figés' in a for a in jan['alertes'])
        # Février reporte le crédit déclaré (200), pas le recalcul (300).
        assert D(str(decl(api, 2)['credit_tva_anterieur'])) == 200


def test_959_rectificative_refus_droits_isolation_et_immuabilite(application):
    _appliquer_129(application)
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        _, cl, banque = dossier(api, application, 'encaissement')
        operation(api, cl, banque, 'vente', '2025-01-10')
        for kw, code in [({'date_depot': '2025-01-31'}, 422), ({'date_depot': '2999-01-01'}, 422),
                         ({'reference_depot': '  '}, 422)]:
            assert deposer(api, **kw).status_code == code
        assert api.post('/api/tva/declarations-deposees', json={'exercice': 2025, 'date_depot': '2025-02-15',
            'reference_depot': 'X'}).status_code == 422
        assert api.post('/api/tva/declarations-deposees', json={'exercice': 2025, 'trimestre': 1,
            'date_depot': '2025-04-15', 'reference_depot': 'X'}).status_code == 422
        d1 = ok(deposer(api), 201)
        assert deposer(api).status_code == 409
        assert deposer(api, remplace_id=d1['id']).status_code == 422
        d2 = ok(deposer(api, remplace_id=d1['id'], motif_rectification='Erreur de base FICTIVE',
                        date_depot='2025-02-20', reference_depot='DGI-RECT-959'), 201)
        liste = ok(api.get('/api/tva/declarations-deposees', params={'exercice': 2025}))
        assert [(x['id'], x['statut']) for x in liste] == [(d1['id'], 'remplacee'), (d2['id'], 'active')]
        assert decl(api, 1)['declaration_deposee']['id'] == d2['id']
        # Autre société : rien de visible, rien de modifiable.
        dossier(autre, application)
        assert ok(autre.get('/api/tva/declarations-deposees', params={'exercice': 2025})) == []
        assert autre.post('/api/tva/declarations-deposees', json={'exercice': 2025, 'mois': 1,
            'date_depot': '2025-02-15', 'reference_depot': 'X', 'remplace_id': d2['id'],
            'motif_rectification': 'x'}).status_code == 404
        # Rôle lecture : consultation seulement.
        email = 'lecture959-' + str(d2['id']) + '@example.com'
        ok(api.post('/api/utilisateurs', json={'nom': 'Lecteur 959', 'email': email,
            'mot_de_passe': 'RasLecture2026!', 'role': 'lecture'}), 201)
        jeton = ok(api.post('/api/auth/login', json={'email': email, 'password': 'RasLecture2026!'}))['access_token']
        assert api.post('/api/tva/declarations-deposees', headers={'Authorization': 'Bearer ' + jeton},
            json={'exercice': 2025, 'mois': 2, 'date_depot': '2025-03-15', 'reference_depot': 'X'}).status_code == 403
        # Immuabilité en base, y compris hors API.
        for sql in ("UPDATE declarations_tva_deposees SET tva_due=0 WHERE id=:i",
                    "UPDATE declarations_tva_deposees SET statut='active' WHERE id=:i",
                    "DELETE FROM declarations_tva_deposees WHERE id=:i"):
            with pytest.raises(DBAPIError):
                with application['engine'].begin() as db:
                    db.execute(text(sql), {'i': d1['id']})
