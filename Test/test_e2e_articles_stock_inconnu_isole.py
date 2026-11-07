"""Stocks historiques NULL/NaN : Edge, API réelle et PostgreSQL nonce."""
import uuid

import httpx
import pytest
from sqlalchemy import text

from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ


def photographie(application):
    with application['engine'].connect() as db:
        return {table: db.execute(text(
            f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id'
        )).scalars().all() for table in ('articles', 'mouvements_stock', 'ecritures')}


def test_stock_inconnu_interface_sans_reparation(application):
    playwright = pytest.importorskip('playwright.sync_api')
    executable = chromium_executable()
    if not executable:
        pytest.skip('Chromium/Edge requis')
    suffixe = uuid.uuid4().hex[:12]
    email, password = suffixe + '@example.com', 'StockInconnu2026!'
    with httpx.Client(base_url=application['api_url']) as api:
        r = api.post('/api/auth/register', json={
            'nom': 'Stock fictif', 'email': email, 'password': password,
            'raison_sociale': 'Stock inconnu fictif ' + suffixe})
        assert r.status_code == 200, r.text
        api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        articles = {}
        for nom, stock, stockable in (
            ('A NULL fictif', 0, True), ('B NaN fictif', 0, True),
            ('C Positif fictif', 5, True), ('D Service fictif', 0, False),
            ('Z Zéro fictif', 0, True),
        ):
            r = api.post('/api/articles', json={
                'code': suffixe + '-' + nom[0], 'designation': nom,
                'stock_actuel': stock, 'is_stockable': stockable,
                'prix_vente': 100, 'prix_achat': 40, 'tva': 20})
            assert r.status_code == 201, r.text
            articles[nom] = r.json()['id']
        cible = application['cluster']
        verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        # Fixture historique uniquement, après création métier valide. Aucune
        # migration, règle ou écriture n'est modifiée pour accepter ces valeurs.
        with application['engine'].begin() as db:
            db.execute(text('UPDATE articles SET stock_actuel=NULL WHERE id=:id'),
                       {'id': articles['A NULL fictif']})
            db.execute(text("UPDATE articles SET stock_actuel='NaN'::double precision WHERE id=:id"),
                       {'id': articles['B NaN fictif']})
        avant = photographie(application)
        lecture = api.get('/api/articles')
        assert lecture.status_code == 200, lecture.text
        for nom in ('A NULL fictif', 'B NaN fictif'):
            article = next(a for a in lecture.json() if a['id'] == articles[nom])
            assert article['stock_actuel'] is None and article['stock_diagnostic']

        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(20000)
                erreurs, erreurs_serveur = observer(page, application['api_url'])
                mutations = []
                page.on('request', lambda request: mutations.append(request.url)
                        if '/api/articles' in request.url and request.method in ('POST', 'PUT', 'PATCH', 'DELETE') else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/articles', wait_until='domcontentloaded')
                for nom in ('A NULL fictif', 'B NaN fictif'):
                    row = page.locator('tbody tr').filter(has_text=nom)
                    row.get_by_text('Stock inconnu', exact=True).wait_for()
                    assert row.get_by_text('À vérifier', exact=True).count() == 1
                    assert row.get_by_text('Rupture', exact=True).count() == 0
                    row.click()
                    modal = page.get_by_role('dialog', name="Modifier l'article")
                    stock = champ(modal, 'Stock actuel')
                    assert stock.input_value() == ''
                    assert stock.get_attribute('placeholder') == 'À vérifier'
                    assert stock.evaluate('(input) => input.readOnly') is True
                    modal.get_by_text('Stock physique inconnu ou invalide : vérifier la source historique.', exact=True).wait_for()
                    modal.get_by_role('button', name='Annuler', exact=True).click()
                zero = page.locator('tbody tr').filter(has_text='Z Zéro fictif')
                zero.get_by_text('Rupture', exact=True).wait_for()
                service = page.locator('tbody tr').filter(has_text='D Service fictif')
                service.get_by_text('Non stockable', exact=True).wait_for()
                assert service.get_by_text('Rupture', exact=True).count() == 0
                assert service.get_by_text('Stock inconnu', exact=True).count() == 0
                page.get_by_role('button', name='Stock faible', exact=True).click()
                lignes = page.locator('tbody tr').all_text_contents()
                position = lambda nom: next(i for i, ligne in enumerate(lignes) if nom in ligne)
                assert position('Z Zéro fictif') < position('C Positif fictif')
                assert all(position('C Positif fictif') < position(nom)
                           for nom in ('A NULL fictif', 'B NaN fictif'))
                page.get_by_role('button', name='Nouvel article', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouvel article')
                assert champ(modal, 'Stock initial').input_value() == '0'
                modal.get_by_role('button', name='Annuler', exact=True).click()
                assert mutations == []
                assert erreurs == [] and erreurs_serveur == []
            finally:
                browser.close()
        assert photographie(application) == avant
