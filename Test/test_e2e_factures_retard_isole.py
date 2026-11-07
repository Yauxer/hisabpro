"""Échéances calendaires et factures partiellement payées, application réelle isolée."""
from datetime import date, timedelta
import json
from pathlib import Path
import subprocess

import httpx
import pytest
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application
from test_e2e_recouvrement_isole import dossier_synthetique


@pytest.mark.parametrize('facture,attendu', [
    ({'date': '2026-10-06', 'delai_paiement': 0, 'statut': 'partiellement_payee'}, -1),
    ({'date': '2026-10-07', 'delai_paiement': 0}, 0),
    ({'date': '2026-01-01', 'delai_paiement': 60, 'date_echeance': '2026-10-08'}, 1),
    ({'date': '2026-02-30', 'delai_paiement': 0}, None),
    ({'date': '2026-10-06', 'statut': 'payee'}, None),
    ({'date': '2026-10-06', 'statut': 'annulee'}, None),
    ({'date': '2026-10-06', 'est_validee': False}, None),
    ({'date': '2026-10-06', 'est_proforma': True}, None),
    ({'date': '2026-10-06', 'date_echeance': 'invalide'}, None),
    ({'date': '2026-10-06', 'delai_paiement': -1}, None),
])
def test_echeance_calendaire_js(facture, attendu):
    script = """import {joursAvantEcheance,factureEnRetard} from './src/utils/echeancesFactures.js';
    const f=JSON.parse(process.argv[1]);const maintenant=new Date(2026,9,7,23,59);
    console.log(JSON.stringify([joursAvantEcheance(f,maintenant),factureEnRetard(f,maintenant)]));"""
    out = subprocess.run(['node', '--input-type=module', '-e', script, json.dumps(facture)],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == [attendu, attendu is not None and attendu < 0]


def test_retard_partiel_factures_et_dashboard_puis_solde(application):
    dossier = dossier_synthetique(application)
    with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer ' + dossier['token']}) as api:
        # Création distincte : aucune facture validée n'est réécrite pour préparer le test.
        response = api.get('/api/factures', params={'exercice': date.today().year})
        assert response.status_code == 200, response.text
        originale = response.json()[0]
        response = api.post('/api/factures', json={'type': 'vente', 'date': (date.today() - timedelta(days=2)).isoformat(),
            'tiers': dossier['nom'], 'tiers_id': originale['tiers_id'], 'delai_paiement': 60,
            'date_echeance': (date.today() - timedelta(days=1)).isoformat(),
            'lignes': [{'description': 'Service fictif échéance passée', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]})
        assert response.status_code == 201, response.text
        dossier['fid'] = response.json()['id']
        assert api.post(f"/api/factures/{dossier['fid']}/valider").status_code == 200
        response = api.post('/api/reglements', json={'facture_id': dossier['fid'], 'tiers': dossier['nom'],
            'date': date.today().isoformat(), 'montant': 400, 'mode': 'virement'})
        assert response.status_code == 201, response.text
        response = api.get('/api/factures', params={'exercice': date.today().year})
        assert response.status_code == 200
        assert next(f for f in response.json() if f['id'] == dossier['fid'])['statut'] == 'partiellement_payee'
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Edge/Chromium requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], dossier['email'], dossier['password'])
                page.goto(application['web_url'] + '/factures', wait_until='domcontentloaded')
                page.get_by_text('1 facture en retard de paiement', exact=True).wait_for()
                page.get_by_role('button', name='En retard', exact=True).click()
                playwright.expect(page.locator('tbody tr').filter(has_text=dossier['nom'])).to_have_count(1)
                page.goto(application['web_url'] + '/', wait_until='domcontentloaded')
                page.get_by_text('1 facture en retard de paiement', exact=True).wait_for()
                response = api.post('/api/reglements', json={'facture_id': dossier['fid'], 'tiers': dossier['nom'],
                    'date': date.today().isoformat(), 'montant': 800, 'mode': 'virement'})
                assert response.status_code == 201, response.text
                page.reload(wait_until='domcontentloaded')
                playwright.expect(page.get_by_text('1 facture en retard de paiement', exact=True)).to_have_count(0)
                page.goto(application['web_url'] + '/factures', wait_until='domcontentloaded')
                playwright.expect(page.locator('tbody tr').filter(has_text=dossier['nom'])).to_have_count(2)
                playwright.expect(page.get_by_text('1 facture en retard de paiement', exact=True)).to_have_count(0)
                page.get_by_role('button', name='En retard', exact=True).click()
                playwright.expect(page.locator('tbody tr').filter(has_text=dossier['nom'])).to_have_count(0)
                assert not errors, errors
                assert not server_errors, server_errors
            finally:
                browser.close()
