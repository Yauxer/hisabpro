"""Vraie saisie fiscale sur copies comptables indépendantes, ordinateur et mobile."""
from contextlib import closing
import pytest
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import text
from fiscal947_support import (
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, copie, lire, reprise_provision, core, ok, D, preuve, ROOT,
)
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer


@pytest.mark.parametrize('variante', ['deficit', 'deduction'])
@pytest.mark.parametrize('largeur', [1440, 390])
def test_947_variante_documentee_interface_et_rechargement(application, variante, largeur):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        sid = copie(api, application, reprise=variante == 'deficit')
        if variante == 'deduction':
            reprise_provision(api)
        avant = core(application, sid)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1050})
            page.set_default_timeout(15000)
            errors, serveur = observer(page, application['api_url'])
            page.on('dialog', lambda d: d.accept())
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/cloture')
            page.get_by_label('Exercice actif', exact=True).select_option('2025')
            page.goto(application['web_url'] + '/fiscalite-is')
            if variante == 'deficit':
                form = page.locator('form').filter(has=page.get_by_placeholder('Origine / justificatif du solde', exact=True))
                form.get_by_label("Exercice d'origine", exact=True).fill('2024')
                form.get_by_label('Part ordinaire', exact=True).fill('10000')
                form.get_by_label('Part amortissements', exact=True).fill('2000')
                form.get_by_placeholder('Origine / justificatif du solde', exact=True).fill('DEF-2024 : attestation FICTIVE explicite HP-FIS-031')
                with page.expect_response(lambda r: r.url.endswith('/api/fiscalite/deficits') and r.request.method == 'POST') as ajout:
                    form.get_by_role('button', name='Ajouter un millésime antérieur', exact=True).click()
                d = ok(ajout.value)
                with page.expect_response(lambda r: r.url.endswith('/api/fiscalite/is/2025/deficits/confirmer-imputation') and r.request.method == 'POST') as confirmation:
                    page.get_by_role('button', name='Confirmer l’imputation', exact=True).click()
                ok(confirmation.value)
                attendu, impot, solde = D('121830'), D('21320.25'), '21.120,25'
            else:
                sans = lire(api)
                assert D(str(sans['calcul']['benefice_fiscal_imposable'])) == 134830
                assert D(str(sans['calcul']['deductions'])) == 0
                form = page.locator('form').filter(has=page.get_by_placeholder('Libellé du retraitement', exact=True))
                form.locator('select').first.select_option('deduction')
                form.locator('select').nth(1).select_option('reprises_provisions_taxees')
                form.get_by_placeholder('Libellé du retraitement', exact=True).fill('REC-REPRISE : provision antérieurement taxée, justificatif FICTIF HP-FIS-032')
                form.get_by_placeholder('Compte (optionnel)', exact=True).fill('71955')
                form.get_by_placeholder('Montant MAD', exact=True).fill('1000')
                with page.expect_response(lambda r: r.url.endswith('/api/fiscalite/is/2025/retraitements') and r.request.method == 'POST') as ajout:
                    form.get_by_role('button', name='Ajouter', exact=True).click()
                ok(ajout.value)
                attendu, impot, solde = D('133830'), D('23420.25'), '23.220,25'
            expect(page.locator('body')).to_contain_text(solde)
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('body')).to_contain_text(solde)
            v = lire(api)
            assert D(str(v['calcul']['benefice_fiscal_imposable'])) == attendu
            assert D(str(v['calcul']['is_theorique'])) == impot
            assert core(application, sid) == avant and not v['liquidation']['confirmee']
            if variante == 'deficit':
                assert v['deficits']['confirmation_a_jour']
                with application['engine'].connect() as db:
                    rows = db.execute(text('SELECT montant_ordinaire,montant_amortissements FROM fiscal_deficit_imputations WHERE societe_id=:s AND deficit_id=:d'), {'s': sid, 'd': d['id']}).all()
                assert rows == [(D('10000'), D('2000'))]
            assert not errors and not serveur, (errors, serveur)
            page.screenshot(path=str(ROOT/f'.codex-tests/fiscal947_{variante}_{largeur}.png'), full_page=True)
            preuve(f'{variante}_{largeur}', variante=variante, largeur=largeur,
                   nonce=application['cluster']['nonce'], situation=v, rechargement=True,
                   ecritures_inchangees=True, preconditions='Copie comptable48opérations préparée par API ;saisies fiscales par interface réelle.')
        finally:
            browser.close()
