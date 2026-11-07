"""Navigation mobile réelle : largeur utile, menu, clavier et sources intactes."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Test'))
import pytest
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_e2e_administration_isole import connexion, observer
from test_validation_facture_montants_historiques_postgres import photographie
from browser_support import chromium_executable


@pytest.mark.parametrize('largeur',[390,767,768,1365])
def test_navigation_adaptee_clavier_et_route(application, largeur):
    api,email,password = client(application)
    try:
        avant = photographie(application)
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page = browser.new_page(viewport={'width':largeur,'height':1000})
                page.set_default_timeout(15000)
                erreurs,serveurs = observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/commercial')
                pw.expect(page.get_by_role('heading',name='Cycle commercial',exact=True)).to_be_visible()
                main = page.get_by_role('main')
                nav = page.get_by_role('complementary')
                bouton = page.get_by_role('button',name='Ouvrir la navigation',exact=True)
                if largeur <= 767:
                    assert main.bounding_box()['width'] >= largeur-1
                    pw.expect(nav).to_be_hidden()
                    pw.expect(bouton).to_be_visible()
                    bouton.click()
                    pw.expect(nav).to_be_visible()
                    pw.expect(bouton).to_have_attribute('aria-expanded','true')
                    fermer = page.get_by_role('button',name='Fermer le menu',exact=True)
                    pw.expect(fermer).to_be_focused()
                    page.keyboard.press('Shift+Tab')
                    pw.expect(page.get_by_role('button',name='Déconnexion',exact=True)).to_be_focused()
                    page.keyboard.press('Tab')
                    pw.expect(fermer).to_be_focused()
                    page.keyboard.press('Escape')
                    pw.expect(nav).to_be_hidden()
                    pw.expect(bouton).to_be_focused()
                    bouton.click()
                    page.get_by_role('link',name='Effets & Chèques',exact=True).click()
                    pw.expect(page).to_have_url(application['web_url']+'/effets')
                    pw.expect(nav).to_be_hidden()
                    pw.expect(page.get_by_role('heading',name='Effets & Chèques',exact=True)).to_be_visible()
                    limites = page.locator('select:has(option[value="actifs"])').evaluate('el => ({champ:el.getBoundingClientRect().right, carte:el.closest("[class*=card]").getBoundingClientRect().right})')
                    assert limites['champ'] <= limites['carte'] + 1, limites
                    bouton.click()
                    page.get_by_role('button',name='Fermer la navigation',exact=True).click(position={'x':largeur-15,'y':975})
                    pw.expect(nav).to_be_hidden()
                    bouton.click()
                    fermer.click()
                    pw.expect(nav).to_be_hidden()
                    # Captures après fin des animations, aucune promesse hors vue testée.
                    page.evaluate('() => Promise.all(document.getAnimations().filter(a=>Number.isFinite(a.effect.getTiming().iterations)).map(a=>a.finished))')
                    page.screenshot(path=str(Path(__file__).resolve().parents[1]/'.codex-tests'/f'navigation370_{largeur}.png'),full_page=True)
                else:
                    pw.expect(nav).to_be_visible()
                    pw.expect(bouton).to_be_hidden()
                    assert abs(nav.bounding_box()['width']-220) <= 1
                    assert main.bounding_box()['width'] >= largeur-221
                assert not erreurs and not serveurs,(erreurs,serveurs)
                assert photographie(application) == avant
            finally:
                browser.close()
    finally:
        api.close()
