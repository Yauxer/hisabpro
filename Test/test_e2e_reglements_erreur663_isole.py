"""Vrai refus SELECT sur le seul cluster nonce : erreur visible et reprise Edge."""
from contextlib import closing, contextmanager
from datetime import date
import re
import pytest
from sqlalchemy import text
from playwright.sync_api import sync_playwright, expect
from test_e2e_runtime_session_isole import application, application090, application089, application087, migration
from test_ras_lecture_conservation import client
from test_reglements_par_tiers_isole import dossier, poster
from test_lecture_reglements_historiques import photo
from test_restauration_runtime_acl_089 import catalogue_acl
from test_e2e_administration_isole import connexion, observer
from test_e2e_ras_capture_isole import ouvrir
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee


@contextmanager
def suspendre_lecture_reglements(app):
    c = app['cluster']
    assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    assert app['role_sql'] == 'hisabpro'
    avant = catalogue_acl(app['engine'])
    with app['engine'].begin() as db:
        assert db.scalar(text("SELECT rolsuper FROM pg_roles WHERE rolname='hisabpro'")) is False
        assert db.scalar(text("SELECT has_table_privilege('hisabpro','reglements','SELECT')"))
        db.execute(text('REVOKE SELECT ON reglements FROM hisabpro'))
    try:
        with app['engine'].connect() as db:
            assert not db.scalar(text("SELECT has_table_privilege('hisabpro','reglements','SELECT')"))
        yield
    finally:
        assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        with app['engine'].begin() as db:
            db.execute(text('GRANT SELECT ON reglements TO hisabpro'))
        assert catalogue_acl(app['engine']) == avant


@pytest.mark.parametrize('largeur', [1440, 390])
def test_663_erreur_native_pas_de_fausse_liste_vide_et_reprise(application, largeur, tmp_path):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        _, _, payload = dossier(api)
        r = poster(api, payload)
        assert r.status_code == 201, r.text
        avant = photo(application)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(15000)
            erreurs, serveurs = observer(page, application['api_url'])
            echecs_reseau = []
            page.on('requestfailed', lambda r: echecs_reseau.append(r.url) if r.url.startswith(application['api_url']) else None)
            connexion(page, application['web_url'], email, password)
            page.wait_for_load_state('networkidle')
            with suspendre_lecture_reglements(application):
                assert api.get('/api/reglements', params={'exercice': date.today().year}).status_code == 500
                # Le vrai500 sans en-tête CORS peut être exposé par Edge en
                # requestfailed, sans événement response exploitable.
                with page.expect_request(lambda r: '/api/reglements?' in r.url):
                    ouvrir(page, application, 'vente')
                expect(page.get_by_role('alert').filter(has_text='Chargement des règlements impossible')).to_be_visible(timeout=4000)
                page.screenshot(path=str(tmp_path/f'lecture663_{largeur}.png'), full_page=True)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert page.get_by_text('Pour encaisser, ouvrez', exact=False).bounding_box()['width'] >= 200
                expect(page.get_by_text('Aucun règlement trouvé', exact=True)).to_have_count(0)
                expect(page.locator('main table')).to_have_count(0)
                with page.expect_request(lambda r: '/api/reglements?' in r.url):
                    page.get_by_role('button', name='Réessayer', exact=True).click()
                assert api.get('/api/reglements', params={'exercice': date.today().year}).status_code == 500
                expect(page.get_by_role('alert').filter(has_text='Chargement des règlements impossible')).to_be_visible()
                assert photo(application) == avant
            with page.expect_response(lambda r: '/api/reglements?' in r.url) as reprise:
                page.get_by_role('button', name='Réessayer', exact=True).click()
            assert reprise.value.status == 200 and len(reprise.value.json()) == 2
            expect(page.locator('tbody tr')).to_have_count(2)
            expect(page.get_by_text('240,00 MAD', exact=True)).to_be_visible()
            retenues = []
            def retenir(route):
                response = route.fetch()
                assert response.status == 200
                retenues.append((route, response))
            page.route(re.compile(r'/api/reglements\?'), retenir, times=1)
            page.get_by_role('button', name='Actualiser les règlements', exact=True).click()
            for _ in range(100):
                if retenues:
                    break
                page.wait_for_timeout(50)
            assert len(retenues) == 1
            expect(page.get_by_text('240,00 MAD', exact=True)).to_have_count(0)
            expect(page.locator('main table')).to_have_count(0)
            retenues[0][0].fulfill(response=retenues[0][1])
            expect(page.locator('tbody tr')).to_have_count(2)
            expect(page.get_by_text('240,00 MAD', exact=True)).to_be_visible()
            # Une panne après un premier succès ne doit pas laisser le total ancien affiché.
            with suspendre_lecture_reglements(application):
                with page.expect_request(lambda r: '/api/reglements?' in r.url):
                    page.get_by_role('button', name='Actualiser les règlements', exact=True).click()
                assert api.get('/api/reglements', params={'exercice': date.today().year}).status_code == 500
                expect(page.get_by_role('alert').filter(has_text='Chargement des règlements impossible')).to_be_visible()
                expect(page.get_by_text('240,00 MAD', exact=True)).to_have_count(0)
                expect(page.locator('main table')).to_have_count(0)
            page.get_by_role('button', name='Réessayer', exact=True).click()
            expect(page.locator('tbody tr')).to_have_count(2)
            assert photo(application) == avant
            assert not erreurs and (serveurs or echecs_reseau), (erreurs, serveurs, echecs_reseau)
            assert all('/api/reglements' in u or '/api/factures' in u for u, _ in serveurs), serveurs
            assert all('/api/reglements' in u or '/api/factures' in u for u in echecs_reseau), echecs_reseau
        finally:
            browser.close()


@pytest.mark.parametrize('largeur', [1440, 390])
def test_663_liste_reellement_vide_reste_distincte(application, largeur):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        avant = photo(application)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(15000)
            erreurs, serveurs = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            ouvrir(page, application, 'achat')
            expect(page.get_by_text('Aucun règlement trouvé', exact=True)).to_be_visible()
            expect(page.get_by_role('alert')).to_have_count(0)
            with page.expect_response(lambda r: '/api/reglements?' in r.url) as relecture:
                page.get_by_role('button', name='Actualiser les règlements', exact=True).click()
            assert relecture.value.status == 200 and relecture.value.json() == []
            expect(page.get_by_text('Aucun règlement trouvé', exact=True)).to_be_visible()
            assert photo(application) == avant and not erreurs and not serveurs
        finally:
            browser.close()
