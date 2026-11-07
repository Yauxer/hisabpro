"""Frais article facultatifs : UI/API réelles et PostgreSQL nonce."""
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ


@pytest.mark.parametrize('largeur', [1365, 390])
def test_article_frais_creation_edition_validation_locale_et_stock_inconnu(application, largeur):
    suffix = uuid.uuid4().hex[:8]
    email, password = f'articles-frais-{suffix}@example.com', 'ArticlesFrais2026!'
    nom = 'Article frais fictif ' + suffix
    nom_inconnu = 'Stock inconnu fictif ' + suffix
    with httpx.Client(base_url=application['api_url']) as api:
        r = api.post('/api/auth/register', json={'nom': 'Administration articles fictive', 'email': email, 'password': password, 'raison_sociale': 'Frais fictifs ' + suffix})
        assert r.status_code == 200, r.text
        api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        sid = api.get('/api/societe/moi').json()['id']
        r = api.post('/api/articles', json={'code': 'HIST-' + suffix, 'designation': nom_inconnu, 'stock_actuel': 0, 'is_stockable': True, 'frais_emballage': 1.25, 'frais_transport': 4.5})
        assert r.status_code == 201, r.text
        hid = r.json()['id']
        # Historique incomplet fictif, exclusivement dans le cluster nonce.
        with Session(application['engine']) as db:
            db.get(models.Article, hid).stock_actuel = None
            db.commit()
            assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
            assert db.query(models.MouvementStock).filter_by(societe_id=sid).count() == 0
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                mutations = []
                page.on('request', lambda request: mutations.append(request) if '/api/articles' in request.url and request.method in {'POST', 'PATCH'} else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/articles', wait_until='domcontentloaded')
                page.get_by_role('button', name='Nouvel article', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouvel article', exact=True)
                champ(modal, 'Code').fill('FRAIS-' + suffix)
                champ(modal, 'Désignation').fill(nom)
                champ(modal, 'Prix vente HT').fill('100')
                champ(modal, 'Prix achat HT').fill('60')
                champ(modal, 'Emballage HT par unité').fill('2.5')
                champ(modal, 'Transport HT par unité').fill('7.25')
                modal.get_by_text('Montants HT par unité, à reporter dans les frais du document selon la quantité.', exact=True).wait_for()
                for label, valeur, restauration in [
                    ('Emballage HT par unité', '-1', '2.5'),
                    ('Transport HT par unité', '1e309', '7.25'),
                    ('Prix vente HT', '1e309', '100'),
                    ('Prix achat HT', '1e309', '60'),
                    ('Stock minimum', '1e309', '0'),
                    ('Stock initial', '1e309', '0'),
                ]:
                    champ(modal, label).fill(valeur)
                    avant = len(mutations)
                    modal.get_by_role('button', name='Créer l’article', exact=True).click()
                    modal.get_by_text('négatif' if valeur == '-1' else 'nombre fini valide', exact=False).wait_for()
                    assert len(mutations) == avant, (label, [r.url for r in mutations])
                    champ(modal, label).fill(restauration)
                with page.expect_response(lambda r: r.url.endswith('/api/articles') and r.request.method == 'POST') as creation:
                    modal.get_by_role('button', name='Créer l’article', exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                article = creation.value.json()
                aid = article['id']
                assert article['frais_emballage'] == 2.5 and article['frais_transport'] == 7.25
                assert article['stock_actuel'] == 0
                modal.wait_for(state='hidden')
                # La mutation rafraîchit réellement la liste, sans F5.
                ligne = page.locator('tbody tr').filter(has_text=nom)
                ligne.click()
                edition = page.get_by_role('dialog', name="Modifier l'article", exact=True)
                assert champ(edition, 'Emballage HT par unité').input_value() == '2.5'
                assert champ(edition, 'Transport HT par unité').input_value() == '7.25'
                playwright.expect(champ(edition, 'Stock actuel')).to_have_attribute('readonly', '')
                champ(edition, 'Emballage HT par unité').fill('3.75')
                champ(edition, 'Transport HT par unité').fill('8.5')
                with page.expect_response(lambda r: r.url.endswith(f'/api/articles/{aid}') and r.request.method == 'PATCH') as changement:
                    edition.get_by_role('button', name='Enregistrer les modifications', exact=True).click()
                assert changement.value.status == 200, changement.value.text()
                assert 'stock_actuel' not in changement.value.request.post_data_json
                edition.wait_for(state='hidden')
                ligne.click()
                assert champ(edition, 'Emballage HT par unité').input_value() == '3.75'
                assert champ(edition, 'Transport HT par unité').input_value() == '8.5'
                edition.get_by_role('button', name='Annuler', exact=True).click()
                # Les frais restent facultatifs : vide explicite conserve le défaut0.
                page.get_by_role('button', name='Nouvel article', exact=True).click()
                champ(modal, 'Code').fill('SANS-' + suffix)
                champ(modal, 'Désignation').fill('Sans frais fictif ' + suffix)
                champ(modal, 'Emballage HT par unité').fill('')
                champ(modal, 'Transport HT par unité').fill('')
                with page.expect_response(lambda r: r.url.endswith('/api/articles') and r.request.method == 'POST') as sans:
                    modal.get_by_role('button', name='Créer l’article', exact=True).click()
                assert sans.value.status == 201
                assert sans.value.json()['frais_emballage'] == sans.value.json()['frais_transport'] == 0
                modal.wait_for(state='hidden')
                page.locator('tbody tr').filter(has_text=nom_inconnu).click()
                assert champ(edition, 'Stock actuel').input_value() == ''
                playwright.expect(champ(edition, 'Stock actuel')).to_have_attribute('readonly', '')
                edition.get_by_text('Stock physique inconnu ou invalide : vérifier la source historique.', exact=True).wait_for()
                assert champ(edition, 'Emballage HT par unité').input_value() == '1.25'
                champ(edition, 'Emballage HT par unité').fill('1.75')
                with page.expect_response(lambda r: r.url.endswith(f'/api/articles/{hid}') and r.request.method == 'PATCH') as historique:
                    edition.get_by_role('button', name='Enregistrer les modifications', exact=True).click()
                assert historique.value.status == 200, historique.value.text()
                assert 'stock_actuel' not in historique.value.request.post_data_json
                assert historique.value.json()['stock_actuel'] is None
                lecture = api.get('/api/articles')
                assert lecture.status_code == 200, lecture.text
                assert next(a for a in lecture.json() if a['id'] == aid)['frais_transport'] == 8.5
                with Session(application['engine']) as db:
                    assert db.get(models.Article, aid).stock_actuel == 0
                    assert db.get(models.Article, hid).stock_actuel is None
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
                    assert db.query(models.MouvementStock).filter_by(societe_id=sid).count() == 0
                assert not errors and not server_errors, (errors, server_errors)
            finally:
                browser.close()
