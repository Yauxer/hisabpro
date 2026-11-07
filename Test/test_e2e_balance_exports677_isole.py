"""Versions de balances et téléchargements natifs Edge/API/PG nonce, sans mock métier."""
from contextlib import closing
from copy import deepcopy
from datetime import date
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import text

from test_e2e_runtime_session_isole import application, application090, application089, application087, migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from test_permissions_tva_runtime_isole import donnees_metier
from test_restauration_runtime_acl_089 import catalogue_acl
from postgres_isole import verifier_cible_isolee
from browser_support import chromium_executable
from test_balance_exports677 import lignes
from test_logo_societe import image_data


BASE = '/api/etats/liasse/balance/dossiers'


def creer(api, comparatif=True):
    y = date.today().year
    n = lignes()
    plan = ok(api.get('/api/plan-comptable'))
    # Le plan initial doit réellement fournir les comptes du jeu, sans insertion SQL.
    assert {r['compte'] for r in n} <= {r['numero'] for r in plan}
    ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG',(20,12))}))
    # Témoin indépendant : cette écriture validée ne provient pas des balances importées.
    e = ok(api.post('/api/ecritures',json={'date':date.today().isoformat(), 'journal':'BQ',
        'reference':'BAL677-TEMOIN', 'libelle':'Capital fictif indépendant des balances',
        'lignes':[{'compte':'5141','debit':333}, {'compte':'1111','credit':333}]}),201)
    ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
    data = {'exercice':y, 'fichier_n':'balance_fictive_N.csv', 'lignes_n':n,
            'fichier_n1':'balance_fictive_N1.csv' if comparatif else None,
            'lignes_n1':lignes(2) if comparatif else None}
    v1 = ok(api.post(BASE,json=data),201)
    second = deepcopy(data); second['lignes_n'] = lignes(2)
    v2 = ok(api.post(BASE,json=second),201)
    assert (v1['version'],v2['version']) == (1,2)
    return v1,v2,e


def verifier_fichiers(xlsx, pdf, v1, comparatif):
    wb = load_workbook(BytesIO(xlsx))
    assert ('Version conservée','1') in list(wb['Dossier'].values)
    assert ('Empreinte des données normalisées',v1['empreinte_sha256']) in list(wb['Dossier'].values)
    assert (None,'TOTAL GÉNÉRAL ACTIF',50000,300,49700,24850 if comparatif else 'Indisponible') in list(wb['Bilan actif'].values)
    sources = list(wb['Balance source N'].values)[1:]
    assert {r[0]:r[1:] for r in sources}['28321'] == (0,300)
    assert ('Balance source N-1' in wb.sheetnames) is comparatif
    reader = PdfReader(BytesIO(pdf))
    texte = ' '.join(' '.join(p.extract_text() for p in reader.pages).split())
    assert '49 700,00' in texte and '50 000,00' in texte and v1['empreinte_sha256'] in texte
    assert 'Sous-postes pour mémoire' in texte and 'Balance source normalisée N' in texte
    assert ('Balance source normalisée N-1' in texte) is comparatif
    assert any(page.images for page in reader.pages)
    with ZipFile(BytesIO(xlsx)) as z:
        assert any(n.startswith('xl/media/') for n in z.namelist())


@pytest.mark.parametrize('largeur,comparatif,role', [(1440,True,'admin'),(390,False,'admin'),(390,True,'lecture')])
def test_677_import_versions_rechargement_et_exports_figes_edge(application,largeur,comparatif,role,tmp_path):
    c = application['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']) and application['role_sql']=='hisabpro'
    api,email,password = client(application)
    with closing(api),sync_playwright() as p:
        v1,v2,e = creer(api,comparatif)
        lecteur = None
        if role == 'lecture':
            lecteur,email,password = client(application)
            sid = ok(api.get('/api/auth/me'))['societe_id']
            ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
            token = ok(lecteur.post(f'/api/societes/switcher/{sid}'))['access_token']
            lecteur.headers['Authorization']='Bearer '+token
        browser = p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page = browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True)
            page.set_default_timeout(15000)
            errors,serveur = observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            if lecteur:
                # Une nouvelle connexion reprend la société principale du lecteur.
                # Changer de contexte par le vrai sélecteur comme l'utilisateur.
                nom = ok(api.get('/api/societe/moi'))['raison_sociale']
                principal = ok(lecteur.get('/api/societes/mes-societes'))
                principal_nom = next(s['raison_sociale'] for s in principal if s['id'] != sid)
                page.get_by_role('button',name=principal_nom,exact=True).click()
                page.get_by_role('button').filter(has_text=nom).click()
                expect(page.get_by_role('button',name=nom,exact=True)).to_be_visible()
            avant, acl = donnees_metier(application), catalogue_acl(application['engine'])
            page.goto(application['web_url']+'/liasse-fiscale')
            panel = page.locator('section').filter(has=page.get_by_role('heading',name='Préparer depuis des balances externes',exact=True))
            panel.get_by_role('button',name='Consulter les préparations' if lecteur else 'Importer N / N-1',exact=True).click()
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v1['id']))
            expect(panel.get_by_role('status')).to_be_visible()
            expect(panel.get_by_text('Version 1 conservée',exact=False)).to_be_visible()
            if lecteur:
                assert panel.get_by_label('Balance N',exact=True).count()==0
                assert lecteur.post(BASE,json={'exercice':date.today().year,'lignes_n':lignes()}).status_code==403
            page.reload()
            panel.get_by_role('button',name='Consulter les préparations' if lecteur else 'Importer N / N-1',exact=True).click()
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v1['id']))
            expect(panel.get_by_role('status')).to_be_visible()
            fichiers={}
            for fmt,libelle in [('xlsx','Excel'),('pdf','PDF')]:
                with page.expect_download() as download, page.expect_response(lambda r:r.url.endswith(f'{BASE}/{v1["id"]}/{fmt}')) as response:
                    panel.get_by_role('button',name='Exporter la préparation '+libelle,exact=True).click()
                assert response.value.status==200,response.value.text()
                dl=download.value
                assert dl.suggested_filename==f'HisabPro_Preparation_{date.today().year}_v1.{fmt}'
                chemin=tmp_path/f'preparation677-{largeur}-{role}.{fmt}';dl.save_as(chemin)
                fichiers[fmt]=chemin.read_bytes()
            verifier_fichiers(fichiers['xlsx'],fichiers['pdf'],v1,comparatif)
            page.screenshot(path=str(tmp_path/f'balance677-{largeur}-{role}.png'),full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors and not serveur,(errors,serveur)
            assert ok(api.get(BASE+f'/{v1["id"]}'))==v1
            assert ok(api.get(BASE+f'/{v2["id"]}'))==v2
            assert donnees_metier(application)==avant
            assert catalogue_acl(application['engine'])==acl
        finally:
            browser.close()
            if lecteur:lecteur.close()


def test_677_api_native_isolation_roles_et_relecture_ancienne_version(application):
    a,_,_=client(application);b,_,_=client(application)
    with closing(a),closing(b):
        row,_,e=creer(a)
        path=BASE+f'/{row["id"]}/xlsx'
        avant=donnees_metier(application)
        assert b.get(path).status_code==404
        with httpx.Client(base_url=application['api_url']) as anonyme:
            assert anonyme.get(path).status_code==401
        xlsx=a.get(path);assert xlsx.status_code==200,xlsx.text
        pdf=a.get(BASE+f'/{row["id"]}/pdf');assert pdf.status_code==200,pdf.text
        verifier_fichiers(xlsx.content,pdf.content,row,True)
        assert ok(a.get(BASE+f'/{row["id"]}'))==row
        assert donnees_metier(application)==avant
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT est_validee FROM ecritures WHERE id=:id'),{'id':e['id']}) is True
