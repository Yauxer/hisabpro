"""Vrais téléchargements Edge des trois classeurs navigateur, PGnonce091."""
from datetime import date
from openpyxl import load_workbook
import pytest
from playwright.sync_api import sync_playwright,expect
from test_e2e_runtime_session_isole import application,application090,application089,application087,migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_logo_societe import image_data
from test_justificatifs_modeles_runtime_isole import ecriture,original
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


@pytest.mark.parametrize('largeur',[1440,390])
def test_logo_et_montants_telecharges_balances_liasse_preparation(application,tmp_path,largeur):
    api,email,password=client(application)
    try:
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data()}))
        eid=ecriture(api);avant=original(application,eid)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':950},accept_downloads=True)
                page.set_default_timeout(20000);errors,server_errors=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/balances')
                expect(page.get_by_text('Balance équilibrée',exact=False)).to_be_visible()
                def telecharger(bouton,nom):
                    with page.expect_download() as event:bouton.click()
                    path=tmp_path/nom;event.value.save_as(path);w=load_workbook(path)
                    assert w.sheetnames[0]=='Logo société'
                    assert len(w['Logo société']._images)==1
                    return w
                w=telecharger(page.get_by_role('button',name='Exporter Excel',exact=True),'balance.xlsx')
                assert next(r for r in w['Balance'].values if r[0]=='5141')[4]==100
                page.goto(application['web_url']+'/liasse-fiscale')
                bouton=page.get_by_role('button',name='Excel',exact=True)
                expect(bouton).to_be_enabled()
                w=telecharger(bouton,'liasse.xlsx')
                assert 'T1 Bilan Actif' in w.sheetnames
                page.get_by_role('button',name='Importer N / N-1').click()
                page.get_by_label('Balance N',exact=True).set_input_files({'name':'FICTIF.csv','mimeType':'text/csv',
                    'buffer':b'compte;debit;credit\n1111;0;1000\n5141;1000;0\n'})
                page.get_by_role('button',name='Contrôler et préparer').click()
                expect(page.get_by_role('status').filter(has_text='Balances contrôlées')).to_be_visible()
                w=telecharger(page.get_by_role('button',name='Exporter la préparation Excel',exact=True),'preparation.xlsx')
                assert ('Total actif',1000) in list(w['Bilan N'].values)
                assert original(application,eid)==avant
                assert not errors,errors
                assert not server_errors,server_errors
            finally:browser.close()
    finally:api.close()
