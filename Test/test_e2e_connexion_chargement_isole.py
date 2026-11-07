"""La connexion réelle ne dépend pas de la fin d'un chargement décoratif."""
import pytest
from playwright.sync_api import sync_playwright, expect
from browser_support import chromium_executable
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import connexion
from test_ras_lecture_conservation import client


@pytest.mark.parametrize('largeur', [1365, 390])
def test_connexion_reelle_ressource_decorative_retenue(application, largeur):
    api, email, password = client(application)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            retenues = []
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(3000)
                logins = []
                # Seule une image témoin ajoutée par le banc est retenue.
                # API, authentification et navigation restent celles du produit.
                page.route('**/temoin-connexion.png', lambda route: retenues.append(route))
                page.add_init_script("""document.addEventListener('DOMContentLoaded', () => {
                  const temoin = document.createElement('img');
                  temoin.src = '/temoin-connexion.png'; temoin.style.display = 'none';
                  document.body.append(temoin);
                }, {once:true});""")
                page.on('response', lambda r: logins.append(r) if r.url.endswith('/api/auth/login') else None)
                connexion(page, application['web_url'], email, password)
                assert len(retenues) == 1
                assert len(logins) == 1 and logins[0].status == 200
                assert page.url.endswith('/dashboard')
                assert page.evaluate('document.readyState') == 'interactive'
                expect(page.get_by_role('main')).to_be_visible()
                token = page.evaluate("localStorage.getItem('hisabpro_token')")
                # Vérifier la session de navigateur par API réelle.
                assert token
                r = api.get('/api/societe/moi', headers={'Authorization': 'Bearer '+token})
                assert r.status_code == 200, r.text
            finally:
                for route in retenues:
                    route.abort()
                browser.close()
    finally:
        api.close()
