"""Soldes historiques indéterminés : lecture Edge/API/CSV, PG exclusivement nonce."""
import csv
from datetime import date
import uuid

import httpx
import pytest
from sqlalchemy import text

from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def snapshot(application, sid):
    with application['engine'].connect() as db:
        result = {table: db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t WHERE societe_id=:sid ORDER BY id'),
            {'sid': sid}).scalars().all() for table in ('factures', 'reglements', 'ecritures')}
        result['lignes_ecriture'] = db.execute(text('SELECT row_to_json(t)::text FROM lignes_ecriture t JOIN ecritures e ON e.id=t.ecriture_id WHERE e.societe_id=:sid ORDER BY t.id'), {'sid': sid}).scalars().all()
        return result


@pytest.mark.parametrize('largeur', [1365, 390])
def test_recouvrement_inconnu_visible_sans_zero_ni_mutation(application, tmp_path, largeur):
    suffixe = uuid.uuid4().hex[:10]
    email, password = suffixe+'@example.com', 'RecouvrementFictif2026!'
    annee = date.today().year
    with httpx.Client(base_url=application['api_url'], timeout=30) as api:
        r = api.post('/api/auth/register', json={'nom': 'Admin fictif', 'email': email,
            'password': password, 'raison_sociale': 'Recouvrement fictif '+suffixe})
        assert r.status_code == 200, r.text
        api.headers['Authorization'] = 'Bearer '+r.json()['access_token']
        sid = api.get('/api/societe/moi').json()['id']
        r = api.post('/api/tiers', json={'nom': 'CLIENT FICTIF '+suffixe, 'type': 'client'})
        assert r.status_code == 201, r.text
        tiers = r.json()
        factures = []
        for historique in (False, True):
            r = api.post('/api/factures', json={'type': 'vente', 'date': f'{annee}-03-15',
                'tiers': tiers['nom'], 'tiers_id': tiers['id'], 'ras_taux': 10,
                'lignes': [{'description': 'Service laboratoire', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]})
            assert r.status_code == 201, r.text
            f = r.json()
            if historique:
                # Altération d'un brouillon fictif seulement, avant passage
                # simultané à l'état validé ; les protections réelles restent actives.
                with application['engine'].begin() as db:
                    db.execute(text("UPDATE factures SET ras_taux='NaN'::float8, numero=:n, est_validee=true WHERE id=:id AND est_validee=false"),
                        {'n': 'LEGACY-INCONNU-'+suffixe, 'id': f['id']})
                f['numero'] = 'LEGACY-INCONNU-'+suffixe
            else:
                r = api.post(f"/api/factures/{f['id']}/valider")
                assert r.status_code == 200, r.text
                f['numero'] = r.json()['numero']
            factures.append(f)
        situation = api.get('/api/recouvrement/situation', params={'exercice': annee})
        assert situation.status_code == 200, situation.text
        data = situation.json()
        inconnue = next(f for f in data['factures'] if f['id'] == factures[1]['id'])
        assert inconnue['reste_du'] is None and inconnue['total_impute'] is None and inconnue['ras_anomalie']
        assert data['resume']['vente']['calcul_incomplet'] and data['resume']['position_nette'] is None
        assert next(f for f in data['factures'] if f['id'] == factures[0]['id'])['reste_du'] == 1200
        avant = snapshot(application, sid)
        # Même année, autre société : aucune pièce étrangère accessible.
        with httpx.Client(base_url=application['api_url'], timeout=30) as autre:
            r = autre.post('/api/auth/register', json={'nom': 'Autre administrateur fictif',
                'email': 'autre'+suffixe+'@example.com', 'password': password, 'raison_sociale': 'AUTRE '+suffixe})
            assert r.status_code == 200, r.text
            autre.headers['Authorization'] = 'Bearer '+r.json()['access_token']
            r = autre.get('/api/recouvrement/situation', params={'exercice': annee})
            assert r.status_code == 200 and r.json()['factures'] == [], r.text
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable: pytest.skip('Edge/Chromium requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                errors, server = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/situation', wait_until='domcontentloaded')
                page.get_by_text('Taux de règlement commercial', exact=True).wait_for()
                kpi = page.get_by_text('Taux de règlement commercial', exact=True).locator('..')
                playwright.expect(kpi).to_contain_text('À vérifier')
                assert '0.0 %' not in kpi.inner_text()
                page.get_by_role('button', name='Échéances & impayés', exact=True).click()
                ligne = page.get_by_role('row').filter(has_text=factures[1]['numero'])
                playwright.expect(ligne).to_be_visible()
                assert ligne.inner_text().count('À vérifier') >= 3
                assert 'RAS historique invalide' in ligne.inner_text()
                assert ligne.get_by_role('button', name='Relancer').count() == 0
                normale = page.get_by_role('row').filter(has_text=factures[0]['numero'])
                playwright.expect(normale).to_be_visible()
                assert '1' in normale.locator('td').nth(5).inner_text() and '200' in normale.locator('td').nth(5).inner_text()
                with page.expect_download() as dl:
                    page.get_by_role('button', name='Exporter', exact=True).click()
                fichier = tmp_path/f'echeances-{largeur}.csv'
                dl.value.save_as(fichier)
                with fichier.open(encoding='utf-8-sig', newline='') as f:
                    rows = list(csv.DictReader(f, delimiter=';'))
                row = next(r for r in rows if r['Facture'] == factures[1]['numero'])
                assert row['Imputé'] == row['Reste dû'] == 'À vérifier'
                assert row['Statut'] == 'À vérifier' and 'RAS historique invalide' in row['Diagnostic']
                assert next(r for r in rows if r['Facture'] == factures[0]['numero'])['Reste dû'] == '1200,00'
                page.get_by_role('button', name='Balance âgée', exact=True).click()
                bloc = page.get_by_text('Balance âgée clients', exact=True).locator('..').locator('..')
                playwright.expect(bloc).to_contain_text('À vérifier')
                assert not errors and not server, (errors, server)
            finally:
                browser.close()
        assert snapshot(application, sid) == avant
