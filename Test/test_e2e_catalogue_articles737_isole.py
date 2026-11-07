"""Catalogue commercial : vraies réponses HTTP et refus SQL exclusivement nonce."""
from contextlib import closing, contextmanager
from pathlib import Path
from uuid import uuid4
import json
import pytest
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import text

from test_e2e_runtime_session_isole import application, application090, application089, application087, migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from test_permissions_tva_runtime_isole import donnees_metier
from test_restauration_runtime_acl_089 import catalogue_acl
from postgres_isole import verifier_cible_isolee
from browser_support import chromium_executable

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = '/api/articles'
PROFILS = {
    'vente': ('Vente', 'Nouveau devis', 'Nouveau devis', 'Créer le devis', '/api/devis'),
    'achat': ('Achat', 'Nouveau BC', 'Nouveau bon de commande', 'Créer la commande', '/api/bons-commande'),
}


def article(api, designation):
    return ok(api.post(CATALOGUE, json={'code': uuid4().hex[:12], 'designation': designation,
        'is_stockable': False, 'prix_vente_ht': 100, 'prix_achat_ht': 80, 'tva': 20}), 201)


def ouvrir(page, app, sens='vente'):
    cycle, action, titre, _save, _endpoint = PROFILS[sens]
    page.goto(app['web_url'] + '/commercial')
    page.get_by_role('button', name=cycle, exact=True).click()
    page.get_by_role('button', name=action, exact=True).click()
    modal = page.get_by_role('dialog', name=titre, exact=True)
    champ = modal.get_by_placeholder('Article ou description...', exact=True)
    champ.click()
    return modal, champ


@contextmanager
def refuser_catalogue(app):
    c = app['cluster']
    assert verifier_cible_isolee(c['url'], c['directory'], c['nonce']) and app['role_sql'] == 'hisabpro'
    avant = catalogue_acl(app['engine'])
    with app['engine'].begin() as db:
        assert db.scalar(text("SELECT rolsuper FROM pg_roles WHERE rolname='hisabpro'")) is False
        db.execute(text('REVOKE SELECT ON articles FROM hisabpro'))
    try:
        yield
    finally:
        assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        with app['engine'].begin() as db: db.execute(text('GRANT SELECT ON articles TO hisabpro'))
        assert catalogue_acl(app['engine']) == avant


@pytest.mark.parametrize('sens,largeur', [('vente', 1440), ('vente', 390), ('achat', 1440), ('achat', 390)])
def test_737_recherche_sans_resultat_puis_selection_prix(application, sens, largeur):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        a = article(api, 'Alpha fictif737'); b = article(api, 'Beta fictif737')
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            connexion(page, application['web_url'], email, password)
            with page.expect_response(lambda r: r.url.endswith(CATALOGUE) and r.request.method == 'GET') as rep:
                modal, champ = ouvrir(page, application, sens)
            assert rep.value.status == 200
            avant = donnees_metier(application)
            champ.fill('INEXISTANT737')
            expect(modal.get_by_text('Aucun article ne correspond à la recherche.', exact=False)).to_be_visible()
            expect(modal.locator('li').filter(has_text=a['designation'])).to_have_count(0)
            expect(modal.locator('li').filter(has_text=b['designation'])).to_have_count(0)
            champ.fill('bEtA')
            expect(modal.locator('li').filter(has_text=b['designation'])).to_be_visible()
            expect(modal.locator('li').filter(has_text=a['designation'])).to_have_count(0)
            modal.locator('li').filter(has_text=b['designation']).click()
            expect(champ).to_have_value(b['designation'])
            prix = modal.locator('.hp-commercial-line-editor input[type="number"]').nth(1)
            expect(prix).to_have_value('80' if sens == 'achat' else '100')
            assert donnees_metier(application) == avant
        finally: browser.close()


@pytest.mark.parametrize('sens,largeur', [('vente', 1440), ('achat', 390)])
def test_737_refus_natif_reessai_et_saisie_libre(application, sens, largeur):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        a = article(api, 'Article reprise fictif737')
        tiers = ok(api.post('/api/tiers', json={'nom': 'Tiers libre fictif737',
                    'type': 'client' if sens == 'vente' else 'fournisseur'}), 201)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            errors, _serveur = observer(page, application['api_url'])
            reseau = []
            page.on('requestfailed', lambda r: reseau.append({'url': r.url, 'methode': r.method, 'echec': r.failure}))
            connexion(page, application['web_url'], email, password)
            avant = donnees_metier(application)
            with refuser_catalogue(application):
                assert api.get(CATALOGUE).status_code == 500
                modal, champ = ouvrir(page, application, sens)
                expect(modal.get_by_role('alert').filter(has_text='Catalogue indisponible')).to_be_visible()
                expect(modal.get_by_text('Aucun article disponible.', exact=False)).to_have_count(0)
                with page.expect_request(lambda r: r.url.endswith(CATALOGUE)):
                    modal.get_by_role('button', name='Réessayer le catalogue', exact=True).click()
                page.wait_for_load_state('networkidle')
                assert api.get(CATALOGUE).status_code == 500
                expect(modal.get_by_role('alert').filter(has_text='Catalogue indisponible')).to_be_visible()
                champ.fill('Description libre737')
                expect(champ).to_have_value('Description libre737')
                page.screenshot(path=str(ROOT / f'.codex-tests/catalogue737-erreur-{sens}-{largeur}.png'))
            with page.expect_response(lambda r: r.url.endswith(CATALOGUE)) as rep:
                modal.get_by_role('button', name='Réessayer le catalogue', exact=True).click()
            assert rep.value.status == 200
            expect(modal.get_by_role('alert')).to_have_count(0)
            champ.fill(a['designation']); modal.locator('li').filter(has_text=a['designation']).click()
            champ.fill('Prestation libre fictive737')
            expect(modal.get_by_text('Aucun article ne correspond à la recherche.', exact=False)).to_be_visible()
            modal.get_by_placeholder('Nom du', exact=False).fill(tiers['nom'])
            modal.get_by_text(tiers['nom'], exact=True).click()
            modal.locator('.hp-commercial-line-editor input[type="number"]').nth(1).fill('100')
            assert donnees_metier(application) == avant
            _cycle, _action, _titre, save, endpoint = PROFILS[sens]
            with page.expect_response(lambda r: r.url.endswith(endpoint) and r.request.method == 'POST') as creation:
                modal.get_by_role('button', name=save, exact=True).click()
            assert creation.value.status == 201, creation.value.text()
            doc = creation.value.json()
            assert doc['total_ttc'] == 120 and doc['lignes'][0]['description'] == 'Prestation libre fictive737'
            assert doc['lignes'][0]['article_id'] is None
            assert not errors
            (ROOT / f'.codex-tests/catalogue737-reseau-{sens}.json').write_text(json.dumps(reseau, ensure_ascii=False, indent=2), encoding='utf8')
        finally: browser.close()


def test_737_vrai_catalogue_vide_et_saisie_libre(application):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        assert ok(api.get(CATALOGUE)) == []
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(); connexion(page, application['web_url'], email, password)
            modal, champ = ouvrir(page, application)
            expect(modal.get_by_text('Aucun article disponible.', exact=False)).to_be_visible()
            expect(modal.get_by_role('alert')).to_have_count(0)
            champ.fill('Prestation libre')
            expect(champ).to_have_value('Prestation libre')
        finally: browser.close()


@pytest.mark.parametrize('action', ['recherche', 'jeton', 'fermeture'])
def test_737_reponse_reelle_tardive_et_contexte(application, action):
    api, email, password = client(application)
    with closing(api), closing(client(application)[0]) as autre, sync_playwright() as p:
        a = article(api, 'Alpha ancienne société737'); b = article(api, 'Beta recherchée737')
        c = article(autre, 'Autre société737')
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(); connexion(page, application['web_url'], email, password)
            pending = []
            def retenir(route):
                rep = route.fetch(); assert rep.status == 200
                pending.append((route, rep)); page.evaluate('window.__catalogue737Retenu=true')
            page.route('**' + CATALOGUE, retenir, times=1)
            modal, champ = ouvrir(page, application)
            page.wait_for_function('window.__catalogue737Retenu===true')
            expect(modal.get_by_text('Chargement du catalogue…', exact=True)).to_be_visible()
            if action == 'recherche': champ.fill('Beta')
            elif action == 'jeton':
                page.evaluate('t=>localStorage.setItem("hisabpro_token",t)', autre.headers['Authorization'].split(' ', 1)[1])
                champ.fill('Autre société737')
                expect(modal.locator('li').filter(has_text=c['designation'])).to_be_visible()
            else:
                modal.get_by_role('button', name='Annuler', exact=True).click()
                page.get_by_role('button', name='Nouveau devis', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouveau devis', exact=True)
                champ = modal.get_by_placeholder('Article ou description...', exact=True)
                champ.fill('Beta')
                expect(modal.locator('li').filter(has_text=b['designation'])).to_be_visible()
            route, rep = pending.pop()
            with page.expect_response(lambda r: r.url.endswith(CATALOGUE)): route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(modal.locator('li').filter(has_text=a['designation'])).to_have_count(0)
            attendu = c if action == 'jeton' else b
            expect(modal.locator('li').filter(has_text=attendu['designation'])).to_be_visible()
        finally: browser.close()
