"""Erreur422 lisible, aucune mutation avec des frais au demi-centime : Edge réel."""
import pytest
from datetime import date
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_e2e_facturation_isole import application,champ
from test_e2e_administration_isole import connexion,observer
from test_ras_lecture_conservation import client
from test_effets_frais_precision_isole import preparer
from test_lecture_reglements_historiques import photo

@pytest.mark.parametrize('largeur',[1365,390])
def test_frais_demi_centime_erreur_precise_et_statut_conserve(application,largeur):
    api,email,password=client(application)
    try:
        reg=preparer(api);avant=photo(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
                errors,server=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/effets');champ(page,'Statut','select').select_option('tous')
                row=page.locator('tbody tr').filter(has_text=reg['reference'])
                row.get_by_title("Confirmer l'encaissement",exact=True).click()
                modal=page.get_by_role('dialog');expect(modal).to_contain_text('montant brut')
                modal.get_by_placeholder('0.00',exact=True).fill('10.005')
                with page.expect_response(lambda r:r.url.endswith(f"/api/reglements/{reg['id']}/transition")) as response:
                    modal.get_by_role('button',name="Confirmer l'encaissement",exact=True).click()
                assert response.value.status==422,response.value.text()
                expect(modal.get_by_role('alert')).to_contain_text('centime')
                assert photo(application)==avant
                response=api.get('/api/reglements',params={'exercice':date.today().year})
                assert response.status_code==200,response.text
                assert response.json()[0]['statut']=='portefeuille'
                assert not errors and not server,(errors,server)
            finally:browser.close()
    finally:api.close()
