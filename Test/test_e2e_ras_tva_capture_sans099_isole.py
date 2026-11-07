"""Ancienne installation083 : disponibilité099 visible, aucun DDL implicite."""
from contextlib import closing
from playwright.sync_api import sync_playwright, expect
from test_e2e_facturation_isole import application
from test_ras_capture_reglement_postgres import appliquer
from test_ras_tva_capture_isole import preparer
from test_ras_lecture_conservation import client
from test_e2e_ras_capture_isole import ouvrir
from test_e2e_administration_isole import connexion, observer
from test_permissions_tva_runtime_isole import donnees_metier
from browser_support import chromium_executable


def test_573_sans099_alerte_sans_post_ni_migration(application):
    appliquer(application)
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        preparer(api,cash='350.00')
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(20000)
            erreurs,serveur=observer(page,application['api_url']);posts=[]
            page.on('request',lambda r:posts.append(r.url) if r.method=='POST' and '/ras-tva' in r.url else None)
            connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application)
            ouvrir(page,application,'vente')
            page.get_by_title('Consulter ou déclarer la RAS',exact=True).click()
            modal=page.get_by_role('dialog')
            modal.get_by_role('button',name='RAS TVA guidée',exact=True).click()
            expect(modal.get_by_role('alert')).to_contain_text('099_ras_tva_details.sql')
            expect(modal.get_by_role('button',name='Préparer la capture RAS TVA et son OD',exact=True)).to_have_count(0)
            assert donnees_metier(application)==avant and not posts
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:browser.close()


def test_579_registre_sans099_indisponible_sans_faux_zero(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        preparer(api)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(20000)
            connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application)
            page.goto(application['web_url']+'/declaration-tva')
            page.get_by_text('Registre des retenues TVA · 2026',exact=True).click()
            registre=page.get_by_role('region',name='Registre interne des retenues TVA',exact=True)
            expect(registre.get_by_text('Registre indisponible',exact=False)).to_be_visible()
            expect(registre.get_by_role('button',name='PDF',exact=True)).to_have_count(0)
            expect(registre.get_by_text('0,00 MAD',exact=True)).to_have_count(0)
            assert donnees_metier(application)==avant
        finally:browser.close()
