"""Latence contrôlée ; les corps HTTP proviennent tous de la vraie API/PG."""
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_balances_exports_isole import preparer
from test_e2e_facturation_isole import application, champ


def test_reponse_client_tardive_ne_remplace_pas_fournisseur_courant(application):
    api, email, password, annee, sid, noms = preparer(application)
    try:
        with Session(application['engine']) as db:
            avant = {(l.id, l.compte, l.debit, l.credit, l.code_lettrage) for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid)}
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(15000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                client_retarde = []
                requetes = []
                def latence(route):
                    # Pas de JSON synthétique ni de remplacement des montants.
                    # route.fetch effectue réellement la requête autorisée.
                    response = route.fetch()
                    assert response.status == 200, response.text()
                    requetes.append((route.request.url, response.json()))
                    if 'compte=3421' in route.request.url and not client_retarde:
                        client_retarde.append((route, response))
                        page.evaluate('window.__clientReelRetenu = true')
                    else:
                        route.fulfill(response=response)
                page.route('**/api/lettrage/comptable?*', latence)
                page.goto(application['web_url'] + '/lettrage', wait_until='domcontentloaded')
                page.wait_for_function('window.__clientReelRetenu === true')
                champ(page, 'Compte', 'select').select_option('4411')
                page.locator('tbody').get_by_text(noms['achat'], exact=True).first.wait_for()
                assert client_retarde and len(requetes) == 2, requetes
                assert all(r['compte'] == '3421' for r in requetes[0][1])
                assert all(r['compte'] == '4411' for r in requetes[1][1])
                with page.expect_response(lambda r: '/api/lettrage/comptable?' in r.url and 'compte=3421' in r.url) as ancienne:
                    route, response = client_retarde[0]
                    route.fulfill(response=response)
                assert ancienne.value.status == 200
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                assert champ(page, 'Compte', 'select').input_value() == '4411'
                texte = page.locator('tbody').inner_text()
                assert noms['achat'] in texte and noms['vente'] not in texte, texte
                assert not errors and not server_errors
            finally:
                browser.close()
        with Session(application['engine']) as db:
            apres = {(l.id, l.compte, l.debit, l.credit, l.code_lettrage) for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid)}
            assert avant == apres
    finally:
        api.close()
