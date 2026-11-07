"""BR fournisseur : retour immédiat non bloquant, Edge/API/PG nonce réels."""
from datetime import date
import uuid

import httpx
import pytest
from sqlalchemy import text

from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


def photo(application, sid):
    with application['engine'].connect() as db:
        return {table: db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t '
            'WHERE societe_id=:sid ORDER BY id'), {'sid': sid}).scalars().all()
            for table in ('articles', 'mouvements_stock', 'ecritures')}


@pytest.mark.parametrize('largeur', [1365, 390])
def test_facture_br_retour_visible_avant_navigation_sans_dialogue(application, largeur):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    executable = chromium_executable()
    if not executable:
        pytest.skip('Edge / Chromium requis')
    pw = pytest.importorskip('playwright.sync_api')
    suffix = uuid.uuid4().hex[:8]
    email, password = 'retour-br-' + suffix + '@example.com', 'RetourBRFictif2026!'
    fournisseur = 'Fournisseur retour ' + suffix
    with httpx.Client(base_url=application['api_url']) as api:
        token = ok(api.post('/api/auth/register', json={'nom': 'Retour BR fictif',
            'email': email, 'password': password, 'raison_sociale': 'Retour BR ' + suffix}))['access_token']
        api.headers['Authorization'] = 'Bearer ' + token
        sid = ok(api.get('/api/societe/moi'))['id']
        ok(api.patch('/api/societe/moi', json={'stock_declencheur_achat': 'br'}))
        tid = ok(api.post('/api/tiers', json={'nom': fournisseur, 'type': 'fournisseur'}), 201)['id']
        article = ok(api.post('/api/articles', json={'code': 'BR-' + suffix,
            'designation': 'Article retour ' + suffix, 'prix_achat_ht': 100,
            'stock_actuel': 0, 'tva': 20}), 201)
        bc = ok(api.post('/api/bons-commande', json={'type': 'achat', 'date': date.today().isoformat(),
            'tiers': fournisseur, 'tiers_id': tid, 'lignes': [{'article_id': article['id'],
                'description': article['designation'], 'quantite': 1, 'prix_unitaire': 100,
                'tva': 20, 'qualification_tva': 'taxable'}]}), 201)
        br = ok(api.post(f"/api/bons-commande/{bc['id']}/convertir-bl", json={'lignes': [
            {'ligne_bc_id': bc['lignes'][0]['id'], 'description': article['designation'], 'quantite': 1}]}))
        ok(api.patch(f"/api/bons-reception/{br['id']}", json={'statut': 'expedie'}))
        ok(api.patch(f"/api/bons-reception/{br['id']}", json={'statut': 'livre'}))
        avant = photo(application, sid)
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            erreurs, serveurs = observer(page, application['api_url'])
            dialogues, conversions = [], []
            # Aucun accept/dismiss automatique : un succès natif tardif est un
            # vrai échec, pas un dialogue que la recette masque.
            page.on('dialog', lambda d: dialogues.append((d.type, d.message)))
            endpoint = f"/api/bons-livraison/{br['id']}/convertir-facture"
            page.on('request', lambda r: conversions.append(r)
                    if r.method == 'POST' and r.url.endswith(endpoint) else None)
            try:
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/commercial')
                page.get_by_role('button', name='Achat', exact=True).click()
                page.get_by_role('button', name='Bons de réception', exact=True).click()
                row = page.locator('tbody tr').filter(has_text=br['numero'])
                row.get_by_title('Créer la facture fournisseur depuis ce bon de réception', exact=True).click()
                modal = page.get_by_role('dialog', name='Facturer le bon de réception ' + br['numero'], exact=True)
                with page.expect_response(lambda r: r.url.endswith(endpoint) and r.request.method == 'POST') as conversion:
                    modal.get_by_role('button', name='Créer la facture en brouillon', exact=True).click()
                assert conversion.value.status == 200, conversion.value.text()
                facture = conversion.value.json()
                assert facture['total_ttc'] == 120
                # Feedback prouvé avant départ, avec l'identité de la facture
                # et les prochaines informations à compléter.
                retour = page.get_by_role('status').filter(has_text=f"#{facture['id']}")
                pw.expect(retour).to_contain_text(br['numero'])
                pw.expect(retour).to_contain_text('numéro fournisseur')
                modal.wait_for(state='hidden')
                page.goto(application['web_url'] + '/factures', wait_until='load', timeout=20000)
                pw.expect(page.locator('tbody tr').filter(has_text=f"Brouillon #{facture['id']}")).to_be_visible()
                assert not dialogues, dialogues
                assert len(conversions) == 1
                factures = ok(api.get('/api/factures', params={'exercice': date.today().year}))
                assert len(factures) == 1 and factures[0]['id'] == facture['id']
                assert not factures[0]['est_validee'] and not factures[0]['est_comptabilisee']
                br_relu = next(b for b in ok(api.get('/api/bons-reception', params={'exercice': date.today().year})) if b['id'] == br['id'])
                assert br_relu['facture_id'] == facture['id']
                assert photo(application, sid) == avant
                assert not erreurs and not serveurs, (erreurs, serveurs)
            finally:
                browser.close()
