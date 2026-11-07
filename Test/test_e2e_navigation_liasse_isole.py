"""Navigation réelle vers états regroupés sans retirer l'éditeur ETIC."""
import pytest
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application
from test_e2e_recouvrement_isole import dossier_synthetique


def test_menu_liasse_et_acces_etats_et_editor_etic(application):
    dossier = dossier_synthetique(application)
    playwright = pytest.importorskip('playwright.sync_api')
    executable = chromium_executable()
    if not executable:
        pytest.skip('Edge/Chromium requis')
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page()
            page.set_default_timeout(20000)
            errors, server_errors = observer(page, application['api_url'])
            connexion(page, application['web_url'], dossier['email'], dossier['password'])
            page.goto(application['web_url'] + '/liasse-fiscale', wait_until='domcontentloaded')
            for href in ['/bilan', '/cpc', '/etic']:
                playwright.expect(page.locator(f'aside a[href="{href}"]')).to_have_count(0)
            playwright.expect(page.locator('aside a[href="/liasse-fiscale"]')).to_have_count(1)
            page.get_by_role('button', name='T1 · Bilan', exact=True).click()
            page.get_by_role('heading', name='T1 · Bilan — Actif', exact=True).wait_for()
            page.get_by_role('button', name='T2 · CPC', exact=True).click()
            page.get_by_role('heading', name='T2 · Compte de Produits et Charges', exact=True).wait_for()
            page.get_by_role('button', name='T3–T25 · ETIC', exact=True).click()
            page.get_by_role('button', name="Ouvrir l'ETIC", exact=True).click()
            playwright.expect(page).to_have_url(application['web_url'] + '/etic')
            page.get_by_role('heading').filter(has_text='ETIC').first.wait_for()
            assert not errors, errors
            assert not server_errors, server_errors
        finally:
            browser.close()
