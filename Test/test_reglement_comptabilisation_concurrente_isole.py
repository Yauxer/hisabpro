"""Sources de règlements stables : HTTP et PostgreSQL nonce, sans mock métier."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import closing
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_reglements_par_tiers_isole import dossier, poster
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou
from recette_restauration_consolidee_084 import empreintes_tables


def preparer(api, sens):
    tid, fids, payload = dossier(api, sens)
    payload['comptabiliser'] = False
    rows = ok(poster(api, payload), 201)
    assert len(rows) == 2 and not any(r['est_comptabilisee'] for r in rows)
    return tid, fids, payload, rows


def comptabiliser(api, rid):
    return api.post(f'/api/reglements/{rid}/comptabiliser', json={})


def mutation(api, rid, operation):
    if operation == 'supprimer':
        return api.delete(f'/api/reglements/{rid}')
    if operation == 'annuler':
        return api.post(f'/api/reglements/{rid}/annuler', json={'motif': 'Annulation fictive530'})
    return api.patch(f'/api/reglements/{rid}', json={'montant': 60})


def croiser(app, api, rid, premier, second):
    """Un verrou natif retient la première requête après sa lecture métier."""
    table = 'lignes_ecriture' if premier == 'comptabiliser' else 'reglements'
    pool = ThreadPoolExecutor(2)
    db = app['engine'].connect()
    tx = db.begin()
    def envoyer(action):
        return comptabiliser(api, rid) if action == 'comptabiliser' else mutation(api, rid, action)
    try:
        db.execute(text(f'LOCK TABLE {table} IN SHARE MODE'))
        f = pool.submit(envoyer, premier)
        attendre_verrou(app, f, table=table)
        g = pool.submit(envoyer, second)
        try:
            r2 = g.result(timeout=2)
        except TimeoutError:
            r2 = None
        tx.rollback()
        r1 = f.result(timeout=30)
        if r2 is None:
            r2 = g.result(timeout=30)
        assert r1.status_code != 500 and r2.status_code != 500, app['api_log'].read_text(encoding='utf8')[-10000:]
        return r1, r2
    finally:
        if tx.is_active:
            tx.rollback()
        db.close()
        pool.shutdown(wait=True)


def sources(app, rid):
    with app['engine'].connect() as c:
        r = c.execute(text('SELECT societe_id,montant,est_comptabilisee,ecriture_id,statut FROM reglements WHERE id=:i'), {'i': rid}).one()
        es = c.execute(text("SELECT id FROM ecritures WHERE societe_id=:s AND source='reglement' ORDER BY id"), {'s': r.societe_id}).scalars().all()
        ls = c.execute(text('SELECT compte,debit,credit,tiers_id FROM lignes_ecriture WHERE ecriture_id=:e ORDER BY compte'), {'e': r.ecriture_id}).all()
        return r, es, ls


def metier(app):
    return {k: v for k, v in empreintes_tables(app['engine']).items() if k != 'audit_actions'}


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_double_comptabilisation_puis_lettrage_et_rapprochement(application, sens):
    with closing(client(application)[0]) as api:
        api.timeout = 30
        tid, fids, p, rows = preparer(api, sens)
        r1, r2 = croiser(application, api, rows[0]['id'], 'comptabiliser', 'comptabiliser')
        assert r1.status_code == 200 and r2.status_code == 400, (r1.text, r2.text)
        r, es, ls = sources(application, rows[0]['id'])
        assert r.montant == 120 and r.est_comptabilisee and len(es) == 1
        assert sum(l.debit for l in ls) == sum(l.credit for l in ls) == Decimal(120)
        assert all(l.tiers_id == tid for l in ls if l.compte == ('3421' if sens == 'vente' else '4411'))
        ok(comptabiliser(api, rows[1]['id']))
        dernier = ok(api.post('/api/reglements', json={'facture_id': fids[1], 'date': p['date'],
            'tiers': 'Tiers repris de la facture', 'montant': 120, 'mode': 'virement'}), 201)
        sid = r.societe_id
        with application['engine'].connect() as c:
            eids = c.execute(text('SELECT id FROM ecritures WHERE societe_id=:s ORDER BY id'), {'s': sid}).scalars().all()
            collectif = '3421' if sens == 'vente' else '4411'
            lids = c.execute(text('SELECT l.id FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s AND l.compte=:c ORDER BY l.id'), {'s': sid, 'c': collectif}).scalars().all()
            assert len(eids) == 5 and len(lids) == 5
        for eid in eids:
            ok(api.post(f'/api/ecritures/{eid}/valider', json={}))
        assert ok(api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': lids, 'code': 'RCA'}))['nb'] == 5
        from test_rapprochement_ventilation_isole import rapprocher, situation
        rid = ok(api.post('/api/rapprochement', json={'compte': '5141', 'date': p['date'],
            'libelle': p['reference'], 'montant': 240, 'sens': 'credit' if sens == 'vente' else 'debit'}), 201)['id']
        avant = metier(application)
        ok(rapprocher(api, rid, p))
        releve = next(x for x in situation(api)['lignes_releve'] if x['id'] == rid)
        assert releve['rapprochee'] and len(releve['ecriture_ligne_ids']) == 2
        # Le pointage peut changer ses liens, jamais les pièces ou le règlement.
        apres = metier(application)
        for table in ('ecritures', 'lignes_ecriture', 'reglements', 'audit_ecritures'):
            assert apres[table] == avant[table]
        assert api.get(f"/api/factures/{fids[1]}/reglements").json()['solde_restant'] == 0
        assert dernier['est_comptabilisee']
        assert api.get('/api/fec/export', params={'exercice': date.today().year}).status_code == 200


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('operation', ['modifier', 'supprimer'])
def test_comptabilisation_en_cours_fige_les_sources(application, sens, operation):
    with closing(client(application)[0]) as api:
        api.timeout = 30
        _, _, _, rows = preparer(api, sens)
        r1, r2 = croiser(application, api, rows[0]['id'], 'comptabiliser', operation)
        assert r1.status_code == 200 and r2.status_code == 409, (r1.text, r2.text)
        r, es, ls = sources(application, rows[0]['id'])
        assert r.montant == 120 and r.est_comptabilisee and len(es) == 1
        assert sum(l.debit for l in ls) == sum(l.credit for l in ls) == Decimal(120)


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('operation', ['modifier', 'supprimer', 'annuler'])
def test_mutation_engagee_avant_comptabilisation_est_relue(application, sens, operation):
    with closing(client(application)[0]) as api:
        api.timeout = 30
        _, _, _, rows = preparer(api, sens)
        r1, r2 = croiser(application, api, rows[0]['id'], operation, 'comptabiliser')
        attendu = {'modifier': 200, 'supprimer': 404, 'annuler': 409}[operation]
        assert r1.status_code == (204 if operation == 'supprimer' else 200), r1.text
        assert r2.status_code == attendu, r2.text
        with application['engine'].connect() as c:
            sid = c.scalar(text('SELECT societe_id FROM reglements WHERE id=:i'), {'i': rows[1]['id']})
            es = c.execute(text("SELECT id FROM ecritures WHERE societe_id=:s AND source='reglement'"), {'s': sid}).scalars().all()
        if operation == 'modifier':
            r, _, ls = sources(application, rows[0]['id'])
            assert r.montant == 60 and r.est_comptabilisee and len(es) == 1
            assert sum(l.debit for l in ls) == sum(l.credit for l in ls) == Decimal(60)
        else:
            assert es == []
        if operation == 'annuler':
            r, _, _ = sources(application, rows[0]['id'])
            assert r.statut == 'annule' and not r.est_comptabilisee and r.ecriture_id is None


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_reglement_annule_non_comptabilise_refuse_sans_mutation(application, sens):
    with closing(client(application)[0]) as api:
        _, _, _, rows = preparer(api, sens)
        reponse = mutation(api, rows[0]['id'], 'annuler')
        assert reponse.status_code == 200, application['api_log'].read_text(encoding='utf8')[-10000:]
        avant = metier(application)
        assert comptabiliser(api, rows[0]['id']).status_code == 409
        assert metier(application) == avant


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_annulation_capture_sous_login_limite_sans_elargir_les_droits(application, sens):
    from test_ras_capture_reglement_postgres import preparer as facture_ras, paiement, payload
    with closing(client(application)[0]) as api:
        api.timeout = 30
        f = facture_ras(api, sens)
        reg = paiement(api, f, 400)
        capture = ok(api.post(f"/api/reglements/{reg['id']}/ras", json=payload(30, sens)))
        for eid in (reg['ecriture_id'], capture['ecriture_id']):
            ok(api.post(f'/api/ecritures/{eid}/valider', json={}))
        avant = metier(application)
        db = application['engine'].connect()
        tx = db.begin()
        pool = ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE lignes_ecriture IN SHARE MODE'))
            first = pool.submit(mutation, api, reg['id'], 'annuler')
            attendre_verrou(application, first, table='lignes_ecriture')
            second = pool.submit(mutation, api, reg['id'], 'annuler')
            try:
                r2 = second.result(timeout=2)
            except TimeoutError:
                r2 = None
            tx.rollback()
            r1 = first.result(timeout=30)
            if r2 is None:
                r2 = second.result(timeout=30)
            assert r1.status_code == r2.status_code == 200, (r1.text, r2.text)
            assert r1.json()['ecriture_annulation_id'] == r2.json()['ecriture_annulation_id']
        finally:
            if tx.is_active:
                tx.rollback()
            db.close()
            pool.shutdown(wait=True)
        apres = metier(application)
        assert avant['ras_reglement_captures'] == apres['ras_reglement_captures']
        with application['engine'].connect() as c:
            assert c.scalar(text('SELECT count(*) FROM ras_reglement_annulations WHERE capture_id=:i'), {'i': capture['id']}) == 1
            for eid in (reg['ecriture_id'], capture['ecriture_id']):
                assert c.scalar(text('SELECT count(*) FROM ecritures WHERE contrepassation_de_id=:i'), {'i': eid}) == 1
            for table in ('ras_reglement_captures', 'ras_reglement_annulations'):
                for droit in ('UPDATE', 'DELETE', 'TRUNCATE'):
                    assert not c.scalar(text("SELECT has_table_privilege('hisabpro',:t,:d)"), {'t': table, 'd': droit})
        situation = ok(api.get(f"/api/factures/{f['id']}/reglements"))
        assert situation['solde_restant'] == 1200 and situation['montant_ras_impute'] == 0
