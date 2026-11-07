"""Inventaire historique : navigateur/API/PostgreSQL nonce, aucune base réelle."""
import csv
from datetime import date
from decimal import Decimal
import io
from io import BytesIO
import re
import uuid

import httpx
import pytest
from pypdf import PdfReader
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def inscrire(api, suffix):
    email, password = 'inventaire-nombres-' + suffix + '@example.com', 'InventaireFictif2026!'
    token = ok(api.post('/api/auth/register', json={'nom': 'Inventaire fictif', 'email': email,
        'password': password, 'raison_sociale': 'Inventaire nombres ' + suffix}))['access_token']
    api.headers['Authorization'] = 'Bearer ' + token
    return email, password, ok(api.get('/api/societe/moi'))['id']


def photo(application, sid):
    with Session(application['engine']) as db:
        return {
            'articles': [(a.id, repr(a.stock_actuel), repr(a.cmup)) for a in db.query(models.Article)
                .filter_by(societe_id=sid).order_by(models.Article.id)],
            'mouvements': [(m.id, m.article_id, repr(m.quantite), repr(m.stock_avant), repr(m.stock_apres))
                for m in db.query(models.MouvementStock).filter_by(societe_id=sid).order_by(models.MouvementStock.id)],
            'inventaires': [(i.id, i.reference, str(i.total_valeur), str(i.total_perte)) for i in db.query(models.InventaireStock)
                .filter_by(societe_id=sid).order_by(models.InventaireStock.id)],
            'ecritures': [(e.id, e.est_validee, e.reference,
                [(l.id, l.compte, str(l.debit), str(l.credit)) for l in e.lignes])
                for e in db.query(models.Ecriture).filter_by(societe_id=sid).order_by(models.Ecriture.id)],
            'archives': [(a.id, a.version, a.empreinte_sha256, a.contenu_json)
                for a in db.query(models.LivreInventaireArchive).filter_by(societe_id=sid)
                .order_by(models.LivreInventaireArchive.id)],
        }


def creer_article(api, code, designation, stock=0, cmup=0, stockable=True):
    return ok(api.post('/api/articles', json={'code': code, 'designation': designation,
        'stock_actuel': 0, 'cmup': cmup, 'is_stockable': stockable, 'prix_achat_ht': 20}), 201)['id']


@pytest.mark.parametrize('largeur', [1365, 390])
def test_inventaire_inconnu_visible_refuse_sans_mutation_et_csv(application, largeur):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    suffix = uuid.uuid4().hex[:8]
    # Exercice écoulé : le refus doit venir du stock, pas de la date future.
    year = date.today().year - 1
    with httpx.Client(base_url=application['api_url'], timeout=30) as api:
        email, password, sid = inscrire(api, suffix)
        ok(api.post('/api/exercices', json={'annee': year, 'date_debut': f'{year}-01-01',
            'date_fin': f'{year}-12-31'}), 201)
        donnees = [('NULL', None, None), ('NAN', float('nan'), 20), ('INF', 10, float('inf')),
            ('NEG', 10, -1), ('GRAND', 1e308, 1e308)]
        ids = {}
        for code, stock, cmup in donnees:
            ids[code] = creer_article(api, code + '-' + suffix, 'Historique ' + code + ' ' + suffix)
            with Session(application['engine']) as db:
                a = db.get(models.Article, ids[code]); a.stock_actuel = stock; a.cmup = cmup; db.commit()
        zero = creer_article(api, 'ZERO-' + suffix, 'Zéro connu ' + suffix)
        service = creer_article(api, 'SERVICE-' + suffix, 'Service hors stock ' + suffix, stockable=False)
        capital = ok(api.post('/api/ecritures', json={'date': f'{year}-12-31', 'journal': 'OD',
            'reference': 'CAPITAL-' + suffix, 'libelle': 'Capital fictif conservé', 'lignes': [
                {'compte': '5141', 'debit': 1000}, {'compte': '1111', 'credit': 1000}]}), 201)
        ok(api.post(f"/api/ecritures/{capital['id']}/valider"))
        avant = photo(application, sid)
        feuille = ok(api.get('/api/inventaire/feuille'))
        assert {l['article_id'] for l in feuille} == set(ids.values()) | {zero}
        assert service not in {l['article_id'] for l in feuille}
        for code, aid in ids.items():
            ligne = next(l for l in feuille if l['article_id'] == aid)
            assert ligne['valeur_theorique'] is None and ligne['nombres_diagnostics'], (code, ligne)
            corps = {'date': f'{year}-12-31', 'reference': 'REFUS-' + code + '-' + suffix,
                'lignes': [{'article_id': aid, 'quantite_reelle': 0 if code in {'NULL', 'NAN'} else 10}]}
            assert api.post('/api/inventaire/simuler', json=corps).status_code == 400
            assert api.post('/api/inventaire/valider', json=corps).status_code == 409
            assert photo(application, sid) == avant
        etat = ok(api.get('/api/inventaire/valorisation'))
        assert etat['total_valeur'] is None and not etat['valorisation_complete']
        cloture = ok(api.get('/api/inventaire/stock/cloture', params={'exercice': year}))
        assert cloture['valeur_physique_brute'] is None and cloture['ecart_brut'] is None
        assert not cloture['stock_rapproche'] and not cloture['valorisation_complete']
        assert api.post('/api/inventaire/comptabiliser-stock', params={'exercice': year}).status_code == 409
        refus_cloture = api.post('/api/cloture/cloturer', params={'exercice': year})
        assert refus_cloture.status_code == 400 and 'stock' in refus_cloture.text.lower(), refus_cloture.text
        livre = ok(api.get('/api/inventaire/livre', params={'exercice': year}))['snapshot']
        assert not livre['stocks']['valorisation_complete']
        assert livre['stocks']['valeur_physique'] is None
        assert not livre['controles']['stock_rapproche']
        assert not livre['controles']['valorisation_stock_complete']
        pdf = api.get('/api/inventaire/livre/pdf', params={'exercice': year})
        assert pdf.status_code == 200 and pdf.content.startswith(b'%PDF'), pdf.text[:200] if pdf.status_code != 200 else ''
        lecteur_pdf = PdfReader(BytesIO(pdf.content))
        texte_pdf = '\n'.join(p.extract_text() for p in lecteur_pdf.pages)
        # Les codes des fixtures « NAN-... » et « INF-... » sont des libellés
        # légitimes ; surveiller les cellules numériques, pas ces références.
        assert 'vérifier' in texte_pdf.lower() and not re.search(
            r'^\s*[+-]?(?:nan|inf|infinity)\s*(?:MAD)?\s*$', texte_pdf, re.I | re.M), texte_pdf
        assert api.post('/api/inventaire/livre/archiver', params={'exercice': year}).status_code == 409
        assert photo(application, sid) == avant
        # Les refus traversent la vraie authentification et le vrai tenant.
        lecture_email = 'lecture-' + email
        ok(api.post('/api/utilisateurs', json={'nom': 'Lecture inventaire', 'email': lecture_email,
            'mot_de_passe': password, 'role': 'lecture'}), 201)
        with httpx.Client(base_url=application['api_url']) as lecture:
            jeton = ok(lecture.post('/api/auth/login', json={'email': lecture_email, 'password': password}))['access_token']
            lecture.headers['Authorization'] = 'Bearer ' + jeton
            ok(lecture.get('/api/inventaire/valorisation'))
            assert lecture.post('/api/inventaire/valider', json=corps).status_code == 403
            assert lecture.post('/api/inventaire/comptabiliser-stock', params={'exercice': year}).status_code == 403
        with httpx.Client(base_url=application['api_url']) as autre:
            inscrire(autre, 'autre-' + suffix)
            assert ok(autre.get('/api/inventaire/feuille')) == []
            assert autre.get('/api/inventaire/historique/' + str(ids['NULL'])).status_code == 404
            assert autre.post('/api/inventaire/simuler', json=corps).status_code == 400
            assert autre.post('/api/inventaire/valider', json=corps).status_code == 409
        assert photo(application, sid) == avant
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Edge/Chromium requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            page = browser.new_page(viewport={'width': largeur, 'height': 1000}, accept_downloads=True)
            page.set_default_timeout(20000)
            errors, server_errors = observer(page, application['api_url'])
            mutations = []
            page.on('request', lambda r: mutations.append(r) if '/api/inventaire/' in r.url and r.method == 'POST' else None)
            try:
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/inventaire')
                for code in ids:
                    row = page.locator('tbody tr').filter(has_text='Historique ' + code + ' ' + suffix)
                    playwright.expect(row).to_contain_text('À vérifier')
                for code in ['NULL', 'NAN']:
                    row = page.locator('tbody tr').filter(has_text='Historique ' + code + ' ' + suffix)
                    assert row.locator('input[type="number"]').input_value() == ''
                assert page.locator('tbody tr').filter(has_text='Zéro connu ' + suffix).locator('input[type="number"]').input_value() == '0'
                for row in page.locator('tbody tr').all():
                    row.locator('input[type="number"]').fill('0')
                playwright.expect(page.get_by_role('button', name='Vérifier', exact=True)).to_be_disabled()
                playwright.expect(page.get_by_role('button', name='Valider l’inventaire', exact=True)).to_be_disabled()
                assert not mutations
                page.get_by_role('button', name='Valeur du stock', exact=True).click()
                for code in ids:
                    playwright.expect(page.locator('tbody tr').filter(has_text='Historique ' + code + ' ' + suffix)).to_contain_text('À vérifier')
                playwright.expect(page.locator('tbody tr').filter(has_text='Valeur totale du stock')).to_contain_text('À vérifier')
                with page.expect_download() as export:
                    page.get_by_role('button', name='Exporter', exact=True).click()
                contenu = open(export.value.path(), encoding='utf-8-sig').read()
                assert 'NaN' not in contenu and 'Infinity' not in contenu
                lignes = list(csv.DictReader(io.StringIO(contenu), delimiter=';'))
                for code in ids:
                    ligne = next(l for l in lignes if l['Code'] == code + '-' + suffix)
                    assert ligne['Valeur'] in {'', 'À vérifier'}, ligne
                page.get_by_role('button', name='Rapprochement comptable', exact=True).click()
                playwright.expect(page.get_by_role('button', name='Générer l’écriture de stock', exact=True)).to_be_disabled()
                playwright.expect(page.locator('body')).to_contain_text('À vérifier')
                page.goto(application['web_url'] + '/cloture')
                page.get_by_label('Exercice actif', exact=True).select_option(str(year))
                playwright.expect(page.locator('body')).to_contain_text('À vérifier')
                playwright.expect(page.get_by_role('button', name=f"Clôturer l'exercice {year}", exact=True)).to_be_disabled()
                assert photo(application, sid) == avant
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                print('Inventaire UI:', page.url, page.locator('body').inner_text()[:10000])
                print('Erreurs:', errors, server_errors)
                raise
            finally:
                browser.close()


@pytest.mark.parametrize('largeur', [1365, 390])
def test_inventaire_connu_perte40_snapshot160_et_ecriture_validee(application, largeur):
    c = application['cluster']; verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    suffix = uuid.uuid4().hex[:8]
    year = date.today().year
    with httpx.Client(base_url=application['api_url'], timeout=30) as api:
        email, password, sid = inscrire(api, suffix)
        nom = 'Marchandise connue ' + suffix
        aid = creer_article(api, 'CONNU-' + suffix, nom, cmup=20)
        zero = creer_article(api, 'ZERO-' + suffix, 'Zéro connu ' + suffix)
        with Session(application['engine']) as db:
            a = db.get(models.Article, aid); a.stock_actuel = 10; a.cmup = 20; db.commit()
        assert ok(api.get('/api/inventaire/valorisation'))['total_valeur'] == 200
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Edge/Chromium requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            errors, server_errors = observer(page, application['api_url'])
            page.on('dialog', lambda d: d.accept())
            try:
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/inventaire')
                page.locator('tbody tr').filter(has_text=nom).locator('input[type="number"]').fill('8')
                with page.expect_response(lambda r: '/api/inventaire/simuler' in r.url) as simulation:
                    page.get_by_role('button', name='Vérifier', exact=True).click()
                apercu = simulation.value.json()
                assert simulation.value.status == 200 and apercu['total_perte'] == 40 and apercu['valeur_stock_compte'] == 160, apercu
                with page.expect_response(lambda r: '/api/inventaire/valider' in r.url) as validation:
                    page.get_by_role('button', name='Valider l’inventaire', exact=True).click()
                inv = validation.value.json()
                assert validation.value.status == 200 and inv['total_perte'] == 40 and inv['total_valeur'] == 160, inv
                assert inv['nb_articles'] == 2 and inv['nb_regularises'] == 1
                with Session(application['engine']) as db:
                    assert db.get(models.Article, aid).stock_actuel == 8
                    assert db.get(models.Article, zero).stock_actuel == 0
                    snapshot = db.get(models.InventaireStock, inv['inventaire_id'])
                    assert snapshot.total_valeur == Decimal('160') and snapshot.total_perte == Decimal('40')
                    assert len(snapshot.lignes) == 2
                    assert db.query(models.MouvementStock).filter_by(societe_id=sid).count() == 1
                page.get_by_role('button', name='Rapprochement comptable', exact=True).click()
                with page.expect_response(lambda r: '/api/inventaire/comptabiliser-stock' in r.url) as compta:
                    page.get_by_role('button', name='Générer l’écriture de stock', exact=True).click()
                assert compta.value.status == 200, compta.value.text()
                eid = compta.value.json()['ecriture_id']
                with Session(application['engine']) as db:
                    ec = db.get(models.Ecriture, eid)
                    assert not ec.est_validee
                    assert {l.compte: (l.debit, l.credit) for l in ec.lignes} == {'3111': (160, 0), '6114': (0, 160)}
                page.goto(application['web_url'] + '/journal')
                # Attendre la donnée chargée avant la validation du lot.
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(1)
                with page.expect_response(lambda r: '/api/ecritures/valider-lot' in r.url) as lot:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert lot.value.status == 200 and lot.value.json()['nb_validees'] == 1
                stable = photo(application, sid)
                page.goto(application['web_url'] + '/inventaire')
                page.get_by_role('button', name='Rapprochement comptable', exact=True).click()
                playwright.expect(page.locator('body')).to_contain_text('Stock rapproché')
                etat = ok(api.get('/api/inventaire/stock/cloture', params={'exercice': year}))
                assert etat['stock_rapproche'] and etat['ecriture_stock_validee']
                assert etat['valeur_physique_brute'] == etat['valeur_comptable_brute'] == 160
                assert etat['ecart_brut'] == 0
                assert photo(application, sid) == stable
                assert not errors and not server_errors, (errors, server_errors)
            except Exception as erreur:
                print('Erreur inventaire originale:', repr(erreur), page.url)
                try:
                    print('Inventaire positif:', page.locator('body').inner_text(timeout=1000)[:10000])
                except Exception as diagnostic:
                    print('Corps indisponible pendant le diagnostic:', repr(diagnostic))
                print('Erreurs:', errors, server_errors)
                raise
            finally:
                browser.close()
