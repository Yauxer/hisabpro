"""Navigateur -> vraie API -> PG isolé : aucun endpoint intercepté."""
from datetime import date
from io import BytesIO
import uuid
import httpx
import pytest
from pypdf import PdfReader
from openpyxl import load_workbook
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from e2e_isole_support import application_isolee
from test_e2e_administration_isole import connexion, observer


def test_preparation_conservee_rechargee_exports_et_zero_ecriture(tmp_path):
    playwright = pytest.importorskip('playwright.sync_api')
    executable = chromium_executable()
    if not executable:
        pytest.skip('Navigateur requis')
    suffix = uuid.uuid4().hex[:8]
    email, password = f'balance-{suffix}@example.com', 'RecetteBalance133!'
    with application_isolee() as app:
        with httpx.Client(base_url=app['api_url']) as api:
            r = api.post('/api/auth/register', json={'nom': 'Admin balance', 'email': email,
                'password': password, 'raison_sociale': 'Société fictive balance '+suffix})
            assert r.status_code == 200, r.text
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': 1366, 'height': 900}, accept_downloads=True)
                page.set_default_timeout(15000)
                errors, server_errors = observer(page, app['api_url'])
                connexion(page, app['web_url'], email, password)
                page.goto(app['web_url'] + '/liasse-fiscale')
                page.get_by_role('button', name='Importer N / N-1').click()
                page.get_by_label('Balance N', exact=True).set_input_files({'name': 'balance_n.csv',
                    'mimeType': 'text/csv', 'buffer': b'compte;debit;credit\n1111;0;100000\n5141;100000;0\n'})
                page.get_by_role('button', name='Contrôler et préparer').click()
                page.get_by_role('status').filter(has_text='Balances contrôlées').wait_for()
                page.get_by_role('button', name='Conserver une nouvelle version').click()
                page.get_by_text('Version 1 conservée', exact=False).wait_for()
                page.reload(); page.get_by_role('button', name='Importer N / N-1').click()
                options = page.get_by_label('Préparations conservées').locator('option')
                options.filter(has_text='Version 1').wait_for(state='attached')
                id = options.filter(has_text='Version 1').get_attribute('value')
                page.get_by_label('Préparations conservées').select_option(id)
                page.get_by_role('status').filter(has_text='Balances contrôlées').wait_for()
                assert page.get_by_label('Balance N', exact=True).input_value() == ''
                with page.expect_download() as pdf:
                    page.get_by_role('button', name='Exporter la préparation PDF').click()
                pdf_path = tmp_path / 'preparation.pdf'; pdf.value.save_as(pdf_path)
                texte = ' '.join(p.extract_text() for p in PdfReader(pdf_path).pages)
                assert '100 000,00' in texte and 'À compléter' in texte
                with page.expect_download() as excel:
                    page.get_by_role('button', name='Exporter la préparation Excel').click()
                excel_path = tmp_path / 'preparation.xlsx'; excel.value.save_as(excel_path)
                wb = load_workbook(excel_path, data_only=True)
                assert ('Total actif', 100000) in list(wb['Bilan N'].values)
                assert 'CPC N-1' not in wb.sheetnames
                assert not errors, errors
                assert not server_errors, server_errors
                with Session(app['engine']) as db:
                    row = db.get(models.LiasseBalancePreparation, int(id))
                    assert row.exercice == date.today().year and row.version == 1
                    assert row.contenu['preparation']['pret_a_deposer'] is False
                    assert db.query(models.Ecriture).count() == 0
                    assert db.query(models.LiasseFiscaleArchive).count() == 0
            finally:
                browser.close()
        processes = app['processus']; directory = app['cluster']['directory']
    assert all(proc.poll() is not None for proc in processes)
    assert not directory.exists()
