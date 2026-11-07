"""Refus réel de facturation BR historique : Edge -> API -> PG nonce."""
from contextlib import closing
from datetime import date
import pytest
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_mutations_stock_historique_postgres import article
from test_conversion_bon_prix_historique_postgres import bon, modifier_prix, photographie


@pytest.mark.parametrize('largeur', [1365, 390])
def test_refus_prix_br_historique_visible_sans_creation(application, largeur):
    pw = pytest.importorskip('playwright.sync_api')
    executable = chromium_executable()
    if not executable:
        pytest.skip('Navigateur Chromium/Edge indisponible')
    api, email, password = client(application)
    with closing(api):
        aid, _ = article(application, api)
        bid = bon(api, 'achat', aid)
        for statut in ('expedie', 'livre'):
            transition = api.patch(f'/api/bons-reception/{bid}', json={'statut': statut})
            assert transition.status_code == 200, transition.text
        liste = api.get('/api/bons-reception', params={'exercice': date.today().year})
        assert liste.status_code == 200, liste.text
        br = next(x for x in liste.json() if x['id'] == bid)
        modifier_prix(application, aid, 'achat', None)
        avant = photographie(application)
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            erreurs, serveurs = observer(page, application['api_url'])
            dialogues = []
            def relever_dialogue(dialogue):
                dialogues.append((dialogue.type, dialogue.message))
                dialogue.dismiss()
            page.on('dialog', relever_dialogue)
            try:
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/commercial')
                page.get_by_role('button', name='Achat', exact=True).click()
                page.get_by_role('button', name='Bons de réception', exact=True).click()
                row = page.locator('tbody tr').filter(has_text=br['numero'])
                row.get_by_title('Créer la facture fournisseur depuis ce bon de réception', exact=True).click()
                modal = page.get_by_role('dialog', name='Facturer le bon de réception '+br['numero'], exact=True)
                endpoint = f'/api/bons-livraison/{bid}/convertir-facture'
                with page.expect_response(lambda r: r.url.endswith(endpoint) and r.request.method == 'POST') as reponse:
                    modal.get_by_role('button', name='Créer la facture en brouillon', exact=True).click()
                assert reponse.value.status == 409, reponse.value.text()
                pw.expect(modal).to_be_visible()
                pw.expect(modal.get_by_role('button', name='Créer la facture en brouillon', exact=True)).to_be_enabled()
                # 967 : le refus s'affiche en notification d'erreur, sans dialogue natif.
                pw.expect(page.locator('[data-notification="erreur"]')).to_contain_text('Prix historique absent ou non fini')
                assert not dialogues, dialogues
                assert photographie(application) == avant
                assert not erreurs and not serveurs, (erreurs, serveurs)
            finally:
                browser.close()
