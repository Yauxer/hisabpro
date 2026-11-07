"""Ventilation réelle dans Edge, validation des écritures puis lettrage."""
from datetime import date
from pathlib import Path
import pytest
from test_e2e_facturation_isole import application, champ
from test_reglements_par_tiers_isole import dossier
from test_ras_lecture_conservation import client
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('largeur', [1365, 390])
def test_ventilation_puis_complement_et_lettrage(application, sens, largeur):
    api, email, password = client(application)
    try:
        tid, ids, payload = dossier(api, sens)
        factures = api.get('/api/factures', params={'exercice': date.today().year}).json()
        numeros = {f['id']: f['numero'] for f in factures}
        nom = next(f['tiers'] for f in factures if f['id'] == ids[0])
        from playwright.sync_api import sync_playwright, expect
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                if largeur == 390:
                    page.add_init_script("Object.defineProperty(crypto, 'randomUUID', { value: undefined })")
                page.set_default_timeout(15000)
                page.on('dialog', lambda d: d.accept())
                erreurs, serveurs = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/commercial')
                page.get_by_role('button', name='Vente' if sens == 'vente' else 'Achat', exact=True).click()
                page.get_by_role('button', name='Règlements', exact=True).click()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Débordement de la page règlements'
                for tour in (1, 2):
                    page.get_by_role('button', name='Ventiler par tiers', exact=True).click()
                    modal = page.get_by_role('dialog', name='Règlement par tiers', exact=True)
                    modal.locator('select').first.select_option(str(tid))
                    montant = modal.get_by_label('Montant du paiement (MAD)', exact=True)
                    montant.fill('240' if tour == 1 else '120')
                    modal.get_by_label('Référence du paiement', exact=True).fill(payload['reference']+f'-{tour}')
                    bouton = modal.get_by_role('button', name='Enregistrer la ventilation', exact=True)
                    expect(bouton).to_be_disabled()
                    if tour == 1:
                        modal.get_by_label('Montant pour '+numeros[ids[0]], exact=True).fill('120')
                        expect(bouton).to_be_disabled()  # 120 manquent encore.
                    modal.get_by_label('Montant pour '+numeros[ids[1]], exact=True).fill('120')
                    expect(bouton).to_be_enabled()
                    # Le formulaire reste dans le viewport, y compris390px.
                    assert modal.evaluate('(e) => e.getBoundingClientRect().right <= innerWidth && e.getBoundingClientRect().left >= 0')
                    if tour == 1:
                        path = Path(__file__).resolve().parents[1]/'.codex-tests'/f'reglements372_{sens}_{largeur}.png'
                        page.screenshot(path=str(path), full_page=True)
                    with page.expect_response(lambda r: r.url.endswith('/api/reglements/par-tiers') and r.request.method == 'POST') as paiement:
                        bouton.click()
                    assert paiement.value.status == 201, paiement.value.text()
                    assert len(paiement.value.json()) == (2 if tour == 1 else 1)
                    modal.wait_for(state='hidden')
                    expect(page.locator('tbody tr')).to_have_count(2 if tour == 1 else 3)
                    if tour == 1:
                        expect(page.locator('tbody tr').filter(has_text=numeros[ids[0]])).to_contain_text('Soldée')
                        expect(page.locator('tbody tr').filter(has_text=numeros[ids[1]])).to_contain_text('Partiel')
                    else:
                        for row in page.locator('tbody tr').all(): expect(row).to_contain_text('Soldée')
                    page.reload()
                    page.get_by_role('button', name='Vente' if sens == 'vente' else 'Achat', exact=True).click()
                    page.get_by_role('button', name='Règlements', exact=True).click()
                    expect(page.locator('tbody tr')).to_have_count(2 if tour == 1 else 3)
                page.goto(application['web_url']+'/journal')
                expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(5)
                page.get_by_role('button', name='Valider les brouillons', exact=True).wait_for()
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as validation:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert validation.value.status == 200 and validation.value.json()['nb_validees'] == 5
                page.goto(application['web_url']+'/lettrage')
                champ(page, 'Compte', 'select').select_option('3421' if sens == 'vente' else '4411')
                champ(page, 'Tiers', 'select').select_option(label=nom)
                expect(page.locator('tbody input[type="checkbox"]')).to_have_count(5)
                for box in page.locator('tbody input[type="checkbox"]').all(): box.check()
                with page.expect_response(lambda r: '/api/lettrage' in r.url and r.request.method == 'POST') as lettrage:
                    page.get_by_role('button', name='Lettrer 5 lignes', exact=True).click()
                assert lettrage.value.status == 200, lettrage.value.text()
                page.get_by_text('5 lettrée(s)', exact=True).wait_for()
                assert not erreurs and not serveurs, (erreurs, serveurs)
            finally:
                browser.close()
    finally:
        api.close()
