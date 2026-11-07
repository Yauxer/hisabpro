"""Diagnostic indicatif création/édition : vrai Edge, HTTP et PostgreSQL nonce."""
from datetime import date
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


def choisir_article(modal, index, nom):
    modal.get_by_placeholder('Article ou description...').nth(index).fill(nom)
    modal.locator('li').filter(has_text=nom).click()


def quantite(modal, index):
    return modal.locator('.hp-commercial-line-editor input[type="number"]').nth(index * 2)


@pytest.mark.parametrize('largeur', [1365, 390])
def test_stock_devis_cumul_service_inconnu_refresh_et_reponse_tardive(application, largeur):
    suffix = uuid.uuid4().hex[:8]
    email, password = 'devis-stock-' + suffix + '@example.com', 'DevisStockFictif!'
    with httpx.Client(base_url=application['api_url']) as api:
        reg = ok(api.post('/api/auth/register', json={'nom': 'Stock fictif', 'email': email,
                   'password': password, 'raison_sociale': 'Devis stock fictif ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + reg['access_token']
        sid = ok(api.get('/api/societe/moi'))['id']
        client = 'Client stock ' + suffix
        ok(api.post('/api/tiers', json={'nom': client, 'type': 'client'}), 201)
        articles = []
        for label, stockable, stock in [('Produit', True, 5), ('Service', False, 0), ('Inconnu', True, 0)]:
            articles.append(ok(api.post('/api/articles', json={'code': label + suffix,
                'designation': label + ' stock fictif ' + suffix, 'is_stockable': stockable,
                'stock_actuel': stock, 'prix_vente_ht': 10, 'tva': 20}), 201))
        with Session(application['engine']) as db:
            # Ancien stock incomplet, exclusivement dans la base nonce.
            db.get(models.Article, articles[2]['id']).stock_actuel = None
            db.commit()
            avant = (db.query(models.MouvementStock).filter_by(societe_id=sid).count(),
                     db.query(models.Ecriture).filter_by(societe_id=sid).count())
        liste = ok(api.get('/api/articles'))
        assert len(liste) == 3, liste
        executable = chromium_executable()
        if not executable:
            pytest.skip('Microsoft Edge / Chromium requis')
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/commercial')
                page.get_by_role('button', name='Nouveau devis', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouveau devis', exact=True)
                modal.get_by_placeholder('Nom du client...').fill(client)
                modal.get_by_text(client, exact=True).click()
                choisir_article(modal, 0, articles[0]['designation'])
                quantite(modal, 0).fill('3')
                modal.get_by_role('button', name='Ajouter', exact=True).click()
                choisir_article(modal, 1, articles[0]['designation'])
                quantite(modal, 1).fill('3')
                diag = modal.get_by_role('region', name='Stock indicatif', exact=True)
                produit = diag.locator('li').filter(has_text=articles[0]['designation'])
                playwright.expect(produit).to_contain_text('Demandé : 6')
                playwright.expect(produit).to_contain_text('Stock physique : 5')
                playwright.expect(produit).to_contain_text('Manquant : 1')
                for index, article in enumerate(articles[1:], start=2):
                    modal.get_by_role('button', name='Ajouter', exact=True).click()
                    choisir_article(modal, index, article['designation'])
                playwright.expect(diag.locator('li').filter(has_text=articles[1]['designation'])).to_contain_text('Non stockable')
                inconnu = diag.locator('li').filter(has_text=articles[2]['designation'])
                playwright.expect(inconnu).to_contain_text('Stock inconnu')
                assert 'Stock physique : 0' not in inconnu.inner_text()
                # La très grande quantité cumulée reste du texte, jamais Infinity.
                quantite(modal, 0).fill('1e308')
                quantite(modal, 1).fill('1e308')
                playwright.expect(produit).to_contain_text('valeur Decimal conservée en texte')
                assert 'Infinity' not in diag.inner_text()
                quantite(modal, 0).fill('3')
                quantite(modal, 1).fill('3')
                playwright.expect(produit).to_contain_text('Manquant : 1')
                with page.expect_response(lambda r: r.url.endswith('/api/devis') and r.request.method == 'POST') as created:
                    modal.get_by_role('button', name='Créer le devis', exact=True).click()
                assert created.value.status == 201, created.value.text()
                devis = created.value.json()
                assert devis['total_ttc'] == 96
                modal.wait_for(state='hidden')
                page.locator('tbody tr').filter(has_text=devis['numero']).locator('button[title="Modifier"]').click()
                modal = page.get_by_role('dialog')
                diag = modal.get_by_role('region', name='Stock indicatif', exact=True)
                produit = diag.locator('li').filter(has_text=articles[0]['designation'])
                playwright.expect(produit).to_contain_text('Manquant : 1')
                # Réponse réelle retenue avant changement de quantité ; aucun corps inventé.
                retenues = []
                def retarder(route):
                    if not retenues:
                        reponse = route.fetch()
                        assert reponse.status == 200
                        retenues.append((route, reponse))
                        page.evaluate('window.__stockRetenu = true')
                    else:
                        route.continue_()
                page.route('**/api/devis/diagnostic-stock', retarder)
                diag.get_by_role('button', name='Actualiser le stock', exact=True).click()
                page.wait_for_function('window.__stockRetenu === true')
                playwright.expect(modal.get_by_role('button', name='Enregistrer', exact=True)).to_be_enabled()
                quantite(modal, 0).fill('1')
                quantite(modal, 1).fill('1')
                playwright.expect(produit).to_contain_text('Demandé : 2')
                playwright.expect(produit).to_contain_text('Disponible')
                route, reponse = retenues[0]
                route.fulfill(response=reponse)
                page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
                playwright.expect(produit).to_contain_text('Demandé : 2')
                assert 'Demandé : 6' not in produit.inner_text()
                page.unroute('**/api/devis/diagnostic-stock')
                ok(api.patch(f'/api/articles/{articles[0]["id"]}/stock', json={'stock_actuel': 0,
                    'reference': 'RECETTE-STOCK-' + suffix, 'note': 'Ajustement fictif isolé pour actualisation devis',
                    'date': date.today().isoformat()}))
                diag.get_by_role('button', name='Actualiser le stock', exact=True).click()
                playwright.expect(produit).to_contain_text('Stock physique : 0')
                playwright.expect(produit).to_contain_text('Manquant : 2')
                with page.expect_response(lambda r: r.url.endswith(f'/api/devis/{devis["id"]}') and r.request.method == 'PATCH') as updated:
                    modal.get_by_role('button', name='Enregistrer', exact=True).click()
                assert updated.value.status == 200, updated.value.text()
                assert updated.value.json()['total_ttc'] == 48
                modal.wait_for(state='hidden')
                assert not errors, errors
                assert not server_errors, server_errors
                with Session(application['engine']) as db:
                    assert db.get(models.Article, articles[0]['id']).stock_actuel == 0
                    assert db.get(models.Article, articles[2]['id']).stock_actuel is None
                    assert db.query(models.MouvementStock).filter_by(societe_id=sid).count() == avant[0] + 1
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == avant[1]
            except Exception:
                print('Écran stock fictif :', page.url, page.locator('body').inner_text()[:8500])
                print('Erreurs :', errors, server_errors)
                raise
            finally:
                browser.close()
