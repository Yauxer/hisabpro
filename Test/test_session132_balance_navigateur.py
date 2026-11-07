"""Import CSV/XLSX dans le composant React réel ; API synthétique interceptée."""
import json
from pathlib import Path
import subprocess
import pytest
from browser_support import chromium_executable
from services.balance_import_service import preparer_balance_liasse

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def bundle(tmp_path_factory):
    target = tmp_path_factory.mktemp('balance-react') / 'balance.js'
    js = '''const esbuild=require('esbuild'); esbuild.buildSync({stdin:{contents:`
    import React from 'react'; import {createRoot} from 'react-dom/client';
    import ImportBalanceLiasse from './src/components/ImportBalanceLiasse.jsx';
    import {ModulesProvider} from './src/data/ModulesContext.jsx';
    createRoot(document.getElementById('root')).render(<ModulesProvider><ImportBalanceLiasse exercice={2025}/></ModulesProvider>);`,
    loader:'jsx',resolveDir:process.cwd()},bundle:true,jsx:'automatic',format:'iife',platform:'browser',outfile:process.argv[1],
    define:{'import.meta.env.VITE_API_URL':'"http://recette.test"','import.meta.env.VITE_APP_VERSION':'"recette"'}});'''
    run = subprocess.run(['node', '-e', js, str(target)], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert run.returncode == 0, run.stderr
    return target.read_text(encoding='utf-8')


@pytest.fixture
def page_recette(bundle):
    playwright = pytest.importorskip('playwright.sync_api')
    executable = chromium_executable()
    if not executable:
        pytest.skip('Navigateur absent')
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 900}, accept_downloads=True)
            errors = []; calls = []
            page.on('pageerror', lambda exc: errors.append(str(exc)))
            def api(route):
                calls.append(route.request.post_data_json)
                data = route.request.post_data_json
                route.fulfill(json=preparer_balance_liasse(data['lignes_n'], data['lignes_n1'], {'1111', '5141'}))
            page.route('**/api/etats/liasse/balance/preview', api)
            page.route('**/api/societe/moi', lambda route: route.fulfill(json={'id':1,'raison_sociale':'Société fictive de balance'}))
            page.route('**/api/societe/modules', lambda route: route.fulfill(json={}))
            page.route('**/api/etats/liasse/balance/dossiers?exercice=*', lambda route: route.fulfill(json=[]))
            page.route('http://recette.test/', lambda r: r.fulfill(body='<div id="root"></div>', content_type='text/html'))
            page.goto('http://recette.test/')
            page.evaluate("localStorage.setItem('hisabpro_token','recette');localStorage.setItem('hisabpro_role','admin')")
            page.add_script_tag(content=bundle)
            page.get_by_role('button', name='Importer N / N-1').click()
            yield page, calls
            assert not errors
        finally:
            browser.close()


def fichier(page, body, name='balance.csv'):
    page.get_by_label('Balance N', exact=True).set_input_files({'name': name, 'mimeType': 'text/csv', 'buffer': body})


def test_import_csv_reel_et_n1_indisponible(page_recette):
    page, calls = page_recette
    fichier(page, b'compte;debit;credit\n1111;0;100\n5141;100;0\n')
    page.get_by_role('button', name='Contrôler et préparer').click()
    page.get_by_role('status').wait_for()
    assert calls == [{'lignes_n': [{'compte': '1111', 'debit': '0', 'credit': '100'},
                                {'compte': '5141', 'debit': '100', 'credit': '0'}], 'lignes_n1': None}]
    assert page.get_by_role('cell', name='Indisponible', exact=True).count() == 4
    assert page.evaluate('document.documentElement.scrollWidth') <= 390


@pytest.mark.parametrize('body', [b'compte;solde\n1111;100', b'compte;debit;credit;debit\n1111;0;100;0',
                                  b'compte;debit;credit;solde\n1111;0;100;100'])
def test_structure_csv_invalide_refusee_avant_api(page_recette, body):
    page, calls = page_recette
    fichier(page, body)
    page.get_by_role('button', name='Contrôler et préparer').click()
    page.get_by_role('alert').filter(has_text='En-têtes requis').wait_for()
    assert calls == []


def test_import_xlsx_reel(page_recette, tmp_path):
    from openpyxl import Workbook
    page, calls = page_recette
    path = tmp_path / 'balance.xlsx'
    wb = Workbook(); ws = wb.active
    ws.append(['compte', 'debit', 'credit']); ws.append(['1111', 0, 100]); ws.append(['5141', 100, 0]); wb.save(path)
    page.get_by_label('Balance N', exact=True).set_input_files(str(path))
    page.get_by_role('button', name='Contrôler et préparer').click()
    page.get_by_role('status').wait_for()
    assert calls[0]['lignes_n'][1] == {'compte': '5141', 'debit': 100, 'credit': 0}


def test_changement_fichier_invalide_ancienne_preparation(page_recette):
    page, _ = page_recette
    fichier(page, b'compte;debit;credit\n1111;0;100\n5141;100;0\n')
    page.get_by_role('button', name='Contrôler et préparer').click(); page.get_by_role('status').wait_for()
    fichier(page, b'compte;debit;credit\n1111;0;200\n5141;200;0\n')
    assert page.get_by_role('status').count() == 0


def test_reponse_en_vol_ne_republie_pas_balance_remplacee(page_recette):
    page, _ = page_recette
    pending = []
    page.route('**/api/etats/liasse/balance/preview', lambda route: pending.append(route))
    fichier(page, b'compte;debit;credit\n1111;0;100\n5141;100;0\n')
    with page.expect_request('**/api/etats/liasse/balance/preview'):
        page.get_by_role('button', name='Contrôler et préparer').click()
    fichier(page, b'compte;debit;credit\n1111;0;200\n5141;200;0\n')
    with page.expect_response('**/api/etats/liasse/balance/preview'):
        data = pending[0].request.post_data_json
        pending[0].fulfill(json=preparer_balance_liasse(data['lignes_n'], None, {'1111', '5141'}))
    from playwright.sync_api import expect
    expect(page.get_by_role('button', name='Contrôler et préparer')).to_be_enabled()
    assert page.get_by_role('status').count() == 0


def test_export_excel_reel_chiffres_et_limites(page_recette, tmp_path):
    from openpyxl import load_workbook
    page, _ = page_recette
    fichier(page, b'compte;debit;credit\n1111;0;100\n5141;100;0\n')
    page.get_by_label('Balance N-1 facultative').set_input_files({
        'name': 'balance_n1.csv', 'mimeType': 'text/csv',
        'buffer': b'compte;debit;credit\n1111;0;50\n5141;50;0\n'})
    page.get_by_role('button', name='Contrôler et préparer').click(); page.get_by_role('status').wait_for()
    with page.expect_download() as download:
        page.get_by_role('button', name='Exporter la préparation Excel').click()
    path = tmp_path / 'preparation.xlsx'; download.value.save_as(path)
    wb = load_workbook(path, data_only=True)
    assert set(wb.sheetnames) == {'Limites', 'CPC N', 'ESG N', 'Bilan N', 'CPC N-1', 'ESG N-1', 'Bilan N-1'}
    assert ('Total actif', 100) in list(wb['Bilan N'].values)
    assert ('Total passif', 50) in list(wb['Bilan N-1'].values)
    assert any('ETIC' in str(row) for row in wb['Limites'].values)


def test_conservation_et_rechargement_sans_fichier(page_recette):
    page, _ = page_recette
    row = {}
    def conserver(route):
        data = route.request.post_data_json
        assert data['exercice'] == 2025 and data['fichier_n'] == 'balance.csv'
        row.update(id=7, version=1, exercice=2025, created_at='2026-10-07T00:00:00', empreinte_sha256='f' * 64,
            contenu={'preparation': preparer_balance_liasse(data['lignes_n'], None, {'1111', '5141'}),
                     'periode': {'debut': '2025-01-01', 'fin': '2025-12-31'},
                     'sources': {'noms_fichiers': {'n': data['fichier_n']}}})
        route.fulfill(status=201, json=row)
    page.route('**/api/etats/liasse/balance/dossiers', conserver)
    page.route('**/api/etats/liasse/balance/dossiers?exercice=*', lambda route: route.fulfill(json=[{
        'id': 7, 'version': 1, 'created_at': '2026-10-07T00:00:00'}] if row else []))
    page.route('**/api/etats/liasse/balance/dossiers/7', lambda route: route.fulfill(json=row))
    def pdf(route):
        from types import SimpleNamespace
        from services.balance_preparation_pdf import generer_preparation_pdf
        route.fulfill(body=generer_preparation_pdf(row, SimpleNamespace(raison_sociale='Société fictive')),
            content_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="Preparation_2025.pdf"'})
    page.route('**/api/etats/liasse/balance/dossiers/7/pdf', pdf)
    fichier(page, b'compte;debit;credit\n1111;0;100\n5141;100;0\n')
    page.get_by_role('button', name='Contrôler et préparer').click(); page.get_by_role('status').wait_for()
    page.get_by_role('button', name='Conserver une nouvelle version').click()
    page.get_by_text('Version 1 conservée', exact=False).wait_for()
    assert page.get_by_label('Préparations conservées').input_value() == '7'
    assert page.evaluate('document.documentElement.scrollWidth') <= 390
    bundle = page.locator('script').last.text_content()
    page.reload(); page.add_script_tag(content=bundle)
    page.get_by_role('button', name='Importer N / N-1').click()
    page.get_by_label('Préparations conservées').select_option('7')
    page.get_by_role('status').wait_for()
    assert page.get_by_label('Balance N', exact=True).input_value() == ''
    assert page.get_by_role('button', name='Conserver une nouvelle version').count() == 0
    page.get_by_text('Sources déclarées : balance.csv').wait_for()
    with page.expect_download() as download:
        page.get_by_role('button', name='Exporter la préparation PDF').click()
    assert download.value.suggested_filename == 'Preparation_2025.pdf'
    assert download.value.path().read_bytes().startswith(b'%PDF-')


def test_lecture_consulte_versions_sans_action_ecriture(page_recette):
    page, _ = page_recette
    preview = preparer_balance_liasse([{'compte': '1111', 'credit': '100'}, {'compte': '5141', 'debit': '100'}], None, {'1111', '5141'})
    page.route('**/api/etats/liasse/balance/dossiers?exercice=*', lambda route: route.fulfill(json=[{'id': 7, 'version': 1}]))
    page.route('**/api/etats/liasse/balance/dossiers/7', lambda route: route.fulfill(json={
        'id': 7, 'version': 1, 'empreinte_sha256': 'a' * 64, 'contenu': {'preparation': preview}}))
    bundle = page.locator('script').last.text_content()
    page.evaluate("localStorage.setItem('hisabpro_role','lecture')")
    page.reload(); page.add_script_tag(content=bundle)
    page.get_by_role('button', name='Consulter les préparations').click()
    page.get_by_label('Préparations conservées').select_option('7'); page.get_by_role('status').wait_for()
    assert page.get_by_label('Balance N', exact=True).count() == 0
    assert page.get_by_role('button', name='Contrôler et préparer').count() == 0
    assert page.get_by_role('button', name='Conserver une nouvelle version').count() == 0
    assert page.get_by_role('button', name='Exporter la préparation Excel').count() == 1
