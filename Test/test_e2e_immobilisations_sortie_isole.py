"""Cession/rebut : oracle indépendant, Edge/API/PostgreSQL nonce réels."""
from decimal import Decimal
import uuid

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ
from postgres_isole import verifier_cible_isolee


# Valeurs de laboratoire, fixées sans appel au moteur de production :
# 10 000 / 5 = 2 000 par an ; 2024 complet + 2025 complet/demi-année.
ORACLES = {
    'cession': {'date': '2025-12-31', 'cumul': Decimal('4000'), 'vnc': Decimal('6000'),
                'prix': Decimal('7500'), 'tva': Decimal('1500'), 'ttc': Decimal('9000'),
                'resultat': Decimal('1500'), 'dotation_2025': Decimal('2000'), 'nouvelles': 4},
    'rebut': {'date': '2025-06-30', 'cumul': Decimal('3000'), 'vnc': Decimal('7000'),
              'prix': Decimal('0'), 'tva': Decimal('0'), 'ttc': Decimal('0'),
              'resultat': Decimal('-7000'), 'dotation_2025': Decimal('1000'), 'nouvelles': 2},
}


def instantane(application, ids):
    with application['engine'].connect() as c:
        return (
            c.execute(text('SELECT row_to_json(e)::text FROM ecritures e WHERE id=ANY(:ids) ORDER BY id'), {'ids': ids}).all(),
            c.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l WHERE ecriture_id=ANY(:ids) ORDER BY id'), {'ids': ids}).all(),
        )


def comptes(ecriture):
    return {l.compte: (l.debit, l.credit) for l in ecriture.lignes}


@pytest.mark.parametrize('type_sortie', ['cession', 'rebut'])
def test_sortie_ui_oracle_validation_refus_et_originaux_immuables(application, type_sortie):
    cible = application['cluster']
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    oracle = ORACLES[type_sortie]
    suffix = uuid.uuid4().hex[:8]
    email, password = f'sortie-immo-{suffix}@example.com', 'SortieImmo2026!'
    designation = f'Matériel fictif {type_sortie} {suffix}'
    with httpx.Client(base_url=application['api_url']) as api:
        r = api.post('/api/auth/register', json={'nom': 'Admin sortie fictive', 'email': email,
            'password': password, 'raison_sociale': f'Sortie immo fictive {suffix}'})
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
        r = api.post(f'/api/immobilisations/{iid}/generer-ecriture?annee=2024')
        assert r.status_code == 200, r.text
        with Session(application['engine']) as db:
            acquisition = db.get(models.Ecriture, acquisition_id)
            sid = acquisition.societe_id
            dotation = db.query(models.Ecriture).filter_by(societe_id=sid, reference=f'AM-2024-{iid}').one()
            dotation_id = dotation.id
            assert comptes(acquisition) == {'2355': (10000, 0), '34551': (2000, 0), '4481': (0, 12000)}
            assert comptes(dotation) == {'61935': (2000, 0), '28355': (0, 2000)}
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
                dialogs = []
                def accepter(dialog):
                    dialogs.append(dialog.message)
                    dialog.accept()
                page.on('dialog', accepter)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/immobilisations', wait_until='domcontentloaded')
                ligne = page.locator('tbody tr').filter(has_text=designation)
                ligne.locator('button[title="Cession / mise au rebut"]').click()
                modal = page.locator('[class*="modalOverlay"]').filter(has_text='Sortie — ' + designation)
                champ(modal, 'Type de sortie', 'select').select_option(type_sortie)
                champ(modal, 'Date de sortie').fill(oracle['date'])
                if type_sortie == 'cession':
                    champ(modal, 'Prix de cession HT').fill('7500')
                    champ(modal, 'TVA cession (%)', 'select').select_option('20')
                    champ(modal, 'Date d’encaissement').fill(oracle['date'])
                with page.expect_response(lambda r: r.url.endswith(f'/api/immobilisations/{iid}/sortie')
                                           and r.request.method == 'POST') as sortie:
                    modal.get_by_role('button', name='Comptabiliser la sortie', exact=True).click()
                assert sortie.value.status == 200, sortie.value.text()
                data = sortie.value.json()
                for nom, valeur in [('cumul_amortissement', oracle['cumul']), ('vnc', oracle['vnc']),
                    ('prix_cession_ht', oracle['prix']), ('tva_cession', oracle['tva']),
                    ('ttc_cession', oracle['ttc']), ('resultat_cession', oracle['resultat'])]:
                    assert Decimal(str(data[nom])) == valeur, (nom, data)
                modal.wait_for(state='hidden')
                ligne.get_by_text('Cédé' if type_sortie == 'cession' else 'Rebut', exact=True).wait_for()
                assert ligne.locator('button[title="Cession / mise au rebut"]').count() == 0
                assert ligne.locator('button[title="Encaisser la cession"]').count() == 0
                # 967 : le résultat s'affiche en notification, sans dialogue natif.
                playwright.expect(page.locator('[data-notification]').filter(has_text='Résultat de sortie')).to_be_visible()
                with Session(application['engine']) as db:
                    ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).all()
                    assert len(ecritures) == 2 + oracle['nouvelles']
                    assert all(sum(l.debit for l in e.lignes) == sum(l.credit for l in e.lignes) for e in ecritures)
                    immo = db.get(models.Immobilisation, iid)
                    assert not immo.actif and immo.type_sortie == type_sortie
                    dotation = db.query(models.Ecriture).filter_by(societe_id=sid, reference=f'AM-2025-{iid}').one()
                    assert comptes(dotation) == {'61935': (oracle['dotation_2025'], 0), '28355': (0, oracle['dotation_2025'])}
                    assert comptes(db.get(models.Ecriture, data['ecriture_sortie_id'])) == {
                        '28355': (oracle['cumul'], 0), '6513': (oracle['vnc'], 0), '2355': (0, 10000)}
                    if type_sortie == 'cession':
                        assert comptes(db.get(models.Ecriture, data['ecriture_cession_id'])) == {
                            '3481': (9000, 0), '7513': (0, 7500), '4455': (0, 1500)}
                        assert comptes(db.get(models.Ecriture, data['ecriture_encaissement_id'])) == {
                            '5141': (9000, 0), '3481': (0, 9000)}
                    else:
                        assert data['ecriture_cession_id'] is None and data['ecriture_encaissement_id'] is None
                assert instantane(application, [acquisition_id, dotation_id]) == originaux
                page.goto(application['web_url'] + '/journal', wait_until='domcontentloaded')
                page.locator('select').filter(has=page.locator('option[value="2025"]')).first.select_option('2025')
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(oracle['nouvelles'])
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as validation:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert validation.value.status == 200, validation.value.text()
                assert validation.value.json()['nb_validees'] == oracle['nouvelles']
                with Session(application['engine']) as db:
                    assert all(e.est_validee for e in db.query(models.Ecriture).filter_by(societe_id=sid))
                    ids = [e.id for e in db.query(models.Ecriture).filter_by(societe_id=sid)]
                apres = instantane(application, ids)
                corps = {'type_sortie': type_sortie, 'date_sortie': oracle['date'], 'prix_cession_ht': float(oracle['prix'])}
                assert api.post(f'/api/immobilisations/{iid}/sortie', json=corps).status_code == 409
                r = api.post(f'/api/immobilisations/{iid}/encaisser-cession', json={'date_encaissement': oracle['date']})
                assert r.status_code == 409, r.text
                assert api.delete(f'/api/immobilisations/{iid}').status_code == 409
                assert instantane(application, ids) == apres
                assert instantane(application, [acquisition_id, dotation_id]) == originaux
                # Vraie contrainte SQL sur les originaux validés, transaction annulée.
                with pytest.raises(DBAPIError) as refus:
                    with application['engine'].begin() as c:
                        c.execute(text('UPDATE ecritures SET libelle=:libelle WHERE id=:id'),
                                  {'libelle': 'Tentative fictive refusée', 'id': acquisition_id})
                assert refus.value.orig.pgcode == '23514'
                assert instantane(application, [acquisition_id, dotation_id]) == originaux
                verifier_permissions_et_societes(api, application, iid, corps)
                assert instantane(application, ids) == apres
                page.goto(application['web_url'] + '/immobilisations', wait_until='domcontentloaded')
                ligne.get_by_text('Cédé' if type_sortie == 'cession' else 'Rebut', exact=True).wait_for()
                page.reload(wait_until='domcontentloaded')
                ligne.get_by_text('Cédé' if type_sortie == 'cession' else 'Rebut', exact=True).wait_for()
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print('Page fictive :', page.url, page.locator('body').inner_text()[:5000])
                print('Log API isolée :', application['api_log'].read_text(encoding='utf-8', errors='replace')[-6000:])
                raise
            finally:
                browser.close()


def verifier_permissions_et_societes(api, application, iid, corps):
    email = f'lecteur-sortie-{uuid.uuid4().hex[:8]}@example.com'
    r = api.post('/api/utilisateurs', json={'nom': 'Lecteur fictif', 'email': email,
        'mot_de_passe': 'LectureSortie2026!', 'role': 'lecture'})
    assert r.status_code == 201, r.text
    with httpx.Client(base_url=application['api_url']) as lecture:
        r = lecture.post('/api/auth/login', json={'email': email, 'password': 'LectureSortie2026!'})
        assert r.status_code == 200, r.text
        lecture.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        assert lecture.get('/api/immobilisations').status_code == 200
        assert lecture.post(f'/api/immobilisations/{iid}/sortie', json=corps).status_code == 403
        assert lecture.post(f'/api/immobilisations/{iid}/encaisser-cession', json={'date_encaissement': corps['date_sortie']}).status_code == 403
    with httpx.Client(base_url=application['api_url']) as autre:
        suffix = uuid.uuid4().hex[:8]
        r = autre.post('/api/auth/register', json={'nom': 'Autre fictif', 'email': f'autre-sortie-{suffix}@example.com',
            'password': 'AutreSortie2026!', 'raison_sociale': 'Autre société fictive ' + suffix})
        assert r.status_code == 200, r.text
        autre.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        assert autre.get('/api/immobilisations').json() == []
        assert autre.post(f'/api/immobilisations/{iid}/sortie', json=corps).status_code == 404
