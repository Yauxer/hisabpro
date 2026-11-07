"""Lot UX 967 : bloc « À faire », libellés visibles, navigation TVA. Vraie UI/API/PG nonce, données fictives."""
from datetime import date

import pytest

from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application  # noqa: F401
from test_ras_lecture_conservation import client
from test_e2e_ras_capture_isole import ok


@pytest.mark.parametrize('largeur,hauteur', [(1366, 768), (390, 844)])
def test_967_a_faire_libelles_et_navigation_tva(application, largeur, hauteur):
    api, email, password = client(application)
    jour = date.today().isoformat()
    try:
        tiers = ok(api.post('/api/tiers', json={'nom': 'Client UX967 fictif', 'type': 'client'}), 201)
        f = ok(api.post('/api/factures', json={'type': 'vente', 'tiers': tiers['nom'], 'tiers_id': tiers['id'], 'date': jour,
            'ras_taux': 0, 'lignes': [{'description': 'Service UX967', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
        ok(api.post(f"/api/factures/{f['id']}/valider"))
        ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))  # écriture laissée en brouillon
        ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': tiers['nom'], 'date': jour, 'montant': 1200,
            'mode': 'cheque', 'reference': 'CHQ-UX967', 'comptabiliser': True}), 201)
    finally:
        api.close()
    pw = pytest.importorskip('playwright.sync_api')
    with pw.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': hauteur}); page.set_default_timeout(20000)
            dialogues = []
            page.on('dialog', lambda d: (dialogues.append(d.message), d.dismiss()))
            erreurs, serveur = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/dashboard')
            bloc = page.get_by_role('region', name='À faire')
            pw.expect(bloc).to_contain_text('écriture(s) en brouillon à valider')
            pw.expect(bloc).to_contain_text('chèque(s)/effet(s) à remettre ou à encaisser')
            bloc.get_by_role('link').filter(has_text='brouillon').click()
            page.wait_for_url('**/journal')
            # Effets : l'action porte un libellé visible, le nom accessible reste l'info-bulle.
            page.goto(application['web_url'] + '/effets')
            ligne = page.locator('tbody tr').filter(has_text='CHQ-UX967')
            bouton = ligne.get_by_role('button', name="Confirmer l'encaissement", exact=True)
            pw.expect(bouton.locator('.libelle-action')).to_be_visible()
            pw.expect(bouton.locator('.libelle-action')).to_have_text('Encaisser')
            # TVA : navigation interne vers chaque section, rien n'est masqué.
            page.goto(application['web_url'] + '/declaration-tva')
            nav = page.get_by_role('navigation', name='Sections de la déclaration TVA')
            for libelle in ('Déclaration', 'Dépôt', 'RAS TVA', 'Paramètres'):
                pw.expect(nav.get_by_role('link', name=libelle, exact=True)).to_be_visible()
            nav.get_by_role('link', name='Paramètres', exact=True).click()
            pw.expect(page.locator('#tva-parametres')).to_be_in_viewport()
            assert page.get_by_role('button', name='Télédéclaration DGI — à venir').count() == 0
            assert page.evaluate('document.documentElement.scrollWidth - window.innerWidth') <= 1
            assert not dialogues and not erreurs and not serveur, (dialogues, erreurs, serveur)
        finally:
            browser.close()
