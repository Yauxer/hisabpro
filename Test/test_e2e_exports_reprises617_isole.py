from contextlib import closing
from io import BytesIO
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from playwright.sync_api import sync_playwright,expect
from test_reprises_provisions615_isole import (
    application,application099,application098,application097,application093,application092,
    application091,application090,application089,application087,migration)
from test_exports_reprises617_isole import preparer_source
from test_reprises_provisions615_isole import PATH
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_e2e_administration_isole import connexion,observer
from test_e2e_reprises_provisions615_isole import ouvrir
from browser_support import chromium_executable


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_617_telechargements_reels_roles_et_logo(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        aid=preparer_source(api)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Fictif617','email':email,'mot_de_passe':password,'role':role}),201)
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            region=ouvrir(page,application,aid);expect(region).to_contain_text('800,00 MAD')
            avant=donnees_metier(application)
            for fmt,libelle in [('pdf','PDF'),('xlsx','Excel')]:
                with page.expect_download() as sortie:region.get_by_role('button',name='Télécharger le suivi '+libelle,exact=True).click()
                d=sortie.value;fichier=tmp_path/f'reprises617_{role}.{fmt}';d.save_as(fichier)
                assert d.suggested_filename==f'suivi_reprises_provision_{aid}.{fmt}'
                if fmt=='pdf':
                    doc=PdfReader(fichier);assert any(x.images for x in doc.pages)
                    assert '800.00' in '\n'.join(x.extract_text() or '' for x in doc.pages)
                else:
                    doc=load_workbook(fichier);assert doc['Synthèse']['B15'].value==800
                    assert doc['Logo société']._images
            assert donnees_metier(application)==avant
            region.scroll_into_view_if_needed()
            assert region.evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
            page.screenshot(path=str(tmp_path/f'reprises617_{role}_{largeur}.png'))
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()


def test_617_reponse_preparee_tardive_apres_changement_exercice_ne_telecharge_pas(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        aid=preparer_source(api)
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(20000)
            erreurs,serveur=observer(page,application['api_url']);telechargements=[];exports=[]
            page.on('download',lambda d:telechargements.append(d.suggested_filename))
            page.on('request',lambda r:exports.append(r.url) if '/reprises-provisions/' in r.url and '/export/' in r.url else None)
            connexion(page,application['web_url'],email,password)
            region=ouvrir(page,application,aid)
            def retarder(route):
                reponse=route.fetch()  # Vraie préparation, corps/status inchangés.
                page.get_by_label('Exercice actif',exact=True).select_option('2025')
                route.fulfill(response=reponse)
            page.route(f'**{PATH}/{aid}/preparation',retarder,times=1)
            with page.expect_response(lambda r:r.url.endswith(f'{PATH}/{aid}/preparation')):
                region.get_by_role('button',name='Télécharger le suivi PDF',exact=True).click()
            expect(page.get_by_role('heading',name="Clôture de l'exercice 2025",exact=True)).to_be_visible()
            page.wait_for_timeout(250)
            assert not telechargements and not exports
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()
