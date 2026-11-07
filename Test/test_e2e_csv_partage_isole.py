"""Téléchargement CSV réel du Journal, sources comptables nonce conservées."""
import csv
from datetime import date
import io

import pytest
from playwright.sync_api import expect

from browser_support import chromium_executable
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import connexion, observer
from test_ras_lecture_conservation import client


@pytest.mark.parametrize('largeur',[1365,390])
def test_journal_csv_texte_protege_montants_exacts_et_sources_inchangees(application,tmp_path,largeur):
    api,email,password=client(application)
    try:
        annee=date.today().year
        r=api.post('/api/ecritures',json={'date':f'{annee}-01-05','journal':'BQ',
            'reference':'=REF-CSV','libelle':'=1+1',
            'lignes':[{'compte':'5141','debit':120.25,'libelle':'@LIGNE-CSV'},
                      {'compte':'1111','credit':120.25}]})
        assert r.status_code==201,r.text
        assert api.post(f"/api/ecritures/{r.json()['id']}/valider").status_code==200
        avant=api.get('/api/ecritures',params={'exercice':annee}).json()
        executable=chromium_executable()
        if not executable:
            pytest.skip('Chromium / Edge absent')
        playwright=pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=executable,headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':900},accept_downloads=True)
                page.set_default_timeout(20000)
                erreurs,serveur=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/journal')
                expect(page.get_by_text('=1+1',exact=True)).to_be_visible()
                with page.expect_download() as output:
                    page.get_by_role('button',name='Exporter CSV',exact=True).click()
                download=output.value
                assert download.suggested_filename==f'journal_{annee}.csv'
                path=tmp_path/f'journal-{largeur}.csv'
                download.save_as(path)
                contenu=path.read_bytes()
                assert contenu.startswith(b'\xef\xbb\xbf')
                rows=list(csv.DictReader(io.StringIO(contenu.decode('utf-8-sig'),newline=''),delimiter=';'))
                assert len(rows)==2
                assert rows[0]['Libellé écriture']=="'=1+1"
                assert rows[0]['Référence pièce']=="'=REF-CSV"
                assert rows[0]['Libellé ligne']=="'@LIGNE-CSV"
                assert [(row['Débit'],row['Crédit']) for row in rows]==[('120,25','0,00'),('0,00','120,25')]
                assert not erreurs and not serveur,(erreurs,serveur)
            finally:
                browser.close()
        assert api.get('/api/ecritures',params={'exercice':annee}).json()==avant
        assert avant[0]['libelle']=='=1+1' and avant[0]['reference']=='=REF-CSV'
    finally:
        api.close()
