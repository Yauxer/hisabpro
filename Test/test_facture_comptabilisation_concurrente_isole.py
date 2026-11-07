"""Une pièce par document malgré deux POST simultanés, PostgreSQL nonce098."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import closing
from datetime import date
from decimal import Decimal
import uuid

import pytest
from sqlalchemy import text
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou


def doubler(app, api, chemin):
    pool = ThreadPoolExecutor(2)
    db = app['engine'].connect(); tx = db.begin()
    try:
        db.execute(text('LOCK TABLE lignes_ecriture IN SHARE MODE'))
        premier = pool.submit(api.post, chemin, json={})
        attendre_verrou(app, premier, table='lignes_ecriture')
        second = pool.submit(api.post, chemin, json={})
        try:
            reponse = second.result(timeout=2)
        except TimeoutError:
            reponse = None
        tx.rollback()
        r1 = premier.result(timeout=30)
        r2 = reponse if reponse is not None else second.result(timeout=30)
        return r1, r2
    finally:
        if tx.is_active: tx.rollback()
        db.close(); pool.shutdown(wait=True)


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('document', ['facture', 'avoir'])
def test_double_comptabilisation_une_piece_validee_et_fec(application, sens, document):
    with closing(client(application)[0]) as api:
        api.timeout = 30
        tid = ok(api.post('/api/tiers', json={'nom': 'Tiers fictif538',
            'type': 'client' if sens == 'vente' else 'fournisseur'}), 201)['id']
        f = ok(api.post('/api/factures', json={'type': sens, 'tiers_id': tid,
            'tiers': 'Tiers fictif538', 'date': date.today().isoformat(),
            'reference': 'FICT538-'+uuid.uuid4().hex[:10], 'lignes': [
                {'description': 'Service fictif538', 'quantite': 1,
                 'prix_unitaire': 100, 'tva': 20}]}), 201)
        ok(api.post(f"/api/factures/{f['id']}/valider", json={}))
        docid = f['id']; montant = Decimal(120); origine = None
        if document == 'avoir':
            origine = ok(api.post(f"/api/factures/{f['id']}/comptabiliser", json={}))['ecriture_id']
            ok(api.post(f'/api/ecritures/{origine}/valider', json={}))
            from test_contrepassation_concurrente_isole import original
            avant = original(application, origine)
            av = ok(api.post('/api/avoirs', json={'facture_id': f['id'],
                'date': date.today().isoformat(), 'motif': 'Avoir fictif538',
                'retour_stock': False, 'lignes': [
                    {'facture_ligne_id': f['lignes'][0]['id'], 'quantite': 0.5}]}), 201)
            docid = av['id']; montant = Decimal(60)
        chemin = f'/api/{document}s/{docid}/comptabiliser'
        r1, r2 = doubler(application, api, chemin)
        assert (r1.status_code, r2.status_code) == (200, 409), (r1.text, r2.text)
        eid = r1.json()['ecriture_id']
        sid = ok(api.get('/api/societe/moi'))['id']
        with application['engine'].connect() as db:
            ids = db.execute(text('SELECT id FROM ecritures WHERE societe_id=:s AND source=:o'),
                {'s': sid, 'o': document}).scalars().all()
            assert ids == [eid]
            lignes = db.execute(text('SELECT debit,credit,compte,tiers_id FROM lignes_ecriture WHERE ecriture_id=:i'), {'i': eid}).all()
            assert sum(l.debit for l in lignes) == sum(l.credit for l in lignes) == montant
            tiers = [l for l in lignes if l.compte == ('3421' if sens == 'vente' else '4411')]
            assert len(tiers) == 1 and tiers[0].tiers_id == tid
        ok(api.post(f'/api/ecritures/{eid}/valider', json={}))
        assert api.get('/api/fec/export', params={'exercice': date.today().year}).status_code == 200
        if origine:
            assert original(application, origine) == avant
