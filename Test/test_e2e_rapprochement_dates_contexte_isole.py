"""Filtres bancaires : réponses véritables retardées, sans écriture métier."""
import pytest
import httpx
import uuid
from sqlalchemy import text

from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application
from test_e2e_grandlivre_dates_contexte_isole import preparer, photographie as photo_ecritures


def photographie(application):
    resultat = photo_ecritures(application)
    with application['engine'].connect() as db:
        for table in ('rapprochement_lignes', 'rapprochement_etats', 'comptes_bancaires'):
            resultat[table] = db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).scalars().all()
    return resultat


def verifier_mars(page, playwright):
    playwright.expect(page.locator('tbody tr').filter(has_text='MARS-GL-DATES')).to_have_count(1)
    playwright.expect(page.locator('tbody tr').filter(has_text='CAP-GL-DATES')).to_have_count(0)
    page.get_by_text('800,00 MAD', exact=True).wait_for()


@pytest.mark.parametrize('retard', ['exercice', 'situation'])
def test_filtre_mars_et_lecture_courante_preserves(application, retard):
    api, email, password, annee, sid = preparer(application)
    try:
        avant = photographie(application)
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium/Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(20000)
                errors, server = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                retenues = []
                motif = '**/api/exercices' if retard == 'exercice' else '**/api/rapprochement/5141/situation?*'

                def retenir(route):
                    # Seule la lecture annuelle initiale est retardée. Le vrai
                    # corps API reste intact, y compris les deux mouvements.
                    if retard == 'situation' and (f'date_fin={annee}-12-31' not in route.request.url
                            or f'date_debut={annee}-01-01' not in route.request.url):
                        route.continue_()
                        return
                    response = route.fetch()
                    assert response.status == 200
                    if retard == 'situation':
                        assert len(response.json()['ecritures']) == 2
                    retenues.append((route, response))
                    page.evaluate('window.__banqueRetenue=true')

                page.route(motif, retenir)
                if retard == 'situation':
                    with page.expect_response(lambda r: r.url.endswith('/api/exercices')) as contexte:
                        page.goto(application['web_url']+'/rapprochement', wait_until='domcontentloaded')
                    assert contexte.value.status == 200
                    playwright.expect(page.locator('select').filter(has=page.locator(f'option[value="{annee}"]')).first).to_be_enabled()
                    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                else:
                    page.goto(application['web_url']+'/rapprochement', wait_until='domcontentloaded')
                page.wait_for_function('window.__banqueRetenue===true')
                dates = page.locator('input[type=date]')
                dates.nth(0).fill(f'{annee}-03-01')
                with page.expect_response(lambda r: '/rapprochement/5141/situation?' in r.url
                        and f'date_debut={annee}-03-01' in r.url and f'date_fin={annee}-03-31' in r.url):
                    dates.nth(1).fill(f'{annee}-03-31')
                verifier_mars(page, playwright)
                page.unroute(motif, retenir)
                with page.expect_response(lambda r: r.url.endswith('/api/exercices') if retard == 'exercice'
                        else '/rapprochement/5141/situation?' in r.url and f'date_fin={annee}-12-31' in r.url) as liberee:
                    for route, response in retenues:
                        route.fulfill(response=response)
                liberee.value.finished()
                # Attendre que React traite cette vraie réponse avant les
                # assertions, sans durée arbitraire ni remplacement de JSON.
                page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                assert dates.nth(0).input_value() == f'{annee}-03-01'
                assert dates.nth(1).input_value() == f'{annee}-03-31'
                verifier_mars(page, playwright)
                assert not errors and not server, (errors, server)
            finally:
                browser.close()
        assert photographie(application) == avant
        assert api.get('/api/rapprochement/5141/situation', params={
            'date_debut': f'{annee}-03-01', 'date_fin': f'{annee}-03-31'}).status_code == 200
    finally:
        api.close()


def test_bornes_decalees_sans_saisie_et_changement_exercice(application):
    api, email, password, annee, sid = preparer(application)
    try:
        r = api.patch(f'/api/exercices/{annee}', json={'date_debut': f'{annee}-01-02', 'date_fin': f'{annee}-06-30'})
        assert r.status_code == 200, r.text
        r = api.post('/api/exercices', json={'annee': annee+1, 'date_debut': f'{annee+1}-04-01', 'date_fin': f'{annee+1}-09-30'})
        assert r.status_code == 201, r.text
        r = api.post('/api/rapprochement', json={'compte': '5141', 'date': f'{annee}-03-15', 'libelle': 'Relevé fictif conservation', 'montant': 200, 'sens': 'debit'})
        assert r.status_code == 201, r.text
        r = api.put('/api/rapprochement/5141/etat', json={'date_debut': f'{annee}-01-02', 'date_fin': f'{annee}-06-30', 'solde_initial': 0, 'solde_final': 800})
        assert r.status_code == 200, r.text
        avant = photographie(application)
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable: pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(20000)
                errors, server = observer(page, application['api_url'])
                mutations = []
                page.on('request', lambda r: mutations.append((r.method, r.url)) if '/api/rapprochement' in r.url and r.method != 'GET' else None)
                connexion(page, application['web_url'], email, password)
                retenues = []
                def retenir(route):
                    response = route.fetch()
                    assert response.status == 200
                    retenues.append((route, response))
                    page.evaluate('window.__bornesBanqueRetenues=true')
                page.route('**/api/exercices', retenir)
                page.goto(application['web_url']+'/rapprochement', wait_until='domcontentloaded')
                page.wait_for_function('window.__bornesBanqueRetenues===true')
                page.locator('tbody tr').filter(has_text='CAP-GL-DATES').wait_for()
                page.unroute('**/api/exercices', retenir)
                with page.expect_response(lambda r: r.url.endswith('/api/exercices')):
                    for route, response in retenues: route.fulfill(response=response)
                dates = page.locator('input[type=date]')
                playwright.expect(dates.nth(0)).to_have_value(f'{annee}-01-02')
                playwright.expect(dates.nth(1)).to_have_value(f'{annee}-06-30')
                page.get_by_text('Relevé fictif conservation', exact=True).wait_for()
                page.get_by_text('800,00 MAD', exact=True).first.wait_for()
                select = page.locator('select').filter(has=page.locator(f'option[value="{annee+1}"]')).first
                playwright.expect(select).to_be_enabled()
                select.select_option(str(annee+1))
                playwright.expect(dates.nth(0)).to_have_value(f'{annee+1}-04-01')
                playwright.expect(dates.nth(1)).to_have_value(f'{annee+1}-09-30')
                playwright.expect(page.locator('tbody tr').filter(has_text='CAP-GL-DATES')).to_have_count(0)
                assert mutations == []
                assert not errors and not server, (errors, server)
            finally:
                browser.close()
        assert photographie(application) == avant
    finally:
        api.close()


def test_changement_societe_dates_situation_et_banques_isolees(application):
    api, email, password, annee, sid = preparer(application)
    try:
        nom_a = api.get('/api/societe/moi').json()['raison_sociale']
        suffix = uuid.uuid4().hex[:8]
        banque_a, banque_b = 'Banque A fictive '+suffix, 'Banque B fictive '+suffix
        r = api.post('/api/banques', json={'banque': banque_a, 'compte_comptable': '5149', 'devise': 'MAD'})
        assert r.status_code == 201, r.text
        nom_b = 'Rapprochement autre fictif '+suffix
        r = api.post('/api/societes/nouvelle', json={'raison_sociale': nom_b})
        assert r.status_code == 201, r.text
        bid = r.json()['id']
        r = api.post(f'/api/societes/switcher/{bid}')
        assert r.status_code == 200, r.text
        with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer '+r.json()['access_token']}) as autre:
            r = autre.patch(f'/api/exercices/{annee}', json={'date_debut': f'{annee}-02-01', 'date_fin': f'{annee}-09-30'})
            assert r.status_code == 200, r.text
            r = autre.post('/api/banques', json={'banque': banque_b, 'compte_comptable': '5148', 'devise': 'MAD'})
            assert r.status_code == 201, r.text
            r = autre.post('/api/ecritures', json={'date': f'{annee}-03-15', 'journal': 'OD', 'reference': 'AUTRE-BANQUE', 'libelle': 'Charge fictive autre société', 'lignes': [{'compte': '6111', 'debit': 17}, {'compte': '5141', 'credit': 17}]})
            assert r.status_code == 201, r.text
            assert autre.post(f"/api/ecritures/{r.json()['id']}/valider").status_code == 200
        avant = photographie(application)
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable: pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(20000)
                errors, server = observer(page, application['api_url'])
                mutations = []
                page.on('request', lambda r: mutations.append((r.method, r.url)) if '/api/rapprochement' in r.url and r.method != 'GET' else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/rapprochement', wait_until='domcontentloaded')
                dates = page.locator('input[type=date]')
                page.locator('tbody tr').filter(has_text='CAP-GL-DATES').wait_for()
                dates.nth(0).fill(f'{annee}-03-01')
                dates.nth(1).fill(f'{annee}-03-31')
                verifier_mars(page, playwright)
                compte = page.locator('select').filter(has=page.locator('option[value="5141"]')).first
                playwright.expect(compte.locator('option[value="5149"]')).to_have_count(1)
                assert banque_a in compte.locator('option[value="5149"]').inner_text()
                page.get_by_role('button', name=nom_a, exact=True).click()
                with page.expect_response(lambda r: r.url.endswith(f'/api/societes/switcher/{bid}')):
                    page.get_by_text(nom_b, exact=True).click()
                page.get_by_role('button', name=nom_b, exact=True).wait_for()
                playwright.expect(dates.nth(0)).to_have_value(f'{annee}-02-01')
                playwright.expect(dates.nth(1)).to_have_value(f'{annee}-09-30')
                page.locator('tbody tr').filter(has_text='AUTRE-BANQUE').wait_for()
                playwright.expect(page.locator('tbody tr').filter(has_text='CAP-GL-DATES')).to_have_count(0)
                playwright.expect(page.locator('tbody tr').filter(has_text='MARS-GL-DATES')).to_have_count(0)
                page.get_by_text('-17,00 MAD', exact=True).wait_for()
                playwright.expect(compte.locator('option[value="5148"]')).to_have_count(1)
                playwright.expect(compte.locator('option[value="5149"]')).to_have_count(0)
                assert banque_b in compte.locator('option[value="5148"]').inner_text()
                compte.select_option('5148')
                playwright.expect(page.locator('tbody tr').filter(has_text='AUTRE-BANQUE')).to_have_count(0)
                compte.select_option('5141')
                page.locator('tbody tr').filter(has_text='AUTRE-BANQUE').wait_for()
                page.get_by_text('-17,00 MAD', exact=True).wait_for()
                assert mutations == []
                assert not errors and not server, (errors, server)
            finally:
                browser.close()
        assert photographie(application) == avant
    finally:
        api.close()
