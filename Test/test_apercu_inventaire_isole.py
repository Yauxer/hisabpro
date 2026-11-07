"""Aperçu d'inventaire sans mutation, parcours connecté et rôles sur nonce098."""
from contextlib import closing
from pathlib import Path
import httpx
import pytest
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ajustements_inventaire_isole import MODELES, donnees, exercice, photo
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


def calendrier(api):
    exercice(api, '2024-07-01', '2025-06-30')
    ok(api.patch('/api/exercices/2026', json={
        'date_debut': '2025-07-01', 'date_fin': '2026-06-30'}))


@pytest.mark.parametrize('type_,activite,contrepartie,debit,credit,reverse', MODELES)
def test_apercu_sans_creation_avec_montants_et_dates_exacts(application, type_, activite, contrepartie, debit, credit, reverse):
    with closing(client(application)[0]) as api:
        calendrier(api)
        sid = ok(api.get('/api/societe/moi'))['id']
        avant = photo(application, sid)
        a = ok(api.post('/api/cloture/ajustements/apercu?exercice=2025',
                        json=donnees(type_, activite, contrepartie)))
        assert photo(application, sid) == avant
        assert a['date'] == '2025-06-30' and a['exercice'] == 2025
        assert a['contrepassation_date'] == ('2025-07-01' if reverse else None)
        assert a['montant'] == '1200.13'
        assert [(l['compte'], l['debit'], l['credit']) for l in a['lignes']] == [
            (debit, '1200.13', '0.00'), (credit, '0.00', '1200.13')]


@pytest.mark.parametrize('role,largeur', [('admin', 1440), ('comptable', 390), ('lecture', 390)])
def test_assistant_apercu_et_actions_selon_role(application, role, largeur):
    playwright = pytest.importorskip('playwright.sync_api')
    admin, email, password = client(application)
    with closing(admin), playwright.sync_playwright() as p:
        calendrier(admin)
        ok(admin.post('/api/cloture/ajustements?exercice=2025',
                      json=donnees('provision_risque', '6195', '1518', montant='100')))
        sid = ok(admin.get('/api/societe/moi'))['id']
        if role != 'admin':
            email = email.replace('@', '-' + role + '@')
            ok(admin.post('/api/utilisateurs', json={'nom': 'Fictif inventaire555',
                'email': email, 'mot_de_passe': password, 'role': role}), 201)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            errors, servers = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/cloture', wait_until='domcontentloaded')
            page.get_by_label('Exercice actif', exact=True).select_option('2025')
            page.get_by_text('Provision pour risques et charges — Justificatif fictif inventaire553', exact=True).wait_for()
            bouton = page.get_by_role('button', name='Ajouter un ajustement', exact=True)
            avant = photo(application, sid)
            if role == 'lecture':
                playwright.expect(bouton).to_be_disabled()
                assert page.get_by_role('button', name="Supprimer l'ajustement", exact=True).count() == 0
                playwright.expect(page.get_by_role('button', name="Clôturer l'exercice 2025", exact=True)).to_be_disabled()
                with httpx.Client(base_url=application['api_url']) as lecteur:
                    lecteur.headers['Authorization'] = 'Bearer ' + ok(lecteur.post('/api/auth/login', json={
                        'email': email, 'password': password}))['access_token']
                    assert lecteur.post('/api/cloture/ajustements?exercice=2025', json=donnees()).status_code == 403
                    aid = ok(admin.get('/api/cloture/ajustements?exercice=2025'))[0]['id']
                    assert lecteur.delete(f'/api/cloture/ajustements/{aid}').status_code == 403
                assert photo(application, sid) == avant
            else:
                bouton.click()
                page.get_by_label('Montant HT / comptable (MAD)', exact=True).fill('1200.13')
                page.get_by_label('Libellé / justification', exact=True).fill('Assurance fictive555')
                creer = page.get_by_role('button', name='Créer l’écriture', exact=True)
                playwright.expect(creer).to_be_disabled()
                page.get_by_role('button', name='Vérifier l’écriture', exact=True).click()
                apercu = page.get_by_role('region', name="Aperçu de l'ajustement", exact=True)
                playwright.expect(apercu).to_contain_text('30/06/2025')
                playwright.expect(apercu).to_contain_text('01/07/2025')
                playwright.expect(apercu).to_contain_text('3491')
                montant_affiche = apercu.locator('tbody tr').first.locator('td').nth(1).inner_text()
                assert montant_affiche.replace('.', '').replace('\u202f', '').replace('\u00a0', '').replace(' ', '') == '1200,13'
                assert apercu.locator('table').locator('..').evaluate('(e) => e.scrollWidth <= e.clientWidth + 1')
                apercu.scroll_into_view_if_needed()
                page.screenshot(path=str(Path(__file__).resolve().parents[1] / '.codex-tests' / f'apercu555_{role}_{largeur}.png'))
                assert photo(application, sid) == avant
                # Un changement de montant invalide immédiatement l'ancien aperçu.
                page.get_by_label('Montant HT / comptable (MAD)', exact=True).fill('1300.13')
                playwright.expect(apercu).to_have_count(0)
                playwright.expect(creer).to_be_disabled()
                retards = []
                def retarder(route):
                    reponse = route.fetch()  # API réelle ; seule la livraison HTTP est différée.
                    assert reponse.status == 200
                    retards.append((route, reponse))
                    page.evaluate('window.__apercuRetarde = true')
                page.route('**/api/cloture/ajustements/apercu?*', retarder)
                page.get_by_role('button', name='Vérifier l’écriture', exact=True).click()
                page.wait_for_function('window.__apercuRetarde === true')
                page.get_by_label('Montant HT / comptable (MAD)', exact=True).fill('1400.13')
                with page.expect_response(lambda r: '/api/cloture/ajustements/apercu?' in r.url):
                    retards[0][0].fulfill(response=retards[0][1])
                page.unroute('**/api/cloture/ajustements/apercu?*', retarder)
                page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
                playwright.expect(apercu).to_have_count(0)
                playwright.expect(creer).to_be_disabled()
                page.get_by_role('button', name='Vérifier l’écriture', exact=True).click()
                playwright.expect(creer).to_be_enabled()
                with page.expect_response(lambda r: r.request.method == 'POST'
                    and '/api/cloture/ajustements?exercice=2025' in r.url) as resultat:
                    creer.click()
                assert resultat.value.status == 200, resultat.value.text()
                page.get_by_text("Charge constatée d'avance (CCA) — Assurance fictive555", exact=True).wait_for()
                assert ok(admin.get('/api/cloture/ajustements?exercice=2025'))[0]['montant'] == 1400.13
            assert not errors and not servers, (errors, servers)
            page.screenshot(path=str(Path(__file__).resolve().parents[1] / '.codex-tests' / f'inventaire555_{role}_{largeur}.png'), full_page=True)
        finally:
            browser.close()


def test_apercu_absent_ou_invalide_ne_prepare_pas_calendrier(application):
    with closing(client(application)[0]) as api:
        sid = ok(api.get('/api/societe/moi'))['id']
        avant = photo(application, sid)
        assert api.post('/api/cloture/ajustements/apercu?exercice=1901', json=donnees()).status_code == 404
        assert photo(application, sid) == avant
        calendrier(api)
        avant = photo(application, sid)
        for valeurs in [{'compte_contrepartie': '1111'}, {'montant': '1e1000'},
                        {'montant': 'NaN'}, {'libelle': ''}]:
            r = api.post('/api/cloture/ajustements/apercu?exercice=2025', json=donnees(**valeurs))
            assert r.status_code in (400, 422), r.text
            assert photo(application, sid) == avant
