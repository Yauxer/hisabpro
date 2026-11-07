"""Simulation RAS TVA : API/Edge réels, données fictives sur PostgreSQL nonce098."""
from contextlib import closing
from pathlib import Path
import httpx
import pytest
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_ras_tva_simulation import donnees
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


def test_api_ras_tva_simule_sans_modifier_aucune_table_metier(application):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        avant = donnees_metier(application)
        a = ok(api.post('/api/tva/ras/simulation', json=donnees()))
        assert a['retenue_tva'] == '75.00' and a['net_apres_cette_ras_tva'] == '525.00'
        assert ok(autre.post('/api/tva/ras/simulation', json=donnees())) == a
        manque = ok(api.post('/api/tva/ras/simulation', json={}))
        assert manque['statut'] == 'a_completer' and manque['retenue_tva'] is None
        for kw in [{'tva_paiement': 'NaN'}, {'montant_paiement_ttc': True},
                   {'tva_paiement': 601}, {'prestation_liste_b': 'true'}, {'taux': 0}]:
            assert api.post('/api/tva/ras/simulation', json=donnees(**kw)).status_code == 422
        assert donnees_metier(application) == avant
        with httpx.Client(base_url=application['api_url']) as anonyme:
            assert anonyme.post('/api/tva/ras/simulation', json=donnees()).status_code == 401


@pytest.mark.parametrize('role,largeur', [('admin', 1440), ('comptable', 390), ('lecture', 390)])
def test_assistant_ras_tva_navigateur_trois_roles_sans_ecriture(application, role, largeur):
    playwright = pytest.importorskip('playwright.sync_api')
    api, email, password = client(application)
    with closing(api), playwright.sync_playwright() as p:
        if role != 'admin':
            email = email.replace('@', '-' + role + '@')
            ok(api.post('/api/utilisateurs', json={'nom': 'Simulation fiscale fictive559', 'email': email,
                'mot_de_passe': password, 'role': role}), 201)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            errors, servers = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/declaration-tva', wait_until='domcontentloaded')
            resume = page.get_by_text('Assistant RAS TVA · 2026', exact=True)
            resume.click()
            panel = resume.locator('..')
            bouton = panel.get_by_role('button', name='Simuler la RAS TVA', exact=True)
            avant = donnees_metier(application)
            bouton.click()
            resultat = panel.get_by_role('region', name='Résultat de la simulation RAS TVA', exact=True)
            playwright.expect(resultat).to_contain_text('Informations à compléter')
            assert resultat.locator('dl').count() == 0
            panel.get_by_label('Date réelle du paiement', exact=True).fill('2026-10-18')
            panel.get_by_label('Situation du payeur', exact=True).select_option('pm_privee_assujettie')
            panel.get_by_label('Situation du prestataire', exact=True).select_option('pp_assujettie')
            panel.get_by_label('Service relevant de la liste B', exact=True).select_option('oui')
            panel.get_by_label('Exclusions de l’article 117', exact=True).select_option('aucune_apres_controle')
            panel.get_by_label('Attestation de régularité fiscale', exact=True).select_option('presentee')
            panel.get_by_label('Date de délivrance de l’attestation', exact=True).fill('2026-09-01')
            panel.get_by_label('Référence de l’attestation', exact=True).fill('FICTIF-REGULARITE-559')
            panel.get_by_label('Quote-part TTC payée avant retenues (MAD)', exact=True).fill('600')
            tva = panel.get_by_label('TVA correspondant à cette quote-part (MAD)', exact=True)
            tva.fill('100')
            bouton.click()
            playwright.expect(resultat).to_contain_text('525,00 MAD')
            playwright.expect(resultat).to_contain_text('75,00 MAD')
            playwright.expect(resultat).to_contain_text('2026-11')
            # Une vraie réponse retenue après changement ne réaffiche pas le résultat ancien.
            tva.fill('60')
            playwright.expect(resultat).to_have_count(0)
            retards = []
            def retarder(route):
                reponse = route.fetch()
                assert reponse.status == 200
                retards.append((route, reponse))
                page.evaluate('window.__simulationRetardee = true')
            page.route('**/api/tva/ras/simulation', retarder)
            bouton.click()
            page.wait_for_function('window.__simulationRetardee === true')
            tva.fill('80')
            with page.expect_response(lambda r: r.url.endswith('/api/tva/ras/simulation')):
                retards[0][0].fulfill(response=retards[0][1])
            page.unroute('**/api/tva/ras/simulation', retarder)
            page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
            playwright.expect(resultat).to_have_count(0)
            bouton.click()
            playwright.expect(resultat).to_contain_text('540,00 MAD')
            resultat.scroll_into_view_if_needed()
            page.screenshot(path=str(Path(__file__).resolve().parents[1] / '.codex-tests' / f'ras_tva559_{role}_{largeur}.png'))
            page.emulate_media(media='print')
            playwright.expect(panel).to_be_hidden()
            page.emulate_media(media='screen')
            panel.get_by_label('Quote-part TTC payée avant retenues (MAD)', exact=True).fill('9999999999999999.99')
            tva.fill('1000000000000000.01')
            bouton.click()
            playwright.expect(resultat).to_contain_text('9.249.999.999.999.999,98 MAD')
            panel.get_by_label('Date de délivrance de l’attestation', exact=True).fill('2026-04-18')
            bouton.click()
            playwright.expect(resultat).to_contain_text('Informations à compléter')
            assert resultat.locator('dl').count() == 0
            panel.get_by_label('Situation du prestataire', exact=True).select_option('autre')
            bouton.click()
            playwright.expect(resultat).to_contain_text('Situation à examiner séparément')
            assert donnees_metier(application) == avant
            assert not errors and not servers, (errors, servers)
        finally:
            browser.close()
