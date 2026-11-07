"""Registre TVA579 : vrai navigateur, exports, trois rôles et mobile."""
from contextlib import closing
from datetime import date
from pathlib import Path
from io import BytesIO
import pytest
from playwright.sync_api import sync_playwright, expect
from openpyxl import load_workbook
from pypdf import PdfReader
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)
from test_ras_tva_registre_isole import jeu
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_logo_societe import image_data
from test_e2e_administration_isole import connexion, observer
from test_permissions_tva_runtime_isole import donnees_metier
from browser_support import chromium_executable


def ouvrir(page,app):
    page.goto(app['web_url']+'/declaration-tva')
    page.get_by_text(f'Registre des retenues TVA · {date.today().year}',exact=True).click()
    return page.get_by_role('region',name='Registre interne des retenues TVA',exact=True)


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_579_registre_visible_exports_logos_trois_roles(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        jeu(api);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Registre fictif579','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            erreurs,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application)
            registre=ouvrir(page,application)
            expect(registre.get_by_role('article')).to_have_count(3)
            operees=registre.get_by_role('region',name='Retenues opérées sur achats',exact=True)
            subies=registre.get_by_role('region',name='Retenues subies sur ventes',exact=True)
            expect(operees.locator('dl > div').filter(has_text='Actives · OD validées')).to_contain_text('0,00 MAD')
            expect(subies.locator('dl > div').filter(has_text='Actives · OD validées')).to_contain_text('75,00 MAD')
            for fmt,nom in [('csv','CSV'),('xlsx','Excel'),('pdf','PDF')]:
                with page.expect_download() as telechargement:registre.get_by_role('button',name=nom,exact=True).click()
                d=telechargement.value;destination=tmp_path/f'registre579_{role}.{fmt}';d.save_as(destination)
                assert destination.stat().st_size>100
                assert d.suggested_filename==f'registre_ras_tva_{date.today().year}.{fmt}'
                if fmt=='pdf':assert any(p.images for p in PdfReader(destination).pages)
                if fmt=='xlsx':assert len(load_workbook(destination)['Logo société']._images)==1
            registre.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'registre579_{role}_{largeur}.png'))
            assert registre.evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
            expect(page.get_by_text('TVA collectée',exact=True)).to_have_count(0)
            assert donnees_metier(application)==avant
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:browser.close()


def test_579_export_perime_demande_actualisation(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        jeu(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(20000)
            connexion(page,application['web_url'],email,password);registre=ouvrir(page,application)
            expect(registre.get_by_role('article')).to_have_count(3)
            ok(api.patch('/api/societe/moi',json={'raison_sociale':'Nouveau nom fictif579'}))
            registre.get_by_role('button',name='PDF',exact=True).click()
            expect(registre.get_by_role('alert')).to_contain_text('Actualisez')
            expect(registre.get_by_role('article')).to_have_count(0)
            registre.get_by_role('button',name='Actualiser le registre',exact=True).click()
            expect(registre.get_by_role('article')).to_have_count(3)
        finally:browser.close()
