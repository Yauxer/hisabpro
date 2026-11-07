"""Nombres historiques inconnus : Edge et API réels, PostgreSQL nonce uniquement."""
import uuid
import json
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application

CHAMPS = ('prix_vente_ht', 'prix_achat_ht', 'frais_emballage', 'frais_transport', 'tva', 'stock_min', 'cmup')


def champ(modal, label):
    return modal.locator('label').filter(has_text=label).locator('..').locator('input, select, textarea').first


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


def photographie(application, aid, sid):
    with Session(application['engine']) as db:
        a = db.get(models.Article, aid)
        return {k: repr(getattr(a, k)) for k in CHAMPS + ('stock_actuel',)}, (
            db.query(models.Ecriture).filter_by(societe_id=sid).count(),
            db.query(models.MouvementStock).filter_by(societe_id=sid).count())


def test_saisie_numerique_stricte_et_valeurs_indicatives_inconnues():
    script = """
      import { nombreSaisieConnu, nombreArticleSaisie, qualificationArticle, montantLignesSaisies } from './src/utils/articlesNombres.js';
      const candidats = [null, undefined, '', '  ', true, false, [], [0], {}, NaN, Infinity, -1, '1e309', 0, '0', ' 1.25 ', '1e308'];
      console.log(JSON.stringify({connus: candidats.map(nombreSaisieConnu),
        inconnus: [null, NaN, Infinity, -1].map(nombreArticleSaisie),
        qualification: qualificationArticle(null), zero: nombreArticleSaisie(0),
        totalInconnu: montantLignesSaisies(0, [{description:'Article',prix_unitaire:'',tva:''}], String),
        totalNonFini: montantLignesSaisies(Infinity, [], String),
        totalZero: montantLignesSaisies(0, [{description:'Article',prix_unitaire:0,tva:0}], String)}));
    """
    result = subprocess.run(['node', '--input-type=module', '-e', script], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=True, encoding='utf-8')
    donnees = json.loads(result.stdout)
    assert donnees == {'connus': [False] * 13 + [True] * 4,
        'inconnus': ['', '', '', ''], 'qualification': '', 'zero': 0,
        'totalInconnu': 'À vérifier', 'totalNonFini': 'À vérifier', 'totalZero': '0'}


@pytest.mark.parametrize('largeur', [1365, 390])
def test_article_historique_lecture_edition_partielle_et_documents_sans_zero(application, largeur):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    suffix = uuid.uuid4().hex[:8]
    email, password = 'historique-nombres-' + suffix + '@example.com', 'NombresFictifs2026!'
    nom, tiers = 'Article inconnu ' + suffix, 'Tiers fictif ' + suffix
    with httpx.Client(base_url=application['api_url']) as api:
        token = ok(api.post('/api/auth/register', json={'nom': 'Recette historique', 'email': email,
            'password': password, 'raison_sociale': 'Nombres historiques fictifs ' + suffix}))['access_token']
        api.headers['Authorization'] = 'Bearer ' + token
        sid = ok(api.get('/api/societe/moi'))['id']
        ok(api.post('/api/tiers', json={'nom': tiers, 'type': 'les_deux'}), 201)
        aid = ok(api.post('/api/articles', json={'code': 'INCONNU-' + suffix,
            'designation': nom, 'stock_actuel': 0}), 201)['id']
        nom_grand = 'Valorisation élevée ' + suffix
        grand_id = ok(api.post('/api/articles', json={'code': 'GRAND-' + suffix,
            'designation': nom_grand, 'stock_actuel': 0, 'prix_vente_ht': 1e308,
            'prix_achat_ht': 0, 'tva': 0}), 201)['id']
        with Session(application['engine']) as db:
            a = db.get(models.Article, aid)
            for k, v in zip(CHAMPS, (float('nan'), float('inf'), None, -1, -1, float('nan'), float('inf'))):
                setattr(a, k, v)
            grand = db.get(models.Article, grand_id)
            grand.stock_actuel = 1e308
            grand.cmup = 1e308
            db.commit()
        avant, comptes = photographie(application, aid, sid)
        grand_avant = photographie(application, grand_id, sid)
        article = next(a for a in ok(api.get('/api/articles')) if a['id'] == aid)
        assert all(article[k] is None for k in CHAMPS), article
        assert set(CHAMPS) <= set(article['nombres_diagnostics'])
        assert article['stock_actuel'] == 0
        assert photographie(application, aid, sid) == (avant, comptes)
        executable = chromium_executable()
        if not executable:
            pytest.skip('Edge / Chromium requis')
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            errors, server_errors = observer(page, application['api_url'])
            mutations, diagnostics_stock = [], []
            def observer_requetes(r):
                chemin = urlsplit(r.url).path
                # Cette route POST photographie le stock sans mutation.
                # Tous les POST/PATCH des documents restent surveillés.
                if r.method == 'POST' and chemin == '/api/devis/diagnostic-stock':
                    diagnostics_stock.append(r)
                elif r.method in {'POST', 'PATCH'} and any(x in chemin for x in ['/api/articles', '/api/devis', '/api/bons-commande', '/api/factures']):
                    mutations.append(r)
            page.on('request', observer_requetes)
            try:
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/articles')
                ligne = page.locator('tbody tr').filter(has_text=nom)
                playwright.expect(ligne).to_contain_text('À vérifier')
                ligne_grande = page.locator('tbody tr').filter(has_text=nom_grand)
                playwright.expect(ligne_grande).to_contain_text('À vérifier')
                assert 'Infinity' not in ligne_grande.inner_text()
                ligne.click()
                modal = page.get_by_role('dialog', name="Modifier l'article", exact=True)
                for label in ['Prix vente HT', 'Prix achat HT', 'Emballage HT par unité', 'Transport HT par unité', 'TVA proposée', 'Stock minimum']:
                    assert champ(modal, label).input_value() == '', label
                champ(modal, 'Description').fill('Note fictive sans correction des montants')
                with page.expect_response(lambda r: r.url.endswith(f'/api/articles/{aid}') and r.request.method == 'PATCH') as edition:
                    modal.get_by_role('button', name='Enregistrer les modifications', exact=True).click()
                assert edition.value.status == 200, edition.value.text()
                assert edition.value.request.post_data_json == {'description': 'Note fictive sans correction des montants'}
                modal.wait_for(state='hidden')
                assert photographie(application, aid, sid) == (avant, comptes)
                ligne.click()
                champ(modal, 'Emballage HT par unité').fill('1')
                champ(modal, 'Emballage HT par unité').fill('')
                n = len(mutations)
                modal.get_by_role('button', name='Enregistrer les modifications', exact=True).click()
                playwright.expect(modal).to_contain_text('renseignez une valeur explicite')
                assert len(mutations) == n
                champ(modal, 'Emballage HT par unité').fill('0')
                with page.expect_response(lambda r: r.url.endswith(f'/api/articles/{aid}') and r.request.method == 'PATCH') as correction:
                    modal.get_by_role('button', name='Enregistrer les modifications', exact=True).click()
                assert correction.value.status == 200, correction.value.text()
                assert correction.value.request.post_data_json == {'frais_emballage': 0}
                modal.wait_for(state='hidden')
                apres, comptes_apres = photographie(application, aid, sid)
                assert apres == {**avant, 'frais_emballage': '0.0'} and comptes_apres == comptes
                ligne.click()
                assert champ(modal, 'Emballage HT par unité').input_value() == '0'
                assert champ(modal, 'Prix vente HT').input_value() == ''
                modal.get_by_role('button', name='Annuler', exact=True).click()
                # Vente : devis ; achat : commande. Aucun devis achat n'est inventé.
                for sens, action, titre, bouton, endpoint in [
                    ('Vente', 'Nouveau devis', 'Nouveau devis', 'Créer le devis', '/api/devis'),
                    ('Achat', 'Nouveau BC', 'Nouveau bon de commande', 'Créer la commande', '/api/bons-commande'),
                ]:
                    page.goto(application['web_url'] + '/commercial')
                    page.get_by_role('button', name=sens, exact=True).click()
                    page.get_by_role('button', name=action, exact=True).click()
                    m = page.get_by_role('dialog', name=titre, exact=True)
                    m.get_by_placeholder('Nom du', exact=False).fill(tiers)
                    m.get_by_text(tiers, exact=True).click()
                    m.get_by_placeholder('Article ou description...').fill(nom)
                    m.locator('li').filter(has_text=nom).click()
                    editor = m.locator('.hp-commercial-line-editor')
                    prix = editor.locator('input[type="number"]').nth(1)
                    tva = editor.locator('select').first
                    assert prix.input_value() == '' and tva.input_value() == ''
                    playwright.expect(m.locator('[class*="totauxLigne"]').filter(has_text='Total HT').first).to_contain_text('À vérifier')
                    n = len(mutations)
                    m.get_by_role('button', name=bouton, exact=True).click()
                    playwright.expect(m).to_contain_text('prix unitaire et un taux de TVA connus')
                    assert len(mutations) == n
                    prix.fill('100'); tva.select_option('20')
                    with page.expect_response(lambda r: r.url.endswith(endpoint) and r.request.method == 'POST') as creation:
                        m.get_by_role('button', name=bouton, exact=True).click()
                    assert creation.value.status == 201, creation.value.text()
                    assert creation.value.json()['total_ttc'] == 120
                    document = creation.value.json()
                    m.wait_for(state='hidden')
                    # Les mêmes sélecteurs en édition ne doivent pas réintroduire 0/20.
                    page.locator('tbody tr').filter(has_text=document['numero']).get_by_title('Modifier', exact=True).click()
                    m = page.get_by_role('dialog')
                    m.get_by_placeholder('Article ou description...').fill(nom)
                    m.locator('li').filter(has_text=nom).click()
                    editor = m.locator('.hp-commercial-line-editor')
                    prix, tva = editor.locator('input[type="number"]').nth(1), editor.locator('select').first
                    assert prix.input_value() == '' and tva.input_value() == ''
                    if endpoint == '/api/devis':
                        # Finir la lecture automatique avant de tester la relance :
                        # sa réponse tardive ne prouve pas le clic "Actualiser".
                        playwright.expect(m.get_by_text('Vérification du stock en cours…', exact=True)).to_have_count(0)
                        playwright.expect(m.get_by_role('button', name='Actualiser le stock', exact=True)).to_be_enabled()
                        n, lectures = len(mutations), len(diagnostics_stock)
                        precedentes = set(diagnostics_stock)
                        with page.expect_response(lambda r: urlsplit(r.url).path == '/api/devis/diagnostic-stock' and r.request.method == 'POST' and r.request not in precedentes) as stock:
                            m.get_by_role('button', name='Actualiser le stock', exact=True).click()
                        assert stock.value.status == 200, stock.value.text()
                        assert len(diagnostics_stock) > lectures and len(mutations) == n
                    n = len(mutations)
                    m.get_by_role('button', name='Enregistrer', exact=True).click()
                    playwright.expect(m).to_contain_text('prix unitaire et un taux de TVA connus')
                    assert len(mutations) == n
                    relu = next(d for d in ok(api.get(endpoint, params={'exercice': document['exercice']})) if d['id'] == document['id'])
                    assert relu['total_ttc'] == 120
                    assert relu['lignes'][0]['prix_unitaire'] == 100 and relu['lignes'][0]['tva'] == 20
                    m.get_by_role('button', name='Annuler', exact=True).click()
                for sens in ['Vente', 'Achat']:
                    page.goto(application['web_url'] + '/factures')
                    page.get_by_role('button', name='Nouvelle facture', exact=True).click()
                    m = page.get_by_role('dialog', name='Nouvelle facture', exact=True)
                    m.get_by_role('button', name=sens, exact=True).click()
                    m.get_by_placeholder('Rechercher un', exact=False).fill(tiers)
                    m.get_by_text(tiers, exact=True).click()
                    m.get_by_placeholder('Description ou article...').fill(nom)
                    m.locator('li').filter(has_text=nom).click()
                    editor = m.locator('.hp-invoice-line-editor')
                    prix = editor.locator('input[type="number"]').nth(1)
                    tva = editor.locator('select').last
                    assert prix.input_value() == '' and tva.input_value() == ''
                    playwright.expect(m.locator('[class*="totauxLigne"]').filter(has_text='Total HT').first).to_contain_text('À vérifier')
                    m.get_by_role('button', name='Enregistrer en brouillon', exact=False).click()
                    n = len(mutations)
                    m.get_by_role('button', name='Enregistrer le brouillon', exact=True).click()
                    playwright.expect(m).to_contain_text('prix unitaire')
                    assert len(mutations) == n
                    prix.fill('100'); tva.select_option('20')
                    with page.expect_response(lambda r: r.url.endswith('/api/factures') and r.request.method == 'POST') as creation:
                        m.get_by_role('button', name='Enregistrer le brouillon', exact=True).click()
                    assert creation.value.status == 201, creation.value.text()
                    assert creation.value.json()['total_ttc'] == 120
                    m.wait_for(state='hidden')
                assert photographie(application, aid, sid) == (apres, comptes)
                assert photographie(application, grand_id, sid) == grand_avant
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                print('Écran historique :', page.url, page.locator('body').inner_text()[:10000])
                print('Erreurs JS / API :', errors, server_errors)
                raise
            finally:
                browser.close()
