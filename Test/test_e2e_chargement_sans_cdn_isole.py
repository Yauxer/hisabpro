"""Chargement local des fontes : Edge, API réelle et PostgreSQL nonce.

Les CSS externes éventuelles sont volontairement laissées sans réponse. Le
test conserve wait_until='load' et un délai de navigation de cinq secondes.
Il doit d'abord reproduire le problème avant localisation des assets320.
"""
from urllib.parse import urlsplit
import uuid

import httpx
import pytest
from sqlalchemy import text

from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import ouvrir_navigation


CDN = {'fonts.googleapis.com', 'fonts.gstatic.com', 'cdn.jsdelivr.net'}


def photographie(application, sid):
    with application['engine'].connect() as db:
        return {
            table: db.execute(text(
                f'SELECT row_to_json(t)::text FROM {table} t '
                'WHERE societe_id=:sid ORDER BY id'), {'sid': sid}).scalars().all()
            for table in ('articles', 'mouvements_stock', 'ecritures')
        }


@pytest.mark.parametrize('largeur', [1365, 390])
def test_chargement_connexion_et_pages_sans_attente_cdn(application, largeur):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    executable = chromium_executable()
    if not executable:
        pytest.skip('Edge / Chromium requis')
    playwright = pytest.importorskip('playwright.sync_api')
    suffix = uuid.uuid4().hex[:8]
    email, password = 'assets-locaux-' + suffix + '@example.com', 'AssetsLocaux2026!'
    designation = 'Article fontes locales ' + suffix
    with httpx.Client(base_url=application['api_url']) as api:
        r = api.post('/api/auth/register', json={'nom': 'Recette assets locaux',
            'email': email, 'password': password,
            'raison_sociale': 'Assets fictifs ' + suffix})
        assert r.status_code == 200, r.text
        api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        r = api.get('/api/societe/moi')
        assert r.status_code == 200, r.text
        sid = r.json()['id']
        r = api.post('/api/articles', json={'code': 'LOCAL-' + suffix,
            'designation': designation, 'stock_actuel': 0, 'tva': 20,
            'prix_achat_ht': 20, 'prix_vente_ht': 30})
        assert r.status_code == 201, r.text
        avant = photographie(application, sid)
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            erreurs_js, erreurs_api, externes, attentes_cdn, fontes = [], [], [], [], []
            origines_locales = {
                (urlsplit(application[k]).scheme, urlsplit(application[k]).netloc)
                for k in ('web_url', 'api_url')
            }

            def requete(request):
                u = urlsplit(request.url)
                if u.scheme in {'http', 'https'} and (u.scheme, u.netloc) not in origines_locales:
                    externes.append(request.url)

            def reponse(response):
                if response.url.startswith(application['api_url']) and response.status >= 500:
                    erreurs_api.append((response.url, response.status))
                if urlsplit(response.url).path.endswith('.woff2'):
                    fontes.append((response.url, response.status))

            def css_suspendue(route):
                # Ni abort, ni fulfill, ni continue : reproduit un CDN qui ne
                # répond pas, sans envoyer une requête sur Internet.
                attentes_cdn.append(route.request.url)

            for domaine in CDN:
                page.route(f'https://{domaine}/**', css_suspendue)
            page.on('request', requete)
            page.on('response', reponse)
            page.on('pageerror', lambda error: erreurs_js.append(str(error)))
            try:
                # Assertion centrale : ne pas remplacer load par DOMContentLoaded
                # et ne pas augmenter ce délai pour rendre le test vert.
                page.goto(application['web_url'], wait_until='load', timeout=5000)
                playwright.expect(page.get_by_role('button', name='Se connecter', exact=True)).to_be_visible()
                assert not attentes_cdn, attentes_cdn
                assert not externes, externes
                page.get_by_placeholder('admin@societe.ma').fill(email)
                page.locator('input[type="password"]').fill(password)
                with page.expect_response(lambda r: r.url.endswith('/api/auth/login')
                                          and r.request.method == 'POST') as connexion:
                    page.get_by_role('button', name='Se connecter', exact=True).click()
                assert connexion.value.status == 200, connexion.value.text()
                page.wait_for_url('**/dashboard')
                ouvrir_navigation(page)
                page.get_by_role('button', name='Déconnexion', exact=True).wait_for()

                police = page.evaluate("""async () => {
                    await Promise.all([400, 500, 600].map(w =>
                        document.fonts.load(`${w} 16px Inter`, 'Comptabilité marocaine')));
                    await document.fonts.load('16px tabler-icons', '\\ueba8');
                    await document.fonts.ready;
                    const icone = document.querySelector('.ti-logout');
                    const style = icone && getComputedStyle(icone, '::before');
                    return {
                        inter: [400, 500, 600].map(w => document.fonts.check(`${w} 16px Inter`)),
                        tabler: document.fonts.check('16px tabler-icons', '\\ueba8'),
                        faces: Array.from(document.fonts).map(f => ({family: f.family, status: f.status})),
                        familleCorps: getComputedStyle(document.body).fontFamily,
                        familleIcone: style?.fontFamily,
                        contenuIcone: style?.content,
                    };
                }""")
                assert police['inter'] == [True, True, True], police
                assert police['tabler'], police
                for famille in ('Inter', 'tabler-icons'):
                    assert any(f['family'].strip('"\'') == famille and f['status'] == 'loaded'
                               for f in police['faces']), police
                assert 'Inter' in police['familleCorps'], police
                assert 'tabler-icons' in police['familleIcone'], police
                # Le glyphe reste rendu ; son alternative vide le rend
                # décoratif dans le nom accessible des boutons.
                assert police['contenuIcone'] == '"\ueba8" / ""', police
                assert fontes and all(statut == 200 for _, statut in fontes), fontes
                assert any('inter' in url.lower() for url, _ in fontes), fontes
                assert any('tabler' in url.lower() for url, _ in fontes), fontes
                for chemin, titre in (
                    ('/articles', 'Articles & Services'),
                    ('/inventaire', 'Inventaire & valorisation'),
                    ('/journal', 'Journal comptable'),
                ):
                    page.goto(application['web_url'] + chemin, wait_until='load', timeout=5000)
                    playwright.expect(page.get_by_role('heading', name=titre, exact=True)).to_be_visible()
                    if chemin == '/articles':
                        playwright.expect(page.locator('tbody tr').filter(has_text=designation)).to_be_visible()
                    elif chemin == '/inventaire':
                        playwright.expect(page.locator('tbody tr').filter(has_text=designation)).to_be_visible()
                    else:
                        playwright.expect(page.get_by_role('button', name='Déconnexion', exact=True, include_hidden=True)).to_be_attached()
                assert not externes and not attentes_cdn, (externes, attentes_cdn)
                assert not erreurs_js and not erreurs_api, (erreurs_js, erreurs_api)
                assert photographie(application, sid) == avant
            finally:
                browser.close()
