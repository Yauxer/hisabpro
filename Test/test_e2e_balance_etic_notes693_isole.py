"""Edge réel, notes multirubriques, lecture seule et réponses hors contexte."""
from contextlib import closing
from io import BytesIO
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_etic_notes693_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,notes,url,BASE)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_echeances687_isole import ouvrir
from browser_support import chromium_executable


def ouvrir_notes(page,app,v,lecture=False):
    panel,_=ouvrir(page,app,v,lecture)
    panel.get_by_text('Documenter les notes de préparation ETIC',exact=True).click()
    detail=panel.get_by_role('region',name='Notes documentaires ETIC de la préparation',exact=True)
    expect(detail.get_by_label('Rubrique ETIC à documenter',exact=True)).to_be_visible()
    return panel,detail


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_693_notes_multirubriques_et_export_edge(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api)
        if role=='lecture':v=ok(api.post(url(v),json=notes(v)),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Notes fictives693','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_notes(page,application,v,role=='lecture')
            if role=='lecture':
                expect(detail.get_by_label('Texte de préparation',exact=True)).to_have_value(notes(v)['lignes'][0]['texte'])
                assert detail.get_by_label('Texte de préparation',exact=True).is_disabled()
                assert detail.get_by_role('button',name='Conserver les notes ETIC dans une nouvelle version',exact=True).count()==0
            else:
                detail.get_by_label('État de la note',exact=True).select_option('renseigne')
                detail.get_by_label('Texte de préparation',exact=True).fill('Note A1 fictive693 <sans interprétation>.')
                detail.get_by_label('Référence ou justification ETIC',exact=True).fill('Annexe fictive693')
                detail.get_by_label('Rubrique ETIC à documenter',exact=True).select_option('B9')
                detail.get_by_label('État de la note',exact=True).select_option('non_applicable')
                detail.get_by_label('Référence ou justification ETIC',exact=True).fill('Revue fictive693 des engagements')
                detail.get_by_label('Rubrique ETIC à documenter',exact=True).select_option('A1')
                expect(detail.get_by_label('Texte de préparation',exact=True)).to_have_value('Note A1 fictive693 <sans interprétation>.')
                detail.get_by_role('checkbox').check()
                with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                    detail.get_by_role('button',name='Conserver les notes ETIC dans une nouvelle version',exact=True).click()
                assert rep.value.status==201,rep.value.text();v=rep.value.json()
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
                panel.get_by_text('Documenter les notes de préparation ETIC',exact=True).click()
                detail=panel.get_by_role('region',name='Notes documentaires ETIC de la préparation',exact=True)
                expect(detail.get_by_label('Texte de préparation',exact=True)).to_have_value('Note A1 fictive693 <sans interprétation>.')
                detail.get_by_label('Rubrique ETIC à documenter',exact=True).select_option('B9')
                expect(detail.get_by_label('État de la note',exact=True)).to_have_value('non_applicable')
            with page.expect_download() as download:
                panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
            dest=tmp_path/'notes693.zip';download.value.save_as(dest)
            with ZipFile(dest) as zip:
                vue=json.loads(zip.read('notes_etic_documentaires.json'))
                assert not vue['pret_a_deposer'] and vue['comptage_notes']['renseigne']==1
            detail.get_by_label('Référence ou justification ETIC',exact=True).scroll_into_view_if_needed()
            page.screenshot(path=str(tmp_path/f'notes693-{role}-{largeur}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors and not serveur,(errors,serveur)
        finally:browser.close()


def test_693_post_reel_tardif_ne_selectionne_pas_ancienne_version(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=notes(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_notes(page,application,v);pending=[]
            detail.get_by_label('Texte de préparation',exact=True).fill('Brouillon fictif693 conservé sur la version source')
            detail.get_by_role('checkbox').check()
            def retenir(route):
                if route.request.method!='POST':return route.continue_()
                rep=route.fetch();assert rep.status==201
                pending.append((route,rep));page.evaluate('window.__notes693PostRetenu = true')
            page.route('**'+url(v),retenir,times=1)
            detail.get_by_role('button',name='Conserver les notes ETIC dans une nouvelle version',exact=True).click()
            page.wait_for_function('window.__notes693PostRetenu === true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
            assert ok(api.get(url(v2)))['lignes'][0]['texte']==notes(v2)['lignes'][0]['texte']
        finally:browser.close()


def test_693_erreur_serveur_saisie_preservee_puis_correction(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_notes(page,application,v)
            detail.get_by_label('État de la note',exact=True).select_option('renseigne')
            detail.get_by_label('Texte de préparation',exact=True).fill('Texte fictif693 à conserver après refus')
            detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name='Conserver les notes ETIC dans une nouvelle version',exact=True).click()
            assert rep.value.status==422
            expect(detail.get_by_role('alert')).to_contain_text('justification')
            expect(detail.get_by_label('Texte de préparation',exact=True)).to_have_value('Texte fictif693 à conserver après refus')
            detail.get_by_label('Référence ou justification ETIC',exact=True).fill('Source fictive693')
            assert not detail.get_by_role('checkbox').is_checked()
            detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name='Conserver les notes ETIC dans une nouvelle version',exact=True).click()
            assert rep.value.status==201
        finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_693_reponse_tardive_abandonnee(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=notes(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__notes693Retenues = true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text('Documenter les notes de préparation ETIC',exact=True).click()
            page.wait_for_function('window.__notes693Retenues === true')
            if action=='version':
                panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            elif action=='fermeture':panel.get_by_role('button',name='Masquer',exact=True).click()
            else:page.evaluate('t => localStorage.setItem("hisabpro_token",t)',autre.headers['Authorization'].split(' ',1)[1])
            route,rep=pending.pop()
            with page.expect_response(lambda r:r.url.endswith(url(v))):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            assert panel.get_by_label('Texte de préparation',exact=True).count()==0
        finally:browser.close()
