"""Pièces645 : réponses réelles du serveur isolé, refus et jetons tardifs."""
from contextlib import closing
import pytest
from playwright.sync_api import sync_playwright,expect,TimeoutError as PlaywrightTimeout
from test_justificatifs_modeles_runtime_isole import (
    application,application090,application089,application087,migration,
    ecriture,pdf_fictif,original,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


def journal(page,app,email,password,ref):
    connexion(page,app['web_url'],email,password)
    page.goto(app['web_url']+'/journal')
    bouton=page.locator('tbody tr').filter(has_text=ref).first.locator('button[title^="Justificatifs"]')
    bouton.wait_for();page.wait_for_load_state('networkidle')
    return bouton


def test_645_liste_refusee_signalee_au_lieu_de_faux_vide(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        eid=ecriture(api,validee=False,reference='FICTIF-LISTE645')
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();page.set_default_timeout(15000)
            bouton=journal(page,application,email,password,'FICTIF-LISTE645')
            # Le parent Journal reçoit sa vraie réponse200 avant disparition.
            # Sinon il ferme le dialogue et masque le comportement du composant.
            url=f'/api/ecritures/{eid}/justificatifs'
            parent=page.request.get(application['api_url']+url,headers={'Authorization':api.headers['Authorization']})
            assert parent.status==200
            assert api.delete(f'/api/ecritures/{eid}').status_code==204
            page.route('**'+url,lambda route:route.fulfill(response=parent),times=1)
            with page.expect_response(lambda r:r.url.endswith(f'/attachments/ecriture/{eid}')) as reponse:bouton.click()
            assert reponse.value.status==404
            expect(page.get_by_role('alert').filter(has_text='Chargement des pièces impossible')).to_be_visible()
            expect(page.get_by_text('Aucune pièce jointe',exact=True)).to_have_count(0)
        finally:browser.close()


def test_645_telechargement_tardif_ne_declenche_pas_de_document_autre_jeton(application):
    a,email,password=client(application);b,_,_=client(application)
    with closing(a),closing(b),sync_playwright() as p:
        eid=ecriture(a,reference='FICTIF-DOWNLOAD645')
        f=ok(a.post(f'/api/attachments/ecriture/{eid}',files={'file':('download645.pdf',pdf_fictif(),'application/pdf')}))
        avant=original(application,eid)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000},accept_downloads=True);page.set_default_timeout(15000)
            journal(page,application,email,password,'FICTIF-DOWNLOAD645').click()
            expect(page.get_by_text(f['nom'],exact=True)).to_be_visible()
            page.wait_for_load_state('networkidle');downloads=[];page.on('download',lambda d:downloads.append(d))
            token_a=page.evaluate("localStorage.getItem('hisabpro_token')")
            def tardive(route):
                reponse=route.fetch();assert reponse.status==200
                page.evaluate("t=>localStorage.setItem('hisabpro_token',t)",b.headers['Authorization'].split(' ',1)[1])
                route.fulfill(response=reponse)
            page.route('**'+f['url'],tardive,times=1)
            with page.expect_response(lambda r:r.url.endswith('/download/'+f['nom'])):
                try:
                    with page.expect_download(timeout=1500):
                        page.get_by_role('button',name='Télécharger',exact=True).click()
                except PlaywrightTimeout:
                    pass  # Absence de document pendant la fenêtre d'observation.
                else:
                    raise AssertionError('Un téléchargement tardif a franchi le changement de jeton')
            page.wait_for_load_state('networkidle')
            assert downloads==[] and original(application,eid)==avant
            page.evaluate("t=>localStorage.setItem('hisabpro_token',t)",token_a)
        finally:browser.close()


@pytest.mark.parametrize('largeur',[1440,390])
def test_645_liste_tardive_autre_jeton_ecartee(application,largeur):
    a,email,password=client(application);b,_,_=client(application)
    with closing(a),closing(b),sync_playwright() as p:
        eid=ecriture(a,reference='FICTIF-TARDIVE645')
        f=ok(a.post(f'/api/attachments/ecriture/{eid}',files={'file':('contexte645.pdf',pdf_fictif(),'application/pdf')}))
        avant=original(application,eid)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
            bouton=journal(page,application,email,password,'FICTIF-TARDIVE645')
            token_a=page.evaluate("localStorage.getItem('hisabpro_token')")
            def tardive(route):
                reponse=route.fetch();assert reponse.status==200
                page.evaluate("t=>localStorage.setItem('hisabpro_token',t)",b.headers['Authorization'].split(' ',1)[1])
                route.fulfill(response=reponse)
            page.route('**'+f'/api/attachments/ecriture/{eid}',tardive,times=1)
            with page.expect_response(lambda r:r.url.endswith(f'/attachments/ecriture/{eid}')):bouton.click()
            page.wait_for_load_state('networkidle')
            expect(page.get_by_text(f['nom'],exact=True)).to_have_count(0)
            assert original(application,eid)==avant
            page.evaluate("t=>localStorage.setItem('hisabpro_token',t)",token_a)
        finally:browser.close()
