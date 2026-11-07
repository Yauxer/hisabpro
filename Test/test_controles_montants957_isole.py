"""Bornes au centime, dates d'imputation et refus de taux TVA explicites. PG nonce, données fictives."""
from contextlib import closing

from test_compensations_tva953_isole import (  # noqa: F401
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, dossier, ok, core, jeu,
)


def _facture(api, tiers, prix=1000):
    f = ok(api.post('/api/factures', json={'type': 'vente', 'tiers': tiers['nom'], 'tiers_id': tiers['id'],
        'date': '2025-01-10', 'reference': 'CTL957', 'lignes': [{'description': 'S957', 'quantite': 1,
        'prix_unitaire': prix, 'tva': 20}]}), 201)
    ok(api.post(f'/api/factures/{f["id"]}/valider'))
    e = ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'))
    ok(api.post(f'/api/ecritures/{e["ecriture_id"]}/valider'))
    return f


def test_957_surreglement_d_un_centime_refuse(application):
    with closing(client(application)[0]) as api:
        _, tiers, banque = dossier(api, application)
        f = _facture(api, tiers)
        regl = lambda m, j: api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': tiers['nom'], 'date': j,
            'montant': m, 'mode': 'virement', 'compte_bancaire_id': banque['id'], 'comptabiliser': True})
        assert regl(700, '2025-01-20').status_code == 201
        assert regl(500.01, '2025-01-21').status_code == 409
        assert regl(500, '2025-01-21').status_code == 201
        assert ok(api.get(f'/api/factures/{f["id"]}/reglements'))['solde_restant'] == 0


def test_957_credit_avoir_borne_au_centime(application):
    with closing(client(application)[0]) as api:
        sid, _, fs, a = jeu(api, application); avant = core(application, sid)
        r = api.post(f'/api/avoirs/{a["id"]}/utiliser', json={'type_utilisation': 'imputation',
            'facture_id': fs[1]['id'], 'montant': 1200.01, 'date_utilisation': '2025-03-15'})
        assert r.status_code == 409, r.text
        assert core(application, sid) == avant
        ok(api.post(f'/api/avoirs/{a["id"]}/utiliser', json={'type_utilisation': 'imputation',
            'facture_id': fs[1]['id'], 'montant': 1200, 'date_utilisation': '2025-03-15'}))


def test_957_imputation_anterieure_aux_pieces_refusee(application):
    with closing(client(application)[0]) as api:
        _, _, fs, a = jeu(api, application)
        for jour in ('2025-01-05', '2025-02-28'):
            r = api.post(f'/api/avoirs/{a["id"]}/utiliser', json={'type_utilisation': 'imputation',
                'facture_id': fs[1]['id'], 'montant': 100, 'date_utilisation': jour})
            assert r.status_code == 422 and 'précéder' in r.text, r.text
        assert ok(api.get('/api/avoirs', params={'exercice': 2025}))[0]['utilisations'] == []


def test_957_taux_tva_hors_catalogue_refuse_en_422(application):
    with closing(client(application)[0]) as api:
        _, tiers, _ = dossier(api, application)
        avant = len(ok(api.get('/api/factures', params={'exercice': 2025})))
        for jour, taux in (('2025-01-10', 14), ('2026-01-10', 14), ('2025-01-10', 7)):
            r = api.post('/api/factures', json={'type': 'vente', 'tiers': tiers['nom'], 'tiers_id': tiers['id'],
                'date': jour, 'lignes': [{'description': 'T957', 'quantite': 1, 'prix_unitaire': 100, 'tva': taux}]})
            assert r.status_code == 422 and 'non proposé' in r.text, r.text
        assert len(ok(api.get('/api/factures', params={'exercice': 2025}))) == avant
        assert api.post('/api/factures', json={'type': 'vente', 'tiers': tiers['nom'], 'tiers_id': tiers['id'],
            'date': '2023-06-10', 'lignes': [{'description': 'T957', 'quantite': 1, 'prix_unitaire': 100,
            'tva': 14}]}).status_code == 201
