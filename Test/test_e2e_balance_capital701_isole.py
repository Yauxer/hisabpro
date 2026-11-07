"""Edge701 : contrôles du snapshot distincts des brouillons, droits et exports."""
from contextlib import closing
import pytest
from playwright.sync_api import sync_playwright,expect
from test_balance_capital701_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,body,url,BASE)
from test_e2e_balance_etic_annexes699_isole import ouvrir_annexes
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_701_controles_figes_brouillon_et_nouvelle_version(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);v=ok(api.post(url(v),json=body(v)),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Contrôles fictifs701','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1100},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            panel,detail=ouvrir_annexes(page,application,v,role=='lecture')
            detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option('C1')
            detail.get_by_text('Vérifier les données chiffrées du capital conservé',exact=True).click()
            controles=detail.get_by_role('region',name='Contrôles arithmétiques du capital conservé',exact=True)
            expect(controles).to_contain_text('Somme des capitaux déclarés : 10000.00 MAD')
            expect(controles).to_contain_text('Écart capitaux déclarés moins balance 111 : 0.00 MAD')
            expect(controles).to_contain_text('pas les modifications du brouillon')
            if role=='lecture':
                assert detail.get_by_label('Montant du capital détenu ligne 1',exact=True).is_disabled()
            else:
                detail.get_by_label('Montant du capital détenu ligne 1',exact=True).fill('9999.99')
                expect(controles).to_contain_text('Somme des capitaux déclarés : 10000.00 MAD')
                detail.get_by_role('checkbox').check()
                with page.expect_response(lambda r:r.url.endswith(url(v)) and r.request.method=='POST') as rep:
                    detail.get_by_role('button',name='Conserver les tableaux ETIC dans une nouvelle version',exact=True).click()
                assert rep.value.status==201;v=rep.value.json()
                expect(panel.get_by_text('Version 3 conservée',exact=False)).to_be_visible()
                panel.get_by_text('Documenter les autres annexes ETIC',exact=True).click()
                detail=panel.get_by_role('region',name='Annexes documentaires ETIC de la préparation',exact=True)
                detail.get_by_label('Tableau ETIC à documenter',exact=True).select_option('C1')
                detail.get_by_text('Vérifier les données chiffrées du capital conservé',exact=True).click()
                controles=detail.get_by_role('region',name='Contrôles arithmétiques du capital conservé',exact=True)
                expect(controles).to_contain_text('Écart capitaux déclarés moins balance 111 : -0.01 MAD')
                expect(controles).to_contain_text('Écart capital déclaré moins produit : -0.01 MAD')
            controles.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'capital701-{role}-{largeur}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            with page.expect_download():panel.get_by_role('button',name='Exporter la préparation Excel',exact=True).click()
            assert not errors and not serveur,(errors,serveur)
        finally:browser.close()
