"""Compatibilité navigateur local sans randomUUID, API métier réelle."""
from contextlib import closing
from playwright.sync_api import sync_playwright,expect
from test_ras_rapprochements681_isole import (
    application,application102,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,application089,application087,migration,
    client,ok,capture,versement,chemin,photo)
from test_e2e_administration_isole import connexion,observer
from test_e2e_ras_tva_registre_isole import ouvrir
from browser_support import chromium_executable


def test_681_cle_idempotence_sans_randomuuid_en_navigateur(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        _,_,c=capture(api);cid=c['capture']['id'];e=versement(api)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(10000)
            page.add_init_script("Object.defineProperty(globalThis.crypto,'randomUUID',{value:undefined,configurable:true})")
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            assert page.evaluate("typeof crypto.randomUUID")=='undefined'
            assert page.evaluate("typeof crypto.getRandomValues")=='function'
            avant=photo(application)
            article=ouvrir(page,application).get_by_role('article',name=f'Capture TVA {cid}',exact=True)
            article.get_by_text('Rapprochement comptable d’un versement',exact=True).click()
            panel=article.get_by_role('region',name=f'Rapprochements de la capture {cid}',exact=True)
            panel.get_by_label('Pièce comptable validée',exact=True).select_option(str(e['id']))
            panel.get_by_label('Montant à rapprocher MAD',exact=True).fill('30')
            panel.get_by_role('checkbox').check()
            try:
                with page.expect_response(lambda r:r.url.endswith(chemin(cid)) and r.request.method=='POST') as rep:
                    panel.get_by_role('button',name='Enregistrer le rapprochement documentaire',exact=True).click()
            except BaseException:
                print('Erreurs navigateur',errors);raise
            assert rep.value.status==201,rep.value.text()
            expect(panel.get_by_text('Actif · 30,00 MAD',exact=True)).to_be_visible()
            assert photo(application)==avant and not errors and not serveur
        finally:browser.close()


def test_681_devise_non_mad_refusee_sans_conversion_presumee(application):
    with closing(client(application)[0]) as api:
        _,_,c=capture(api);cid=c['capture']['id'];e=versement(api)
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}))
        try:
            assert api.get(chemin(cid)).status_code==409
            assert api.get(chemin(cid)+'/options').status_code==409
            assert api.get(chemin(cid)+'/pdf').status_code==409
        finally:ok(api.patch('/api/societe/moi',json={'devise':'MAD'}))
