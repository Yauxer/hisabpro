"""Familles historiques : choix TVA explicite, API/Edge/PostgreSQL nonce."""
import uuid

import httpx
import pytest
from sqlalchemy import text

from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


def champ(modal, label):
    return modal.locator('label').filter(has_text=label).locator('..').locator('input,select,textarea').first


def photo(application, sid):
    with application['engine'].connect() as db:
        familles = db.execute(text('SELECT row_to_json(t)::text FROM familles_articles t '
            'WHERE societe_id=:sid ORDER BY id'), {'sid': sid}).scalars().all()
        comptes = [db.execute(text(f'SELECT count(*) FROM {table} WHERE societe_id=:sid'),
            {'sid': sid}).scalar_one() for table in ('ecritures', 'mouvements_stock')]
        return familles, comptes


@pytest.fixture
def dossier(application):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    suffix = uuid.uuid4().hex[:8]
    email, password = 'familles-ui-' + suffix + '@example.com', 'FamillesHistorique2026!'
    with httpx.Client(base_url=application['api_url']) as api:
        token = ok(api.post('/api/auth/register', json={'nom': 'Familles fictives',
            'email': email, 'password': password, 'raison_sociale': 'Familles UI ' + suffix}))['access_token']
        api.headers['Authorization'] = 'Bearer ' + token
        sid = ok(api.get('/api/societe/moi'))['id']
        familles = {}
        for nom, taux in [('inconnue', 20), ('zero', 0), ('connue', 20)]:
            familles[nom] = ok(api.post('/api/familles', json={'code': nom + suffix,
                'libelle': 'Famille ' + nom + ' ' + suffix, 'tva_defaut': taux}), 201)
        with application['engine'].begin() as db:
            db.execute(text('UPDATE familles_articles SET tva_defaut=NULL WHERE id=:id AND societe_id=:sid'),
                {'id': familles['inconnue']['id'], 'sid': sid})
        # Précondition backend réelle : lecture saine de la famille historique.
        historique = next(f for f in ok(api.get('/api/familles')) if f['id'] == familles['inconnue']['id'])
        assert historique['tva_defaut'] is None and historique['nombres_diagnostics']
        linked = ok(api.post('/api/articles', json={'code': 'LIE-' + suffix,
            'designation': 'Article lié ' + suffix, 'famille_id': historique['id'],
            'tva': 0, 'stock_actuel': 0}), 201)
        assert linked['tva'] == 0 and linked['famille']['tva_defaut'] is None
        avant = photo(application, sid)
        yield api, sid, suffix, email, password, familles, avant


@pytest.mark.parametrize('largeur', [1365, 390])
def test_article_famille_inconnue_ne_conserve_pas_tva_ancienne(application, dossier, largeur):
    api, sid, suffix, email, password, familles, avant = dossier
    executable = chromium_executable()
    if not executable:
        pytest.skip('Edge / Chromium requis')
    pw = pytest.importorskip('playwright.sync_api')
    with pw.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        page = browser.new_page(viewport={'width': largeur, 'height': 1000})
        page.set_default_timeout(20000)
        erreurs, serveurs = observer(page, application['api_url'])
        mutations = []
        page.on('request', lambda r: mutations.append(r)
                if r.method in {'POST', 'PATCH'} and '/api/articles' in r.url else None)
        try:
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/articles')
            for taux in ('0', '20'):
                page.get_by_role('button', name='Nouvel article', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouvel article', exact=True)
                modal.get_by_placeholder('ART-001').fill('EXPL-' + taux + '-' + suffix)
                modal.get_by_placeholder("Nom de l'article ou service").fill('TVA explicite ' + taux + ' ' + suffix)
                choix = champ(modal, 'Famille')
                tva = champ(modal, 'TVA proposée')
                choix.select_option(str(familles['zero']['id']))
                assert tva.input_value() == '0'
                choix.select_option(str(familles['connue']['id']))
                assert tva.input_value() == '20'
                choix.select_option(str(familles['inconnue']['id']))
                assert tva.input_value() == '', 'Une famille inconnue ne doit conserver ni0 ni20.'
                pw.expect(modal).to_contain_text('TVA de cette famille est inconnue')
                n = len(mutations)
                modal.get_by_role('button', name="Créer l’article", exact=True).click()
                pw.expect(modal).to_contain_text('valeur explicite')
                assert len(mutations) == n
                tva.select_option(taux)
                with page.expect_response(lambda r: r.url.endswith('/api/articles')
                                          and r.request.method == 'POST') as creation:
                    modal.get_by_role('button', name="Créer l’article", exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                assert creation.value.request.post_data_json['tva'] == int(taux)
                assert creation.value.json()['famille']['tva_defaut'] is None
                modal.wait_for(state='hidden')
            ligne = page.locator('tbody tr').filter(has_text='Article lié ' + suffix)
            ligne.click()
            modal = page.get_by_role('dialog', name="Modifier l'article", exact=True)
            choix, tva = champ(modal, 'Famille'), champ(modal, 'TVA proposée')
            assert tva.input_value() == '0'
            choix.select_option(str(familles['connue']['id']))
            choix.select_option(str(familles['inconnue']['id']))
            assert tva.input_value() == ''
            n = len(mutations)
            modal.get_by_role('button', name='Enregistrer les modifications', exact=True).click()
            pw.expect(modal).to_contain_text('valeur explicite')
            assert len(mutations) == n
            # Quitter la famille ne rétablit pas une TVA implicite.
            choix.select_option('')
            assert tva.input_value() == ''
            tva.select_option('20')
            with page.expect_response(lambda r: '/api/articles/' in r.url
                                      and r.request.method == 'PATCH') as edition:
                modal.get_by_role('button', name='Enregistrer les modifications', exact=True).click()
            assert edition.value.status == 200, edition.value.text()
            assert edition.value.request.post_data_json['tva'] == 20
            modal.wait_for(state='hidden')
            assert photo(application, sid) == avant
            assert not erreurs and not serveurs, (erreurs, serveurs)
        except Exception:
            print('Diagnostic article :', page.url, erreurs, serveurs, page.locator('body').inner_text()[:2500])
            raise
        finally:
            browser.close()


@pytest.mark.parametrize('largeur', [1365, 390])
def test_creation_rapide_famille_inconnue_exige_tva_explicite(application, dossier, largeur):
    api, sid, suffix, email, password, familles, avant = dossier
    executable = chromium_executable()
    if not executable:
        pytest.skip('Edge / Chromium requis')
    pw = pytest.importorskip('playwright.sync_api')
    with pw.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        page = browser.new_page(viewport={'width': largeur, 'height': 1000})
        page.set_default_timeout(20000)
        erreurs, serveurs = observer(page, application['api_url'])
        mutations = []
        page.on('request', lambda r: mutations.append(r)
                if r.method == 'POST' and r.url.endswith('/api/articles') else None)
        try:
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/factures')
            page.get_by_role('button', name='Nouvelle facture', exact=True).click()
            facture = page.get_by_role('dialog', name='Nouvelle facture', exact=True)
            for taux in ('0', '20'):
                designation = 'Rapide ' + taux + ' ' + suffix
                facture.get_by_placeholder('Description ou article...').fill(designation)
                facture.get_by_role('button', name='Créer cet article', exact=False).click()
                mini = page.locator('div[style*="z-index: 3000"]')
                choix = champ(mini, 'Famille')
                choix.select_option(str(familles['inconnue']['id']))
                select_tva = mini.get_by_label('TVA proposée pour cet article', exact=True)
                assert select_tva.count() == 1, 'La création rapide doit exposer la TVA inconnue, sans repli20.'
                assert select_tva.input_value() == ''
                n = len(mutations)
                mini.get_by_role('button', name='Créer', exact=True).click()
                pw.expect(mini).to_contain_text('valeur explicite')
                assert len(mutations) == n
                select_tva.select_option(taux)
                with page.expect_response(lambda r: r.url.endswith('/api/articles')
                                          and r.request.method == 'POST') as creation:
                    mini.get_by_role('button', name='Créer', exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                assert creation.value.request.post_data_json['tva'] == int(taux)
                assert creation.value.json()['tva'] == int(taux)
                mini.wait_for(state='hidden')
            # Un taux choisi pour une famille inconnue ne fuit pas vers une famille connue.
            facture.get_by_placeholder('Description ou article...').fill('Rapide connu ' + suffix)
            facture.get_by_role('button', name='Créer cet article', exact=False).click()
            mini = page.locator('div[style*="z-index: 3000"]')
            champ(mini, 'Famille').select_option(str(familles['zero']['id']))
            assert mini.get_by_label('TVA proposée pour cet article', exact=True).count() == 0
            with page.expect_response(lambda r: r.url.endswith('/api/articles')
                                      and r.request.method == 'POST') as connue:
                mini.get_by_role('button', name='Créer', exact=True).click()
            assert connue.value.status == 201 and connue.value.json()['tva'] == 0
            assert photo(application, sid) == avant
            assert not erreurs and not serveurs, (erreurs, serveurs)
        finally:
            browser.close()
