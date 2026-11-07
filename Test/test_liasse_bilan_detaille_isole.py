"""Bilan détaillé partagé : exports réels et Edge/API/PG nonce."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import json
import subprocess
import uuid

import httpx
import pytest
from pypdf import PdfReader

from browser_support import chromium_executable
from services.bilan_presentation import lignes_bilan_detaille
from services.liasse_pdf import generer_liasse_pdf
from services.liasse_service import calculer_bilan, empreinte_liasse
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application
from test_patch09_3_liasse_fiscale import _dummy_liasse

ROOT = Path(__file__).resolve().parents[1]
SOLDES = {str(code): {'debit': montant, 'credit': 0} for code, montant in
          ((2311, 1000), (2321, 2000), (2331, 3000), (2341, 4000),
           (2351, 5000), (2381, 6000), (3111, 7000), (3421, 8000), (5141, 9000))}
SOLDES.update({'28321': {'debit': 0, 'credit': 300}, '1111': {'debit': 0, 'credit': 44700}})


def dossier_detaille():
    bilan = calculer_bilan(SOLDES, 0)
    data = _dummy_liasse()
    data['etats']['bilan'] = {**bilan, 'detail': {
        cote: lignes_bilan_detaille(bilan, SOLDES, calculer_bilan({}, 0), {}, cote, False)
        for cote in ('actif', 'passif')}}
    return data


def test_oracle_pdf_detail_sans_ventilation_arbitraire():
    data = dossier_detaille()
    before, digest = deepcopy(data), empreinte_liasse(data)
    assert data['etats']['bilan']['actif']['total'] == {'brut': 45000, 'amort_prov': 300, 'net': 44700}
    detail = data['etats']['bilan']['detail']['actif']
    assert next(r for r in detail if r.get('numero') == 'C')['valeurs'][:3] == [21000, 300, 20700]
    for code, montant in (('231', 1000), ('232', 2000), ('233', 3000), ('234', 4000), ('235', 5000), ('238', 6000)):
        assert next(r for r in detail if r.get('numero') == code)['valeurs'] == [montant, None, None, None]
    assert detail[-1]['valeurs'] == [45000, 300, 44700, None]
    texte = '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(generer_liasse_pdf(data))).pages)
    for code in ('231', '232', '233', '234', '235', '238'):
        assert next(r['label'] for r in detail if r.get('numero') == code) in texte
    assert '45 000.00' in texte and '44 700.00' in texte
    assert 'Sous-postes pour mémoire' in texte
    assert data == before and empreinte_liasse(data) == digest


def test_excel_detail_et_archive_ancienne_reels():
    script = r'''
const fs=require('fs'), assert=require('assert/strict'), XLSX=require('xlsx');
const numerotation=JSON.parse(fs.readFileSync('hisabpro-backend/services/liasse_numerotation_interne.json','utf8'));
const helper=fs.readFileSync('src/utils/liassePresentation.js','utf8').replace(/^import .*\n/,'').replaceAll('export ','');
const p=new Function('numerotation',helper+'; return {numeroTableau,referenceEtic,NOTE_NUMEROTATION};')(numerotation);
const source=fs.readFileSync('src/pages/LiasseFiscale.jsx','utf8');
const code=source.slice(source.indexOf('function flattenBilan(data, side)'),source.indexOf('export default function'));
const capture=require('./Test/liasse_xlsx_capture.cjs').capturerXlsx();
const fn=new Function('XLSX','numeroTableau','referenceEtic','NOTE_NUMEROTATION','telechargerXlsxAvecLogo',code+';return {exporterExcel,flattenBilan};')(XLSX,p.numeroTableau,p.referenceEtic,p.NOTE_NUMEROTATION,capture.telecharger);
const data=JSON.parse(fs.readFileSync(0,'utf8')), before=JSON.stringify(data);fn.exporterExcel(data);
const reloaded=XLSX.read(capture.lire(),{type:'array'});
const rows=XLSX.utils.sheet_to_json(reloaded.Sheets['T1 Bilan Actif'],{header:1,defval:null});
assert.deepEqual(rows.find(r=>r[0]==='232').slice(2),[2000,null,null,null]);
assert.deepEqual(rows.find(r=>r[1]==='TOTAL GÉNÉRAL ACTIF').slice(2),[45000,300,44700,null]);
assert.ok(rows.find(r=>r[0]==='232')[1].startsWith('    ')); assert.equal(JSON.stringify(data),before);
const old={etats:{bilan:{actif:{immobilise:[{code:'ancien',libelle:'Snapshot seul',brut:123,net:123,net_n1:null}]}}}};
const frozen=JSON.stringify(old);assert.equal(fn.flattenBilan(old,'actif').find(r=>r.code==='ancien').net,123);assert.equal(JSON.stringify(old),frozen);
console.log('OK détail Excel et ancien snapshot');
'''
    r = subprocess.run(['node', '-e', script], cwd=ROOT, input=json.dumps(dossier_detaille()),
                       capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert r.returncode == 0, r.stderr


def test_api_et_interface_bilan_detaille(application, tmp_path):
    suffixe = uuid.uuid4().hex[:10]
    email, password = suffixe + '@example.com', 'BilanDetail2026!'
    with httpx.Client(base_url=application['api_url'], timeout=30) as api:
        r = api.post('/api/auth/register', json={'nom': 'Bilan fictif', 'email': email,
            'password': password, 'raison_sociale': 'Bilan détaillé fictif ' + suffixe})
        assert r.status_code == 200, r.text
        api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        tiers = api.post('/api/tiers', json={'nom': 'Client fictif du bilan', 'type': 'client'})
        assert tiers.status_code == 201, tiers.text
        # Comptes réels du référentiel existant, sans ajouter de compte fictif.
        lignes = [{'compte': {'2341': '2340', '2381': '2380'}.get(compte, compte), **solde} for compte, solde in SOLDES.items()]
        next(l for l in lignes if l['compte'] == '3421')['tiers_id'] = tiers.json()['id']
        r = api.post('/api/ecritures', json={'date': '2026-01-01', 'journal': 'OD',
            'reference': 'BILAN-FICTIF', 'libelle': 'Bilan fictif indépendant', 'lignes': lignes})
        assert r.status_code == 201, r.text
        validation = api.post(f"/api/ecritures/{r.json()['id']}/valider")
        assert validation.status_code == 200, validation.text
        r = api.get('/api/etats/liasse/2026')
        assert r.status_code == 200, r.text
        data = r.json()
        assert data['etats']['bilan']['actif']['total'] == {'brut': 45000, 'amort_prov': 300, 'net': 44700}
        assert data['etats']['bilan']['detail']['actif'][-1]['valeurs'][:3] == [45000, 300, 44700]
        pdf = api.get('/api/etats/liasse/2026/pdf')
        assert pdf.status_code == 200
        assert 'Constructions' in '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(pdf.content)).pages)
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium/Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(accept_downloads=True)
                erreurs, serveur = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/liasse-fiscale')
                page.get_by_role('button', name='T1 · Bilan', exact=True).click()
                row = page.locator('tbody tr').filter(has_text='Constructions')
                row.wait_for()
                valeurs = row.locator('td').all_text_contents()[2:]
                assert valeurs[0].replace('.', '').replace(' ', '').replace('\u202f', '').replace('\u00a0', '') == '2000,00'
                assert valeurs[1:] == ['—', '—', '—']
                assert row.locator('td').nth(1).evaluate('(td)=>parseFloat(getComputedStyle(td).paddingLeft)') == 24
                assert page.get_by_text('Sous-postes pour mémoire', exact=False).count() == 1
                with page.expect_download() as download:
                    page.get_by_role('button', name='Excel', exact=True).click()
                target = tmp_path / 'liasse.xlsx'
                download.value.save_as(target)
                from openpyxl import load_workbook
                ws = load_workbook(target, data_only=True)['T1 Bilan Actif']
                assert next(tuple(r) for r in ws.values if r[0] == '232')[2:] == (2000, None, None, None)
                assert erreurs == [] and serveur == []
            finally:
                browser.close()
