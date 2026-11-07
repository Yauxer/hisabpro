"""Lettrage partiel (959) : règlement partiel lettré, complété, puis délettré. PG nonce, données fictives."""
from contextlib import closing
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


def _appliquer_130(app):
    for _ in range(2):  # rejouable
        raw = app['engine'].raw_connection()
        try:
            raw.autocommit = True
            with raw.cursor() as cur:
                cur.execute((ROOT / 'hisabpro-backend/130_lettrage_partiel.sql').read_text(encoding='utf8'))
        finally:
            raw.close()


def _valider_tout(api, app, sid):
    with app['engine'].connect() as db:
        ids = db.scalars(text('SELECT id FROM ecritures WHERE societe_id=:s AND NOT est_validee ORDER BY id'), {'s': sid}).all()
    for i in ids:
        ok(api.post(f'/api/ecritures/{i}/valider'))


def lignes(api):
    return ok(api.get('/api/lettrage/comptable', params={'exercice': 2025, 'compte': '3421'}))


def test_959_lettrage_partiel_complete_puis_delettre(application):
    _appliquer_130(application)
    with closing(client(application)[0]) as api:
        sid, tiers, banque = dossier(api, application)
        f = ok(api.post('/api/factures', json={'type': 'vente', 'tiers': tiers['nom'], 'tiers_id': tiers['id'],
            'date': '2025-01-10', 'reference': 'LP959', 'lignes': [{'description': 'S959', 'quantite': 1,
            'prix_unitaire': 1000, 'tva': 20}]}), 201)
        ok(api.post(f'/api/factures/{f["id"]}/valider'))
        ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'))
        for jour, m in (('2025-01-20', 700), ('2025-02-05', 500)):
            ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': tiers['nom'], 'date': jour,
                'montant': m, 'mode': 'virement', 'compte_bancaire_id': banque['id'], 'comptabiliser': True}), 201)
        _valider_tout(api, application, sid)
        ls = lignes(api)
        fac = next(l['ligne_id'] for l in ls if l['debit'] == 1200)
        r700 = next(l['ligne_id'] for l in ls if l['credit'] == 700)
        r500 = next(l['ligne_id'] for l in ls if l['credit'] == 500)
        # Sans la case « partiel », une sélection déséquilibrée reste refusée.
        refus = api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': [fac, r700]})
        assert refus.status_code == 400 and 'partiel' in refus.text
        # Un partiel exige au moins un débit et un crédit.
        assert api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': [r700, r500], 'partiel': True}).status_code == 400
        p = ok(api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': [fac, r700], 'partiel': True}))
        assert p['partiel'] is True
        etat = {l['ligne_id']: (l['code_lettrage'], l['lettrage_partiel']) for l in lignes(api)}
        assert etat[fac] == etat[r700] == (p['code'], True) and etat[r500] == (None, False)
        # Compléter le même code avec le second règlement : le lettrage devient total.
        t = ok(api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': [r500], 'code': p['code']}))
        assert (t['code'], t['partiel']) == (p['code'], False)
        etat = {l['ligne_id']: (l['code_lettrage'], l['lettrage_partiel']) for l in lignes(api)}
        assert {etat[i] for i in (fac, r700, r500)} == {(p['code'], False)}
        # Un code soldé n'est jamais étendu ; une ligne déjà lettrée n'est pas reprise.
        assert api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': [r500], 'code': p['code']}).status_code == 409
        ok(api.post(f"/api/lettrage/comptable/delettrer/{p['code']}"))
        assert all(l['code_lettrage'] is None for l in lignes(api))
        # Code délettré : réservé, non réutilisable.
        assert api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': [fac, r700, r500],
                                                                'code': p['code']}).status_code == 409
        # Garde SQL conservée : sans ligne déclarée partielle, un code déséquilibré est refusé.
        with pytest.raises(DBAPIError):
            with application['engine'].begin() as db:
                for lid in (fac, r700):
                    db.execute(text("INSERT INTO lettrages_comptables(societe_id, ligne_ecriture_id, code, actif, partiel) "
                                    "VALUES (:s, :l, 'ZZZZ', TRUE, FALSE)"), {'s': sid, 'l': lid})


def test_959_partiel_reste_mono_tiers(application):
    _appliquer_130(application)
    with closing(client(application)[0]) as api:
        sid, t1, banque = dossier(api, application)
        t2 = ok(api.post('/api/tiers', json={'nom': 'Second client FICTIF959', 'type': 'client', 'categorie_fiscale': 'particulier'}), 201)
        for t in (t1, t2):
            f = ok(api.post('/api/factures', json={'type': 'vente', 'tiers': t['nom'], 'tiers_id': t['id'],
                'date': '2025-01-10', 'lignes': [{'description': 'S', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
            ok(api.post(f'/api/factures/{f["id"]}/valider')); ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'))
            ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': t['nom'], 'date': '2025-01-20',
                'montant': 300, 'mode': 'virement', 'compte_bancaire_id': banque['id'], 'comptabiliser': True}), 201)
        _valider_tout(api, application, sid)
        ls = lignes(api)
        d1 = next(l['ligne_id'] for l in ls if l['debit'] == 1200 and l['tiers_id'] == t1['id'])
        c1 = next(l['ligne_id'] for l in ls if l['credit'] == 300 and l['tiers_id'] == t1['id'])
        c2 = next(l['ligne_id'] for l in ls if l['credit'] == 300 and l['tiers_id'] == t2['id'])
        p = ok(api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': [d1, c1], 'partiel': True}))
        assert api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': [c2], 'code': p['code']}).status_code == 400
