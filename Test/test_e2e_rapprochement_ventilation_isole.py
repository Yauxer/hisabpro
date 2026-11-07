"""Pointage natif de deux paiements par une ligne bancaire, Edge/API/PGnonce."""
import pytest
from contextlib import closing
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import connexion,observer
from test_ras_lecture_conservation import client
from test_rapprochement_ventilation_isole import migration,preparer,situation
from test_lecture_reglements_historiques import photo

@pytest.mark.parametrize('sens',['vente','achat'])
@pytest.mark.parametrize('largeur',[1365,390])
def test_pointage_collectif_reload_et_depointage_edge(application,migration,sens,largeur):
    api,email,password=client(application)
    try:
        payload,_,rid,lids=preparer(application,api,sens)
        avant=photo(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000})
                page.set_default_timeout(20000)
                erreurs,serveurs=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/rapprochement')
                row=page.locator('tbody tr').filter(has_text=payload['reference']).filter(has=page.locator('select'))
                select=row.locator('select')
                value='VT:'+payload['operation_id']
                expect(select.locator(f'option[value="{value}"]')).to_have_count(1)
                with page.expect_response(lambda r:r.url.endswith(f'/api/rapprochement/{rid}/rapprocher-ventilation') and r.request.method=='POST') as pointage:
                    select.select_option(value)
                assert pointage.value.status==200,pointage.value.text()
                expect(select).to_have_value(value)
                expect(page.get_by_text('Rapprochée',exact=True)).to_have_count(2)
                assert len(situation(api)['lignes_releve'])==1
                assert photo(application)==avant
                page.reload()
                expect(select).to_have_value(value)
                expect(page.get_by_text('Rapprochée',exact=True)).to_have_count(2)
                with page.expect_response(lambda r:r.url.endswith(f'/api/rapprochement/{rid}/derapprocher') and r.request.method=='POST') as depointage:
                    select.select_option('')
                assert depointage.value.status==200,depointage.value.text()
                expect(select).to_have_value('')
                expect(page.get_by_text('Rapprochée',exact=True)).to_have_count(0)
                assert not any(l['rapprochee'] for l in situation(api)['ecritures'])
                assert photo(application)==avant
                assert not erreurs and not serveurs,(erreurs,serveurs)
            finally:browser.close()
    finally:api.close()
