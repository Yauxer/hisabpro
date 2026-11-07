"""Logo société : vraie UI/API, raster intégré et PostgreSQL éphémère uniquement."""
from datetime import date
from io import BytesIO
import base64
import uuid

import httpx
import pytest
from pypdf import PdfReader
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application
from test_logo_societe import image_data


def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def test_logo_import_apercu_pdf_effacement_et_permissions(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = f'logo-{suffix}@example.com', 'LogoFictif132!'
    lecteur = f'lecture-logo-{suffix}@example.com'
    data = image_data()
    png = base64.b64decode(data.split(',')[1])
    with httpx.Client(base_url=application['api_url'], timeout=30) as api:
        admin = ok(api.post('/api/auth/register', json={'nom': 'Admin logo fictif', 'email': email,
            'password': password, 'raison_sociale': 'Logo fictif ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + admin['access_token']
        company = ok(api.get('/api/societe/moi'))
        ok(api.post('/api/utilisateurs', json={'nom': 'Lecteur logo fictif', 'email': lecteur,
            'mot_de_passe': password, 'role': 'lecture'}), 201)
        # Ancienne référence : injectée uniquement dans ce laboratoire isolé.
        with Session(application['engine']) as db:
            societe = db.get(models.Societe, company['id'])
            societe.logo_url = 'https://example.com/ancien-logo.png'
            db.commit()
        assert api.patch('/api/societe/moi', json={'ville': 'Rabat'}).status_code == 200
        assert ok(api.get('/api/societe/moi'))['logo_url'] == 'https://example.com/ancien-logo.png'
        assert api.patch('/api/societe/moi', json={'logo_url': 'http://127.0.0.1/logo.png'}).status_code == 422
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium/Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(); page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                external_logos = []
                page.on('request', lambda request: external_logos.append(request.url) if 'example.com/ancien-logo' in request.url else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/parametres')
                page.get_by_text('Logo existant enregistré.', exact=False).wait_for()
                with page.expect_response(lambda r: r.url.endswith('/api/societe/moi') and r.request.method == 'PATCH') as sauvegarde_ancienne:
                    page.get_by_role('button', name='Enregistrer', exact=True).click()
                assert sauvegarde_ancienne.value.status == 200
                assert 'logo_url' not in sauvegarde_ancienne.value.request.post_data_json
                assert not external_logos
                page.get_by_label('Logo de la société', exact=True).set_input_files({'name': 'logo-fictif.svg', 'mimeType': 'image/svg+xml', 'buffer': b'<svg />'})
                page.get_by_role('alert').filter(has_text='PNG ou JPEG').wait_for()
                page.get_by_label('Logo de la société', exact=True).set_input_files({'name': 'logo-fictif.png', 'mimeType': 'image/png', 'buffer': png})
                preview = page.get_by_alt_text('Aperçu du logo de la société', exact=True)
                preview.wait_for()
                assert preview.evaluate('(image) => image.complete && image.naturalWidth === 20')
                with page.expect_response(lambda r: r.url.endswith('/api/societe/moi') and r.request.method == 'PATCH') as sauvegarde:
                    page.get_by_role('button', name='Enregistrer', exact=True).click()
                assert sauvegarde.value.status == 200
                assert ok(api.get('/api/societe/moi'))['logo_url'] == data
                page.reload(); page.get_by_alt_text('Aperçu du logo de la société', exact=True).wait_for()
                tiers = ok(api.post('/api/tiers', json={'nom': 'Client logo fictif', 'type': 'client'}), 201)
                facture = ok(api.post('/api/factures', json={'type': 'vente', 'date': date.today().isoformat(),
                    'tiers': tiers['nom'], 'tiers_id': tiers['id'], 'statut': 'en_attente',
                    'lignes': [{'description': 'Prestation fictive', 'quantite': 1, 'prix_unitaire': 100, 'tva': 20}]}), 201)
                ok(api.post(f"/api/factures/{facture['id']}/valider"))
                pdf = api.get(f"/api/factures/{facture['id']}/pdf")
                assert pdf.status_code == 200, pdf.text
                assert len(PdfReader(BytesIO(pdf.content)).pages[0].images) == 1
                page.get_by_role('button', name='Retirer le logo', exact=True).click()
                with page.expect_response(lambda r: r.url.endswith('/api/societe/moi') and r.request.method == 'PATCH') as suppression:
                    page.get_by_role('button', name='Enregistrer', exact=True).click()
                assert suppression.value.status == 200
                assert ok(api.get('/api/societe/moi'))['logo_url'] == ''
                ok(api.patch('/api/societe/moi', json={'logo_url': data}))
                page.get_by_role('button', name='Déconnexion', exact=True).click()
                connexion(page, application['web_url'], lecteur, password)
                page.goto(application['web_url'] + '/parametres')
                page.get_by_alt_text('Aperçu du logo de la société', exact=True).wait_for()
                playwright.expect(page.get_by_label('Logo de la société', exact=True)).to_be_disabled()
                playwright.expect(page.get_by_role('button', name='Retirer le logo', exact=True)).to_be_disabled()
                token = page.evaluate("localStorage.getItem('hisabpro_token')")
                refused = api.patch('/api/societe/moi', headers={'Authorization': 'Bearer ' + token}, json={'logo_url': ''})
                assert refused.status_code == 403, refused.text
                assert ok(api.get('/api/societe/moi'))['logo_url'] == data
                assert not errors, errors
                assert not server_errors, server_errors
            finally:
                browser.close()
