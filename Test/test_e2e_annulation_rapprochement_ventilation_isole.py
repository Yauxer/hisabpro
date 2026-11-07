"""Annulation après pointage : contrepassations et relevé conservés, Edge/PGnonce."""
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import connexion,observer
from test_ras_lecture_conservation import client
from test_rapprochement_ventilation_isole import migration,preparer,rapprocher,situation
from test_annulation_ventilation_isole import annuler
from test_lecture_reglements_historiques import photo

@pytest.mark.parametrize('sens,largeur',[('vente',1365),('achat',390)])
def test_annulation_lot_pointe_releve_preserve_et_depointage_explicite(application,migration,sens,largeur):
    api,email,password=client(application)
    try:
        payload,rows,rid,lids=preparer(application,api,sens)
        assert rapprocher(api,rid,payload).status_code==200
        originaux=photo(application)
        r=annuler(api,payload)
        assert r.status_code==200,r.text
        assert {x['statut'] for x in r.json()}=={'annule'}
        apres=photo(application)
        # La photo contient les nouvelles contrepassations mais les origines restent identiques.
        assert len(apres['ecritures'])==len(originaux['ecritures'])+2
        for table in ('ecritures','lignes_ecriture'):
            for row in originaux[table]:
                assert row in apres[table]
        d=situation(api)
        releve=next(x for x in d['lignes_releve'] if x['id']==rid)
        assert releve['rapprochee'] and releve['ecriture_ligne_ids']==lids
        assert releve['montant']==240 and len(d['lignes_releve'])==1
        assert not d['ventilations']
        assert rapprocher(api,rid,payload).status_code==409
        assert annuler(api,payload).status_code==200
        assert photo(application)==apres
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000})
                page.set_default_timeout(20000)
                errors,server=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/rapprochement')
                select=page.locator('tbody tr').filter(has_text=payload['reference']).filter(has=page.locator('select')).locator('select')
                expect(select).to_have_value('VT:'+payload['operation_id'])
                expect(select.locator('option').filter(has_text='Ventilation rapprochée')).to_have_count(1)
                with page.expect_response(lambda r:r.url.endswith(f'/api/rapprochement/{rid}/derapprocher') and r.request.method=='POST') as response:
                    select.select_option('')
                assert response.value.status==200,response.value.text()
                expect(select).to_have_value('')
                page.reload()
                expect(select).to_have_value('')
                expect(select.locator('option[value^="VT:"]')).to_have_count(0)
                assert not errors and not server,(errors,server)
            finally:
                browser.close()
        final=situation(api)
        assert len(final['lignes_releve'])==1 and final['lignes_releve'][0]['montant']==240
        assert not final['lignes_releve'][0]['rapprochee']
        assert not any(x['rapprochee'] for x in final['ecritures'])
        assert photo(application)==apres
    finally:
        api.close()
