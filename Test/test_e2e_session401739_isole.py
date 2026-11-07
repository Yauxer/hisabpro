"""401 natifs : connexion réelle et client HTTP du produit dans Edge."""
from contextlib import closing
from pathlib import Path
import json
import subprocess
import pytest
from playwright.sync_api import sync_playwright, expect

from test_balance_etic_notes693_isole import (
    application, application103, application102, application101, application100, application099,
    application098, application097, application093, application092, application091, application090,
    application089, application087, migration, client, ok, donnees_metier)
from browser_support import chromium_executable
from test_e2e_administration_isole import observer

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def client_http(application, tmp_path_factory):
    """Même service compilé, fetch et API réels ; aucune réponse substituée."""
    target = tmp_path_factory.mktemp('http739') / 'http739.js'
    entry = "import {authAPI,etatsAPI} from './src/services/api.js'; window.__http739={authAPI,etatsAPI};"
    js = '''const esbuild=require('esbuild');esbuild.buildSync({stdin:{contents:process.argv[2],resolveDir:process.cwd()},
        bundle:true,platform:'browser',format:'iife',outfile:process.argv[1],define:{
        'import.meta.env.VITE_API_URL':JSON.stringify(process.argv[3]),'import.meta.env.VITE_APP_VERSION':'"test739"'}})'''
    r = subprocess.run(['node', '-e', js, str(target), entry, application['api_url']], cwd=ROOT,
                       capture_output=True, text=True, encoding='utf8', timeout=30)
    assert r.returncode == 0, r.stderr
    return target.read_text(encoding='utf8')


@pytest.mark.parametrize('largeur', [1440, 390])
def test_739_mauvais_secret_message_sans_rechargement_puis_connexion(application, largeur):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            errors, _ = observer(page, application['api_url'])
            page.goto(application['web_url'], wait_until='domcontentloaded')
            page.evaluate('window.__document739="initial"')
            page.get_by_placeholder('admin@societe.ma').fill(email)
            page.locator('input[type=password]').fill('SecretIncorrect739!')
            avant = donnees_metier(application)
            with page.expect_response(lambda r: r.url.endswith('/api/auth/login') and r.request.method == 'POST') as rep:
                page.get_by_role('button', name='Se connecter', exact=True).click()
            assert rep.value.status == 401
            expect(page.get_by_text('Email ou mot de passe incorrect', exact=True)).to_be_visible()
            assert page.evaluate('window.__document739') == 'initial'
            expect(page.get_by_placeholder('admin@societe.ma')).to_have_value(email)
            assert page.evaluate('localStorage.getItem("hisabpro_token")') is None
            assert donnees_metier(application) == avant
            page.screenshot(path=str(ROOT / f'.codex-tests/session739-connexion-{largeur}.png'))
            page.locator('input[type=password]').fill(password)
            with page.expect_response(lambda r: r.url.endswith('/api/auth/login') and r.request.method == 'POST') as rep:
                page.get_by_role('button', name='Se connecter', exact=True).click()
            assert rep.value.status == 200
            page.wait_for_url('**/dashboard', wait_until='domcontentloaded')
            token = page.evaluate('localStorage.getItem("hisabpro_token")')
            assert ok(api.get('/api/auth/me', headers={'Authorization': 'Bearer ' + token}))['email'] == email
            assert not errors
        finally: browser.close()


@pytest.mark.parametrize('genre', ['json', 'telechargement'])
@pytest.mark.parametrize('nouvelle_session', [False, True])
def test_739_401_reel_jeton_courant_ou_ancien(application, client_http, genre, nouvelle_session):
    api, _, _ = client(application)
    with closing(api), sync_playwright() as p:
        nouveau = api.headers['Authorization'].split(' ', 1)[1]
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(); observer(page, application['api_url'])
            page.goto(application['web_url'], wait_until='domcontentloaded')
            page.add_script_tag(content=client_http)
            page.evaluate('localStorage.setItem("hisabpro_token","ancien-invalide739");localStorage.setItem("hisabpro_role","lecture");window.__document739="initial"')
            endpoint = '/api/auth/me' if genre == 'json' else '/api/etats/liasse/balance/dossiers/1/pdf'
            pending = []
            def retenir(route):
                rep = route.fetch(); assert rep.status == 401
                pending.append((route, rep)); page.evaluate('window.__retenu739=true')
            page.route('**' + endpoint, retenir, times=1)
            avant = donnees_metier(application)
            expression = 'window.__http739.authAPI.me()' if genre == 'json' else 'window.__http739.etatsAPI.preparationBalancePDF(1)'
            page.evaluate('expression => { window.__resultat739=null; eval(expression).then(() => window.__resultat739={succes:true}).catch(e => window.__resultat739={erreur:e.message}) }', expression)
            page.wait_for_function('window.__retenu739===true')
            if nouvelle_session:
                page.evaluate('t=>{localStorage.setItem("hisabpro_token",t);localStorage.setItem("hisabpro_role","admin")}', nouveau)
            route, rep = pending.pop()
            if nouvelle_session:
                with page.expect_response(lambda r: r.url.endswith(endpoint)): route.fulfill(response=rep)
                page.wait_for_function('window.__resultat739!==null')
                assert page.evaluate('window.__document739') == 'initial'
                assert page.evaluate('localStorage.getItem("hisabpro_token")') == nouveau
                assert page.evaluate('localStorage.getItem("hisabpro_role")') == 'admin'
                assert 'session a changé' in page.evaluate('window.__resultat739.erreur')
                assert ok(api.get('/api/auth/me', headers={'Authorization': 'Bearer ' + nouveau}))
            else:
                with page.expect_navigation(wait_until='domcontentloaded'): route.fulfill(response=rep)
                assert page.evaluate('localStorage.getItem("hisabpro_token")') is None
                expect(page.get_by_role('button', name='Se connecter', exact=True)).to_be_visible()
            assert donnees_metier(application) == avant
        finally: browser.close()
