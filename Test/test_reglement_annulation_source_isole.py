"""Annulations : identité de source et concurrence avec le Journal, PG nonce."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import date, timedelta

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
from test_reglement_comptabilisation_concurrente_isole import metier
from test_contrepassation_concurrente_isole import original


def preparer(api, sens, validee=True):
    _, _, p = dossier(api, sens)
    rows = ok(poster(api, p), 201)
    r = rows[0]
    if validee:
        ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider", json={}))
    return p, r


def annuler(api, rid):
    return api.post(f'/api/reglements/{rid}/annuler', json={
        'date_annulation': date.today().isoformat(), 'motif': 'Annulation fictive532'})


def corriger(api, eid):
    return api.post(f'/api/ecritures/{eid}/contrepasser', json={
        'date_correction': date.today().isoformat(), 'motif': 'Correction Journal fictive532'})


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('cas', ['manuelle', 'autre_societe', 'autre_reglement', 'date', 'montant', 'deja_corrigee'])
def test_source_incoherente_ou_deja_corrigee_refusee_sans_mutation(application, sens, cas):
    with closing(client(application)[0]) as api:
        p, r = preparer(api, sens, validee=cas not in {'date', 'montant'})
        eid = r['ecriture_id']
        if cas == 'manuelle':
            lien = ok(api.post('/api/ecritures', json={'date': date.today().isoformat(),
                'journal': 'OD', 'reference': 'MANUEL-FICTIF532', 'libelle': 'Pièce manuelle fictive532',
                'est_validee': True, 'lignes': [{'compte': '5141', 'debit': 120}, {'compte': '4481', 'credit': 120}]}), 201)['id']
        elif cas == 'autre_societe':
            with closing(client(application)[0]) as autre:
                _, reg_autre = preparer(autre, sens)
                lien = reg_autre['ecriture_id']
            # Le fallback local est unique : le refus doit venir du lien
            # explicite étranger, pas d'une ambiguïté accidentelle de référence.
            rows = ok(api.get('/api/reglements/par-tiers/'+p['operation_id']))
            autre = next(x for x in rows if x['id'] != r['id'])
            ok(api.patch(f"/api/ecritures/{autre['ecriture_id']}", json={'reference': 'AUTRE-REFERENCE-FICTIVE532'}))
        elif cas == 'autre_reglement':
            rows = ok(api.get('/api/reglements/par-tiers/'+p['operation_id']))
            lien = next(x['ecriture_id'] for x in rows if x['id'] != r['id'])
        elif cas == 'date':
            ok(api.patch(f'/api/ecritures/{eid}', json={'date': (date.today()-timedelta(days=1)).isoformat()}))
        elif cas == 'montant':
            collectif = '3421' if sens == 'vente' else '4411'
            lignes = [{'compte': '5141', 'debit': 60}, {'compte': collectif, 'credit': 60}] if sens == 'vente' else [
                {'compte': collectif, 'debit': 60}, {'compte': '5141', 'credit': 60}]
            ok(api.patch(f'/api/ecritures/{eid}', json={'lignes': lignes}))
        else:
            ok(corriger(api, eid))
        if cas in {'manuelle', 'autre_societe', 'autre_reglement'}:
            # Lien synthétique incohérent, uniquement dans le cluster nonce.
            c = application['cluster']
            from postgres_isole import verifier_cible_isolee
            assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
            with application['engine'].begin() as db:
                assert db.execute(text('UPDATE reglements SET ecriture_id=:e WHERE id=:i'), {'e': lien, 'i': r['id']}).rowcount == 1
        avant = metier(application)
        reponse = annuler(api, r['id'])
        assert reponse.status_code == 409, reponse.text
        assert metier(application) == avant


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_lien_natif_reference_renommee_et_historique_unique_restent_annulables(application, sens):
    with closing(client(application)[0]) as api:
        p, r = preparer(api, sens, validee=False)
        eid = r['ecriture_id']
        ok(api.patch(f'/api/ecritures/{eid}', json={'reference': 'REFERENCE-RENOMMEE-FICTIVE532'}))
        ok(api.post(f'/api/ecritures/{eid}/valider', json={}))
        avant = original(application, eid)
        resultat = ok(annuler(api, r['id']))
        assert resultat['ecriture_id'] == eid and resultat['ecriture_annulation_id']
        assert original(application, eid) == avant
        # Un autre règlement perd seulement son lien dans le laboratoire.
        rows = ok(api.get('/api/reglements/par-tiers/'+p['operation_id']))
        autre = next(x for x in rows if x['id'] != r['id'])
        with application['engine'].begin() as db:
            db.execute(text('UPDATE reglements SET ecriture_id=NULL WHERE id=:i'), {'i': autre['id']})
        resultat = ok(annuler(api, autre['id']))
        assert resultat['ecriture_id'] == autre['ecriture_id'] and resultat['ecriture_annulation_id']


@pytest.mark.parametrize('premier', ['journal', 'annulation'])
def test_journal_et_annulation_ne_creent_quune_correction(application, premier):
    with closing(client(application)[0]) as api:
        api.timeout = 30
        _, r = preparer(api, 'vente')
        eid = r['ecriture_id']; avant = original(application, eid)
        db = application['engine'].connect(); tx = db.begin(); pool = ThreadPoolExecutor(2)
        def requete(action):
            return corriger(api, eid) if action == 'journal' else annuler(api, r['id'])
        try:
            db.execute(text('LOCK TABLE lignes_ecriture IN SHARE MODE'))
            f = pool.submit(requete, premier)
            attendre_verrou(application, f, table='lignes_ecriture')
            g = pool.submit(requete, 'annulation' if premier == 'journal' else 'journal')
            try:
                r2 = g.result(timeout=2)
            except TimeoutError:
                r2 = None
            tx.rollback(); r1 = f.result(timeout=30)
            if r2 is None:
                r2 = g.result(timeout=30)
            assert r1.status_code == 200, r1.text
            assert r2.status_code == (409 if premier == 'journal' else 200), r2.text
            if premier == 'annulation':
                assert r2.json()['deja_existante']
                assert r2.json()['id'] == r1.json()['ecriture_annulation_id']
        finally:
            if tx.is_active:
                tx.rollback()
            db.close(); pool.shutdown(wait=True)
        assert original(application, eid) == avant
        with application['engine'].connect() as c:
            assert c.scalar(text('SELECT count(*) FROM ecritures WHERE contrepassation_de_id=:i'), {'i': eid}) == 1


@pytest.mark.parametrize('operation', ['modifier', 'supprimer'])
def test_source_brouillon_en_cours_de_mutation_refuse_sans_interblocage(application, operation):
    with closing(client(application)[0]) as api:
        api.timeout = 30
        _, r = preparer(api, 'vente', validee=False)
        eid = r['ecriture_id']
        db = application['engine'].connect(); tx = db.begin(); pool = ThreadPoolExecutor(2)
        table = 'lignes_ecriture' if operation == 'modifier' else 'reglements'
        try:
            db.execute(text(f'LOCK TABLE {table} IN SHARE MODE'))
            if operation == 'modifier':
                f = pool.submit(api.patch, f'/api/ecritures/{eid}', json={
                    'libelle': 'Libellé fictif532 modifié', 'lignes': [
                        {'compte': '5141', 'debit': 120},
                        {'compte': '3421', 'credit': 120, 'tiers_id': r['tiers_id']}]})
            else:
                f = pool.submit(api.delete, f'/api/ecritures/{eid}')
            attendre_verrou(application, f, table=table)
            g = pool.submit(annuler, api, r['id'])
            try:
                r2 = g.result(timeout=2)
            except TimeoutError:
                r2 = None
            tx.rollback(); r1 = f.result(timeout=30)
            if r2 is None:
                r2 = g.result(timeout=30)
            assert r1.status_code == (200 if operation == 'modifier' else 204), r1.text
            assert r2.status_code == 409, r2.text
        finally:
            if tx.is_active:
                tx.rollback()
            db.close(); pool.shutdown(wait=True)
        # Après le refus concurrent, une nouvelle demande relit l'état stabilisé.
        resultat = ok(annuler(api, r['id']))
        assert resultat['statut'] == 'annule'
        if operation == 'supprimer':
            assert not resultat['est_comptabilisee'] and resultat['ecriture_annulation_id'] is None
        else:
            assert resultat['ecriture_annulation_id']
