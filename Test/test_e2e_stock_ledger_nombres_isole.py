"""Audit CMUP : navigateur connecté et PostgreSQL nonce, conservation des sources."""
import pytest
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_stock_ledger_nombres_historique import application, dossier, photo


@pytest.mark.parametrize('largeur', [1365, 390])
def test_ledger_inconnu_visible_filtrable_sans_mutation(application, dossier, largeur):
    api,sid,suffix,email,password,ids = dossier
    avant = photo(application, sid)
    playwright = pytest.importorskip('playwright.sync_api')
    executable = chromium_executable()
    if not executable:
        pytest.skip('Edge/Chromium requis')
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        page = browser.new_page(viewport={'width': largeur, 'height': 1000})
        page.set_default_timeout(20000)
        errors, server_errors = observer(page, application['api_url'])
        mutations = []
        page.on('request', lambda r: mutations.append(r.url) if
            '/api/inventaire/' in r.url and r.method in {'POST','PATCH','DELETE','PUT'} else None)
        try:
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/inventaire')
            with page.expect_response(lambda r: '/api/inventaire/controle-mouvements' in r.url) as req:
                page.get_by_role('button', name='Mouvements & CMUP', exact=True).click()
            assert req.value.status == 200
            assert req.value.json()['valeur_stock'] is None
            playwright.expect(page.get_by_role('alert')).to_contain_text('Audit incomplet')
            table = page.locator('table').filter(has=page.get_by_role('columnheader', name='Diagnostic', exact=True))
            playwright.expect(table.locator('tbody tr')).to_have_count(4)
            row = table.locator('tbody tr').filter(has_text='INCONNU fictif '+suffix)
            playwright.expect(row.locator('td').nth(2)).to_have_text('À vérifier')
            playwright.expect(row.locator('td').nth(3)).to_have_text('À vérifier')
            sain = table.locator('tbody tr').filter(has_text='SAIN fictif '+suffix)
            playwright.expect(sain.locator('td').nth(2)).to_have_text('6')
            playwright.expect(sain.locator('td').nth(5)).to_have_text('OK')
            cout = table.locator('tbody tr').filter(has_text='COUT fictif '+suffix)
            playwright.expect(cout).to_contain_text('cout_unitaire')
            with page.expect_response(lambda r: '/api/inventaire/controle-mouvements' in r.url) as filtre:
                page.get_by_role('checkbox', name='Afficher uniquement les anomalies').check()
            assert filtre.value.status == 200 and filtre.value.json()['articles_controles'] == 4
            playwright.expect(table.locator('tbody tr')).to_have_count(3)
            playwright.expect(sain).to_have_count(0)
            with page.expect_response(lambda r: '/api/inventaire/controle-mouvements' in r.url) as reload:
                page.get_by_role('button', name='Recontrôler', exact=True).click()
            assert reload.value.status == 200
            playwright.expect(table.locator('tbody tr')).to_have_count(3)
            assert photo(application, sid) == avant
            assert not errors and not server_errors and not mutations, (errors,server_errors,mutations)
        except Exception:
            print('Ledger UI:',page.url,page.locator('body').inner_text()[:9000])
            print('Erreurs:',errors,server_errors,mutations)
            raise
        finally:
            browser.close()
