"""Archive annuelle : Edge, vraie API et PostgreSQL éphémère exclusivement.

Dossier synthétique explicite : capital de 10 000, aucune exploitation,
immobilisation, stock, sûreté, engagement, devise ou changement de méthode.
La CM est celle calculée par le produit, sans qualification fiscale inventée.
"""
import hashlib
import json
from pathlib import Path
import uuid

import httpx
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def test_archive_liasse_finalisation_exports_empreinte_et_immutabilite(application, tmp_path):
    cible = application['cluster']
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    connection = application['engine'].raw_connection()
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute((Path(__file__).resolve().parents[1] / 'hisabpro-backend' /
                            '027_liasse_fiscale_archive.sql').read_text(encoding='utf-8'))
    finally:
        connection.close()
    suffix = uuid.uuid4().hex[:8]
    email, password = f'archive-{suffix}@example.com', 'ArchiveE2E132!'
    nom = 'Archive fictive E2E ' + suffix
    with httpx.Client(base_url=application['api_url'], timeout=30) as api:
        inscription = ok(api.post('/api/auth/register', json={'nom': 'Admin archive fictive',
            'email': email, 'password': password, 'raison_sociale': nom}))
        api.headers['Authorization'] = 'Bearer ' + inscription['access_token']
        societe = ok(api.patch('/api/societe/moi', json={'identifiant_fiscal': '99000001',
            'ice': '009900000000001', 'exercice_debut': 2025, 'capital_social': 10000,
            'forme_juridique': 'SARL', 'adresse': 'Adresse fictive du laboratoire'}))
        capital = ok(api.post('/api/ecritures', json={'date': '2025-01-01', 'journal': 'OD',
            'reference': 'CAP-ARCHIVE', 'libelle': 'Capital fictif archive',
            'lignes': [{'compte': '5141', 'debit': 10000}, {'compte': '1111', 'credit': 10000}]}), 201)
        ok(api.post(f"/api/ecritures/{capital['id']}/valider"))
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium/Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': 1366, 'height': 1000}, accept_downloads=True)
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                page.on('dialog', lambda dialog: dialog.accept())
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/cloture')
                page.get_by_label('Exercice actif', exact=True).select_option('2025')
                page.goto(application['web_url'] + '/liasse-fiscale')
                playwright.expect(page.get_by_role('button', name='Finaliser', exact=True)).to_be_disabled()
                avant = ok(api.get('/api/etats/liasse/2025'))
                assert not avant['controles']['pret_a_finaliser']
                assert api.post('/api/etats/liasse/2025/finaliser').status_code == 409
                ok(api.post('/api/cloture/cloturer?exercice=2025'))
                fiscal = ok(api.get('/api/fiscalite/is/2025'))
                assert fiscal['comptabilisation_is']['coherente'], fiscal
                ok(api.post('/api/fiscalite/is/2025/liquidation/confirmer'))
                etic = ok(api.get('/api/etats/etic/2025'))
                for section in etic['sections']:
                    code = section['code']
                    if section['mode'] == 'manuel':
                        contenu = {'neant': True}
                        if code == 'A1':
                            contenu = {'texte': 'Dossier fictif sans exploitation : banque au nominal, capital libéré intégralement.'}
                        elif code == 'C1':
                            contenu = {'lignes': [{'associe': 'Associé unique fictif', 'identifiant': 'Adresse fictive',
                                'titres': 100, 'nominal': 100, 'capital': 10000, 'pourcentage': 100}]}
                        elif code == 'C5':
                            contenu = {'texte': 'Comptes arrêtés dans le laboratoire ; aucun événement postérieur dans ce scénario fictif.'}
                    else:
                        contenu = {'confirme': True, 'texte': 'Données du scénario fictif vérifiées explicitement.'}
                        if code in ('B6', 'B7'):
                            # Le scénario prévoit toutes dettes fiscales exigibles en N+1,
                            # aucune dette échue, devise, entreprise liée ou effet.
                            contenu.update({'autres_analyses_neant': True, 'ventilations': {
                                ligne['compte']: {'plus_un_an': 0, 'moins_un_an': ligne['montant'], 'echues': 0}
                                for ligne in section['automatique'].get('lignes', [])}})
                    ok(api.put(f'/api/etats/etic/2025/{code}', json={'contenu': contenu}))
                prete = ok(api.get('/api/etats/liasse/2025'))
                assert prete['controles']['pret_a_finaliser'], prete['controles']
                assert prete['etats']['bilan']['actif']['total']['net'] == 10000
                assert prete['etats']['bilan']['passif']['total'] == 10000
                page.reload()
                bouton = page.get_by_role('button', name='Finaliser', exact=True)
                playwright.expect(bouton).to_be_enabled()
                with page.expect_response(lambda r: r.url.endswith('/api/etats/liasse/2025/finaliser')) as finalisation:
                    bouton.click()
                assert finalisation.value.status == 200, finalisation.value.text()
                empreinte = finalisation.value.json()['empreinte_sha256']
                page.get_by_text('Archive fiscale immuable — version 1', exact=True).wait_for()
                page.get_by_text('Empreinte SHA-256 : ' + empreinte, exact=True).wait_for()
                page.reload()
                page.get_by_text('Archive fiscale immuable — version 1', exact=True).wait_for()
                assert page.get_by_role('button', name='Finaliser', exact=True).count() == 0
                page.get_by_text("T1 à T25 : numérotation interne HisabPro", exact=False).wait_for()
                page.get_by_role('button', name='T1 · Bilan', exact=True).click()
                page.get_by_role('button', name='T2 · CPC', exact=True).click()
                page.get_by_role('button', name='T3–T25 · ETIC', exact=True).click()
                page.get_by_text('T3', exact=True).wait_for()
                page.get_by_text('T8', exact=True).wait_for()
                page.get_by_text('T25', exact=True).wait_for()
                assert page.get_by_text('A1 —', exact=False).count() == 1
                assert page.get_by_text('B2bis —', exact=False).count() == 1
                assert page.get_by_text('C5 —', exact=False).count() == 1
                with page.expect_download() as pdf:
                    page.get_by_role('button', name='PDF', exact=True).click()
                pdf_path = tmp_path / 'archive.pdf'; pdf.value.save_as(pdf_path)
                pdf_text = ' '.join(x.extract_text() or '' for x in PdfReader(pdf_path).pages)
                assert nom in pdf_text and empreinte in pdf_text
                assert 'T1 - Bilan - Actif' in pdf_text
                assert 'T2 - Compte de Produits et Charges' in pdf_text
                assert 'T3 / A1' in pdf_text and 'T8 / B2bis' in pdf_text and 'T25 / C5' in pdf_text
                assert 'numérotation interne HisabPro' in pdf_text
                with page.expect_download() as excel:
                    page.get_by_role('button', name='Excel', exact=True).click()
                excel_path = tmp_path / 'archive.xlsx'; excel.value.save_as(excel_path)
                workbook = load_workbook(excel_path, data_only=True)
                assert 'ETIC' in workbook.sheetnames
                synthese = [row[:2] for row in workbook['Synthese'].values]
                assert ('Statut', 'finalisee') in synthese
                assert ('Raison sociale', nom) in synthese
                assert ('Version archive', 1) in synthese
                assert ('Empreinte SHA-256', empreinte) in synthese
                assert 'T1 Bilan Actif' in workbook.sheetnames and 'T1 Bilan Passif' in workbook.sheetnames
                assert any(row[0] == 'XV' and row[2] == -3000 for row in workbook['T2 CPC'].values)
                etic_references = {row[0] for row in workbook['ETIC'].values}
                assert {'T3 / A1', 'T8 / B2bis', 'T25 / C5'} <= etic_references
                assert excel.value.suggested_filename.endswith('_FINAL.xlsx')
                archive = ok(api.get('/api/etats/liasse/2025/archive'))
                assert archive['archive']['version'] == 1
                assert archive['archive']['empreinte_sha256'] == empreinte
                assert api.post('/api/etats/liasse/2025/finaliser').status_code == 409
                assert api.put('/api/etats/etic/2025/A1', json={'contenu': {'texte': 'Mutation interdite'}}).status_code == 409
                refus_fiscal = api.put('/api/fiscalite/is/2025/parametres', json={'taux_is_force': 20,
                    'justification_taux_force': 'Tentative FICTIVE949 après archive'})
                assert refus_fiscal.status_code == 409, refus_fiscal.text
                operation2026 = ok(api.post('/api/ecritures', json={'date': '2026-01-02', 'journal': 'BQ',
                    'reference': 'CAP-N1-FICTIF949', 'libelle': 'Mutation N+1 FICTIVE949',
                    'lignes': [{'compte': '5141', 'debit': 10}, {'compte': '1111', 'credit': 10}]}), 201)
                ok(api.post(f'/api/ecritures/{operation2026["id"]}/valider'))
                ok(api.patch('/api/societe/moi', json={'raison_sociale': nom + ' modifiée après archive'}))
                relecture = ok(api.get('/api/etats/liasse/2025'))
                assert relecture['societe']['raison_sociale'] == nom
                assert relecture['archive']['empreinte_sha256'] == empreinte
                (Path(__file__).resolve().parents[1] / '.codex-tests/archive949_preuve.json').write_text(
                    json.dumps({'nonce': cible['nonce'], 'empreinte_avant': empreinte,
                        'empreinte_apres_N1': relecture['archive']['empreinte_sha256'],
                        'refus_etic': 409, 'refus_fiscal': refus_fiscal.status_code,
                        'ecriture_N1': operation2026['id'], 'jeu': 'Capital-seul fictif, distinct du dossier annuel20/23'},
                        ensure_ascii=False, indent=2), encoding='utf8')
                with Session(application['engine']) as db:
                    rec = db.query(models.LiasseFiscaleArchive).filter_by(societe_id=societe['id'], exercice=2025).one()
                    assert rec.version == 1 and rec.empreinte_sha256 == empreinte
                    assert hashlib.sha256(rec.contenu_json.encode('utf-8')).hexdigest() == empreinte
                    assert json.loads(rec.contenu_json)['societe']['raison_sociale'] == nom
                    assert [s['code'] for s in json.loads(rec.contenu_json)['etic']['sections']] == [s['code'] for s in etic['sections']]
                    archive_id = rec.id
                for sql in ('UPDATE liasses_fiscales_archives SET version=2 WHERE id=:id',
                            'DELETE FROM liasses_fiscales_archives WHERE id=:id'):
                    with pytest.raises(DBAPIError, match='immuable'):
                        with application['engine'].begin() as db:
                            db.execute(text(sql), {'id': archive_id})
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print('UI archive fictive :', page.url, page.locator('body').inner_text()[:6000])
                print('Log API isolée :', application['api_log'].read_text(encoding='utf-8', errors='replace')[-6000:])
                raise
            finally:
                browser.close()
