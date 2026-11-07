"""Financement indépendant dans Edge : flux explicites, rôles et abandon de contexte."""
from contextlib import closing
from zipfile import ZipFile
import json
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_financement695_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,flux,url,BASE)
from test_e2e_administration_isole import connexion,observer
from test_e2e_balance_echeances687_isole import ouvrir
from browser_support import chromium_executable


def ouvrir_financement(page,app,v,lecture=False):
    panel,_=ouvrir(page,app,v,lecture)
    panel.get_by_text('Préparer le tableau de financement depuis les balances',exact=True).click()
    detail=panel.get_by_role('region',name='Financement documentaire de la préparation',exact=True)
    expect(detail.get_by_label('Flux à documenter',exact=True)).to_be_visible()
    return panel,detail


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_695_flux_complets_n_controles_et_zip_edge(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);body=flux(v)
        if role=='lecture':v=ok(api.post(url(v),json=body),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Financement fictif695','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_financement(page,application,v,role=='lecture')
            if role=='lecture':
                expect(detail.get_by_label('Montant du flux MAD',exact=True)).to_have_value('0.00')
                assert detail.get_by_label('Montant du flux MAD',exact=True).is_disabled()
                assert detail.get_by_role('button',name='Conserver le financement dans une nouvelle version',exact=True).count()==0
            else:
                expect(detail.get_by_label('Montant du flux MAD',exact=True)).to_have_value('')
                expect(detail.get_by_text('Total ressources N : Inconnu',exact=False)).to_be_visible()
                for r in body['lignes']:
                    detail.get_by_label('Flux à documenter',exact=True).select_option(r['code'])
                    detail.get_by_label('Montant du flux MAD',exact=True).fill(r['n'])
                    detail.get_by_label('Justification du flux',exact=True).fill(r['justification_n'])
                # Les champs N-1 restent vides sans aucune copie des fluxN.
                detail.get_by_label('Période du flux',exact=True).select_option('n1')
                expect(detail.get_by_label('Montant du flux MAD',exact=True)).to_have_value('')
                if role=='admin':
                    for r in body['lignes']:
                        detail.get_by_label('Flux à documenter',exact=True).select_option(r['code'])
                        detail.get_by_label('Montant du flux MAD',exact=True).fill('6000' if r['code']=='augmentations_capitaux_propres' else '0')
                        detail.get_by_label('Justification du flux',exact=True).fill('État fictif695 N-1')
                detail.get_by_label('Période du flux',exact=True).select_option('n')
                detail.get_by_role('checkbox').check()
                with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                    detail.get_by_role('button',name='Conserver le financement dans une nouvelle version',exact=True).click()
                assert rep.value.status==201,rep.value.text();v=rep.value.json()
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
                panel.get_by_text('Préparer le tableau de financement depuis les balances',exact=True).click()
                detail=panel.get_by_role('region',name='Financement documentaire de la préparation',exact=True)
            expect(detail.get_by_text('Total ressources N : 11.000,00 MAD',exact=False)).to_be_visible()
            expect(detail.get_by_text('Total emplois N : 4.000,00 MAD',exact=False)).to_be_visible()
            expect(detail.get_by_text('Écart de rapprochement N : 0,00 MAD',exact=False)).to_be_visible()
            expect(detail.get_by_text('Total ressources N-1 : '+('6.000,00 MAD' if role=='admin' else 'Inconnu'),exact=False)).to_be_visible()
            with page.expect_download() as dl:
                panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
            dest=tmp_path/'financement695.zip';dl.value.save_as(dest)
            with ZipFile(dest) as z:
                d=json.loads(z.read('financement_documentaire.json'))
                assert d['tableau']['total_ressources']==11000 and d['tableau']['ecart_controle']==0 and not d['pret_a_deposer']
            detail.get_by_label('Justification du flux',exact=True).scroll_into_view_if_needed()
            page.screenshot(path=str(tmp_path/f'financement695-{role}-{largeur}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors and not serveur,(errors,serveur)
        finally:browser.close()


def test_695_post_tardif_ne_selectionne_pas_une_version_hors_contexte(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=flux(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_financement(page,application,v);pending=[]
            detail.get_by_label('Montant du flux MAD',exact=True).fill('0')
            detail.get_by_label('Justification du flux',exact=True).fill('Déclaration fictive695 tardive')
            detail.get_by_role('checkbox').check()
            def retenir(route):
                if route.request.method!='POST':return route.continue_()
                rep=route.fetch();assert rep.status==201
                pending.append((route,rep));page.evaluate('window.__financement695Post = true')
            page.route('**'+url(v),retenir,times=1)
            detail.get_by_role('button',name='Conserver le financement dans une nouvelle version',exact=True).click()
            page.wait_for_function('window.__financement695Post === true')
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            route,rep=pending.pop();saved=rep.json()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST'):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(panel.get_by_label('Préparations conservées',exact=True)).to_have_value(str(v2['id']))
            assert ok(api.get(BASE+f'/{saved["id"]}'))==saved
        finally:browser.close()


def test_695_zero_sans_source_refuse_saisie_preservee_et_n1_absent(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api,comparatif=False);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_financement(page,application,v)
            detail.get_by_label('Montant du flux MAD',exact=True).fill('0');detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name='Conserver le financement dans une nouvelle version',exact=True).click()
            assert rep.value.status==422
            expect(detail.get_by_role('alert')).to_contain_text('y compris pour un zéro')
            expect(detail.get_by_label('Montant du flux MAD',exact=True)).to_have_value('0')
            detail.get_by_label('Justification du flux',exact=True).fill('Absence explicitement revue — fictif695')
            detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name='Conserver le financement dans une nouvelle version',exact=True).click()
            assert rep.value.status==201
            panel.get_by_text('Préparer le tableau de financement depuis les balances',exact=True).click()
            detail.get_by_label('Période du flux',exact=True).select_option('n1')
            assert detail.get_by_label('Montant du flux MAD',exact=True).is_disabled()
            expect(detail.get_by_text('Balance N-1 absente',exact=False)).to_be_visible()
        finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_695_get_tardif_abandonne(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(url(v),json=flux(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v);pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__flux695Retenu = true')
            page.route('**'+url(v),retenir,times=1)
            panel.get_by_text('Préparer le tableau de financement depuis les balances',exact=True).click()
            page.wait_for_function('window.__flux695Retenu === true')
            if action=='version':
                panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            elif action=='fermeture':panel.get_by_role('button',name='Masquer',exact=True).click()
            else:page.evaluate('t => localStorage.setItem("hisabpro_token",t)',autre.headers['Authorization'].split(' ',1)[1])
            route,rep=pending.pop()
            with page.expect_response(lambda r:r.url.endswith(url(v))):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            assert panel.get_by_label('Montant du flux MAD',exact=True).count()==0
        finally:browser.close()
