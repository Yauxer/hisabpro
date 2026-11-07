"""Diagnostic explicite, hors collecte globale : oracle lecture200, PostgreSQL nonce."""
from contextlib import closing
from datetime import date
import pytest
from sqlalchemy import text

from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_articles_alertes_stock_historique_postgres import cible
from test_validation_facture_montants_historiques_postgres import creer, photographie


def preparer(application, api, champ, valeur):
    sain = creer(api, 'vente', False, 100)
    historique = creer(api, 'vente', False, 100)
    cible(application)
    assert champ in {'prix_unitaire', 'quantite'}
    with application['engine'].begin() as db:
        db.execute(text(f'UPDATE lignes_facture SET {champ}=:val WHERE facture_id=:id'),
                   {'val': valeur, 'id': historique})
    return sain, historique


@pytest.mark.parametrize('champ,valeur', [
    ('prix_unitaire', 100), ('prix_unitaire', 0), ('prix_unitaire', float('nan')),
    ('prix_unitaire', float('inf')), ('prix_unitaire', float('-inf')),
    ('prix_unitaire', 1e308), ('quantite', None),
], ids=['sain', 'zero-explicite', 'nan', 'inf', 'moins-inf', 'depassement', 'quantite-null'])
def test_lecture_avec_source_historique_conserve_facture_saine(application, champ, valeur):
    with closing(client(application)[0]) as api:
        sain, historique = preparer(application, api, champ, valeur)
        avant = photographie(application)
        r = api.get('/api/factures', params={'exercice': date.today().year})
        assert photographie(application) == avant
        print('Diagnostic GET factures :champ', champ, 'source', repr(valeur),
              'statut', r.status_code, 'base inchangee', True)
        assert r.status_code == 200, 'Lecture attendue200, obtenue'+str(r.status_code)
        rows = {f['id']: f for f in r.json()}
        assert sain in rows and historique in rows
        assert (rows[sain]['total_ht'], rows[sain]['total_tva'], rows[sain]['total_ttc']) == (100, 20, 120)
        if champ == 'prix_unitaire' and valeur == 0:
            assert rows[historique]['total_ttc'] == 0


def test_ui_facture_saine_reste_visible_avec_prix_nan(application):
    api, email, password = client(application)
    try:
        sain, historique = preparer(application, api, 'prix_unitaire', float('nan'))
        avant = photographie(application)
        with application['engine'].connect() as db:
            nom = db.execute(text('SELECT tiers FROM factures WHERE id=:id'), {'id': sain}).scalar_one()
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': 1365, 'height': 1000})
                page.set_default_timeout(15000)
                errors, server = observer(page, application['api_url'])
                reponses, echecs = [], []
                page.on('response', lambda r: reponses.append(r.status) if '/api/factures?' in r.url else None)
                page.on('requestfailed', lambda r: echecs.append((r.method, r.url, r.failure)) if '/api/factures?' in r.url else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/factures')
                row = page.locator('tbody tr').filter(has_text=nom)
                alerte = page.get_by_role('alert').filter(has_text='Les indicateurs ne sont pas calculés')
                pw.expect(row.or_(alerte).first).to_be_visible()
                assert photographie(application) == avant
                print('Diagnostic Edge :reponses', reponses, 'echecs reseau', echecs,
                      'lignes facture saine', row.count(), 'base inchangee', True,
                      'erreursJS', len(errors), 'erreursAPI', len(server))
                pw.expect(row).to_have_count(1)
            finally:
                browser.close()
    finally:
        api.close()
