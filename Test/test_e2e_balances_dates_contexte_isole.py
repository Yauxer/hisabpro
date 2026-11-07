"""Contexte exercice retardé : vrais corps HTTP, Edge et PostgreSQL nonce."""
import pytest
import httpx
import uuid
from openpyxl import load_workbook
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_balances_exports_isole import preparer, telecharger, cellules, pdf_texte
from test_e2e_facturation_isole import application


@pytest.mark.parametrize('saisie_utilisateur', [True, False], ids=['filtre-mars-conserve', 'bornes-exercice-initialisees'])
def test_dates_balance_preservees_a_arrivee_tardive_exercice(application, tmp_path, saisie_utilisateur):
    api, email, password, annee, sid, noms = preparer(application)
    try:
        if not saisie_utilisateur:
            r = api.patch(f'/api/exercices/{annee}', json={'date_debut': f'{annee}-01-02', 'date_fin': f'{annee}-06-30'})
            assert r.status_code == 200, r.text
        r = api.post('/api/exercices', json={'annee': annee + 1, 'date_debut': f'{annee+1}-04-01', 'date_fin': f'{annee+1}-09-30'})
        assert r.status_code == 201, r.text
        with Session(application['engine']) as db:
            avant = {(l.id, l.compte, l.debit, l.credit) for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid)}
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(accept_downloads=True)
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                retenues = []
                def retenir(route):
                    reponse = route.fetch()
                    assert reponse.status == 200, reponse.text()
                    assert any(x['annee'] == annee for x in reponse.json())
                    retenues.append((route, reponse))
                    page.evaluate('window.__exercicesReelsRetenus = true')
                page.route('**/api/exercices', retenir)
                page.goto(application['web_url'] + '/balances', wait_until='domcontentloaded')
                page.wait_for_function('window.__exercicesReelsRetenus === true')
                page.get_by_text('Balance équilibrée', exact=False).wait_for()
                dates = page.locator('input[type=date]')
                if saisie_utilisateur:
                    dates.nth(0).fill(f'{annee}-03-01')
                    with page.expect_response(lambda r: '/api/ecritures/reporting/balance?' in r.url and f'date_from={annee}-03-01' in r.url and f'date_to={annee}-03-31' in r.url):
                        dates.nth(1).fill(f'{annee}-03-31')
                    page.get_by_text('Balance équilibrée', exact=False).wait_for()
                    page.get_by_role('button', name='Balance Comparative', exact=False).click()
                    periode = f'{annee}-03-01 au {annee}-03-31 comparé au {annee-1}-03-01 au {annee-1}-03-31'
                    wb = load_workbook(telecharger(page, 'Excel', tmp_path, 'avant_contexte'))
                    assert cellules(wb)[2][1] == periode
                page.unroute('**/api/exercices', retenir)
                with page.expect_response(lambda r: r.url.endswith('/api/exercices')):
                    for route, reponse in retenues:
                        route.fulfill(response=reponse)
                # L'option est rendue à partir du vrai contexte reçu ; pas de sleep.
                select_exercice = page.locator('select').filter(has=page.locator(f'option[value="{annee+1}"]')).first
                pytest.importorskip('playwright.sync_api').expect(select_exercice).to_be_enabled()
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                attendu_debut = f'{annee}-03-01' if saisie_utilisateur else f'{annee}-01-02'
                attendu_fin = f'{annee}-03-31' if saisie_utilisateur else f'{annee}-06-30'
                print('Dates après vrai contexte exercice :', dates.nth(0).input_value(), dates.nth(1).input_value())
                assert dates.nth(0).input_value() == attendu_debut
                assert dates.nth(1).input_value() == attendu_fin
                if saisie_utilisateur:
                    page.get_by_role('button', name='Exporter Excel', exact=True).wait_for()
                    wb = load_workbook(telecharger(page, 'Excel', tmp_path, 'apres_contexte'))
                    rows = cellules(wb)
                    assert rows[2][1] == periode
                    assert next(r for r in rows[7:] if r[0] == '6111')[3] == 500
                    assert next(r for r in rows[7:] if r[0] == '7111')[3] == -1000
                    texte = pdf_texte(telecharger(page, 'PDF', tmp_path, 'apres_contexte'))
                    assert f'{annee}-03-01 au {annee}-03-31' in texte
                    assert f'{annee-1}-03-01 au {annee-1}-03-31' in texte
                # Un vrai changement d'exercice doit remplacer l'ancien filtre.
                select_exercice.select_option(str(annee + 1))
                pytest.importorskip('playwright.sync_api').expect(dates.nth(0)).to_have_value(f'{annee+1}-04-01')
                pytest.importorskip('playwright.sync_api').expect(dates.nth(1)).to_have_value(f'{annee+1}-09-30')
                assert not errors and not server_errors, (errors, server_errors)
            finally:
                browser.close()
        with Session(application['engine']) as db:
            apres = {(l.id, l.compte, l.debit, l.credit) for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid)}
            assert avant == apres
    finally:
        api.close()


def test_changement_societe_reinitialise_periode_et_exports(application, tmp_path):
    api, email, password, annee, sid, noms = preparer(application)
    try:
        nom_a = api.get('/api/societe/moi').json()['raison_sociale']
        nom_b = 'Autre balance fictive ' + uuid.uuid4().hex[:8]
        r = api.post('/api/societes/nouvelle', json={'raison_sociale': nom_b})
        assert r.status_code == 201, r.text
        bid = r.json()['id']
        r = api.post(f'/api/societes/switcher/{bid}')
        assert r.status_code == 200, r.text
        with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer ' + r.json()['access_token']}) as autre:
            r = autre.patch(f'/api/exercices/{annee}', json={'date_debut': f'{annee}-02-01', 'date_fin': f'{annee}-09-30'})
            assert r.status_code == 200, r.text
            r = autre.post('/api/ecritures', json={'date': f'{annee}-05-10', 'journal': 'OD', 'reference': 'AUTRE-BALANCE', 'libelle': 'Charge fictive société B', 'lignes': [{'compte': '6111', 'debit': 17}, {'compte': '5141', 'credit': 17}]})
            assert r.status_code == 201, r.text
            assert autre.post(f"/api/ecritures/{r.json()['id']}/valider").status_code == 200
        with Session(application['engine']) as db:
            avant = {(l.id, l.compte, l.debit, l.credit) for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id.in_([sid, bid]))}
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(accept_downloads=True)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/balances', wait_until='domcontentloaded')
                page.get_by_text('Balance équilibrée', exact=False).wait_for()
                dates = page.locator('input[type=date]')
                dates.nth(0).fill(f'{annee}-03-01')
                dates.nth(1).fill(f'{annee}-03-31')
                page.get_by_text('Balance équilibrée', exact=False).wait_for()
                page.get_by_role('button', name=nom_a, exact=True).click()
                with page.expect_response(lambda r: r.url.endswith(f'/api/societes/switcher/{bid}')) as changement:
                    page.get_by_text(nom_b, exact=True).click()
                assert changement.value.status == 200
                page.get_by_role('button', name=nom_b, exact=True).wait_for()
                playwright.expect(dates.nth(0)).to_have_value(f'{annee}-02-01')
                playwright.expect(dates.nth(1)).to_have_value(f'{annee}-09-30')
                page.get_by_text('Balance équilibrée', exact=False).wait_for()
                rows = cellules(load_workbook(telecharger(page, 'Excel', tmp_path, 'societe_b')))
                assert rows[1][1] == nom_b
                assert rows[2][1] == f'{annee}-02-01 au {annee}-09-30'
                assert next(r for r in rows[7:] if r[0] == '6111')[4:6] == (17, 0)
                assert not any(r[0] == '1111' for r in rows[7:])
                texte = pdf_texte(telecharger(page, 'PDF', tmp_path, 'societe_b'))
                assert nom_b in texte and nom_a not in texte
                assert f'{annee}-02-01 au {annee}-09-30' in texte
                assert not errors and not server_errors, (errors, server_errors)
            finally:
                browser.close()
        with Session(application['engine']) as db:
            apres = {(l.id, l.compte, l.debit, l.credit) for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id.in_([sid, bid]))}
            assert avant == apres
    finally:
        api.close()
