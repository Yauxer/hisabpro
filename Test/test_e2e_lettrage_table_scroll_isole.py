"""Sélection et lettrage natifs quand les filtres/barres occupent la hauteur."""
from datetime import date
from decimal import Decimal
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ


def originaux(app, sid):
    with Session(app['engine']) as db:
        ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).order_by(models.Ecriture.id).all()
        return tuple((e.id, e.date, e.journal, e.reference, e.libelle, e.est_validee, e.date_validation,
            tuple((l.id, l.compte, l.debit, l.credit, l.tiers_id, l.compte_auxiliaire_snapshot)
                  for l in sorted(e.lignes, key=lambda l: l.id))) for e in ecritures)


def geometrie(page):
    return page.locator('table').locator('..').evaluate('e => ({height:e.clientHeight,header:e.querySelector("thead").getBoundingClientRect().height,scrollHeight:e.scrollHeight})')


@pytest.mark.parametrize('largeur,hauteur', [(390, 1000), (1365, 600), (1365, 1000)])
def test_lettrage_hauteur_apres_selection_clic_natif_et_originaux(application, largeur, hauteur):
    suffix = uuid.uuid4().hex[:8]
    nom = 'Fournisseur sélection fictif ' + suffix
    email, password = 'lettrage-scroll-' + suffix + '@example.com', 'LettrageScrollFictif!'
    with httpx.Client(base_url=application['api_url']) as api:
        reg = api.post('/api/auth/register', json={'nom': 'Admin sélection fictive', 'email': email,
                'password': password, 'raison_sociale': 'Sélection fictive ' + suffix})
        assert reg.status_code == 200, reg.text
        api.headers['Authorization'] = 'Bearer ' + reg.json()['access_token']
        sid = api.get('/api/societe/moi').json()['id']
        tiers = api.post('/api/tiers', json={'nom': nom, 'type': 'fournisseur', 'compte_fournisseur': '4411'})
        assert tiers.status_code == 201, tiers.text
        tid = tiers.json()['id']
        # Trois écritures synthétiques équilibrées, pas une facture réelle.
        for index, (debit, credit) in enumerate([(0, 1200), (400, 0), (800, 0)], start=1):
            r = api.post('/api/ecritures', json={'date': date.today().isoformat(), 'journal': 'OD',
                'reference': f'SCROLL-FICTIF-{suffix}-{index}', 'libelle': f'Sélection fictive {index}',
                'est_validee': True, 'lignes': [
                    {'compte': '4411', 'tiers_id': tid, 'libelle': nom, 'debit': debit, 'credit': credit},
                    {'compte': '5141', 'libelle': 'Contrepartie fictive', 'debit': credit, 'credit': debit}]})
            assert r.status_code == 201, r.text
        avant = originaux(application, sid)
        assert len(avant) == 3 and all(e[5] for e in avant)
        executable = chromium_executable()
        if not executable:
            pytest.skip('Microsoft Edge / Chromium requis')
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': hauteur})
                page.set_default_timeout(15000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/lettrage')
                champ(page, 'Compte', 'select').select_option('4411')
                champ(page, 'Tiers', 'select').select_option(label=nom)
                cases = page.locator('tbody input[type="checkbox"]')
                playwright.expect(cases).to_have_count(3)
                avant_selection = geometrie(page)
                print('Hauteur avant sélection', largeur, hauteur, avant_selection)
                assert avant_selection['height'] > avant_selection['header']
                cases.nth(0).check()
                apres_selection = geometrie(page)
                print('Hauteur après sélection', largeur, hauteur, apres_selection)
                assert apres_selection['height'] > apres_selection['header']
                cases.nth(1).check()
                cases.nth(2).check()
                playwright.expect(page.get_by_text('Sélection équilibrée', exact=True)).to_be_visible()
                with page.expect_response(lambda r: '/api/lettrage' in r.url and r.request.method == 'POST') as lettre:
                    page.get_by_role('button', name='Lettrer 3 lignes', exact=True).click()
                assert lettre.value.status == 200, lettre.value.text()
                assert lettre.value.json()['code'] == 'AAA'
                page.get_by_text('3 lettrée(s)', exact=True).wait_for()
                page.reload()
                champ(page, 'Compte', 'select').select_option('4411')
                champ(page, 'Tiers', 'select').select_option(label=nom)
                page.get_by_text('3 lettrée(s)', exact=True).wait_for()
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                print('Écran lettrage fictif :', page.url, page.locator('body').inner_text()[:6500])
                raise
            finally:
                browser.close()
        assert originaux(application, sid) == avant
        with Session(application['engine']) as db:
            lignes = db.query(models.LigneEcriture).join(models.Ecriture).filter(
                models.Ecriture.societe_id == sid, models.LigneEcriture.compte == '4411').all()
            assert len(lignes) == 3 and all(l.code_lettrage == 'AAA' for l in lignes)
            assert sum(Decimal(str(l.debit)) for l in lignes) == Decimal('1200')
            assert sum(Decimal(str(l.credit)) for l in lignes) == Decimal('1200')
