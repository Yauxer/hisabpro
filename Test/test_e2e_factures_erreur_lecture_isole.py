"""Lecture qualifiée : deux pièces visibles, montants inconnus et reprise réelle."""
import pytest
from pathlib import Path
from sqlalchemy import text
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_articles_alertes_stock_historique_postgres import cible
from diagnostic_lecture_factures_historiques import preparer, photographie


def compteur(page, label):
    return page.locator('div[class*="kpiCard"]').filter(has=page.get_by_text(label, exact=True))


@pytest.mark.parametrize('largeur', [1365, 390])
@pytest.mark.parametrize('champ,valeur', [('prix_unitaire', float('nan')), ('prix_unitaire', float('inf')), ('quantite', None)],
                         ids=['nan', 'inf', 'quantite-null'])
def test_lecture_qualifiee_ne_signifie_pas_zero_et_reessayer_recharge(application, largeur, champ, valeur):
    api, email, password = client(application)
    try:
        sain, historique = preparer(application, api, champ, valeur)
        avant = photographie(application)
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/factures')
                pw.expect(page.get_by_role('alert').filter(has_text='Les indicateurs ne sont pas calculés')).to_be_visible()
                assert photographie(application) == avant
                pw.expect(compteur(page, 'En attente')).to_contain_text('—')
                pw.expect(compteur(page, 'En retard')).to_contain_text('—')
                pw.expect(page.get_by_text('Montants historiques à vérifier.', exact=False)).to_be_visible()
                pw.expect(page.locator('tbody tr').filter(has_text='Validation fictive')).to_have_count(2)
                historique_row = page.locator('tbody tr').filter(has=page.get_by_text(f'Brouillon #{historique}', exact=True))
                pw.expect(historique_row).to_contain_text('À vérifier')
                for titre in ('Modifier le brouillon', 'Valider définitivement'):
                    pw.expect(historique_row.locator(f'button[title="{titre}"]')).to_be_disabled()
                historique_row.click()
                modal = page.get_by_role('dialog')
                pw.expect(modal).to_contain_text('Les données sources sont conservées')
                pw.expect(modal).to_contain_text('Total TTC : À vérifier')
                if champ == 'prix_unitaire' and valeur != valeur:
                    dossier = Path(__file__).resolve().parents[1] / '.codex-tests'
                    dossier.mkdir(exist_ok=True)
                    page.screenshot(path=str(dossier / f'lecture363_detail_{largeur}.png'), full_page=True)
                # Fermer avec le contrôle réel du modal avant de relancer la lecture.
                page.keyboard.press('Escape')
                pw.expect(page.get_by_text('Aucune facture trouvée', exact=True)).to_have_count(0)
                pw.expect(page.get_by_role('button', name='Exporter CSV', exact=True)).to_be_disabled()
                # Seulement le jeu fictif nonce est remis àune valeur connue
                # afin de vérifier la reprise UI ; aucune réparation produit.
                cible(application)
                with application['engine'].begin() as db:
                    db.execute(text(f'UPDATE lignes_facture SET {champ}=:v WHERE facture_id=:id'),
                               {'v': 100 if champ == 'prix_unitaire' else 1, 'id': historique})
                apres_preparation = photographie(application)
                with page.expect_response(lambda r: '/api/factures?' in r.url and r.request.method == 'GET') as lecture:
                    page.get_by_role('button', name='Réessayer', exact=True).click()
                assert lecture.value.status == 200
                assert len(lecture.value.json()) == 2
                assert all(f['statut'] == 'en_attente' for f in lecture.value.json())
                pw.expect(page.locator('tbody tr').filter(has_text='Validation fictive')).to_have_count(2)
                pw.expect(page.get_by_role('button', name='Exporter CSV', exact=True)).to_be_enabled()
                pw.expect(compteur(page, 'En attente')).to_contain_text('2 factures')
                pw.expect(compteur(page, 'En retard')).to_contain_text('0 facture')
                pw.expect(page.get_by_role('alert').filter(has_text='Les indicateurs ne sont pas calculés')).to_have_count(0)
                assert photographie(application) == apres_preparation
            finally:
                browser.close()
    finally:
        api.close()


@pytest.mark.parametrize('largeur', [1365, 390])
def test_liste_vide_chargee_conserve_zero_et_export_disponible(application, largeur):
    api, email, password = client(application)
    try:
        avant = photographie(application)
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/factures')
                pw.expect(page.get_by_text('Aucune facture trouvée', exact=True)).to_be_visible()
                pw.expect(page.get_by_role('button', name='Exporter CSV', exact=True)).to_be_enabled()
                pw.expect(compteur(page, 'En attente')).to_contain_text('0 facture')
                pw.expect(compteur(page, 'En retard')).to_contain_text('0 facture')
                assert photographie(application) == avant
            finally:
                browser.close()
    finally:
        api.close()
