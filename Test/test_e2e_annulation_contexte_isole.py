"""Preview native retardée : aucun POST après changement de contexte."""
import re
from datetime import date
import pytest
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_reglements_par_tiers_isole import dossier, poster
from test_lecture_reglements_historiques import photo
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


@pytest.mark.parametrize('cas', ['exercice', 'jeton'])
@pytest.mark.parametrize('largeur', [1365, 390])
def test_preview_tardive_ne_confirme_ni_annule_dans_nouveau_contexte(application, cas, largeur):
    from playwright.sync_api import sync_playwright, expect
    api, email, password = client(application)
    autre = None
    try:
        _, _, payload = dossier(api)
        assert poster(api, payload).status_code == 201
        if cas == 'exercice':
            annee = date.today().year-1
            r = api.post('/api/exercices', json={'annee': annee, 'date_debut': f'{annee}-01-01', 'date_fin': f'{annee}-12-31'})
            assert r.status_code == 201, r.text
        else:
            autre = client(application)[0]
            _, _, p2 = dossier(autre)
            # Même UUID autorisé dans deux sociétés : le POST ne doit jamais
            # être réémis sous le nouveau jeton après une ancienne preview.
            p2['operation_id'] = payload['operation_id']
            assert poster(autre, p2).status_code == 201
        avant = photo(application)
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                erreurs, serveurs = observer(page, application['api_url'])
                dialogs, posts, tenue = [], [], []
                def dialogue(d): dialogs.append(d.message); d.accept()
                page.on('dialog', dialogue)
                page.on('request', lambda q: posts.append(q.url) if q.method == 'POST' and '/par-tiers/' in q.url and q.url.endswith('/annuler') else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/commercial')
                page.get_by_role('button', name='Vente', exact=True).click()
                page.get_by_role('button', name='Règlements', exact=True).click()
                expect(page.locator('tbody tr')).to_have_count(2)
                def retenir(route):
                    response = route.fetch()
                    assert response.status == 200, response.text()
                    tenue.append((route, response))
                page.route(re.compile(r'/api/reglements/par-tiers/[a-f0-9]{32}$'), retenir)
                page.get_by_title('Annuler toute la ventilation', exact=True).click()
                for _ in range(30):
                    if tenue: break
                    page.wait_for_timeout(100)
                assert len(tenue) == 1
                if cas == 'exercice':
                    page.locator('select').filter(has=page.locator(f'option[value="{annee}"]')).first.select_option(str(annee))
                else:
                    page.evaluate('(t) => localStorage.setItem("hisabpro_token", t)', autre.headers['Authorization'].removeprefix('Bearer '))
                tenue[0][0].fulfill(response=tenue[0][1])
                page.wait_for_timeout(500)
                assert not dialogs, 'Une preview devenue obsolète ne doit pas demander confirmation'
                expect(page.get_by_role('dialog', name='Annuler toute la ventilation', exact=True)).to_have_count(0)
                assert not posts, 'Aucune annulation ne doit partir avec le nouveau contexte'
                assert photo(application) == avant
                assert not erreurs and not serveurs, (erreurs, serveurs)
            finally:
                browser.close()
    finally:
        api.close()
        if autre: autre.close()
