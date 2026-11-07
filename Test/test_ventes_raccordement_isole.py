"""Raccordement ventes/Journal réel, export et concurrence sous PostgreSQL nonce."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from io import BytesIO
from threading import Event
import httpx
import pytest
from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from pypdf import PdfReader

from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from services.ventes_preparation_service import construire
from test_e2e_ventes_preparation_isole import ouvrir
from browser_support import chromium_executable

REFERENCE_LONGUE = '=FORMULE-FICTIVE561-' + 'JUSTIFICATIF-' * 5


def facture(api, montant=100, *, exercice=2025, comptabiliser=True):
    if not any(e['annee'] == exercice for e in ok(api.get('/api/exercices'))):
        ok(api.post('/api/exercices', json={'annee': exercice, 'date_debut': f'{exercice}-01-01', 'date_fin': f'{exercice}-12-31'}), 201)
    tiers = ok(api.post('/api/tiers', json={'nom': 'Client fictif561', 'type': 'client', 'ice': '001234567890123'}), 201)
    f = ok(api.post('/api/factures', json={'type': 'vente', 'date': f'{exercice}-03-15',
        'tiers': tiers['nom'], 'tiers_id': tiers['id'], 'lignes': [
            {'description': 'Vente fictive561', 'quantite': 1, 'prix_unitaire': montant, 'tva': 20}]}), 201)
    ok(api.post(f"/api/factures/{f['id']}/valider"))
    if comptabiliser:
        eid = ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))['ecriture_id']
        ok(api.post(f'/api/ecritures/{eid}/valider'))
    return f


def preparer(api):
    return ok(api.get('/api/etats/ventes/preparation/2025'))


def manuel(api, montant=50, reference='HORS-FACTURATION561', valide=True):
    return ok(api.post('/api/ecritures', json={'date': '2025-06-30', 'journal': 'OD',
        'reference': reference, 'libelle': 'Vente manuelle fictive561', 'est_validee': valide,
        'lignes': [{'compte': '5141', 'debit': montant}, {'compte': '7124', 'credit': montant}]}), 201)


def valider(api):
    for e in ok(api.get('/api/ecritures', params={'exercice': 2025})):
        if not e['est_validee']:
            ok(api.post(f"/api/ecritures/{e['id']}/valider"))


def test_ventes_avoirs_od_et_cloture_conservent_raccordement(application):
    with closing(client(application)[0]) as api:
        f = facture(api, comptabiliser=False)
        d = preparer(api)
        assert d['comptabilite']['ca_net'] == '0.00' and d['comptabilite']['ecart_ca_moins_ht'] == '-100.00'
        eid = ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))['ecriture_id']
        c = preparer(api)['comptabilite']
        assert c['ca_net'] == '0.00' and c['brouillons_exclus'] == 1
        ok(api.post(f'/api/ecritures/{eid}/valider'))
        assert preparer(api)['comptabilite']['ecart_ca_moins_ht'] == '0.00'
        avoir = ok(api.post('/api/avoirs', json={'facture_id': f['id'], 'date': '2025-04-15',
            'motif': 'Réduction fictive561', 'retour_stock': False,
            'lignes': [{'facture_ligne_id': f['lignes'][0]['id'], 'quantite': 0.4}]}), 201)
        assert preparer(api)['comptabilite']['ecart_ca_moins_ht'] == '40.00'
        ok(api.post(f"/api/avoirs/{avoir['id']}/comptabiliser"))
        valider(api)
        manuel(api)
        manuel(api, 70, 'BROUILLON561', False)
        avant = preparer(api)
        assert avant['totaux']['ht'] == '60.00'
        assert avant['comptabilite']['ca_net'] == '110.00'
        assert avant['comptabilite']['ecart_ca_moins_ht'] == '50.00'
        assert avant['comptabilite']['brouillons_exclus'] == 1
        # Conserver le brouillon mais le valider par le flux normal avant clôture.
        valider(api)
        avant = preparer(api)
        assert avant['comptabilite']['ca_net'] == '180.00'
        cloture = ok(api.post('/api/cloture/cloturer?exercice=2025'))
        assert cloture['a_nouveaux_sur'] == 2026
        apres = preparer(api)
        assert apres['comptabilite']['ca_net'] == '180.00'
        assert apres['comptabilite']['ecart_ca_moins_ht'] == '120.00'
        assert apres['comptabilite']['mouvements'] == avant['comptabilite']['mouvements']
        assert all(m['journal'] != 'CL' for m in apres['comptabilite']['mouvements'])


def test_ecart_nul_ne_prouve_pas_facture_et_comptes_isoles(application):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        facture(api, comptabiliser=False)
        manuel(api, 100)
        facture(autre, 800)
        avant = donnees_metier(application)
        d = preparer(api)
        assert d['comptabilite']['ca_net'] == '100.00' and d['comptabilite']['ecart_ca_moins_ht'] == '0.00'
        assert not d['documents'][0]['comptabilisee']
        assert 'ne prouve' in d['comptabilite']['note']
        assert len(d['comptabilite']['mouvements']) == 1
        assert preparer(autre)['comptabilite']['ca_net'] == '800.00'
        assert donnees_metier(application) == avant


@pytest.mark.parametrize('format_', ['pdf', 'xlsx'])
def test_export_raccordement_et_changement_comptable_seul_refuse_ancien(application, format_):
    with closing(client(application)[0]) as api:
        facture(api)
        d = preparer(api)
        manuel(api, 50, REFERENCE_LONGUE)
        r = api.get(f'/api/etats/ventes/preparation/2025/export/{format_}', params={'empreinte': d['empreinte_sha256']})
        assert r.status_code == 409, r.text
        d = preparer(api); avant = donnees_metier(application)
        r = api.get(f'/api/etats/ventes/preparation/2025/export/{format_}', params={'empreinte': d['empreinte_sha256']})
        assert r.status_code == 200, r.text
        assert donnees_metier(application) == avant
        if format_ == 'xlsx':
            w = load_workbook(BytesIO(r.content))
            assert w['Synthèse']['B26'].value == 150 and w['Synthèse']['B28'].value == 50
            assert w['Comptabilité'].max_row == 3
            refs = [c for row in w['Comptabilité'] for c in row if c.value == REFERENCE_LONGUE]
            assert len(refs) == 1 and refs[0].data_type == 's'
            assert w['Comptabilité'].row_dimensions[refs[0].row].height >= 45
            assert not any(c.data_type == 'f' for s in w for row in s for c in row)
        else:
            texte = '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(r.content)).pages)
            assert 'RACCORDEMENT COMPTABLE' in texte and '150,00' in texte and '50,00' in texte
        assert d['comptabilite']['ecart_ca_moins_ht'] == '50.00'
        assert 'Raccordement comptable' in d['csv'] and "'=FORMULE-FICTIVE561" in d['csv']


def test_lecture_concurrente_ne_melange_pas_deux_instants(application):
    with closing(client(application)[0]) as api:
        facture(api)
        sid = ok(api.get('/api/societe/moi'))['id']
        atteint, liberer = Event(), Event()
        engine = application['engine']
        def pause(conn, cursor, statement, params, context, many):
            if 'join lignes_ecriture' in statement.lower() and statement.lstrip().lower().startswith('select'):
                atteint.set()
                assert liberer.wait(20), 'Fenêtre de lecture non libérée'
        def lecture():
            with Session(engine) as db:
                return construire(db, sid, 2025)
        event.listen(engine, 'before_cursor_execute', pause)
        try:
            with ThreadPoolExecutor(1) as pool:
                futur = pool.submit(lecture)
                try:
                    assert atteint.wait(15), 'Lecture comptable non atteinte'
                    facture(api, 200)  # Flux API réel concurrent, sans modification d'un définitif.
                finally:
                    liberer.set()
                d = futur.result(timeout=20)
        finally:
            liberer.set(); event.remove(engine, 'before_cursor_execute', pause)
        assert d['totaux']['ht'] == '100.00'
        assert d['comptabilite']['ca_net'] == '100.00'
        assert d['comptabilite']['ecart_ca_moins_ht'] == '0.00'
        fresh = preparer(api)
        assert fresh['totaux']['ht'] == fresh['comptabilite']['ca_net'] == '300.00'


def test_lecture_authentifiee_une_seule_connexion_disponible(application):
    from database import get_db
    from routers.etats import router
    from routers.auth import router as auth_router
    api, email, password = client(application)
    with closing(api):
        facture(api)
        # Le même LOGIN applicatif et les mêmes JWT réels, avec une seule place.
        # Cela détecte un interblocage si l'authentification garde la connexion
        # pendant que la préparation tente d'en emprunter une seconde.
        moteur = create_engine(make_url(application['cluster']['url']).set(username='hisabpro'),
            pool_size=1, max_overflow=0, pool_timeout=1)
        app = FastAPI(); app.include_router(router); app.include_router(auth_router)
        def session():
            with Session(moteur) as db:
                yield db
        app.dependency_overrides[get_db] = session
        try:
            with TestClient(app, raise_server_exceptions=False) as local:
                # Le serveur nonce et ce processus ont chacun leur clé JWT de
                # laboratoire : authentifier réellement l'utilisateur ici aussi.
                token = ok(local.post('/api/auth/login', json={'email': email, 'password': password}))['access_token']
                r = local.get('/api/etats/ventes/preparation/2025', headers={'Authorization': 'Bearer ' + token})
                assert r.status_code == 200, r.text
                assert r.json()['comptabilite']['ca_net'] == '100.00'
            assert moteur.pool.checkedout() == 0
        finally:
            moteur.dispose()


@pytest.mark.parametrize('role,largeur', [('admin', 1365), ('lecture', 390)])
def test_raccordement_visible_et_exporte_dans_le_navigateur(application, role, largeur, tmp_path):
    playwright = pytest.importorskip('playwright.sync_api')
    api, email, password = client(application)
    with closing(api), playwright.sync_playwright() as p:
        facture(api); manuel(api)
        if role != 'admin':
            email = email.replace('@', '-lecture@')
            ok(api.post('/api/utilisateurs', json={'nom': 'Lecteur ventes561', 'email': email,
                'mot_de_passe': password, 'role': role}), 201)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            region = ouvrir(page, application, email, password)
            page.locator('select').filter(has=page.locator('option[value="2025"]')).first.select_option('2025')
            region.get_by_role('button', name='Préparer les ventes', exact=True).click()
            controle = region.get_by_role('region', name='Raccordement comptable des ventes', exact=True)
            playwright.expect(controle).to_contain_text('150,00 MAD')
            playwright.expect(controle).to_contain_text('50,00 MAD')
            playwright.expect(controle).to_contain_text('Un écart nul ne prouve')
            with page.expect_download() as dl:
                region.get_by_role('button', name='Exporter les ventes Excel', exact=True).click()
            chemin_xlsx = tmp_path / 'ventes561.xlsx'
            dl.value.save_as(chemin_xlsx)
            w = load_workbook(chemin_xlsx)
            assert w['Synthèse']['B28'].value == 50 and w['Comptabilité'].max_row == 3
            with page.expect_download() as dl:
                region.get_by_role('button', name='Exporter les ventes PDF', exact=True).click()
            chemin_pdf = tmp_path / 'ventes561.pdf'
            dl.value.save_as(chemin_pdf)
            texte = '\n'.join(p.extract_text() or '' for p in PdfReader(chemin_pdf).pages)
            assert 'RACCORDEMENT COMPTABLE' in texte and '150,00' in texte
            controle.scroll_into_view_if_needed()
            page.screenshot(path=str(tmp_path / f'ventes561_{role}_{largeur}.png'))
            assert len(ok(api.get('/api/ecritures', params={'exercice': 2025}))) == 2
        finally:
            browser.close()
