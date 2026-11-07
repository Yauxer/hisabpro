"""Cession différée : Edge, API/JWT et PostgreSQL nonce réels, sans tiers inventé."""
from decimal import Decimal
import uuid
import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ
from test_e2e_immobilisations_sortie_isole import instantane, comptes


def source_snapshot(application, iid, ids):
    with application['engine'].connect() as db:
        immo = db.execute(text('SELECT row_to_json(i)::text FROM immobilisations i WHERE id=:id'), {'id': iid}).scalar_one()
    return immo, instantane(application, ids)


def test_cession_differee_encaissement_et_validations_browser(application):
    cible = application['cluster']
    assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    suffix = uuid.uuid4().hex[:8]
    email, password = f'cession-diff-{suffix}@example.com', 'CessionDiff2026!'
    designation = 'Matériel fictif différé ' + suffix
    with httpx.Client(base_url=application['api_url']) as api:
        r = api.post('/api/auth/register', json={'nom': 'Admin fictif', 'email': email,
            'password': password, 'raison_sociale': 'Cession différée fictive ' + suffix})
        assert r.status_code == 200, r.text
        api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        for annee in (2024, 2025):
            r = api.post('/api/exercices', json={'annee': annee,
                'date_debut': f'{annee}-01-01', 'date_fin': f'{annee}-12-31'})
            assert r.status_code == 201, r.text
        r = api.post('/api/immobilisations', json={'designation': designation,
            'categorie': 'Matériel informatique', 'date_acquisition': '2024-01-01',
            'date_mise_en_service': '2024-01-01', 'prix_acquisition_ht': 10000,
            'duree_amort': 5, 'methode': 'lineaire', 'compte_immo': '2355',
            'compte_amort': '28355', 'compte_dotation': '61935'})
        assert r.status_code == 201, r.text
        iid, acquisition_id = r.json()['id'], r.json()['ecriture_acquisition_id']
        assert api.post(f'/api/ecritures/{acquisition_id}/valider').status_code == 200
        assert api.post(f'/api/immobilisations/{iid}/generer-ecriture?annee=2024').status_code == 200
        with Session(application['engine']) as db:
            sid = db.get(models.Ecriture, acquisition_id).societe_id
            dotation_id = db.query(models.Ecriture).filter_by(societe_id=sid, reference=f'AM-2024-{iid}').one().id
            assert comptes(db.get(models.Ecriture, acquisition_id)) == {'2355': (10000, 0), '34551': (2000, 0), '4481': (0, 12000)}
            assert comptes(db.get(models.Ecriture, dotation_id)) == {'61935': (2000, 0), '28355': (0, 2000)}
        assert api.post(f'/api/ecritures/{dotation_id}/valider').status_code == 200
        originaux = instantane(application, [acquisition_id, dotation_id])
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium/Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                def dialogue(dialog):
                    if dialog.type == 'prompt':
                        dialog.accept('5141' if 'Compte de trésorerie' in dialog.message else '2026-01-15')
                    else:
                        dialog.accept()
                page.on('dialog', dialogue)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/immobilisations', wait_until='domcontentloaded')
                ligne = page.locator('tbody tr').filter(has_text=designation)
                ligne.locator('button[title="Cession / mise au rebut"]').click()
                modal = page.locator('[class*="modalOverlay"]').filter(has_text='Sortie — ' + designation)
                champ(modal, 'Date de sortie').fill('2025-12-31')
                champ(modal, 'Prix de cession HT').fill('7500')
                champ(modal, 'TVA cession (%)', 'select').select_option('20')
                modal.get_by_role('checkbox', name='Cession encaissée immédiatement').uncheck()
                with page.expect_response(lambda r: r.url.endswith(f'/api/immobilisations/{iid}/sortie') and r.request.method == 'POST') as sortie:
                    modal.get_by_role('button', name='Comptabiliser la sortie', exact=True).click()
                assert sortie.value.status == 200, sortie.value.text()
                data = sortie.value.json()
                for nom, attendu in {'cumul_amortissement': '4000', 'vnc': '6000',
                    'prix_cession_ht': '7500', 'tva_cession': '1500', 'ttc_cession': '9000', 'resultat_cession': '1500'}.items():
                    assert Decimal(str(data[nom])) == Decimal(attendu), data
                assert data['ecriture_encaissement_id'] is None
                modal.wait_for(state='hidden')
                ligne.get_by_text('Cédé', exact=True).wait_for()
                ligne.locator('button[title="Encaisser la cession"]').wait_for()
                with Session(application['engine']) as db:
                    ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).all()
                    assert len(ecritures) == 5
                    ids = [e.id for e in ecritures]
                    assert comptes(db.get(models.Ecriture, data['ecriture_sortie_id'])) == {'28355': (4000, 0), '6513': (6000, 0), '2355': (0, 10000)}
                    cession = db.get(models.Ecriture, data['ecriture_cession_id'])
                    assert comptes(cession) == {'3481': (9000, 0), '7513': (0, 7500), '4455': (0, 1500)}
                    assert db.get(models.Immobilisation, iid).date_encaissement_cession is None
                    assert all(l.tiers_id is None and l.compte_auxiliaire_snapshot is None for l in cession.lignes)
                    dotation = db.query(models.Ecriture).filter_by(societe_id=sid, reference=f'AM-2025-{iid}').one()
                    assert comptes(dotation) == {'61935': (2000, 0), '28355': (0, 2000)}
                avant_refus = source_snapshot(application, iid, ids)
                r = api.post(f'/api/immobilisations/{iid}/encaisser-cession', json={'date_encaissement': '2025-12-30'})
                assert r.status_code == 400, r.text
                assert source_snapshot(application, iid, ids) == avant_refus
                page.goto(application['web_url'] + '/journal', wait_until='domcontentloaded')
                page.locator('select').filter(has=page.locator('option[value="2025"]')).first.select_option('2025')
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(3)
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as validation:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert validation.value.status == 200 and validation.value.json()['nb_validees'] == 3
                avant_encaissement = instantane(application, ids)
                r = api.patch('/api/exercices/2026/periodes/1', json={'statut': 'fermee'})
                assert r.status_code == 200, r.text
                sources_periode_fermee = source_snapshot(application, iid, ids)
                r = api.post(f'/api/immobilisations/{iid}/encaisser-cession', json={'date_encaissement': '2026-01-15'})
                assert r.status_code == 423, r.text
                assert instantane(application, ids) == avant_encaissement
                assert source_snapshot(application, iid, ids) == sources_periode_fermee
                assert api.patch('/api/exercices/2026/periodes/1', json={'statut': 'ouverte'}).status_code == 200
                page.goto(application['web_url'] + '/immobilisations', wait_until='domcontentloaded')
                ligne = page.locator('tbody tr').filter(has_text=designation)
                with page.expect_response(lambda r: r.url.endswith(f'/api/immobilisations/{iid}/encaisser-cession') and r.request.method == 'POST') as encaissement:
                    ligne.locator('button[title="Encaisser la cession"]').click()
                assert encaissement.value.status == 200, encaissement.value.text()
                enc_id = encaissement.value.json()['ecriture_id']
                playwright.expect(ligne.locator('button[title="Encaisser la cession"]')).to_have_count(0)
                page.reload(wait_until='domcontentloaded')
                playwright.expect(page.locator('tbody tr').filter(has_text=designation).locator('button[title="Encaisser la cession"]')).to_have_count(0)
                with Session(application['engine']) as db:
                    enc = db.get(models.Ecriture, enc_id)
                    assert enc.exercice == 2026 and enc.date.isoformat() == '2026-01-15' and not enc.est_validee
                    assert comptes(enc) == {'5141': (9000, 0), '3481': (0, 9000)}
                    assert all(l.tiers_id is None for l in enc.lignes)
                    assert len(db.query(models.Ecriture).filter_by(societe_id=sid).all()) == 6
                    assert all(sum(l.debit for l in e.lignes) == sum(l.credit for l in e.lignes) for e in db.query(models.Ecriture).filter_by(societe_id=sid))
                    creance = db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid, models.LigneEcriture.compte == '3481').all()
                    assert sum(l.debit - l.credit for l in creance) == 0
                    assert db.query(models.Facture).filter_by(societe_id=sid).count() == 0
                assert instantane(application, ids) == avant_encaissement
                page.goto(application['web_url'] + '/journal', wait_until='domcontentloaded')
                page.locator('select').filter(has=page.locator('option[value="2026"]')).first.select_option('2026')
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(1)
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as validation:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert validation.value.status == 200 and validation.value.json()['nb_validees'] == 1
                with Session(application['engine']) as db:
                    assert all(e.est_validee for e in db.query(models.Ecriture).filter_by(societe_id=sid))
                final = source_snapshot(application, iid, ids + [enc_id])
                assert api.post(f'/api/immobilisations/{iid}/encaisser-cession', json={'date_encaissement': '2026-01-16'}).status_code == 409
                assert source_snapshot(application, iid, ids + [enc_id]) == final
                assert instantane(application, [acquisition_id, dotation_id]) == originaux
                assert not errors and not server_errors, (errors, server_errors)
            finally:
                browser.close()
        with httpx.Client(base_url=application['api_url']) as autre:
            r = autre.post('/api/auth/register', json={'nom': 'Autre fictif', 'email': f'autre-diff-{suffix}@example.com',
                'password': password, 'raison_sociale': 'Autre cession fictive ' + suffix})
            assert r.status_code == 200, r.text
            autre.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
            assert autre.post(f'/api/immobilisations/{iid}/encaisser-cession', json={'date_encaissement': '2026-01-15'}).status_code == 404
        assert source_snapshot(application, iid, ids + [enc_id]) == final
