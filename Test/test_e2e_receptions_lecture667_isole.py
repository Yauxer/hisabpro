"""Réceptions : vraies lectures refusées/tardives, aucune donnée ou réponse fabriquée."""
from contextlib import closing, contextmanager
from datetime import date
import re
import pytest
from sqlalchemy import text
from playwright.sync_api import sync_playwright, expect
from test_e2e_runtime_session_isole import application, application090, application089, application087, migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_restauration_runtime_acl_089 import catalogue_acl
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee


def reception(api, annee, numero):
    tiers = ok(api.post('/api/tiers', json={'nom': 'FOURNISSEUR FICTIF '+numero, 'type': 'fournisseur'}), 201)
    return ok(api.post('/api/bons-reception', json={'type': 'achat', 'date': f'{annee}-06-01',
        'tiers_id': tiers['id'], 'tiers': tiers['nom'], 'numero': numero,
        'lignes': [{'description': 'Service fictif667', 'quantite_prevue': 1,
            'quantite_livree': 0, 'prix_unitaire': 100, 'tva': 20}]}), 201)


def ouvrir(page, app):
    page.goto(app['web_url']+'/commercial')
    page.get_by_role('button', name='Achat', exact=True).click()
    page.get_by_role('button', name='Bons de réception', exact=True).click()


@contextmanager
def suspendre_lecture(app):
    c = app['cluster']
    assert verifier_cible_isolee(c['url'], c['directory'], c['nonce']) and app['role_sql'] == 'hisabpro'
    avant = catalogue_acl(app['engine'])
    with app['engine'].begin() as db:
        assert db.scalar(text("SELECT rolsuper FROM pg_roles WHERE rolname='hisabpro'")) is False
        db.execute(text('REVOKE SELECT ON bons_livraison FROM hisabpro'))
    try:
        with app['engine'].connect() as db:
            assert not db.scalar(text("SELECT has_table_privilege('hisabpro','bons_livraison','SELECT')"))
        yield
    finally:
        assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        with app['engine'].begin() as db:
            db.execute(text('GRANT SELECT ON bons_livraison TO hisabpro'))
        assert catalogue_acl(app['engine']) == avant


@pytest.mark.parametrize('largeur', [1440, 390])
def test_667_refus_natif_reprise_et_vide_distinct(application, largeur, tmp_path):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        reception(api, date.today().year, 'BR-FICTIF667-LECTURE')
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000});page.set_default_timeout(15000)
            erreurs, _ = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            page.wait_for_load_state('networkidle')
            avant = donnees_metier(application)
            with suspendre_lecture(application):
                assert api.get('/api/bons-reception', params={'exercice': date.today().year}).status_code == 500
                with page.expect_request(lambda r: '/api/bons-reception?' in r.url):ouvrir(page, application)
                expect(page.get_by_role('alert').filter(has_text='Chargement des réceptions impossible')).to_be_visible(timeout=4000)
                expect(page.get_by_text('Aucun bon de réception', exact=True)).to_have_count(0)
                expect(page.get_by_text('0 bons de réception', exact=True)).to_have_count(0)
                with page.expect_request(lambda r: '/api/bons-reception?' in r.url):
                    page.get_by_role('button', name='Réessayer', exact=True).click()
                expect(page.get_by_role('alert').filter(has_text='Chargement des réceptions impossible')).to_be_visible()
                page.screenshot(path=str(tmp_path/f'receptions667_{largeur}.png'), full_page=True)
            with page.expect_response(lambda r: '/api/bons-reception?' in r.url) as reprise:
                page.get_by_role('button', name='Réessayer', exact=True).click()
            assert reprise.value.status == 200 and len(reprise.value.json()) == 1
            expect(page.locator('tbody tr')).to_have_count(1)
            expect(page.get_by_text('BR-FICTIF667-LECTURE', exact=True)).to_be_visible()
            assert donnees_metier(application) == avant and not erreurs
        finally:browser.close()


@pytest.mark.parametrize('largeur', [1440, 390])
def test_667_vrai_vide_et_actualisation(application, largeur):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000});page.set_default_timeout(15000)
            erreurs, serveur = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            ouvrir(page, application)
            expect(page.get_by_text('Aucun bon de réception', exact=True)).to_be_visible()
            avant = donnees_metier(application)
            with page.expect_response(lambda r: '/api/bons-reception?' in r.url) as relecture:
                page.get_by_role('button', name='Actualiser les réceptions', exact=True).click()
            assert relecture.value.status == 200 and relecture.value.json() == []
            expect(page.get_by_text('Aucun bon de réception', exact=True)).to_be_visible()
            expect(page.get_by_role('alert')).to_have_count(0)
            assert donnees_metier(application) == avant and not erreurs and not serveur
        finally:browser.close()


@pytest.mark.parametrize('cas', ['exercice', 'jeton'])
@pytest.mark.parametrize('largeur', [1440, 390])
def test_667_reponse_tardive_ecartee(application, cas, largeur):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        annee = date.today().year
        ok(api.post('/api/exercices', json={'annee': annee-1, 'date_debut': f'{annee-1}-01-01', 'date_fin': f'{annee-1}-12-31'}), 201)
        reception(api, annee, 'BR-FICTIF667-ANCIEN-GET')
        reception(api, annee-1, 'BR-FICTIF667-EXERCICE-CIBLE')
        attendu = 'BR-FICTIF667-EXERCICE-CIBLE'
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000});page.set_default_timeout(15000)
            erreurs, serveur = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            avant = donnees_metier(application)
            retenues = []
            def retenir(route):
                response = route.fetch();assert response.status == 200
                retenues.append((route,response))
            page.route(re.compile(r'/api/bons-reception\?exercice='+str(annee)), retenir, times=1)
            ouvrir(page, application)
            for _ in range(100):
                if retenues:break
                page.wait_for_timeout(50)
            assert len(retenues) == 1
            if cas == 'jeton':
                # Un vrai renouvellement du même compte conserve le contexte
                # société/plan. Injecter un JWT d'une autre société sans son
                # contexte est volontairement refusé par Layout.
                actuel = page.evaluate('localStorage.getItem("hisabpro_token")')
                nouveau = ok(api.post('/api/auth/login', json={'email': email, 'password': password}))['access_token']
                if nouveau == actuel:
                    page.wait_for_timeout(1100)
                    nouveau = ok(api.post('/api/auth/login', json={'email': email, 'password': password}))['access_token']
                assert nouveau != actuel
                avant = donnees_metier(application)
                page.evaluate('t=>localStorage.setItem("hisabpro_token",t)', nouveau)
            with page.expect_response(lambda r: f'/api/bons-reception?exercice={annee-1}' in r.url):
                page.locator('select').filter(has=page.locator(f'option[value="{annee-1}"]')).first.select_option(str(annee-1))
            expect(page.get_by_text(attendu, exact=True)).to_be_visible()
            retenues[0][0].fulfill(response=retenues[0][1]);page.wait_for_load_state('networkidle')
            expect(page.get_by_text('BR-FICTIF667-ANCIEN-GET', exact=True)).to_have_count(0)
            expect(page.get_by_text(attendu, exact=True)).to_be_visible()
            assert donnees_metier(application) == avant and not erreurs and not serveur
        finally:
            browser.close()
