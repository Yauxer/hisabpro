"""Vrais téléchargements Excel/PDF depuis la préparation,Edge etPGnonce."""
from datetime import date
from io import BytesIO
from pathlib import Path
import pytest
from pypdf import PdfReader
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_e2e_ventes_preparation_isole import application,ouvrir
from test_ventes_preparation_isole import facture,ok,photographie
from test_ras_lecture_conservation import client


@pytest.mark.parametrize('largeur',[1365,390])
def test_exports_depuis_interface_et_sources_changees_refusees(application,largeur,tmp_path):
    api,email,password=client(application)
    try:
        facture(api,100)
        avant=photographie(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
                region=ouvrir(page,application,email,password)
                for format in ('Excel','PDF'):
                    expect(region.get_by_role('button',name='Exporter les ventes '+format,exact=True)).to_be_disabled()
                region.get_by_role('button',name='Préparer les ventes',exact=True).click()
                for format,extension in [('Excel','xlsx'),('PDF','pdf')]:
                    btn=region.get_by_role('button',name='Exporter les ventes '+format,exact=True)
                    expect(btn).to_be_enabled()
                    with page.expect_download() as fichier:btn.click()
                    assert fichier.value.suggested_filename==f'VENTES_PREPARATION_INTERNE_{date.today().year}.{extension}'
                    path=tmp_path/f'ventes.{extension}';fichier.value.save_as(path)
                    if extension=='xlsx':
                        w=load_workbook(path);assert w['Synthèse']['B12'].value==100 and w['Synthèse']['B14'].value==120
                    else:
                        texte='\n'.join(p.extract_text() or '' for p in PdfReader(path).pages)
                        assert '100,00' in texte and '120,00' in texte and 'PRÉPARATION INTERNE' in texte
                assert photographie(application)==avant
                facture(api,200);apres_creation=photographie(application)
                with page.expect_response(lambda r:'/export/pdf?' in r.url) as refus:
                    region.get_by_role('button',name='Exporter les ventes PDF',exact=True).click()
                assert refus.value.status==409
                expect(region.get_by_role('alert')).to_contain_text('Les sources ont changé')
                region.get_by_role('button',name='Actualiser les ventes',exact=True).click()
                expect(region.locator('tbody tr')).to_have_count(2)
                expect(region.get_by_role('alert')).to_have_count(0)
                with page.expect_download() as fichier:
                    region.get_by_role('button',name='Exporter les ventes PDF',exact=True).click()
                fichier.value.save_as(tmp_path/'actualise.pdf')
                texte='\n'.join(p.extract_text() or '' for p in PdfReader(tmp_path/'actualise.pdf').pages)
                assert '300,00' in texte and '360,00' in texte
                assert photographie(application)==apres_creation
            finally:browser.close()
    finally:api.close()


def test_export_pdf_tardif_ignore_apres_changement_exercice(application):
    api,email,password=client(application)
    try:
        annee=date.today().year;facture(api,100)
        ok(api.post('/api/exercices',json={'annee':annee-1,'date_debut':f'{annee-1}-01-01','date_fin':f'{annee-1}-12-31'}),201)
        avant=photographie(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True);retenues=[]
            try:
                page=browser.new_page();page.set_default_timeout(20000);downloads=[]
                page.on('download',lambda d:downloads.append(d))
                region=ouvrir(page,application,email,password)
                region.get_by_role('button',name='Préparer les ventes',exact=True).click()
                expect(region.get_by_role('button',name='Exporter les ventes PDF',exact=True)).to_be_enabled()
                def retenir(route):
                    reponse=route.fetch();assert reponse.status==200
                    retenues.append((route,reponse));page.evaluate("console.log('EXPORT423_PDF_RETENU')")
                motif=f'**/ventes/preparation/{annee}/export/pdf?*'
                page.route(motif,retenir)
                with page.expect_console_message(lambda m:m.text=='EXPORT423_PDF_RETENU'):
                    region.get_by_role('button',name='Exporter les ventes PDF',exact=True).click()
                expect(region.get_by_role('button',name='Actualiser les ventes',exact=True)).to_be_disabled()
                page.locator('select').filter(has=page.locator(f'option[value="{annee-1}"]')).first.select_option(str(annee-1))
                region=page.get_by_role('region',name='Préparation annuelle des ventes',exact=True)
                expect(region.get_by_role('button',name='Préparer les ventes',exact=True)).to_be_enabled()
                with page.expect_event('requestfinished',predicate=lambda r:'/export/pdf?' in r.url):
                    for route,reponse in retenues:route.fulfill(response=reponse)
                retenues.clear();page.unroute(motif)
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                assert downloads==[]
                expect(region.get_by_role('button',name='Exporter les ventes PDF',exact=True)).to_be_disabled()
                assert photographie(application)==avant
            finally:
                for route,reponse in retenues:route.fulfill(response=reponse)
                browser.close()
    finally:api.close()
