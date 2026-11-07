"""Confirmation des propositions, contexte retardé et refus réel : Edge/PGnonce."""
import pytest
import re
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import connexion,observer
from test_ras_lecture_conservation import client
from test_rapprochement_ventilation_isole import migration
from test_rapprochement_propositions_isole import deux_propositions,flags
from test_lecture_reglements_historiques import photo

@pytest.mark.parametrize('largeur',[1365,390])
def test_selection_confirmation_rechargement_et_origines_preservees(application,migration,largeur):
    api,email,password=client(application)
    try:
        rid,simple=deux_propositions(application,api);avant=photo(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
                errors,server=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/rapprochement')
                page.get_by_role('button',name='Proposer les rapprochements',exact=True).click()
                dialog=page.get_by_role('dialog',name='Propositions de rapprochement')
                expect(dialog.locator('input[type=checkbox]')).to_have_count(2)
                assert photo(application)==avant and not any(flags(api).values())
                # La sélection est ajustable : ne pointer que le lot240 au premier passage.
                dialog.locator('label').filter(has_text=re.compile(r'60[,.]00')).locator('input').uncheck()
                with page.expect_response(lambda r:r.url.endswith('/5141/rapprocher-propositions')) as response:
                    dialog.get_by_role('button',name='Rapprocher la sélection',exact=True).click()
                assert response.value.status==200,response.value.text()
                expect(dialog).to_have_count(0)
                assert flags(api)=={rid:True,simple:False}
                with page.expect_response(lambda r:'/5141/propositions?' in r.url) as preview:
                    page.get_by_role('button',name='Proposer les rapprochements',exact=True).click()
                assert len(preview.value.json()['propositions'])==1,preview.value.text()
                expect(dialog.locator('input[type=checkbox]')).to_have_count(1)
                with page.expect_response(lambda r:r.url.endswith('/5141/rapprocher-propositions')) as response:
                    dialog.get_by_role('button',name='Rapprocher la sélection',exact=True).click()
                assert response.value.status==200,response.value.text()
                page.reload()
                expect(page.get_by_text('Rapprochée',exact=True)).to_have_count(3)
                assert all(flags(api).values()) and photo(application)==avant
                assert not errors and not server,(errors,server)
            finally:browser.close()
    finally:api.close()


def test_preview_obsolete_affiche_refus_et_ne_pointe_rien(application,migration):
    api,email,password=client(application)
    try:
        rid,simple=deux_propositions(application,api);avant=photo(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page();page.set_default_timeout(20000)
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/rapprochement')
                with page.expect_response(lambda r:'/5141/propositions?' in r.url) as preview:
                    page.get_by_role('button',name='Proposer les rapprochements',exact=True).click()
                assert len(preview.value.json()['propositions'])==2,preview.value.text()
                dialog=page.get_by_role('dialog',name='Propositions de rapprochement')
                expect(dialog.locator('input[type=checkbox]')).to_have_count(2)
                assert api.patch(f'/api/rapprochement/{simple}',json={'libelle':'CHANGEMENT-FICTIF-405'}).status_code==200
                with page.expect_response(lambda r:r.url.endswith('/5141/rapprocher-propositions')) as response:
                    dialog.get_by_role('button',name='Rapprocher la sélection',exact=True).click()
                assert response.value.status==409,response.value.text()
                expect(dialog.get_by_role('alert')).to_contain_text('a changé')
                assert not any(flags(api).values()) and photo(application)==avant
            finally:browser.close()
    finally:api.close()


def test_proposition_retardee_ignoree_apres_changement_compte(application,migration):
    api,email,password=client(application)
    try:
        deux_propositions(application,api);avant=photo(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page();page.set_default_timeout(20000)
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/rapprochement')
                held=[];posts=[]
                def retenir(route):
                    response=route.fetch();assert response.status==200
                    held.append((route,response));page.evaluate('window.__preview405Retenue=true')
                page.route('**/api/rapprochement/5141/propositions?**',retenir)
                page.on('request',lambda r:posts.append(r.url) if r.method=='POST' and '/rapprocher-propositions' in r.url else None)
                page.get_by_role('button',name='Proposer les rapprochements',exact=True).click()
                page.wait_for_function('window.__preview405Retenue===true')
                page.locator('select').filter(has=page.locator('option[value="5142"]')).first.select_option('5142')
                with page.expect_response(lambda r:'/5141/propositions?' in r.url):
                    for route,response in held:route.fulfill(response=response)
                page.unroute('**/api/rapprochement/5141/propositions?**',retenir)
                page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                expect(page.get_by_role('dialog')).to_have_count(0)
                assert not posts and not any(flags(api).values())
                page.get_by_role('button',name='Proposer les rapprochements',exact=True).click()
                dialog=page.get_by_role('dialog',name='Propositions de rapprochement')
                expect(dialog).to_contain_text('Aucun pointage')
                expect(dialog.get_by_role('button',name='Rapprocher la sélection')).to_be_disabled()
                assert photo(application)==avant
            finally:browser.close()
    finally:api.close()


def test_societe_retardee_interdit_preview_avant_contexte_pret(application,migration):
    api,email,password=client(application)
    try:
        deux_propositions(application,api)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page();page.set_default_timeout(20000)
                connexion(page,application['web_url'],email,password)
                held=[]
                def retenir(route):
                    response=route.fetch();assert response.status==200
                    held.append((route,response));page.evaluate('window.__societe405Retenue=true')
                page.route('**/api/societe/moi',retenir)
                page.goto(application['web_url']+'/rapprochement',wait_until='domcontentloaded')
                page.wait_for_function('window.__societe405Retenue===true')
                bouton=page.get_by_role('button',name='Proposer les rapprochements',exact=True)
                try:
                    expect(bouton).to_be_disabled()
                finally:
                    for route,response in held:route.fulfill(response=response)
                    page.unroute('**/api/societe/moi',retenir)
                expect(bouton).to_be_enabled()
                bouton.click()
                expect(page.get_by_role('dialog',name='Propositions de rapprochement').locator('input[type=checkbox]')).to_have_count(2)
                assert not any(flags(api).values())
            finally:browser.close()
    finally:api.close()
