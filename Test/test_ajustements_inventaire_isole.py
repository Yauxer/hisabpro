"""Sept ajustements existants : API réelle et PostgreSQL nonce, aucun mock métier."""
from contextlib import closing
from decimal import Decimal
import pytest
from sqlalchemy import text

from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok


MODELES = [
    ('cca', '6125', '3491', '3491', '6125', True),
    ('pca', '7124', '4491', '7124', '4491', True),
    ('fnp', '6125', '4417', '6125', '4417', True),
    ('fae', '7124', '3427', '3427', '7124', True),
    ('provision_risque', '6195', '1518', '6195', '1518', False),
    ('depreciation_client', '61964', '3942', '61964', '3942', False),
    ('depreciation_stock', '61961', '3911', '61961', '3911', False),
]


def exercice(api, debut='2025-01-01', fin='2025-12-31'):
    return ok(api.post('/api/exercices', json={
        'annee': 2025, 'date_debut': debut, 'date_fin': fin}), 201)


def donnees(type_='cca', activite='6125', contrepartie='3491', **kw):
    return {'type': type_, 'libelle': 'Justificatif fictif inventaire553',
            'montant': '1200.125', 'compte_activite': activite,
            'compte_contrepartie': contrepartie, **kw}


def photo(application, sid):
    with application['engine'].connect() as c:
        return {table: c.execute(text(f'SELECT row_to_json(t)::text FROM {table} t '
            'WHERE societe_id=:s ORDER BY id'), {'s': sid}).scalars().all()
            for table in ('ajustements_inventaire', 'ecritures', 'exercices_comptables')}


@pytest.mark.parametrize('type_,activite,contrepartie,debit,credit,reverse', MODELES)
def test_sept_modeles_creation_validation_et_trace(application, type_, activite, contrepartie, debit, credit, reverse):
    with closing(client(application)[0]) as api:
        exercice(api)
        a = ok(api.post('/api/cloture/ajustements?exercice=2025',
                        json=donnees(type_, activite, contrepartie)))
        sid = ok(api.get('/api/societe/moi'))['id']
        with application['engine'].connect() as c:
            def piece(eid):
                return c.execute(text('SELECT e.date,e.exercice,e.est_validee,l.compte,l.debit,l.credit '
                    'FROM ecritures e JOIN lignes_ecriture l ON l.ecriture_id=e.id '
                    'WHERE e.id=:i ORDER BY l.id'), {'i': eid}).all()
            e = piece(a['ecriture_id'])
            assert [(r.compte, r.debit, r.credit) for r in e] == [
                (debit, Decimal('1200.13'), 0), (credit, 0, Decimal('1200.13'))]
            assert all(str(r.date) == '2025-12-31' and r.exercice == 2025 and not r.est_validee for r in e)
            assert bool(a['contrepassation_id']) == reverse
            if reverse:
                cp = piece(a['contrepassation_id'])
                assert all(str(r.date) == '2026-01-01' and r.exercice == 2026 for r in cp)
                assert [(r.compte, r.debit, r.credit) for r in cp] == [(r.compte, r.credit, r.debit) for r in e]
        ok(api.post(f"/api/ecritures/{a['ecriture_id']}/valider", json={}))
        avant = photo(application, sid)
        r = api.delete(f"/api/cloture/ajustements/{a['id']}")
        assert r.status_code == 409, r.text
        assert photo(application, sid) == avant
        assert ok(api.get('/api/cloture/ajustements?exercice=2025'))[0]['est_validee']


@pytest.mark.parametrize('changement', [
    {'montant': 'NaN'}, {'montant': 'Infinity'}, {'montant': '-Infinity'},
    {'montant': '10000000000000000'}, {'montant': '1e1000'},
    {'montant': 0}, {'montant': -1}, {'montant': '0.001'},
    {'compte_activite': '6inconnu'}, {'compte_activite': '61250000000'},
    {'compte_contrepartie': '1111'}, {'libelle': 'x' * 301},
])
def test_rejet_sans_creation_ni_contrepassation(application, changement):
    with closing(client(application)[0]) as api:
        exercice(api)
        sid = ok(api.get('/api/societe/moi'))['id']
        avant = photo(application, sid)
        r = api.post('/api/cloture/ajustements?exercice=2025', json=donnees(**changement))
        assert r.status_code in (400, 422), r.text
        assert photo(application, sid) == avant


def test_contrepassation_exercice_decale_et_suppression_brouillon(application):
    with closing(client(application)[0]) as api:
        exercice(api, '2024-07-01', '2025-06-30')
        sid = ok(api.get('/api/societe/moi'))['id']
        avant = photo(application, sid)
        # L'inscription a déjà créé 2026 en calendrier civil. Ne pas le déplacer
        # silencieusement, ni accepter une contrepassation six mois trop tard.
        for url, body in [('/api/cloture/ajustements?exercice=2025', donnees()),
                          ('/api/exercices/2025/preparer-suivant', {})]:
            refus = api.post(url, json=body)
            assert refus.status_code == 409 and 'calendrier' in refus.text, refus.text
            assert photo(application, sid) == avant
        ok(api.patch('/api/exercices/2026', json={
            'date_debut': '2025-07-01', 'date_fin': '2026-06-30'}))
        a = ok(api.post('/api/cloture/ajustements?exercice=2025', json=donnees()))
        with application['engine'].connect() as c:
            dates = c.execute(text('SELECT date,exercice FROM ecritures WHERE id IN (:e,:cp) ORDER BY date'),
                {'e': a['ecriture_id'], 'cp': a['contrepassation_id']}).all()
            assert [(str(d), an) for d, an in dates] == [('2025-06-30', 2025), ('2025-07-01', 2026)]
        ok(api.delete(f"/api/cloture/ajustements/{a['id']}"))
        assert not photo(application, sid)['ecritures']
        assert ok(api.get('/api/cloture/ajustements?exercice=2025')) == []
