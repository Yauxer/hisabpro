"""Notes de devis existantes : vraie interface Edge, API et PG isolé."""
from datetime import date
from io import BytesIO
import uuid

import httpx
import pytest
from pypdf import PdfReader
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ


@pytest.mark.parametrize('largeur', [1365, 390])
def test_notes_devis_creation_edition_consultation_pdf_et_achat(application, tmp_path, largeur):
    suffix = uuid.uuid4().hex[:8]
    email, password = f'devis-notes-{suffix}@example.com', 'DevisNotesRecette!'
    nom = f'Client notes {suffix}'
    initiale = 'Offre valable trente jours.\nLivraison sur rendez-vous.'
    finale = 'Offre valable trente jours.\nLivraison sur rendez-vous confirmé.'
    with httpx.Client(base_url=application['api_url']) as api:
        reponse = api.post('/api/auth/register', json={'nom': 'Recette devis', 'email': email,
                            'password': password, 'raison_sociale': f'Devis notes fictif {suffix}'})
        assert reponse.status_code == 200, reponse.text
        api.headers['Authorization'] = 'Bearer ' + reponse.json()['access_token']
        tiers = api.post('/api/tiers', json={'nom': nom, 'type': 'client'})
        assert tiers.status_code == 201, tiers.text
        with Session(application['engine']) as db:
            sid = db.get(models.Tiers, tiers.json()['id']).societe_id
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Microsoft Edge / Chromium requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 900}, accept_downloads=True)
                page.set_default_timeout(15000)
                errors, server_errors = observer(page, application['api_url'])
                failed_requests, login_statuses = [], []
                page.on('requestfailed', lambda request: failed_requests.append(
                    (request.method, request.url, request.failure))
                    if request.url.startswith(application['api_url']) else None)
                page.on('response', lambda response: login_statuses.append(response.status)
                    if response.url == application['api_url'] + '/api/auth/login' else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/commercial')
                page.get_by_role('button', name='Nouveau devis', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouveau devis', exact=True)
                champ(modal, 'Date').fill(date.today().isoformat())
                modal.get_by_placeholder('Nom du client...').fill(nom)
                modal.get_by_text(nom, exact=True).click()
                modal.get_by_placeholder('Article ou description...').fill('Prestation fictive devis')
                editor = modal.locator('.hp-commercial-line-editor')
                editor.locator('input[type="number"]').nth(0).fill('2')
                editor.locator('input[type="number"]').nth(1).fill('100')
                modal.locator('summary').filter(has_text='Notes internes / commerciales').click()
                champ(modal, 'Notes', 'textarea').fill(initiale)
                with page.expect_response(lambda r: r.url.endswith('/api/devis') and r.request.method == 'POST') as creation:
                    modal.get_by_role('button', name='Créer le devis', exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                devis = creation.value.json()
                assert devis['notes'] == initiale and devis['total_ttc'] == 240
                modal.wait_for(state='hidden')
                row = page.locator('tbody tr').filter(has_text=devis['numero'])
                bouton = row.locator('button[title="Voir détail / note"]')
                bouton.focus()
                bouton.press('Enter')
                playwright.expect(page.get_by_text(initiale, exact=True)).to_be_visible()
                row.locator('button[title="Modifier"]').click()
                modal = page.get_by_role('dialog')
                playwright.expect(champ(modal, 'Notes', 'textarea')).to_have_value(initiale)
                champ(modal, 'Notes', 'textarea').fill(finale)
                with page.expect_response(lambda r: r.url.endswith(f'/api/devis/{devis["id"]}') and r.request.method == 'PATCH') as edition:
                    modal.get_by_role('button', name='Enregistrer', exact=True).click()
                assert edition.value.status == 200, edition.value.text()
                modal.wait_for(state='hidden')
                playwright.expect(page.get_by_text(finale, exact=True)).to_be_visible()
                playwright.expect(page.get_by_text(initiale, exact=True)).to_have_count(0)
                # Le devis accepté fige les notes documentaires du PDF.
                with page.expect_response(lambda r: r.url.endswith(f'/api/devis/{devis["id"]}') and r.request.method == 'PATCH') as acceptation:
                    row.locator('button[title="Marquer accepté"]').click()
                assert acceptation.value.status == 200, acceptation.value.text()
                page.reload()
                row = page.locator('tbody tr').filter(has_text=devis['numero'])
                row.locator('button[title="Voir détail / note"]').click()
                playwright.expect(page.get_by_text(finale, exact=True)).to_be_visible()
                with page.expect_download() as download:
                    row.locator('button[title="Télécharger PDF"]').click()
                fichier = tmp_path / f'devis-notes-{largeur}.pdf'
                download.value.save_as(str(fichier))
                assert download.value.failure() is None
                contenu = fichier.read_bytes()
                assert contenu.startswith(b'%PDF')
                texte = ' '.join(' '.join(page_pdf.extract_text() or '' for page_pdf in PdfReader(BytesIO(contenu)).pages).split())
                assert ' '.join(finale.split()) in texte, texte
                assert devis['numero'] in texte and '240,00' in texte
                page.get_by_role('button', name='Achat', exact=True).click()
                playwright.expect(page.get_by_role('button', name='Devis', exact=True)).to_have_count(0)
                playwright.expect(page.get_by_role('button', name='Bons de commande', exact=True)).to_be_visible()
                page.get_by_role('button', name='Vente', exact=True).click()
                row = page.locator('tbody tr').filter(has_text=devis['numero'])
                row.locator('button[title="Voir détail / note"]').click()
                playwright.expect(page.get_by_text(finale, exact=True)).to_be_visible()
                assert not errors, errors
                assert not server_errors, server_errors
                persisted = api.get(f'/api/devis?exercice={date.today().year}').json()
                assert next(d for d in persisted if d['id'] == devis['id'])['notes'] == finale
                with Session(application['engine']) as db:
                    piece = db.get(models.Devis, devis['id'])
                    assert piece.notes == piece.notes_snapshot == finale
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
            except Exception:
                print('Écran devis fictif :', page.url, page.locator('body').inner_text()[:7000])
                print('Erreurs :', errors, server_errors)
                print('Transport API / statuts connexion :', failed_requests, login_statuses)
                print('Serveur API actif :', all(process.poll() is None for process in application['processus']))
                raise
            finally:
                browser.close()
