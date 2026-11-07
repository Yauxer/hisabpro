"""Grand livre : contexte retardé réel, CSV, Edge et PostgreSQL nonce."""
import csv
from datetime import date
from decimal import Decimal
import uuid

import httpx
import pytest
from sqlalchemy import text

from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def preparer(application):
    suffixe = uuid.uuid4().hex[:10]
    email, password, annee = suffixe+'@example.com', 'GrandLivreDates2026!', date.today().year
    api = httpx.Client(base_url=application['api_url'])
    r = api.post('/api/auth/register', json={'nom': 'Grand livre fictif', 'email': email,
        'password': password, 'raison_sociale': 'Grand livre dates fictif '+suffixe})
    assert r.status_code == 200, r.text
    api.headers['Authorization'] = 'Bearer '+r.json()['access_token']
    sid = api.get('/api/societe/moi').json()['id']
    for jour, reference, lignes in (
        ('01-05', 'CAP-GL-DATES', [{'compte': '5141', 'debit': 1000}, {'compte': '1111', 'credit': 1000}]),
        ('03-15', 'MARS-GL-DATES', [{'compte': '6111', 'debit': 200}, {'compte': '5141', 'credit': 200}]),
    ):
        r = api.post('/api/ecritures', json={'date': f'{annee}-{jour}', 'journal': 'OD',
            'reference': reference, 'libelle': 'Opération fictive '+reference, 'lignes': lignes})
        assert r.status_code == 201, r.text
        r = api.post(f"/api/ecritures/{r.json()['id']}/valider")
        assert r.status_code == 200, r.text
    return api, email, password, annee, sid


def photographie(application):
    with application['engine'].connect() as db:
        return {table: db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).scalars().all()
                for table in ('ecritures', 'lignes_ecriture')}


def exporter(page, tmp_path, nom):
    with page.expect_download() as sortie:
        page.get_by_role('button', name='Exporter CSV', exact=True).click()
    path = tmp_path/(nom+'.csv')
    sortie.value.save_as(path)
    assert sortie.value.suggested_filename == 'grand_livre.csv'
    with path.open(encoding='utf-8-sig', newline='') as fichier:
        return list(csv.DictReader(fichier, delimiter=';'))


def verifier_mars(rows, annee, initial='1000.00', credit='200.00', cumul='800.00'):
    assert len(rows) == 1, rows
    row = rows[0]
    assert row['Compte'] == '5141' and row['Date'] == f'{annee}-03-15'
    assert Decimal(row['Solde initial'].replace(',', '.')) == Decimal(initial)
    assert Decimal(row['Débit'].replace(',', '.')) == 0
    assert Decimal(row['Crédit'].replace(',', '.')) == Decimal(credit)
    assert Decimal(row['Solde cumulé'].replace(',', '.')) == Decimal(cumul)


@pytest.mark.parametrize('saisie', [True, False], ids=['filtre-mars-conserve', 'bornes-decalees-initialisees'])
def test_dates_preservees_a_arrivee_tardive_exercice(application, tmp_path, saisie):
    api, email, password, annee, sid = preparer(application)
    try:
        if not saisie:
            r = api.patch(f'/api/exercices/{annee}', json={'date_debut': f'{annee}-01-02', 'date_fin': f'{annee}-06-30'})
            assert r.status_code == 200, r.text
        r = api.post('/api/exercices', json={'annee': annee+1, 'date_debut': f'{annee+1}-04-01', 'date_fin': f'{annee+1}-09-30'})
        assert r.status_code == 201, r.text
        avant = photographie(application)
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable: pytest.skip('Chromium/Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(accept_downloads=True)
                page.set_default_timeout(20000)
                errors, server = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                retenues = []
                def retenir(route):
                    response = route.fetch()
                    assert response.status == 200
                    assert any(x['annee'] == annee for x in response.json())
                    retenues.append((route, response))
                    page.evaluate('window.__exercicesGLRetenus=true')
                page.route('**/api/exercices', retenir)
                page.goto(application['web_url']+'/grand-livre', wait_until='domcontentloaded')
                page.wait_for_function('window.__exercicesGLRetenus===true')
                page.get_by_text('5141', exact=True).wait_for()
                page.get_by_placeholder('Compte, libellé, tiers, référence, n° écriture…').fill('5141')
                dates = page.locator('input[type=date]')
                if saisie:
                    dates.nth(0).fill(f'{annee}-03-01')
                    with page.expect_response(lambda r: '/reporting/grand-livre?' in r.url and f'date_from={annee}-03-01' in r.url and f'date_to={annee}-03-31' in r.url):
                        dates.nth(1).fill(f'{annee}-03-31')
                    verifier_mars(exporter(page, tmp_path, 'avant_contexte'), annee)
                page.unroute('**/api/exercices', retenir)
                with page.expect_response(lambda r: r.url.endswith('/api/exercices')):
                    for route, response in retenues: route.fulfill(response=response)
                select = page.locator('select').filter(has=page.locator(f'option[value="{annee+1}"]')).first
                playwright.expect(select).to_be_enabled()
                page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                debut = f'{annee}-03-01' if saisie else f'{annee}-01-02'
                fin = f'{annee}-03-31' if saisie else f'{annee}-06-30'
                print('Dates grand livre après contexte réel :', dates.nth(0).input_value(), dates.nth(1).input_value())
                assert dates.nth(0).input_value() == debut
                assert dates.nth(1).input_value() == fin
                rows = exporter(page, tmp_path, 'apres_contexte')
                if saisie: verifier_mars(rows, annee)
                else:
                    assert [row['Date'] for row in rows] == [f'{annee}-01-05', f'{annee}-03-15']
                    assert Decimal(rows[-1]['Solde cumulé'].replace(',', '.')) == 800
                select.select_option(str(annee+1))
                playwright.expect(dates.nth(0)).to_have_value(f'{annee+1}-04-01')
                playwright.expect(dates.nth(1)).to_have_value(f'{annee+1}-09-30')
                assert not errors and not server, (errors, server)
            finally:
                browser.close()
        assert photographie(application) == avant
    finally:
        api.close()


def test_changement_societe_reinitialise_dates_et_csv(application, tmp_path):
    api, email, password, annee, sid = preparer(application)
    try:
        nom_a = api.get('/api/societe/moi').json()['raison_sociale']
        nom_b = 'Grand livre autre fictif '+uuid.uuid4().hex[:8]
        r = api.post('/api/societes/nouvelle', json={'raison_sociale': nom_b})
        assert r.status_code == 201, r.text
        bid = r.json()['id']
        r = api.post(f'/api/societes/switcher/{bid}')
        assert r.status_code == 200, r.text
        with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer '+r.json()['access_token']}) as autre:
            r = autre.patch(f'/api/exercices/{annee}', json={'date_debut': f'{annee}-02-01', 'date_fin': f'{annee}-09-30'})
            assert r.status_code == 200, r.text
            r = autre.post('/api/ecritures', json={'date': f'{annee}-03-15', 'journal': 'OD', 'reference': 'AUTRE-GL',
                'libelle': 'Charge fictive autre société', 'lignes': [{'compte': '6111', 'debit': 17}, {'compte': '5141', 'credit': 17}]})
            assert r.status_code == 201, r.text
            assert autre.post(f"/api/ecritures/{r.json()['id']}/valider").status_code == 200
        avant = photographie(application)
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable: pytest.skip('Chromium/Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(accept_downloads=True)
                page.set_default_timeout(20000)
                errors, server = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/grand-livre', wait_until='domcontentloaded')
                page.get_by_text('5141', exact=True).wait_for()
                page.get_by_placeholder('Compte, libellé, tiers, référence, n° écriture…').fill('5141')
                dates = page.locator('input[type=date]')
                dates.nth(0).fill(f'{annee}-03-01')
                dates.nth(1).fill(f'{annee}-03-31')
                verifier_mars(exporter(page, tmp_path, 'societe_a'), annee)
                page.get_by_role('button', name=nom_a, exact=True).click()
                with page.expect_response(lambda r: r.url.endswith(f'/api/societes/switcher/{bid}')):
                    page.get_by_text(nom_b, exact=True).click()
                page.get_by_role('button', name=nom_b, exact=True).wait_for()
                playwright.expect(dates.nth(0)).to_have_value(f'{annee}-02-01')
                playwright.expect(dates.nth(1)).to_have_value(f'{annee}-09-30')
                page.get_by_placeholder('Compte, libellé, tiers, référence, n° écriture…').fill('5141')
                rows = exporter(page, tmp_path, 'societe_b')
                verifier_mars(rows, annee, initial='0', credit='17', cumul='-17')
                assert rows[0]['Référence'] == 'AUTRE-GL'
                assert not errors and not server, (errors, server)
            finally:
                browser.close()
        assert photographie(application) == avant
    finally:
        api.close()
