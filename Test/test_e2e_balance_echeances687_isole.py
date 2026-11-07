"""Saisie documentaire et exports réels dans Edge, trois rôles et deux largeurs."""
from contextlib import closing
from io import BytesIO
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from playwright.sync_api import sync_playwright, expect
from test_balance_echeances687_isole import (
    application,application102,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,application089,
    application087,migration,client,ok,creer,demande,chemin,BASE,donnees_metier)
from test_e2e_administration_isole import connexion,observer
from test_logo_societe import image_data
from browser_support import chromium_executable


def ouvrir(page,app,v,lecture=False):
    page.goto(app['web_url']+'/liasse-fiscale')
    panel=page.locator('section').filter(has=page.get_by_role('heading',name='Préparer depuis des balances externes',exact=True))
    panel.get_by_role('button',name='Consulter les préparations' if lecture else 'Importer N / N-1',exact=True).click()
    panel.get_by_label('Préparations conservées',exact=True).select_option(str(v['id']))
    expect(panel.get_by_text(f'Version {v["version"]} conservée',exact=False)).to_be_visible()
    panel.get_by_text('Compléter les échéances documentaires des balances',exact=True).click()
    detail=panel.get_by_role('region',name='Échéances documentaires de la préparation',exact=True)
    expect(detail.get_by_label('Compte à documenter',exact=True)).to_be_visible()
    return panel,detail


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_687_saisie_version_relecture_et_exports_natifs(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        if role=='lecture':v=ok(api.post(chemin(v),json=demande(v)),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Balances fictives687','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application)
            panel,detail=ouvrir(page,application,v,role=='lecture')
            if role=='lecture':
                expect(detail.get_by_label('Plus d’un an MAD',exact=True)).to_have_value('2000.00')
                expect(detail.get_by_label('Moins d’un an MAD',exact=True)).to_have_value('')
                expect(detail.get_by_label('État / organismes publics MAD',exact=True)).to_have_value('0.00')
                assert detail.get_by_label('Plus d’un an MAD',exact=True).is_disabled()
                assert detail.get_by_role('button',name='Conserver les compléments dans une nouvelle version',exact=True).count()==0
            else:
                detail.get_by_label('Plus d’un an MAD',exact=True).fill('2000,00')
                detail.get_by_label('Échues MAD',exact=True).fill('1000')
                detail.get_by_label('Justification / référence de source',exact=True).fill('État fictif687 : justificatif à vérifier')
                detail.get_by_role('checkbox').check()
                with page.expect_response(lambda r:r.url.endswith(chemin(v)) and r.request.method=='POST') as rep:
                    detail.get_by_role('button',name='Conserver les compléments dans une nouvelle version',exact=True).click()
                assert rep.value.status==201,rep.value.text();v=rep.value.json()
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
                panel.get_by_text('Compléter les échéances documentaires des balances',exact=True).click()
                detail=panel.get_by_role('region',name='Échéances documentaires de la préparation',exact=True)
                expect(detail.get_by_label('Plus d’un an MAD',exact=True)).to_have_value('2000.00')
                expect(detail.get_by_text('Solde N conservé',exact=False)).to_contain_text('5.000,00')
            for fmt,libelle in [('xlsx','Excel'),('pdf','PDF')]:
                with page.expect_download() as export:
                    panel.get_by_role('button',name='Exporter la préparation '+libelle,exact=True).click()
                assert f'_v{v["version"]}.' in export.value.suggested_filename
                destination=tmp_path/f'version687-{role}.{fmt}'
                export.value.save_as(destination)
                if fmt=='xlsx':
                    wb=load_workbook(destination);assert 'Échéances documentaires' in wb.sheetnames
                    assert wb['Échéances documentaires']['L2'].value==5000
                else:
                    pdf=PdfReader(destination);t=' '.join(p.extract_text() or '' for p in pdf.pages)
                    assert v['empreinte_sha256'] in t and '5 000,00' in t and any(p.images for p in pdf.pages)
            detail.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'echeances687-{role}-{largeur}.png'),full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            apres=donnees_metier(application)
            assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')
            assert not errors and not serveur,(errors,serveur)
            page.reload();panel,detail=ouvrir(page,application,v,role=='lecture')
            expect(detail.get_by_label('Plus d’un an MAD',exact=True)).to_have_value('2000.00')
        finally:browser.close()


def test_687_depassement_refuse_et_reprise_sans_perte_de_saisie(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(10000)
            connexion(page,application['web_url'],email,password);panel,detail=ouvrir(page,application,v)
            detail.get_by_label('Échues MAD',exact=True).fill('8001')
            detail.get_by_label('Justification / référence de source',exact=True).fill('Dépassement fictif687')
            detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(chemin(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name='Conserver les compléments dans une nouvelle version',exact=True).click()
            assert rep.value.status==422
            expect(detail.get_by_role('alert')).to_contain_text('dépasse')
            expect(detail.get_by_label('Échues MAD',exact=True)).to_have_value('8001')
            assert len(ok(api.get(BASE,params={'exercice':v['exercice']})))==1
            detail.get_by_label('Échues MAD',exact=True).fill('1000');detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(chemin(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name='Conserver les compléments dans une nouvelle version',exact=True).click()
            assert rep.value.status==201
        finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_687_reponse_reelle_tardive_ignoree(application,action):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre,sync_playwright() as p:
        v=creer(api);v2=ok(api.post(chemin(v),json=demande(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(10000)
            connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/liasse-fiscale')
            panel=page.locator('section').filter(has=page.get_by_role('heading',name='Préparer depuis des balances externes',exact=True))
            panel.get_by_role('button',name='Importer N / N-1',exact=True).click()
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v['id']))
            expect(panel.get_by_text('Version 1 conservée',exact=False)).to_be_visible()
            pending=[]
            def retenir(route):
                rep=route.fetch();assert rep.status==200
                pending.append((route,rep));page.evaluate('window.__echeances687Retenues = true')
            page.route('**'+chemin(v),retenir,times=1)
            panel.get_by_text('Compléter les échéances documentaires des balances',exact=True).click()
            page.wait_for_function('window.__echeances687Retenues === true')
            if action=='version':
                panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
                expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
                panel.get_by_text('Compléter les échéances documentaires des balances',exact=True).click()
                expect(panel.get_by_label('Plus d’un an MAD',exact=True)).to_have_value('2000.00')
            elif action=='fermeture':panel.get_by_text('Compléter les échéances documentaires des balances',exact=True).click()
            else:
                token=autre.headers['Authorization'].split(' ',1)[1]
                page.evaluate('t => localStorage.setItem("hisabpro_token",t)',token)
            route,rep=pending.pop();route.fulfill(response=rep)
            if action=='version':expect(panel.get_by_label('Plus d’un an MAD',exact=True)).to_have_value('2000.00')
            else:expect(panel.get_by_label('Compte à documenter',exact=True)).to_have_count(0)
        finally:browser.close()


def test_687_plusieurs_comptes_filtre_et_brouillons_conserves(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(10000)
            connexion(page,application['web_url'],email,password);panel,detail=ouvrir(page,application,v)
            detail.get_by_label('Plus d’un an MAD',exact=True).fill('2000')
            detail.get_by_label('Échues MAD',exact=True).fill('1000')
            detail.get_by_label('Justification / référence de source',exact=True).fill('Créances fictives687')
            detail.get_by_label('Filtrer les comptes à documenter',exact=True).fill('4411')
            assert detail.get_by_label('Plus d’un an MAD',exact=True).count()==0
            detail.get_by_label('Compte à documenter',exact=True).select_option('B7:4411')
            for label in ('Plus d’un an MAD','Moins d’un an MAD','Échues MAD'):
                detail.get_by_label(label,exact=True).fill('1000')
            detail.get_by_label('État / organismes publics MAD',exact=True).fill('0')
            detail.get_by_label('Justification / référence de source',exact=True).fill('Dettes fictives687')
            detail.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(chemin(v)) and r.request.method=='POST') as rep:
                detail.get_by_role('button',name='Conserver les compléments dans une nouvelle version',exact=True).click()
            assert rep.value.status==201,rep.value.text();v2=rep.value.json()
            vue=ok(api.get(chemin(v2)));a,b=vue['lignes']
            assert a['qualifie']=='3000.00' and a['reliquat']=='5000.00' and a['moins_un_an'] is None
            assert b['qualifie']=='3000.00' and b['reliquat']=='0.00' and b['etat_organismes_publics']=='0.00'
            assert b['devises'] is None and b['entreprises_liees'] is None and b['effets'] is None
        finally:browser.close()
