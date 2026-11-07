"""Chèque/effet client impayé après encaissement. PG nonce, données fictives."""
from contextlib import closing
from decimal import Decimal as D

from sqlalchemy import text

from test_compensations_tva953_isole import (  # noqa: F401
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, dossier, ok,
)


def tva(api, mois):
    return D(str(ok(api.get('/api/tva/declaration', params={'exercice': 2025, 'mois': mois}))['collectee']['total']))


def cheque_encaisse(api, app):
    _, tiers, banque = dossier(api, app, 'encaissement')
    f = ok(api.post('/api/factures', json={'type': 'vente', 'tiers': tiers['nom'], 'tiers_id': tiers['id'],
        'date': '2025-01-10', 'reference': 'IMP957', 'lignes': [{'description': 'S957', 'quantite': 1,
        'prix_unitaire': 1000, 'tva': 20}]}), 201)
    ok(api.post(f'/api/factures/{f["id"]}/valider'))
    e = ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'))
    ok(api.post(f'/api/ecritures/{e["ecriture_id"]}/valider'))
    r = ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': tiers['nom'], 'date': '2025-01-15',
        'montant': 1200, 'mode': 'cheque', 'reference': 'CHQ957', 'compte_bancaire_id': banque['id'],
        'comptabiliser': True}), 201)
    ok(api.post(f'/api/reglements/{r["id"]}/transition', json={'action': 'encaisser', 'date_effective': '2025-01-20'}))
    return f, r


def test_957_impaye_apres_encaissement_ecriture_creance_et_tva(application):
    with closing(client(application)[0]) as api:
        f, r = cheque_encaisse(api, application)
        assert tva(api, 1) == 200
        assert api.post(f'/api/reglements/{r["id"]}/transition',
                        json={'action': 'rejeter', 'date_effective': '2025-01-18'}).status_code == 400
        rej = ok(api.post(f'/api/reglements/{r["id"]}/transition',
                          json={'action': 'rejeter', 'date_effective': '2025-02-03', 'frais': 50}))
        assert rej['statut'] == 'rejete'
        with application['engine'].connect() as db:
            row = db.execute(text('SELECT date_encaissement, date_rejet_effective FROM reglements WHERE id=:i'),
                             {'i': r['id']}).one()
            assert tuple(map(str, row)) == ('2025-01-20', '2025-02-03')
            ecr = db.execute(text("""SELECT e.id, e.journal FROM ecritures e WHERE e.libelle LIKE 'Impayé%'
                                     AND e.date='2025-02-03'""")).one()
            lignes = sorted((c, str(d), str(cr)) for c, d, cr in db.execute(text(
                'SELECT compte, debit, credit FROM lignes_ecriture WHERE ecriture_id=:i'), {'i': ecr[0]}))
        assert ecr[1] == 'BQ'
        assert ('3421', '1250.00', '0.00') in lignes and ('6147', '50.00', '0.00') in lignes
        assert ('7127', '0.00', '50.00') in lignes
        assert any(c.startswith('514') and cr == '1250.00' for c, _, cr in lignes)
        ok(api.post(f'/api/ecritures/{ecr[0]}/valider'))
        assert ok(api.get(f'/api/factures/{f["id"]}/reglements'))['solde_restant'] == 1200
        assert tva(api, 1) == 200 and tva(api, 2) == -200


def test_957_rejet_avant_encaissement_inchange(application):
    with closing(client(application)[0]) as api:
        _, tiers, banque = dossier(api, application, 'encaissement')
        f = ok(api.post('/api/factures', json={'type': 'vente', 'tiers': tiers['nom'], 'tiers_id': tiers['id'],
            'date': '2025-01-10', 'lignes': [{'description': 'S957', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
        ok(api.post(f'/api/factures/{f["id"]}/valider'))
        r = ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': tiers['nom'], 'date': '2025-01-15',
            'montant': 1200, 'mode': 'cheque', 'reference': 'CHQ957B', 'compte_bancaire_id': banque['id'],
            'comptabiliser': True}), 201)
        rej = ok(api.post(f'/api/reglements/{r["id"]}/transition', json={'action': 'rejeter', 'date_effective': '2025-01-25'}))
        assert rej['statut'] == 'rejete' and rej['date_encaissement'] is None
        assert tva(api, 1) == 0
