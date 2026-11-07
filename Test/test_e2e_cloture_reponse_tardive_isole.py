"""Réponses réelles retardées : aucune donnée2026 ne remplace l'exercice2025."""
from pathlib import Path
import pytest
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_lecture_reglements_historiques import photo
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


@pytest.mark.parametrize('largeur', [1365, 390])
def test_cloture_reponse_ancienne_ignoree(application, largeur):
    api, email, password = client(application)
    try:
        r = api.post('/api/exercices', json={'annee': 2025, 'date_debut': '2025-01-01', 'date_fin': '2025-12-31'})
        assert r.status_code == 201, r.text
        r = api.post('/api/ecritures', json={'date': '2025-12-31', 'journal': 'OD',
            'reference': 'CAPITAL-FICT-LATENCE', 'libelle': 'Capital fictif attente2025',
            'lignes': [{'compte': '5141', 'debit': 100}, {'compte': '1111', 'credit': 100}]})
        assert r.status_code == 201, r.text
        avant = photo(application)
        from playwright.sync_api import sync_playwright, expect
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                erreurs, serveurs = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                retards = []
                def retarder(route):
                    response = route.fetch()  # Vraie API, aucune valeur métier simulée.
                    assert response.status == 200, response.text()
                    url = route.request.url
                    if 'exercice=2026' in url or '/2026/periodes' in url:
                        retards.append((route, response))
                        page.evaluate('n => window.__retardsCloture = n', len(retards))
                    else:
                        route.fulfill(response=response)
                page.route('**/api/cloture/**', retarder)
                page.route('**/api/exercices/*/periodes', retarder)
                page.goto(application['web_url']+'/cloture', wait_until='domcontentloaded')
                page.wait_for_function('window.__retardsCloture === 3')
                page.get_by_label('Exercice actif', exact=True).select_option('2025')
                expect(page.get_by_text('1 écriture(s) encore en brouillon', exact=True)).to_be_visible()
                for route, response in retards: route.fulfill(response=response)
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                expect(page.get_by_text('1 écriture(s) encore en brouillon', exact=True)).to_be_visible()
                expect(page.get_by_text('Janvier 2025', exact=True)).to_be_visible()
                expect(page.get_by_text('Janvier 2026', exact=True)).to_have_count(0)
                expect(page.get_by_role('button', name="Clôturer l'exercice 2025", exact=True)).to_be_disabled()
                page.screenshot(path=str(Path(__file__).resolve().parents[1]/'.codex-tests'/f'cloture377_{largeur}.png'), full_page=True)
                assert not erreurs and not serveurs, (erreurs, serveurs)
            finally:
                browser.close()
        assert photo(application) == avant
    finally:
        api.close()
