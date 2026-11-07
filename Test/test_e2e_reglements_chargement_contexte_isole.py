"""Un GET retardé ne remplace pas les règlements du nouvel exercice."""
from datetime import date
import re
import pytest
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_reglements_par_tiers_isole import dossier, poster
from test_lecture_reglements_historiques import photo
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


@pytest.mark.parametrize('largeur', [1365, 390])
def test_ancien_get_ne_repeint_pas_nouvel_exercice(application, largeur):
    from playwright.sync_api import sync_playwright, expect
    api, email, password = client(application)
    try:
        _, _, p1 = dossier(api)
        assert poster(api, p1).status_code == 201
        old, courant = date.today().year, date.today().year-1
        r = api.post('/api/exercices', json={'annee': courant, 'date_debut': f'{courant}-01-01', 'date_fin': f'{courant}-12-31'})
        assert r.status_code == 201, r.text
        avant = photo(application)
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                erreurs, serveurs = observer(page, application['api_url'])
                tenue = []
                def retenir(route):
                    response = route.fetch()
                    assert response.status == 200 and len(response.json()) == 2
                    tenue.append((route, response))
                connexion(page, application['web_url'], email, password)
                page.route(re.compile(r'/api/reglements\?exercice='+str(old)+r'$'), retenir)
                page.goto(application['web_url']+'/commercial')
                page.get_by_role('button', name='Vente', exact=True).click()
                page.get_by_role('button', name='Règlements', exact=True).click()
                for _ in range(30):
                    if tenue: break
                    page.wait_for_timeout(100)
                assert len(tenue) == 1
                page.locator('select').filter(has=page.locator(f'option[value="{courant}"]')).first.select_option(str(courant))
                expect(page.get_by_text('Aucun règlement trouvé', exact=True)).to_be_visible()
                tenue[0][0].fulfill(response=tenue[0][1])
                page.wait_for_timeout(500)
                expect(page.get_by_text('Aucun règlement trouvé', exact=True)).to_be_visible()
                expect(page.locator('tbody tr')).to_have_count(0)
                assert photo(application) == avant
                assert not erreurs and not serveurs, (erreurs, serveurs)
            finally:
                browser.close()
    finally:
        api.close()
