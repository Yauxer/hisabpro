"""La facture hors première page reste visible dans les règlements du bon sens."""
from datetime import date
import pytest
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_validation_facture_montants_historiques_postgres import creer
from test_lecture_reglements_historiques import photo
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('largeur', [1365, 390])
def test_paiement_facture_hors_premiere_page(application, sens, largeur):
    api, email, password = client(application)
    try:
        fid = creer(api, sens, False, 100)
        r = api.post(f'/api/factures/{fid}/valider', json={})
        assert r.status_code == 200, r.text
        numero = r.json()['numero']
        r = api.post('/api/reglements', json={'facture_id': fid,
            'date': date.today().isoformat(), 'tiers': 'Repris de facture',
            'montant': 20, 'mode': 'virement', 'comptabiliser': False})
        assert r.status_code == 201, r.text
        for _ in range(100):
            creer(api, sens, False, 1)
        premiere = api.get('/api/factures', params={'exercice': date.today().year})
        assert premiere.status_code == 200 and len(premiere.json()) == 100
        assert fid not in {f['id'] for f in premiere.json()}
        avant = photo(application)
        from playwright.sync_api import sync_playwright, expect
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                erreurs, serveurs = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/commercial')
                page.get_by_role('button', name='Vente' if sens == 'vente' else 'Achat', exact=True).click()
                page.get_by_role('button', name='Règlements', exact=True).click()
                expect(page.locator('tbody tr')).to_have_count(1, timeout=15000)
                expect(page.locator('tbody tr')).to_contain_text(numero)
                expect(page.locator('tbody tr')).to_contain_text('Partiel')
                page.get_by_role('button', name='Achat' if sens == 'vente' else 'Vente', exact=True).click()
                page.get_by_role('button', name='Règlements', exact=True).click()
                expect(page.locator('tbody tr')).to_have_count(0)
                assert not erreurs and not serveurs, (erreurs, serveurs)
            finally:
                browser.close()
        assert photo(application) == avant
    finally:
        api.close()
