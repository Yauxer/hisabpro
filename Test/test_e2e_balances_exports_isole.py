"""Exports balances : vrais téléchargements Edge/API/PostgreSQL éphémère."""
from datetime import date
from pathlib import Path
import uuid

import httpx
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def pdf_texte(path):
    return '\n'.join(p.extract_text() or '' for p in PdfReader(path).pages)


def cellules(wb):
    return list(wb['Balance'].values)


def preparer(application):
    suffix = uuid.uuid4().hex[:8]
    email, password, annee = f'balances-export-{suffix}@example.com', 'BalanceExports2026!', date.today().year
    api = httpx.Client(base_url=application['api_url'], timeout=30)
    r = api.post('/api/auth/register', json={'nom': 'Administration balances fictive', 'email': email, 'password': password, 'raison_sociale': 'Balances fictives ' + suffix})
    assert r.status_code == 200, r.text
    api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
    sid = api.get('/api/societe/moi').json()['id']
    r = api.post('/api/ecritures', json={'date': f'{annee}-01-05', 'journal': 'OD', 'reference': 'CAP-EXPORT', 'libelle': 'Capital fictif exports', 'lignes': [{'compte': '5141', 'debit': 10000}, {'compte': '1111', 'credit': 10000}]})
    assert r.status_code == 201, r.text
    assert api.post(f"/api/ecritures/{r.json()['id']}/valider").status_code == 200
    fids, noms = {}, {}
    for nature, prix, jour in [('vente', 1000, '05'), ('achat', 500, '06')]:
        nom = '=Tiers fictif ' + nature + ' ' + suffix
        r = api.post('/api/tiers', json={'nom': nom, 'type': 'client' if nature == 'vente' else 'fournisseur'})
        assert r.status_code == 201, r.text
        tid = r.json()['id']
        r = api.post('/api/factures', json={'type': nature, 'date': f'{annee}-03-{jour}', 'date_echeance': f'{annee}-03-15', 'tiers': nom, 'tiers_id': tid, 'reference': 'EXPORT-' + nature, 'lignes': [{'description': 'Prestation fictive exports', 'quantite': 1, 'prix_unitaire': prix, 'tva': 20}]})
        assert r.status_code == 201, r.text
        fid = r.json()['id']; fids[nature] = fid; noms[nature] = nom
        assert api.post(f'/api/factures/{fid}/valider').status_code == 200
        r = api.post(f'/api/factures/{fid}/comptabiliser')
        assert r.status_code == 200, r.text
        assert api.post(f"/api/ecritures/{r.json()['ecriture_id']}/valider").status_code == 200
    r = api.post('/api/reglements', json={'date': f'{annee}-03-10', 'facture_id': fids['vente'], 'tiers': noms['vente'], 'montant': 400, 'mode': 'virement', 'comptabiliser': True})
    assert r.status_code == 201, r.text
    assert api.post(f"/api/ecritures/{r.json()['ecriture_id']}/valider").status_code == 200
    return api, email, password, annee, sid, noms


def telecharger(page, format, tmp_path, nom):
    with page.expect_download() as output:
        page.get_by_role('button', name='Exporter ' + format, exact=True).click()
    download = output.value
    suffix = '.xlsx' if format == 'Excel' else '.pdf'
    assert download.suggested_filename.endswith(suffix)
    path = tmp_path / (nom + suffix)
    download.save_as(path)
    assert path.exists() and path.stat().st_size > 100
    return path


def test_balances_generale_auxiliaire_agee_filtres_excel_pdf_reels(application, tmp_path):
    api, email, password, annee, sid, noms = preparer(application)
    try:
        with Session(application['engine']) as db:
            avant = {(l.id, l.ecriture_id, l.compte, l.debit, l.credit, l.tiers_id) for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid)}
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(accept_downloads=True)
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/balances', wait_until='domcontentloaded')
                page.get_by_text('Balance équilibrée', exact=False).wait_for()
                page.locator('input[type=date]').nth(0).fill(f'{annee}-03-01')
                with page.expect_response(lambda r: '/api/ecritures/reporting/balance?' in r.url and f'date_from={annee}-03-01' in r.url and f'date_to={annee}-03-31' in r.url and f'exercice={annee}&' in r.url):
                    page.locator('input[type=date]').nth(1).fill(f'{annee}-03-31')
                page.get_by_text('Balance équilibrée', exact=False).wait_for()
                general = load_workbook(telecharger(page, 'Excel', tmp_path, 'generale'), data_only=False)
                lignes = cellules(general)
                assert lignes[2][1] == f'{annee}-03-01 au {annee}-03-31'
                compte_banque = next(r for r in lignes[7:] if r[0] == '5141')
                assert compte_banque[2:] == (10000, 0, 400, 0, 10400, 0)
                assert general['Balance']['A8'].data_type == 's'
                assert general['Balance']['E8'].data_type == 'n'
                total = next(r for r in lignes if r[0] == 'TOTAL GÉNÉRAL')
                assert total[2:] == (10000, 10000, 2200, 2200, 11800, 11800)
                texte = pdf_texte(telecharger(page, 'PDF', tmp_path, 'generale'))
                assert f'{annee}-03-01 au {annee}-03-31' in texte and 'Écritures définitives uniquement' in texte
                assert '10 400,00' in texte and '11 800,00' in texte and '5141' in texte
                page.get_by_role('button', name='Balance Auxiliaire', exact=False).click()
                page.get_by_text(noms['vente'], exact=False).wait_for()
                aux = cellules(load_workbook(telecharger(page, 'Excel', tmp_path, 'aux-client'), data_only=False))
                client = next(r for r in aux[7:] if r[0] == noms['vente'])
                assert client[3:] == (0, 0, 1200, 400, 800, 0)
                assert next(c for row in load_workbook(tmp_path/'aux-client.xlsx')['Balance'] for c in row if c.value == noms['vente']).data_type == 's'
                texte = pdf_texte(telecharger(page, 'PDF', tmp_path, 'aux-client'))
                assert 'Clients (3421)' in texte and noms['vente'] in texte and '800,00' in texte
                assert noms['achat'] not in texte
                page.get_by_role('button', name='Fournisseurs (4411)', exact=True).click()
                aux_fournisseur = cellules(load_workbook(telecharger(page, 'Excel', tmp_path, 'aux-fournisseur'), data_only=True))
                fournisseur = next(r for r in aux_fournisseur[7:] if r[0] == noms['achat'])
                assert fournisseur[3:] == (0, 0, 0, 600, 0, 600)
                texte = pdf_texte(telecharger(page, 'PDF', tmp_path, 'aux-fournisseur'))
                assert 'Fournisseurs (4411)' in texte and noms['achat'] in texte and noms['vente'] not in texte
                page.get_by_role('button', name='Balance Âgée', exact=False).click()
                page.get_by_text(noms['vente'], exact=False).wait_for()
                agee = cellules(load_workbook(telecharger(page, 'Excel', tmp_path, 'agee-client'), data_only=True))
                assert next(r for r in agee[7:] if r[0] == noms['vente'])[4:] == (800, 0, 800, 0, 0, 0)
                texte = pdf_texte(telecharger(page, 'PDF', tmp_path, 'agee-client'))
                assert '1-30 j' in texte and '800,00' in texte and f'Date d’arrêté : {annee}-03-31' in texte
                page.get_by_role('button', name='Fournisseurs (4411)', exact=True).click()
                agee_f = cellules(load_workbook(telecharger(page, 'Excel', tmp_path, 'agee-fournisseur'), data_only=True))
                assert next(r for r in agee_f[7:] if r[0] == noms['achat'])[4:] == (600, 0, 600, 0, 0, 0)
                texte = pdf_texte(telecharger(page, 'PDF', tmp_path, 'agee-fournisseur'))
                assert noms['achat'] in texte and noms['vente'] not in texte
                assert not errors, errors
                assert not server_errors, server_errors
            finally:
                browser.close()
        with Session(application['engine']) as db:
            apres = {(l.id, l.ecriture_id, l.compte, l.debit, l.credit, l.tiers_id) for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid)}
            assert avant == apres
    finally:
        api.close()


def test_pdf_balance_lecture_isolation_et_rejet_filtres(application):
    api, email, password, annee, sid, noms = preparer(application)
    try:
        params = {'exercice': annee, 'genre': 'generale', 'date_from': f'{annee}-03-01', 'date_to': f'{annee}-03-31'}
        lecteur = 'lecture-' + uuid.uuid4().hex[:8] + '@example.com'
        r = api.post('/api/utilisateurs', json={'nom': 'Lecture balances fictive', 'email': lecteur, 'mot_de_passe': password, 'role': 'lecture'})
        assert r.status_code == 201, r.text
        token = api.post('/api/auth/login', json={'email': lecteur, 'password': password}).json()['access_token']
        r = api.get('/api/ecritures/reporting/balance/pdf', params=params, headers={'Authorization': 'Bearer ' + token})
        assert r.status_code == 200 and r.headers['X-HisabPro-Source'] == 'comptabilite-serveur'
        from io import BytesIO
        assert '10 400,00' in '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(r.content)).pages)
        assert api.get('/api/ecritures/reporting/balance/pdf', params={**params, 'genre': 'inventee'}).status_code == 422
        assert api.get('/api/ecritures/reporting/balance/pdf', params={**params, 'date_from': f'{annee}-04-01'}).status_code == 422
        with httpx.Client(base_url=application['api_url']) as autre:
            autre_email = 'autre-' + uuid.uuid4().hex[:8] + '@example.com'
            r = autre.post('/api/auth/register', json={'nom': 'Autre société fictive', 'email': autre_email, 'password': password, 'raison_sociale': 'Autre balance fictive'})
            assert r.status_code == 200
            autre.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
            r = autre.get('/api/ecritures/reporting/balance/pdf', params=params)
            assert r.status_code == 200
            texte = '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(r.content)).pages)
            assert 'Aucune ligne pour cette sélection' in texte and '10 400,00' not in texte and noms['vente'] not in texte
    finally:
        api.close()


def test_libelles_societe_inactifs_subdivisions_et_pdf_pagine(application, tmp_path):
    api, email, password, annee, sid, noms = preparer(application)
    try:
        libelle = 'Banque personnelle fictive ' + uuid.uuid4().hex[:8]
        r = api.patch('/api/plan-comptable/5141', json={'libelle': libelle})
        assert r.status_code == 200, r.text
        subdivisions = {}
        for index in range(25):
            numero = '51419' + f'{index:02d}'
            label = f'Subdivision fictive {index:02d} — ' + ('IdentitéLongue' * 16)
            r = api.post('/api/plan-comptable', json={'numero': numero, 'libelle': label})
            assert r.status_code == 201, r.text
            subdivisions[numero] = label
        r = api.post('/api/ecritures', json={'date': f'{annee}-03-20', 'journal': 'OD', 'reference': 'SUBDIV-EXPORT', 'libelle': 'Ventilation fictive banque', 'lignes': [{'compte': c, 'debit': 1} for c in subdivisions] + [{'compte': '5141', 'credit': 25}]})
        assert r.status_code == 201, r.text
        assert api.post(f"/api/ecritures/{r.json()['id']}/valider").status_code == 200
        for numero in ('5141', next(iter(subdivisions))):
            assert api.patch('/api/plan-comptable/' + numero, json={'actif': False}).status_code == 200
        params = {'exercice': annee, 'date_from': f'{annee}-03-01', 'date_to': f'{annee}-03-31'}
        r = api.get('/api/ecritures/reporting/balance', params=params)
        assert r.status_code == 200, r.text
        comptes = {c['compte']: c for c in r.json()['comptes']}
        assert comptes['5141']['libelle'] == libelle and comptes['5141']['solde_final'] == 10375
        assert all(comptes[c]['libelle'] == label and comptes[c]['solde_final'] == 1 for c, label in subdivisions.items())
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(accept_downloads=True)
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/balances')
                page.get_by_text(libelle, exact=True).wait_for()
                page.get_by_text(next(iter(subdivisions.values())), exact=True).wait_for()
                excel = cellules(load_workbook(telecharger(page, 'Excel', tmp_path, 'libelles'), data_only=True))
                assert next(row for row in excel[7:] if row[0] == '5141')[1] == libelle
                assert all(next(row for row in excel[7:] if row[0] == c)[1] == label for c, label in subdivisions.items())
                pdf = telecharger(page, 'PDF', tmp_path, 'libelles')
                lecteur = PdfReader(pdf)
                assert len(lecteur.pages) >= 2
                texte = pdf_texte(pdf)
                assert libelle in texte
                assert all(c in texte for c in subdivisions)
                assert all('Compte / tiers / référence' in page_pdf.extract_text() for page_pdf in lecteur.pages)
                assert not errors and not server_errors
            finally:
                browser.close()
        with httpx.Client(base_url=application['api_url']) as autre:
            r = autre.post('/api/auth/register', json={'nom': 'Autre société libellés', 'email': 'libelles-' + uuid.uuid4().hex[:8] + '@example.com', 'password': password, 'raison_sociale': 'Autre plan fictif'})
            assert r.status_code == 200
            autre.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
            label_autre = 'Banque propre seconde société'
            assert autre.patch('/api/plan-comptable/5141', json={'libelle': label_autre}).status_code == 200
            r = autre.post('/api/ecritures', json={'date': f'{annee}-03-20', 'journal': 'OD', 'reference': 'ISO-LABEL', 'libelle': 'Capital fictif autre', 'lignes': [{'compte': '5141', 'debit': 75}, {'compte': '1111', 'credit': 75}]})
            assert r.status_code == 201, r.text
            assert autre.post(f"/api/ecritures/{r.json()['id']}/valider").status_code == 200
            r = autre.get('/api/ecritures/reporting/balance', params=params)
            assert next(c for c in r.json()['comptes'] if c['compte'] == '5141')['libelle'] == label_autre
            r = autre.get('/api/ecritures/reporting/balance/pdf', params=params)
            assert r.status_code == 200
            from io import BytesIO
            texte_autre = '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(r.content)).pages)
            assert label_autre in texte_autre and libelle not in texte_autre
    finally:
        api.close()


def test_resultat_comparative_dates_n1_variations_et_exports_reels(application, tmp_path):
    api, email, password, annee, sid, noms = preparer(application)
    try:
        r = api.post('/api/exercices', json={'annee': annee - 1, 'date_debut': f'{annee-1}-01-01', 'date_fin': f'{annee-1}-12-31'})
        assert r.status_code == 201, r.text
        for libelle, jour, lignes in [
            ('Charge fictive N-1', '05', [{'compte': '6111', 'debit': 400}, {'compte': '5141', 'credit': 400}]),
            ('Produit fictif N-1', '06', [{'compte': '5141', 'debit': 600}, {'compte': '7111', 'credit': 600}]),
        ]:
            r = api.post('/api/ecritures', json={'date': f'{annee-1}-03-{jour}', 'journal': 'OD', 'reference': 'COMP-N1-' + jour, 'libelle': libelle, 'lignes': lignes})
            assert r.status_code == 201, r.text
            assert api.post(f"/api/ecritures/{r.json()['id']}/valider").status_code == 200
        label_charge = '=Charges personnelles ' + uuid.uuid4().hex[:8]
        label_produit = 'Produits personnels ' + uuid.uuid4().hex[:8]
        assert api.patch('/api/plan-comptable/6111', json={'libelle': label_charge}).status_code == 200
        assert api.patch('/api/plan-comptable/7111', json={'libelle': label_produit}).status_code == 200
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(accept_downloads=True)
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/balances')
                page.get_by_text('Balance équilibrée', exact=False).wait_for()
                page.locator('input[type=date]').nth(0).fill(f'{annee}-03-01')
                with page.expect_response(lambda r: '/api/ecritures/reporting/balance?' in r.url and f'date_from={annee}-03-01' in r.url and f'date_to={annee}-03-31' in r.url and f'exercice={annee}&' in r.url):
                    page.locator('input[type=date]').nth(1).fill(f'{annee}-03-31')
                page.get_by_text('Balance équilibrée', exact=False).wait_for()
                page.get_by_role('button', name='Balance Résultat', exact=False).click()
                page.get_by_text(label_charge, exact=True).wait_for()
                xlsx = load_workbook(telecharger(page, 'Excel', tmp_path, 'resultat'), data_only=False)
                rows = cellules(xlsx)
                assert next(r for r in rows[7:] if r[0] == '6111')[1:] == (label_charge, 500, 0)
                assert next(r for r in rows[7:] if r[0] == '7111')[1:] == (label_produit, 0, 1000)
                assert next(r for r in rows if r[0] == 'TOTAL')[2:] == (500, 1000)
                assert next(r for r in rows if r[0] == 'Résultat net signé')[1] == 500
                assert next(c for row in xlsx['Balance'] for c in row if c.value == label_charge).data_type == 's'
                texte = pdf_texte(telecharger(page, 'PDF', tmp_path, 'resultat'))
                assert label_charge in texte and label_produit in texte and 'Résultat net signé : 500,00 MAD' in texte
                page.get_by_role('button', name='Balance Comparative', exact=False).click()
                page.get_by_text(label_charge, exact=True).wait_for()
                xlsx = load_workbook(telecharger(page, 'Excel', tmp_path, 'comparative'), data_only=False)
                rows = cellules(xlsx)
                assert rows[2][1] == f'{annee}-03-01 au {annee}-03-31 comparé au {annee-1}-03-01 au {annee-1}-03-31'
                assert next(r for r in rows[7:] if r[0] == '6111')[1:] == (label_charge, 400, 500, 100, 25)
                assert next(r for r in rows[7:] if r[0] == '7111')[2:5] == (-600, -1000, -400)
                assert next(r for r in rows[7:] if r[0] == '7111')[5] == pytest.approx(-200/3)
                assert next(r for r in rows[7:] if r[0] == '4455')[5] == 'N/A'
                variation_cell = next(row[5] for row in list(xlsx['Balance'])[7:] if row[0].value == '6111')
                assert variation_cell.data_type == 'n' and variation_cell.number_format == '0.0"%"'
                texte = pdf_texte(telecharger(page, 'PDF', tmp_path, 'comparative'))
                assert label_charge in texte and label_produit in texte and '25.0%' in texte and '-66.7%' in texte and 'N/A' in texte
                assert f'Comparé au {annee-1}-03-01 au {annee-1}-03-31' in texte
                assert 'hors soldes d’ouverture' in texte
                assert not errors and not server_errors
            finally:
                browser.close()
        params = {'genre': 'comparative', 'exercice': 2024, 'date_from': '2024-02-29', 'date_to': '2024-03-31'}
        r = api.get('/api/ecritures/reporting/balance/pdf', params=params)
        assert r.status_code == 200, r.text
        from io import BytesIO
        assert '2023-02-28' in '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(r.content)).pages)
        assert api.get('/api/ecritures/reporting/balance/pdf', params={**params, 'date_from': '2023-02-29'}).status_code == 422
    finally:
        api.close()
