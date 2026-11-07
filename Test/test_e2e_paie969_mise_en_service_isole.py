"""969 — un administrateur met la paie en service en un clic depuis n'importe quelle page Paie. PG nonce, données fictives."""
import pytest
from playwright.sync_api import sync_playwright, expect
from browser_support import chromium_executable
from test_paie974_validation_unique_isole import application, application131
from test_paie968_bulletins_isole import (
    application124, application123, application122, application121, application120, application119, application118, application117,
    application116, application115, application114, application113, application112, application111, application110, application109, application108,
    application107, application875, application873, application093, application092, application091, application090, application089, application087,
    migration, cles_coffre885)
from test_ras_lecture_conservation import client
from contextlib import contextmanager
import httpx


@contextmanager
def closing_client(application, email, password):
    c = httpx.Client(base_url=application['api_url'])
    try:
        jeton = c.post('/api/auth/login', data={'username': email, 'password': password})
        if jeton.status_code != 200:
            jeton = c.post('/api/auth/login', json={'email': email, 'password': password})
        c.headers['Authorization'] = 'Bearer ' + jeton.json()['access_token']
        yield c
    finally:
        c.close()
from test_e2e_administration_isole import connexion, observer

PAGES = ['elements', 'traitement', 'charges-sociales', 'fiscalite', 'bulletins', 'avances', 'paiements', 'comptabilisation', 'etats']


@pytest.mark.parametrize('largeur', [1440, 390])
def test_969_mise_en_service_en_un_clic_puis_toutes_les_pages_paie(application, largeur):
    api, email, password = client(application)  # société neuve : protection jamais activée
    try:
        assert api.get('/api/employes/securite/acces').json()['mode'] != 'protege'
    finally:
        api.close()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            erreurs, serveur = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/personnel-paie/bulletins')
            bloc = page.get_by_role('region', name='Mise en service de la paie')
            expect(bloc).to_contain_text('Protection des données du personnel activée — à faire')
            assert page.get_by_text('Activez le module et la protection Personnel', exact=False).count() == 0
            bloc.get_by_role('button', name='Tout activer maintenant', exact=True).click()
            expect(page.locator('[data-notification="succes"]')).to_contain_text('Paie mise en service')
            expect(page.get_by_role('button', name='Établir un bulletin', exact=True)).to_be_visible()
            with closing_client(application, email, password) as verif:
                assert verif.get('/api/employes/securite/acces').json()['validation_unique'] is True
            for cle in PAGES:
                page.goto(application['web_url'] + '/personnel-paie/' + cle)
                page.get_by_role('main').wait_for()
                expect(page.get_by_role('region', name='Mise en service de la paie')).to_have_count(0)
                expect(page.get_by_role('heading', name='Rubrique à venir', exact=True)).to_have_count(0)
                expect(page.get_by_text('Chargement', exact=False)).to_have_count(0)
                assert page.get_by_role('alert').count() == 0, (cle, page.get_by_role('alert').all_inner_texts())
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), cle
            assert not erreurs and not serveur, (erreurs, serveur)
        finally:
            browser.close()
