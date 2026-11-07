"""Date d'opération du relevé : Edge et PostgreSQL nonce, aucune interception API."""
from datetime import date
import pytest
from sqlalchemy import text
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application
from test_e2e_grandlivre_dates_contexte_isole import preparer, photographie


@pytest.mark.parametrize('largeur', [1365, 390])
@pytest.mark.parametrize('zone,heure', [('Europe/Paris', 0), ('America/New_York', 23)])
def test_date_releve_manuelle_locale_et_ecritures_preservees(application, largeur, zone, heure):
    api, email, password, annee, sid = preparer(application)
    jour = date.today()
    avant = photographie(application)
    try:
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000}, timezone_id=zone)
                page.set_default_timeout(15000)
                errors, server = observer(page, application['api_url'])
                page.add_init_script(f'''
                    const NativeDate = Date;
                    const now = new NativeDate({jour.year},{jour.month-1},{jour.day},{heure},30).getTime();
                    window.Date = class extends NativeDate {{
                        constructor(...args) {{ super(...(args.length ? args : [now])); }}
                        static now() {{ return now; }}
                    }};
                ''')
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/rapprochement')
                assert page.evaluate('new Date().toISOString().slice(0,10)') != jour.isoformat()
                field = page.locator('input[type=date]').nth(2)
                pw.expect(field).to_have_value(jour.isoformat())
                libelle = f'RELEVE-DATE-LOCALE-{sid}'
                page.get_by_placeholder('Libellé…', exact=True).fill(libelle)
                page.get_by_placeholder('Montant', exact=True).fill('40')
                with page.expect_response(lambda r: r.url == application['api_url']+'/api/rapprochement' and r.request.method == 'POST') as response:
                    page.get_by_title("Ajouter l'opération", exact=True).click()
                assert response.value.status == 201, response.value.text()
                data = response.value.json()
                assert data['date'] == jour.isoformat() and data['montant'] == 40
                pw.expect(page.locator('tbody tr').filter(has_text=libelle)).to_have_count(1)
                assert not errors and not server, (errors, server)
                with application['engine'].connect() as db:
                    line = db.execute(text('SELECT date,montant,compte FROM rapprochement_lignes WHERE id=:id AND societe_id=:sid'), {'id':data['id'],'sid':sid}).one()
                assert line.date == jour and line.montant == 40 and line.compte == '5141'
                assert photographie(application) == avant
            finally:
                browser.close()
    finally:
        api.close()


@pytest.mark.parametrize('largeur', [1365, 390])
def test_date_saisie_conservee_a_arrivee_tardive_exercice(application, largeur):
    api, email, password, annee, sid = preparer(application)
    try:
        avant = photographie(application)
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                errors, server = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                retenues = []
                def retenir(route):
                    response = route.fetch()
                    assert response.status == 200
                    retenues.append((route, response))
                    page.evaluate('window.__contexteDateBanqueRetenu=true')
                page.route('**/api/exercices', retenir)
                page.goto(application['web_url']+'/rapprochement', wait_until='domcontentloaded')
                page.wait_for_function('window.__contexteDateBanqueRetenu===true')
                field = page.locator('input[type=date]').nth(2)
                choisie = f'{annee}-03-17'
                field.fill(choisie)
                page.unroute('**/api/exercices', retenir)
                with page.expect_response(lambda r: r.url.endswith('/api/exercices')):
                    for route, response in retenues:
                        route.fulfill(response=response)
                pw.expect(page.locator('select').filter(has=page.locator(f'option[value="{annee}"]')).first).to_be_enabled()
                page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                pw.expect(field).to_have_value(choisie)
                assert not errors and not server, (errors, server)
                assert photographie(application) == avant
            finally:
                browser.close()
    finally:
        api.close()


@pytest.mark.parametrize('decalage', [-1, 1], ids=['exercice-passe', 'exercice-futur'])
def test_date_proposee_dans_bornes_exercice_selectionne(application, decalage):
    api, email, password, annee, sid = preparer(application)
    try:
        cible_annee = annee+decalage
        debut, fin = f'{cible_annee}-04-01', f'{cible_annee}-09-30'
        r = api.post('/api/exercices', json={'annee': cible_annee, 'date_debut': debut, 'date_fin': fin})
        assert r.status_code == 201, r.text
        avant = photographie(application)
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(15000)
                errors, server = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/rapprochement')
                choix = page.locator('select').filter(has=page.locator(f'option[value="{cible_annee}"]')).first
                pw.expect(choix).to_be_enabled()
                choix.select_option(str(cible_annee))
                pw.expect(page.locator('input[type=date]').nth(0)).to_have_value(debut)
                pw.expect(page.locator('input[type=date]').nth(1)).to_have_value(fin)
                field = page.locator('input[type=date]').nth(2)
                pw.expect(field).to_have_value(fin if decalage < 0 else debut)
                assert debut <= field.input_value() <= fin
                assert not errors and not server, (errors, server)
                assert photographie(application) == avant
            finally:
                browser.close()
    finally:
        api.close()
