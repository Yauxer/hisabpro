"""Consultation détaillée : vrais GET/ACL et réponses tardives sur PG nonce."""
from contextlib import closing
from datetime import date
import re

import pytest
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import text

from test_e2e_balance_exports677_isole import (
    application,application090,application089,application087,migration,creer,BASE,
    client,ok,connexion,observer,donnees_metier,catalogue_acl,verifier_cible_isolee,chromium_executable)
from test_balance_exports677 import lignes


def ouvrir(page,app,vid):
    page.goto(app['web_url']+'/liasse-fiscale')
    panel=page.locator('section').filter(has=page.get_by_role('heading',name='Préparer depuis des balances externes',exact=True))
    panel.get_by_role('button',name='Importer N / N-1',exact=True).click()
    panel.get_by_label('Préparations conservées',exact=True).select_option(str(vid))
    expect(panel.get_by_role('status')).to_be_visible()
    panel.get_by_role('button',name='Consulter le bilan et les comptes sources',exact=True).click()
    return panel.get_by_role('region',name='Détail de la préparation conservée',exact=True)


@pytest.mark.parametrize('largeur,comparatif',[(1440,True),(390,False)])
def test_679_bilan_sources_filtre_et_comparatif_natifs(application,largeur,comparatif,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v1,v2,_=creer(api,comparatif)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            avant,acl=donnees_metier(application),catalogue_acl(application['engine'])
            detail=ouvrir(page,application,v1['id'])
            expect(detail.get_by_role('heading',name='Bilan de la version 1',exact=True)).to_be_visible()
            bilan=detail.get_by_role('region',name='Bilan détaillé de la préparation',exact=True)
            total=bilan.get_by_role('row').filter(has_text='TOTAL GÉNÉRAL ACTIF')
            expect(total).to_contain_text('49.700,00')
            corporelles=bilan.get_by_role('row').filter(has_text='C · Immobilisations corporelles')
            expect(corporelles).to_contain_text('21.000,00')
            expect(corporelles).to_contain_text('300,00')
            construction=bilan.get_by_role('row').filter(has_text='232 · Constructions')
            assert construction.get_by_role('cell',name='Indisponible',exact=True).count()==3
            bilan.screenshot(path=str(tmp_path/f'actif679-{largeur}.png'))
            if largeur==390:
                assert bilan.evaluate('e => e.scrollWidth > e.clientWidth')
                bilan.evaluate('e => e.scrollLeft = e.scrollWidth')
                expect(bilan.get_by_role('columnheader',name='Net N-1 MAD',exact=True)).to_be_in_viewport()
                bilan.screenshot(path=str(tmp_path/'actif679-390-droite.png'))
            detail.get_by_label('Côté du bilan',exact=True).select_option('passif')
            expect(bilan.get_by_role('row').filter(has_text='TOTAL GÉNÉRAL PASSIF')).to_contain_text('49.700,00')
            detail.get_by_label('Rechercher un compte source',exact=True).fill('283')
            source=detail.get_by_role('region',name='Comptes sources de la préparation',exact=True)
            expect(source.locator('tbody tr')).to_have_count(1)
            expect(source.locator('tbody tr')).to_contain_text('28321')
            expect(source.locator('tbody tr')).to_contain_text('300,00')
            detail.get_by_label('Balance source',exact=True).select_option('n1')
            if comparatif:
                detail.get_by_label('Rechercher un compte source',exact=True).fill('283')
                expect(source.locator('tbody tr')).to_contain_text('150,00')
            else:
                expect(detail.get_by_text('Balance source N-1 indisponible dans cette version.',exact=True)).to_be_visible()
                assert source.count()==0
            page.screenshot(path=str(tmp_path/f'bilan679-{largeur}.png'),full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert donnees_metier(application)==avant and catalogue_acl(application['engine'])==acl
            assert not errors and not serveur,(errors,serveur)
        finally:browser.close()


def test_679_plus50_comptes_recherche_reinitialise_page_et_inconnus(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v1,_,_=creer(api,False)
        n=lignes();comptes={r['compte'] for r in n}
        extras=[r['numero'] for r in ok(api.get('/api/plan-comptable'))
                if re.fullmatch(r'[1-7][0-9]{3,9}',r['numero']) and r['numero'] not in comptes][:60]
        assert len(extras)==60
        n += [{'compte':c,'debit':'0','credit':'0'} for c in extras]
        version=ok(api.post(BASE,json={'exercice':date.today().year,'lignes_n':n}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(10000)
            observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application)
            detail=ouvrir(page,application,version['id'])
            source=detail.get_by_role('region',name='Comptes sources de la préparation',exact=True)
            expect(source.locator('tbody tr')).to_have_count(50)
            detail.get_by_role('button',name='Comptes suivants',exact=True).click()
            expect(detail.get_by_text('Page 2 sur 2',exact=True)).to_be_visible()
            expect(source.locator('tbody tr')).to_have_count(23)
            detail.get_by_label('Rechercher un compte source',exact=True).fill('28321')
            expect(detail.get_by_text('Page 1 sur 1',exact=True)).to_be_visible()
            expect(source.locator('tbody tr')).to_have_count(1)
            detail.get_by_label('Rechercher un compte source',exact=True).fill('9999999999')
            expect(detail.get_by_text('Aucun compte ne correspond à cette recherche.',exact=True)).to_be_visible()
            assert source.count()==0
            assert donnees_metier(application)==avant
        finally:browser.close()


@pytest.mark.parametrize('action',['version','fermeture','jeton'])
def test_679_vrai_get_tardif_ignore_apres_changement(application,action):
    api,email,password=client(application)
    autre,_,_=client(application)
    with closing(api),closing(autre),sync_playwright() as p:
        v1,v2,_=creer(api)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(10000)
            observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application);pending=[]
            path=BASE+f'/{v1["id"]}/detail'
            def retenir(route):
                reponse=route.fetch();assert reponse.status==200
                pending.append((route,reponse))
                page.evaluate('window.__detail679Retenu = true')
            page.route('**'+path,retenir,times=1)
            detail=ouvrir(page,application,v1['id'])
            expect(detail.get_by_role('status')).to_have_text('Chargement de la version conservée…')
            page.wait_for_function('window.__detail679Retenu === true')
            assert len(pending)==1
            if action=='version':
                page.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
                page.get_by_role('button',name='Consulter le bilan et les comptes sources',exact=True).click()
                detail=page.get_by_role('region',name='Détail de la préparation conservée',exact=True)
                expect(detail.get_by_role('heading',name='Bilan de la version 2',exact=True)).to_be_visible()
            elif action=='fermeture':
                detail.get_by_role('button',name='Masquer le bilan et les comptes sources',exact=True).click()
            else:
                page.evaluate("t => localStorage.setItem('hisabpro_token',t)",autre.headers['Authorization'].split(' ',1)[1])
            with page.expect_response(lambda r:r.url.endswith(path)):
                pending[0][0].fulfill(response=pending[0][1])
            expect(page.get_by_role('heading',name='Bilan de la version 1',exact=True)).to_have_count(0)
            if action=='version':
                expect(detail.get_by_role('heading',name='Bilan de la version 2',exact=True)).to_be_visible()
            assert donnees_metier(application)==avant
        finally:browser.close()


def test_679_lecture_native_dans_societe_invitee_et_refus_autre_societe(application):
    a,_,_=client(application);b,email,_=client(application)
    with closing(a),closing(b):
        v1,_,_=creer(a)
        sid=ok(a.get('/api/auth/me'))['societe_id']
        propre=b.headers['Authorization']
        path=BASE+f'/{v1["id"]}/detail'
        assert b.get(path).status_code==404
        ok(a.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        token=ok(b.post(f'/api/societes/switcher/{sid}'))['access_token']
        b.headers['Authorization']='Bearer '+token
        avant=donnees_metier(application)
        r=b.get(path);assert r.status_code==200,r.text
        assert r.json()['bilan']['actif'][-1]['valeurs']==[50000,300,49700,24850]
        assert b.post(BASE,json={'exercice':date.today().year,'lignes_n':lignes()}).status_code==403
        b.headers['Authorization']=propre
        assert b.get(path).status_code==404
        assert donnees_metier(application)==avant


def test_679_refus_natif_sql_reprise_et_lecture_sans_mutation(application):
    api,email,password=client(application)
    c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    with closing(api),sync_playwright() as p:
        v1,_,_=creer(api)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(10000)
            observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/liasse-fiscale')
            page.get_by_role('button',name='Importer N / N-1',exact=True).click()
            page.get_by_label('Préparations conservées',exact=True).select_option(str(v1['id']))
            expect(page.get_by_text('Version 1 conservée',exact=False)).to_be_visible()
            avant,acl=donnees_metier(application),catalogue_acl(application['engine'])
            with application['engine'].begin() as db:db.execute(text('REVOKE SELECT ON liasse_balances_preparation FROM hisabpro'))
            try:
                page.get_by_role('button',name='Consulter le bilan et les comptes sources',exact=True).click()
                detail=page.get_by_role('region',name='Détail de la préparation conservée',exact=True)
                expect(detail.get_by_role('alert')).to_be_visible()
                assert detail.get_by_role('region',name='Bilan détaillé de la préparation',exact=True).count()==0
            finally:
                assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
                with application['engine'].begin() as db:db.execute(text('GRANT SELECT ON liasse_balances_preparation TO hisabpro'))
            detail.get_by_role('button',name='Réessayer le détail',exact=True).click()
            expect(detail.get_by_role('heading',name='Bilan de la version 1',exact=True)).to_be_visible()
            assert donnees_metier(application)==avant and catalogue_acl(application['engine'])==acl
        finally:browser.close()
