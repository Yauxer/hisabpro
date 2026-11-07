"""Annulation atomique d'une ventilation native, sur PostgreSQL nonce uniquement."""
from contextlib import closing
from datetime import date, timedelta
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import httpx
import uuid
import pytest
from sqlalchemy.orm import Session
import models
from sqlalchemy import text
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_reglements_par_tiers_isole import dossier, poster
from test_lecture_reglements_historiques import photo
from test_articles_alertes_stock_historique_postgres import cible


def annuler(api, payload):
    return api.post('/api/reglements/par-tiers/'+payload['operation_id']+'/annuler',
        json={'date_annulation': date.today().isoformat(), 'motif': 'Correction fictive du lot'})


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_annulation_native_inverse_exacte_origines_definitives_et_rejeu(application, sens):
    with closing(client(application)[0]) as api:
        _, ids, payload = dossier(api, sens)
        r = poster(api, payload)
        assert r.status_code == 201, r.text
        rows = r.json()
        originaux = {}
        with Session(application['engine']) as db:
            for row in rows:
                e = db.get(models.Ecriture, row['ecriture_id'])
                originaux[e.id] = [(l.compte, l.debit, l.credit, l.tiers_id,
                    l.compte_auxiliaire_snapshot) for l in e.lignes]
        for eid in originaux:
            r = api.post(f'/api/ecritures/{eid}/valider', json={})
            assert r.status_code == 200, r.text
        r = annuler(api, payload)
        assert r.status_code == 200, r.text
        assert [x['id'] for x in r.json()] == [x['id'] for x in rows]
        assert {x['statut'] for x in r.json()} == {'annule'}
        with Session(application['engine']) as db:
            for row in r.json():
                original = db.get(models.Ecriture, row['ecriture_id'])
                inverse = db.get(models.Ecriture, row['ecriture_annulation_id'])
                assert original.est_validee
                assert [(l.compte, l.debit, l.credit, l.tiers_id,
                    l.compte_auxiliaire_snapshot) for l in original.lignes] == originaux[original.id]
                assert inverse.contrepassation_de_id == original.id
                assert [(l.compte, l.credit, l.debit, l.tiers_id,
                    l.compte_auxiliaire_snapshot) for l in inverse.lignes] == originaux[original.id]
                assert sum(l.debit for l in inverse.lignes) == sum(l.credit for l in inverse.lignes) == Decimal(120)
        for fid, solde in zip(ids, [120, 240]):
            r = api.get(f'/api/factures/{fid}/reglements')
            assert r.status_code == 200, r.text
            assert r.json()['total_regle'] == 0 and r.json()['solde_restant'] == solde
        avant = photo(application)
        assert annuler(api, payload).status_code == 200
        assert photo(application) == avant
        assert poster(api, payload).status_code == 409
        assert photo(application) == avant


@pytest.mark.parametrize('cas', ['absent', 'autre_societe', 'partiel', 'origine_absente', 'periode', 'numero_incomplet', 'tiers_absent'])
def test_refus_et_rollback_integral(application, cas):
    with closing(client(application)[0]) as api:
        _, _, payload = dossier(api)
        r = poster(api, payload)
        assert r.status_code == 201, r.text
        rows = r.json()
        attendu = 409
        if cas == 'absent':
            payload['operation_id'] = str(uuid.uuid4()); attendu = 404
        elif cas == 'partiel':
            r = api.post(f"/api/reglements/{rows[0]['id']}/annuler", json={})
            assert r.status_code == 200, r.text
        elif cas == 'origine_absente':
            # Corruption fictive d'un lien non définitif : la seconde ligne
            # échoue APRÈS la préparation de la première contrepassation.
            cible(application)
            with Session(application['engine']) as db:
                r = db.get(models.Reglement, rows[1]['id'])
                r.ecriture_id = None
                r.reference = 'SOURCE FICTIVE INTROUVABLE'
                db.commit()
        elif cas == 'periode':
            cible(application)
            with Session(application['engine']) as db:
                sid = db.get(models.Reglement, rows[0]['id']).societe_id
                ex = db.query(models.ExerciceComptable).filter_by(societe_id=sid, annee=date.today().year).one()
                ex.statut = 'cloture'; db.commit()
            attendu = 423
        elif cas in {'numero_incomplet', 'tiers_absent'}:
            cible(application)
            with Session(application['engine']) as db:
                r = db.get(models.Reglement, rows[1]['id'])
                if cas == 'numero_incomplet': r.numero = r.numero[:-2]+'03'
                else: r.tiers_id = None
                db.commit()
        if cas == 'autre_societe':
            with closing(client(application)[0]) as autre:
                avant = photo(application)
                r = annuler(autre, payload)
            attendu = 404
        else:
            avant = photo(application)
            r = annuler(api, payload)
        assert r.status_code == attendu, r.text
        assert photo(application) == avant


def test_annulation_concurrente_unique_et_lecture_sans_mutation(application):
    with closing(client(application)[0]) as api:
        _, _, payload = dossier(api)
        rows = poster(api, payload).json()
        avant = photo(application)
        r = api.get('/api/reglements/par-tiers/'+payload['operation_id'])
        assert r.status_code == 200, r.text
        assert [x['id'] for x in r.json()] == [x['id'] for x in rows]
        assert photo(application) == avant
        def envoyer(_):
            with httpx.Client(base_url=application['api_url'], headers=dict(api.headers)) as concurrent:
                return annuler(concurrent, payload)
        with ThreadPoolExecutor(max_workers=2) as pool:
            rs = list(pool.map(envoyer, range(2)))
        assert [r.status_code for r in rs] == [200, 200], [r.text for r in rs]
        assert [x['ecriture_annulation_id'] for x in rs[0].json()] == [x['ecriture_annulation_id'] for x in rs[1].json()]
        with Session(application['engine']) as db:
            eids = [r['ecriture_id'] for r in rows]
            assert db.query(models.Ecriture).filter(models.Ecriture.contrepassation_de_id.in_(eids)).count() == 2


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('largeur', [1365, 390])
def test_edge_confirmation_lot_complet_et_refresh(application, sens, largeur):
    from test_e2e_administration_isole import connexion, observer
    from browser_support import chromium_executable
    from playwright.sync_api import sync_playwright, expect
    api, email, password = client(application)
    try:
        _, _, payload = dossier(api, sens, jour=(date.today()-timedelta(days=2)).isoformat())
        r = poster(api, payload)
        assert r.status_code == 201, r.text
        rows = r.json()
        ids = [x['id'] for x in rows]
        originaux = {}
        for row in rows:
            eid = row['ecriture_id']
            assert api.post(f'/api/ecritures/{eid}/valider').status_code == 200
            originaux[eid] = api.get(f'/api/ecritures/{eid}').json()
        avant = photo(application)
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                messages = []
                def accepter(d):
                    messages.append(d.message); d.accept()
                page.on('dialog', accepter)
                erreurs, serveurs = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/commercial')
                page.get_by_role('button', name='Vente' if sens == 'vente' else 'Achat', exact=True).click()
                page.get_by_role('button', name='Règlements', exact=True).click()
                expect(page.locator('tbody tr')).to_have_count(2)
                page.get_by_title('Annuler toute la ventilation', exact=True).click()
                modal = page.get_by_role('dialog', name='Annuler toute la ventilation', exact=True)
                expect(modal).to_contain_text('2 règlement(s)')
                expect(modal).to_contain_text('240,00 MAD')
                for row in rows:
                    expect(modal).to_contain_text(row['numero'])
                modal.get_by_label('Date d’annulation *', exact=True).fill((date.today()+timedelta(days=1)).isoformat())
                motif = 'Annulation collective fictive659, date choisie'
                modal.get_by_label('Motif (facultatif)', exact=True).fill(motif)
                with page.expect_response(lambda r: '/par-tiers/' in r.url and r.url.endswith('/annuler') and r.request.method == 'POST') as refus:
                    modal.get_by_role('button', name='Confirmer l’annulation', exact=True).click()
                assert refus.value.status == 422, refus.value.text()
                expect(modal.get_by_role('alert')).to_contain_text('future')
                assert photo(application) == avant
                choisie = (date.today()-timedelta(days=1)).isoformat()
                modal.get_by_label('Date d’annulation *', exact=True).fill(choisie)
                with page.expect_response(lambda r: '/par-tiers/' in r.url and r.url.endswith('/annuler') and r.request.method == 'POST') as annulation:
                    modal.get_by_role('button', name='Confirmer l’annulation', exact=True).click()
                assert annulation.value.status == 200, annulation.value.text()
                assert annulation.value.request.post_data_json == {'date_annulation': choisie, 'motif': motif}
                assert not messages
                modal.wait_for(state='hidden')
                for row in annulation.value.json():
                    assert api.get(f"/api/ecritures/{row['ecriture_id']}").json() == originaux[row['ecriture_id']]
                    inverse = api.get(f"/api/ecritures/{row['ecriture_annulation_id']}").json()
                    assert inverse['date'] == inverse['date_piece'] == choisie
                    assert inverse['motif_correction'] == motif and not inverse['est_validee']
                expect(page.locator('tbody tr')).to_have_count(2)
                for row in page.locator('tbody tr').all(): expect(row).to_contain_text('annule')
                expect(page.get_by_title('Annuler toute la ventilation', exact=True)).to_have_count(0)
                page.reload()
                page.get_by_role('button', name='Vente' if sens == 'vente' else 'Achat', exact=True).click()
                page.get_by_role('button', name='Règlements', exact=True).click()
                for row in page.locator('tbody tr').all(): expect(row).to_contain_text('annule')
                r = api.get('/api/reglements', params={'exercice': date.today().year})
                assert {x['statut'] for x in r.json() if x['id'] in ids} == {'annule'}
                assert not erreurs and not serveurs, (erreurs, serveurs)
            finally:
                browser.close()
    finally:
        api.close()


def test_permission_lecture_et_uuid_invalide_sans_mutation(application):
    with closing(client(application)[0]) as api:
        _, _, p = dossier(api)
        assert poster(api, p).status_code == 201
        email = uuid.uuid4().hex+'@example.com'
        r = api.post('/api/utilisateurs', json={'nom': 'Lecteur fictif', 'email': email,
            'mot_de_passe': 'Lecture2026!', 'role': 'lecture'})
        assert r.status_code == 201, r.text
        with httpx.Client(base_url=application['api_url']) as lecteur:
            r = lecteur.post('/api/auth/login', json={'email': email, 'password': 'Lecture2026!'})
            assert r.status_code == 200, r.text
            lecteur.headers['Authorization'] = 'Bearer '+r.json()['access_token']
            avant = photo(application)
            assert lecteur.get('/api/reglements/par-tiers/'+p['operation_id']).status_code == 200
            assert annuler(lecteur, p).status_code == 403
            assert api.post('/api/reglements/par-tiers/pas-un-uuid/annuler', json={}).status_code == 422
            assert photo(application) == avant


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_annulation_lot_contrepassation_capture_ras_et_origines_conservees(application, sens):
    from test_ras_capture_reglement_postgres import appliquer, payload as ras_payload
    appliquer(application)
    with closing(client(application)[0]) as api:
        _, ids, p = dossier(api, sens, ras=10)
        p['ventilations'][0]['montant'] = 110
        p['montant'] = 230
        r = poster(api, p)
        assert r.status_code == 201, r.text
        rows = r.json()
        r = api.post(f"/api/reglements/{rows[0]['id']}/ras", json=ras_payload(10, sens, 'RAS-LOT-FICTIF'))
        assert r.status_code == 200, r.text
        capture = r.json()
        eids = [x['ecriture_id'] for x in rows]+[capture['ecriture_id']]
        for eid in eids:
            assert api.post(f'/api/ecritures/{eid}/valider', json={}).status_code == 200
        with Session(application['engine']) as db:
            origines = {eid: [(l.id, l.compte, l.debit, l.credit, l.tiers_id) for l in db.get(models.Ecriture, eid).lignes] for eid in eids}
        r = annuler(api, p)
        assert r.status_code == 200, r.text
        with Session(application['engine']) as db:
            assert db.query(models.Ecriture).filter(models.Ecriture.contrepassation_de_id.in_(eids)).count() == 3
            assert all(db.get(models.Ecriture, eid).est_validee for eid in eids)
            assert {eid: [(l.id, l.compte, l.debit, l.credit, l.tiers_id) for l in db.get(models.Ecriture, eid).lignes] for eid in eids} == origines
        for fid, solde in zip(ids, [120, 240]):
            s = api.get(f'/api/factures/{fid}/reglements').json()
            assert s['total_regle'] == 0 and s['montant_ras_impute'] == 0 and s['solde_restant'] == solde
        c = api.get(f"/api/reglements/{rows[0]['id']}/ras").json()['captures'][0]
        assert c['annulation_id'] and c['ecriture_annulation_id']
        avant = photo(application)
        assert annuler(api, p).status_code == 200
        assert photo(application) == avant


@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), float('-inf'), 0, -10], ids=['nan', 'inf', '-inf', 'zero', 'negatif'])
def test_lot_historique_montant_invalide_lisible_et_annulation_refusee(application, valeur):
    with closing(client(application)[0]) as api:
        _, _, p = dossier(api)
        p['comptabiliser'] = False
        r = poster(api, p)
        assert r.status_code == 201, r.text
        rid = r.json()[1]['id']
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text('UPDATE reglements SET montant=:v WHERE id=:id AND est_comptabilisee=false'), {'v': valeur, 'id': rid})
        avant = photo(application)
        r = api.get('/api/reglements/par-tiers/'+p['operation_id'])
        assert r.status_code == 200, r.text
        mauvais = next(x for x in r.json() if x['id'] == rid)
        assert mauvais['montant_valide'] is False and mauvais['montant_anomalie']
        assert annuler(api, p).status_code == 422
        assert photo(application) == avant
