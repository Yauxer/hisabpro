"""Ventilation par tiers : vraie API/PostgreSQL nonce, oracles indépendants."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date, timedelta
from decimal import Decimal
import copy
import json
import uuid
import httpx
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
import models
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_lecture_reglements_historiques import photo
from test_articles_alertes_stock_historique_postgres import cible


def dossier(api, sens='vente', ras=0, jour=None):
    jour = jour or date.today().isoformat()
    nom = 'Ventilation fictive '+uuid.uuid4().hex[:8]
    r = api.post('/api/tiers', json={'nom': nom, 'type': 'client' if sens == 'vente' else 'fournisseur'})
    assert r.status_code == 201, r.text
    tid = r.json()['id']
    ids = []
    for prix in (100, 200):
        r = api.post('/api/factures', json={'type': sens, 'date': jour,
            'tiers': nom, 'tiers_id': tid, 'reference': 'FICT-'+uuid.uuid4().hex[:10],
            'ras_taux': ras,
            'lignes': [{'description': 'Service fictif', 'quantite': 1, 'prix_unitaire': prix, 'tva': 20}]})
        assert r.status_code == 201, r.text
        fid = r.json()['id']
        r = api.post(f'/api/factures/{fid}/valider', json={})
        assert r.status_code == 200, r.text
        r = api.post(f'/api/factures/{fid}/comptabiliser', json={})
        assert r.status_code == 200, r.text
        ids.append(fid)
    payload = {'operation_id': str(uuid.uuid4()), 'tiers_id': tid,
        'date': jour, 'mode': 'virement', 'montant': 240,
        'reference': 'VIR-FICT-'+uuid.uuid4().hex[:8], 'comptabiliser': True,
        'ventilations': [{'facture_id': fid, 'montant': 120} for fid in ids]}
    return tid, ids, payload


def poster(api, payload):
    return api.post('/api/reglements/par-tiers', content=json.dumps(payload), headers={'Content-Type': 'application/json'})


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_oracle_120_240_paiement240_solde120_lettrage(application, sens):
    with closing(client(application)[0]) as api:
        tid, ids, payload = dossier(api, sens)
        r = poster(api, payload)
        assert r.status_code == 201, r.text
        rows = r.json()
        assert [x['facture_id'] for x in rows] == ids
        assert [x['montant'] for x in rows] == [120, 120]
        assert all(x['est_comptabilisee'] and x['tiers_id'] == tid for x in rows)
        assert len({x['numero'] for x in rows}) == 2
        assert {x['reference'] for x in rows} == {payload['reference']}
        for fid, solde, statut in zip(ids, [0, 120], ['payee', 'partiellement_payee']):
            r = api.get(f'/api/factures/{fid}/reglements')
            assert r.status_code == 200, r.text
            assert r.json()['total_regle'] == 120 and r.json()['solde_restant'] == solde
            r = api.get('/api/factures', params={'exercice': date.today().year})
            assert next(f['statut'] for f in r.json() if f['id'] == fid) == statut
        avant = photo(application)
        retry = poster(api, payload)
        assert retry.status_code == 201 and [x['id'] for x in retry.json()] == [x['id'] for x in rows]
        assert photo(application) == avant
        final = api.post('/api/reglements', json={'facture_id': ids[1], 'date': date.today().isoformat(),
            'tiers': 'Repris de la facture', 'montant': 120, 'mode': 'virement'})
        assert final.status_code == 201, final.text
        compte = '3421' if sens == 'vente' else '4411'
        with Session(application['engine']) as db:
            f = db.get(models.Facture, ids[0]); sid = f.societe_id
            ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).all()
            assert len(ecritures) == 5
            for e in ecritures:
                assert sum(l.debit for l in e.lignes) == sum(l.credit for l in e.lignes)
            lignes = [l for e in ecritures for l in e.lignes if l.compte == compte]
            assert len(lignes) == 5 and sum(l.debit-l.credit for l in lignes) == Decimal(0)
            assert all(l.tiers_id == tid and l.compte_auxiliaire_snapshot for l in lignes)
            banques = [l for e in ecritures if e.source == 'reglement' for l in e.lignes if l.compte == '5141']
            assert sum(l.debit if sens == 'vente' else l.credit for l in banques) == Decimal('360')
            eids = [e.id for e in ecritures]
            lids = [l.id for l in lignes]
        for eid in eids:
            r = api.post(f'/api/ecritures/{eid}/valider', json={})
            assert r.status_code == 200, r.text
        r = api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': lids, 'code': 'VTA'})
        assert r.status_code == 200, r.text
        assert r.json()['nb'] == 5 and r.json()['code'] == 'VTA'


@pytest.mark.parametrize('cas', ['total', 'doublon', 'surreglement', 'centime_en_trop', 'autre_tiers', 'autre_societe',
    'sens', 'brouillon', 'proforma', 'date', 'periode', 'historique', 'cheque', 'effet',
    'nan', 'inf', 'negatif', 'zero', 'booleen', 'fraction', 'reference'])
def test_refus_atomique_sans_mutation(application, cas):
    with closing(client(application)[0]) as api:
        tid, ids, payload = dossier(api)
        attendu = 422
        if cas == 'total': payload['montant'] = 241
        elif cas == 'doublon': payload['ventilations'][1]['facture_id'] = ids[0]
        elif cas == 'surreglement':
            payload['montant'] = 361; payload['ventilations'][1]['montant'] = 241; attendu = 409
        elif cas == 'centime_en_trop':
            payload['montant'] = 240.01; payload['ventilations'][0]['montant'] = 120.01; attendu = 409
        elif cas in {'autre_tiers', 'sens', 'autre_societe'}:
            autre = client(application)[0] if cas == 'autre_societe' else api
            try:
                _, autres_ids, _ = dossier(autre, 'achat' if cas == 'sens' else 'vente')
                payload['ventilations'][1]['facture_id'] = autres_ids[0]
            finally:
                if autre is not api: autre.close()
            attendu = 404 if cas == 'autre_societe' else 409
        elif cas == 'date': payload['date'] = (date.today()-timedelta(days=1)).isoformat(); attendu = 409
        elif cas in {'brouillon', 'proforma'}:
            r = api.post('/api/factures', json={'type': 'vente', 'date': date.today().isoformat(),
                'tiers': 'Repris du tiers', 'tiers_id': tid, 'est_proforma': cas == 'proforma',
                'lignes': [{'description': 'Document fictif non definitif', 'quantite': 1, 'prix_unitaire': 100, 'tva': 20}]})
            assert r.status_code == 201, r.text
            payload['ventilations'][1]['facture_id'] = r.json()['id']
            attendu = 409
        elif cas == 'historique':
            r = api.post('/api/reglements', json={'facture_id': ids[1], 'date': date.today().isoformat(),
                'tiers': 'Repris du tiers', 'montant': 10, 'mode': 'virement', 'comptabiliser': False})
            assert r.status_code == 201, r.text
            cible(application)
            with application['engine'].begin() as db:
                db.execute(text('UPDATE reglements SET montant=:v WHERE id=:id AND est_comptabilisee=false'),
                    {'v': float('nan'), 'id': r.json()['id']})
        elif cas == 'periode':
            cible(application)
            with Session(application['engine']) as db:
                f = db.get(models.Facture, ids[1])
                exercice = db.query(models.ExerciceComptable).filter_by(societe_id=f.societe_id, annee=date.today().year).one()
                exercice.statut = 'cloture'
                db.commit()
            attendu = 423
        elif cas in {'cheque', 'effet'}: payload['mode'] = cas
        elif cas == 'reference': payload['reference'] = 'x'*101
        else:
            val = {'nan': float('nan'), 'inf': float('inf'), 'negatif': -120,
                'zero': 0, 'booleen': True, 'fraction': 120.001}[cas]
            payload['ventilations'][1]['montant'] = val
        avant = photo(application)
        r = poster(api, payload)
        assert r.status_code == attendu, (cas, r.text)
        assert photo(application) == avant


def test_idempotence_concurrente_et_refus_reemploi_modifie(application):
    with closing(client(application)[0]) as api:
        _, _, payload = dossier(api)
        def envoyer(_):
            with httpx.Client(base_url=application['api_url'], headers=dict(api.headers)) as concurrent:
                return poster(concurrent, payload)
        with ThreadPoolExecutor(max_workers=2) as pool:
            rs = list(pool.map(envoyer, range(2)))
        assert [r.status_code for r in rs] == [201, 201], [r.text for r in rs]
        assert [x['id'] for x in rs[0].json()] == [x['id'] for x in rs[1].json()]
        avant = photo(application)
        modifie = copy.deepcopy(payload)
        modifie['reference'] = 'Changement apres enregistrement'
        r = poster(api, modifie)
        assert r.status_code == 409, r.text
        assert photo(application) == avant


def test_concurrence_operations_distinctes_pas_de_surreglement(application):
    with closing(client(application)[0]) as api:
        _, _, payload = dossier(api)
        def envoyer(_):
            p = copy.deepcopy(payload); p['operation_id'] = str(uuid.uuid4())
            with httpx.Client(base_url=application['api_url'], headers=dict(api.headers)) as concurrent:
                return poster(concurrent, p)
        with ThreadPoolExecutor(max_workers=2) as pool:
            rs = list(pool.map(envoyer, range(2)))
        assert sorted(r.status_code for r in rs) == [201, 409], [r.text for r in rs]
        r = api.get('/api/reglements', params={'exercice': date.today().year})
        assert r.status_code == 200 and len(r.json()) == 2


def test_role_lecture_refuse_ventilation(application):
    with closing(client(application)[0]) as api:
        _, _, payload = dossier(api)
        email = uuid.uuid4().hex+'@example.com'
        r = api.post('/api/utilisateurs', json={'nom': 'Lecteur fictif', 'email': email,
            'mot_de_passe': 'Lecture2026!', 'role': 'lecture'})
        assert r.status_code == 201, r.text
        with httpx.Client(base_url=application['api_url']) as lecteur:
            r = lecteur.post('/api/auth/login', json={'email': email, 'password': 'Lecture2026!'})
            assert r.status_code == 200, r.text
            lecteur.headers['Authorization'] = 'Bearer '+r.json()['access_token']
            avant = photo(application)
            r = poster(lecteur, payload)
            assert r.status_code == 403, r.text
            assert photo(application) == avant


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('source', ['acompte', 'avoir', 'ras'])
def test_ventilation_respecte_imputations_existantes(application, sens, source):
    from pathlib import Path
    from test_ras_capture_reglement_postgres import appliquer, payload as ras_payload
    cible(application)
    raw = application['engine'].raw_connection()
    try:
        raw.autocommit = True
        with raw.cursor() as cursor:
            cursor.execute((Path(__file__).resolve().parents[1]/'hisabpro-backend/041_factC_cycle_documentaire.sql').read_text(encoding='utf-8'))
    finally:
        raw.close()
    appliquer(application)
    with closing(client(application)[0]) as api:
        tid, ids, p = dossier(api, sens, ras=10)
        f = next(f for f in api.get('/api/factures', params={'exercice': date.today().year}).json() if f['id'] == ids[0])
        if source == 'acompte':
            r = api.post('/api/acomptes', json={'type': 'client' if sens == 'vente' else 'fournisseur',
                'tiers': f['tiers'], 'tiers_id': tid, 'date': date.today().isoformat(),
                'montant': 40, 'tva_applicable': False, 'mode': 'virement', 'comptabiliser': True})
            assert r.status_code == 201, r.text
            r = api.post(f"/api/acomptes/{r.json()['id']}/imputer", json={'facture_id': ids[0], 'montant': 40})
            assert r.status_code == 200, r.text
            attendu = 80
        elif source == 'avoir':
            r = api.post('/api/avoirs', json={'facture_id': ids[0], 'date': date.today().isoformat(),
                'motif': 'Correction fictive', 'retour_stock': False,
                'lignes': [{'facture_ligne_id': f['lignes'][0]['id'], 'quantite': 0.2}]})
            assert r.status_code == 201, r.text
            r = api.post(f"/api/avoirs/{r.json()['id']}/comptabiliser", json={})
            assert r.status_code == 200, r.text
            attendu = 96
        else:
            r = api.post('/api/reglements', json={'facture_id': ids[0], 'date': date.today().isoformat(),
                'tiers': f['tiers'], 'montant': 20, 'mode': 'virement'})
            assert r.status_code == 201, r.text
            r = api.post(f"/api/reglements/{r.json()['id']}/ras", json=ras_payload(10, sens, 'RAS-FICT-VENT'))
            assert r.status_code == 200, r.text
            attendu = 90
        s = api.get(f'/api/factures/{ids[0]}/reglements').json()
        assert s['solde_restant'] == attendu
        p['ventilations'][0]['montant'] = attendu
        p['montant'] = attendu+120
        r = poster(api, p)
        assert r.status_code == 201, r.text
        assert api.get(f'/api/factures/{ids[0]}/reglements').json()['solde_restant'] == 0
        assert api.get(f'/api/factures/{ids[1]}/reglements').json()['solde_restant'] == 120
        with Session(application['engine']) as db:
            sid = db.get(models.Facture, ids[0]).societe_id
            ras = db.query(models.Ecriture).filter_by(societe_id=sid, source='ras_reglement').all()
            assert len(ras) == (1 if source == 'ras' else 0)
            for e in db.query(models.Ecriture).filter_by(societe_id=sid):
                assert sum(l.debit for l in e.lignes) == sum(l.credit for l in e.lignes)


def test_centimes_exactes_et_rejeu_apres_annulation_refuse(application):
    with closing(client(application)[0]) as api:
        _, ids, p = dossier(api)
        p['ventilations'][0]['montant'] = 0.1
        p['ventilations'][1]['montant'] = 0.2
        p['montant'] = 0.3
        r = poster(api, p)
        assert r.status_code == 201, r.text
        rows = r.json()
        for x in rows:
            assert api.post(f"/api/ecritures/{x['ecriture_id']}/valider", json={}).status_code == 200
        r = api.post(f"/api/reglements/{rows[0]['id']}/annuler", json={'date_annulation': date.today().isoformat(), 'motif': 'Correction fictive'})
        assert r.status_code == 200, r.text
        avant = photo(application)
        assert poster(api, p).status_code == 409
        assert photo(application) == avant
        assert api.get(f'/api/factures/{ids[0]}/reglements').json()['solde_restant'] == 120
