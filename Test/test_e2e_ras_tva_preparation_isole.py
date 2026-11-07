"""Préparation593 : Edge réel, API réelles, téléchargements et isolation."""
from contextlib import closing
from datetime import date
import pytest
from playwright.sync_api import sync_playwright, expect
from openpyxl import load_workbook
from pypdf import PdfReader
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)
from test_ras_tva_preparation_isole import jeu, periode_suivante
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_logo_societe import image_data
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable
from sqlalchemy import text
from urllib.parse import urlparse, parse_qs


def ouvrir(page,application):
    page.goto(application['web_url']+'/declaration-tva')
    page.get_by_text('Préparation mensuelle des retenues opérées',exact=True).click()
    region=page.get_by_role('region',name='Préparation mensuelle RAS TVA',exact=True)
    a,m=periode_suivante()
    region.get_by_label('Mois de versement prévu',exact=True).fill(f'{a}-{m:02d}')
    return region


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_593_trois_roles_mobile_exports_et_absence_mutation(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        jeu(api);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Fictif593','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            erreurs,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application);region=ouvrir(page,application)
            expect(region.get_by_role('article')).to_have_count(3)
            carte=region.get_by_role('region',name='Montants capturés du mois',exact=True)
            expect(carte.locator('dl > div').filter(has_text='Captures actives')).to_contain_text('150,00 MAD')
            expect(carte.locator('dl > div').filter(has_text='Actives · OD validées')).to_contain_text('75,00 MAD')
            expect(region.get_by_text('Annulée · à rapprocher',exact=True)).to_have_count(1)
            a,m=periode_suivante()
            for fmt,nom in [('csv','CSV'),('xlsx','Excel'),('pdf','PDF')]:
                with page.expect_download() as en_cours:region.get_by_role('button',name=nom,exact=True).click()
                d=en_cours.value;fichier=tmp_path/f'preparation593_{role}.{fmt}';d.save_as(fichier)
                assert d.suggested_filename==f'preparation_ras_tva_{a}_{m:02d}.{fmt}'
                assert fichier.stat().st_size>100
                if fmt=='xlsx':
                    w=load_workbook(fichier);assert w['Synthèse']['C8'].value==150 and len(w['Logo société']._images)==1
                if fmt=='pdf':assert any(p.images for p in PdfReader(fichier).pages)
            region.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'preparation593_{role}_{largeur}.png'))
            assert region.evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
            assert donnees_metier(application)==avant and not erreurs and not serveur,(erreurs,serveur)
        finally:browser.close()


def test_593_changement_periode_et_export_perime(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        jeu(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(20000)
            connexion(page,application['web_url'],email,password);region=ouvrir(page,application)
            expect(region.get_by_role('article')).to_have_count(3)
            champ=region.get_by_label('Mois de versement prévu',exact=True)
            champ.fill('2027-02');expect(region.get_by_role('article')).to_have_count(0)
            expect(region.get_by_text('Aucune capture guidée opérée sur achats pour ces paiements.',exact=True)).to_be_visible()
            a,m=periode_suivante();champ.fill(f'{a}-{m:02d}');expect(region.get_by_role('article')).to_have_count(3)
            ok(api.patch('/api/societe/moi',json={'raison_sociale':'Nouvelle identité fictive593'}))
            region.get_by_role('button',name='PDF',exact=True).click()
            expect(region.get_by_role('alert')).to_contain_text('Actualisez')
            expect(region.get_by_role('article')).to_have_count(0)
            region.get_by_role('button',name='Actualiser la préparation',exact=True).click()
            expect(region.get_by_role('article')).to_have_count(3)
        finally:browser.close()


def test_593_recalcul_tva_garde_la_preparation_ouverte(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        jeu(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(20000)
            connexion(page,application['web_url'],email,password);region=ouvrir(page,application)
            expect(region.get_by_role('article')).to_have_count(3)
            a,m=periode_suivante();periode=f'{a}-{m:02d}'
            # Latence réelle de lecture côté PostgreSQL, sans interception API.
            with application['engine'].connect() as db:
                tx=db.begin();db.execute(text('LOCK TABLE ras_tva_reglement_details IN ACCESS EXCLUSIVE MODE'))
                try:
                    page.get_by_role('button',name='Trimestrielle',exact=True).click()
                    expect(page.get_by_text('Calcul de la déclaration…',exact=True)).to_be_visible()
                    expect(region).to_be_visible()
                    expect(region.get_by_label('Mois de versement prévu',exact=True)).to_have_value(periode)
                    expect(region.get_by_role('article')).to_have_count(3)
                finally:tx.rollback()
            expect(page.get_by_text('Calcul de la déclaration…',exact=True)).to_have_count(0)
            expect(region.get_by_label('Mois de versement prévu',exact=True)).to_have_value(periode)
        finally:browser.close()


def test_593_libelle_credit_suit_annee_civile_en_exercice_decale(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        annee=date.today().year
        ok(api.patch(f'/api/exercices/{annee}',json={'date_debut':f'{annee-1}-07-01','date_fin':f'{annee}-06-30'}))
        ok(api.post('/api/exercices',json={'annee':annee+1,'date_debut':f'{annee}-07-01','date_fin':f'{annee+1}-06-30'}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(20000)
            connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application);page.goto(application['web_url']+'/declaration-tva')
            page.get_by_title(f'Exercice {annee+1}',exact=True).click()
            choix=page.get_by_label('Année civile TVA',exact=True)
            choix.select_option(str(annee))
            expect(page.get_by_text(f'Crédit TVA d’ouverture — {annee}',exact=True)).to_be_visible()
            choix.select_option(str(annee+1))
            expect(page.get_by_text(f'Crédit TVA d’ouverture — {annee+1}',exact=True)).to_be_visible()
            assert donnees_metier(application)==avant
        finally:browser.close()


def test_593_calendrier_retarde_ne_declenche_jamais_annee_zero(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();page.set_default_timeout(20000)
            connexion(page,application['web_url'],email,password)
            requetes=[]
            page.on('request',lambda r:requetes.append(r.url) if '/api/tva/declaration?' in r.url else None)
            with application['engine'].connect() as db:
                tx=db.begin();db.execute(text('LOCK TABLE exercices_comptables IN ACCESS EXCLUSIVE MODE'))
                try:
                    page.goto(application['web_url']+'/declaration-tva',wait_until='domcontentloaded')
                    page.get_by_role('heading',name='Déclaration TVA',exact=True).wait_for()
                    page.get_by_text('Mois',exact=True).locator('..').locator('select').select_option('3')
                    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                    assert requetes==[],requetes
                    expect(page.get_by_role('button',name='Imprimer',exact=True)).to_be_disabled()
                finally:tx.rollback()
            expect(page.get_by_role('button',name='Imprimer',exact=True)).to_be_enabled()
            assert requetes and all(int(parse_qs(urlparse(u).query)['exercice'][0])==date.today().year for u in requetes)
            assert any(parse_qs(urlparse(u).query).get('mois')==['3'] for u in requetes)
        finally:browser.close()
