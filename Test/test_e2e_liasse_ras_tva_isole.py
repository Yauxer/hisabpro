"""Cockpit583 : registre099 connecté, trois rôles, années et sociétés réelles."""
from contextlib import closing
from datetime import date
import re
import pytest
from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)
from test_ras_tva_registre_isole import jeu
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_logo_societe import image_data
from test_e2e_administration_isole import connexion, observer
from test_permissions_tva_runtime_isole import donnees_metier
from browser_support import chromium_executable
from test_e2e_navigation_liasse_isole import test_menu_liasse_et_acces_etats_et_editor_etic as test_583_navigation_bilan_cpc_etic_conservee


def ouvrir(page, app, annee=None):
    annee = annee or date.today().year
    page.goto(app['web_url'] + '/liasse-fiscale')
    page.get_by_role('button', name='Retenues TVA', exact=True).click()
    page.get_by_text(f'Registre des retenues TVA · {annee}', exact=True).click()
    return page.get_by_role('region', name='Registre interne des retenues TVA', exact=True)


@pytest.mark.parametrize('role,largeur', [('admin',1440), ('comptable',390), ('lecture',390)])
def test_583_liasse_registre_export_et_lecture_sans_mutation(application, role, largeur, tmp_path):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        jeu(api)
        ok(api.patch('/api/societe/moi', json={'logo_url': image_data('PNG')}))
        if role != 'admin':
            email = email.replace('@', '-' + role + '@')
            ok(api.post('/api/utilisateurs', json={'nom':'Cockpit fictif583', 'email':email,
                'mot_de_passe':password, 'role':role}), 201)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width':largeur, 'height':1000})
            page.set_default_timeout(20000)
            erreurs, serveur = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            avant = donnees_metier(application)
            registre = ouvrir(page, application)
            expect(registre.get_by_role('article')).to_have_count(3)
            expect(page.get_by_text('Suivi interne à la date de consultation', exact=False)).to_be_visible()
            expect(page.get_by_role('button', name='T1 · Bilan', exact=True)).to_have_count(1)
            expect(page.get_by_role('button', name='T2 · CPC', exact=True)).to_have_count(1)
            with page.expect_download() as attente:
                registre.get_by_role('button', name='PDF', exact=True).click()
            fichier = tmp_path / f'cockpit583_{role}.pdf'
            attente.value.save_as(fichier)
            assert attente.value.suggested_filename == f'registre_ras_tva_{date.today().year}.pdf'
            pdf = PdfReader(fichier)
            assert any(p.images for p in pdf.pages)
            assert '75,00' in '\n'.join(p.extract_text() or '' for p in pdf.pages)
            assert registre.evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
            registre.scroll_into_view_if_needed()
            page.screenshot(path=str(tmp_path / f'cockpit583_{role}_{largeur}.png'))
            if role == 'lecture':
                expect(page.get_by_role('button', name='Finaliser', exact=True)).to_have_count(0)
            assert donnees_metier(application) == avant
            assert not erreurs and not serveur, (erreurs, serveur)
        finally:
            browser.close()


def test_583_changement_exercice_recharge_sans_anciennes_captures(application):
    api, email, password = client(application)
    annee = date.today().year
    with closing(api), sync_playwright() as p:
        jeu(api)
        ok(api.post('/api/exercices', json={'annee':annee-1, 'date_debut':f'{annee-1}-01-01',
            'date_fin':f'{annee-1}-12-31'}), 201)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page();page.set_default_timeout(20000)
            observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            avant = donnees_metier(application)
            registre = ouvrir(page, application)
            expect(registre.get_by_role('article')).to_have_count(3)
            page.get_by_title(f'Exercice {annee-1}', exact=True).click()
            page.get_by_text(f'Registre des retenues TVA · {annee-1}', exact=True).click()
            expect(registre.get_by_role('article')).to_have_count(0)
            expect(registre.get_by_text('Aucune capture TVA guidée tracée pour cette année.', exact=True)).to_be_visible()
            page.get_by_title(f'Exercice {annee}', exact=True).click()
            page.get_by_text(f'Registre des retenues TVA · {annee}', exact=True).click()
            expect(registre.get_by_role('article')).to_have_count(3)
            assert donnees_metier(application) == avant
        finally:
            browser.close()


def test_583_changement_societe_ne_conserve_pas_les_captures(application):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        jeu(api)
        nom = ok(api.get('/api/societe/moi'))['raison_sociale']
        seconde = ok(api.post('/api/societes/nouvelle', json={'raison_sociale':'Seconde fictive583'}), 201)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page();page.set_default_timeout(20000)
            observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            avant = donnees_metier(application)
            registre = ouvrir(page, application)
            expect(registre.get_by_role('article')).to_have_count(3)
            page.get_by_role('button', name=nom, exact=True).click()
            page.get_by_role('button', name=re.compile(re.escape(seconde['raison_sociale']))).click()
            expect(page.get_by_role('button', name=seconde['raison_sociale'], exact=True)).to_be_visible()
            registre = ouvrir(page, application)
            expect(registre.get_by_role('article')).to_have_count(0)
            expect(registre.get_by_text('Aucune capture TVA guidée tracée pour cette année.', exact=True)).to_be_visible()
            assert donnees_metier(application) == avant
        finally:
            browser.close()


def test_589_exercice_decale_selection_annee_civile_explicite(application):
    api, email, password = client(application)
    annee = date.today().year
    with closing(api), sync_playwright() as p:
        ok(api.patch(f'/api/exercices/{annee}', json={'date_debut':f'{annee-1}-07-01',
            'date_fin':f'{annee}-06-30'}))
        ok(api.post('/api/exercices', json={'annee':annee+1,'date_debut':f'{annee}-07-01',
            'date_fin':f'{annee+1}-06-30'}),201)
        jeu(api)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(20000)
            erreurs, serveur = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            avant = donnees_metier(application)
            page.goto(application['web_url']+'/liasse-fiscale')
            page.get_by_title(f'Exercice {annee+1}',exact=True).click()
            page.get_by_role('button',name='Retenues TVA',exact=True).click()
            page.get_by_text(f'Registre des retenues TVA · {annee}',exact=True).click()
            registre = page.get_by_role('region',name='Registre interne des retenues TVA',exact=True)
            expect(registre.get_by_role('article')).to_have_count(3)
            choix = page.get_by_label('Année civile du registre', exact=True)
            assert choix.locator('option').all_text_contents() == [str(annee),str(annee+1)]
            expect(page.get_by_text('Le registre couvre l’année civile entière choisie', exact=False)).to_be_visible()
            choix.select_option(str(annee+1))
            page.get_by_text(f'Registre des retenues TVA · {annee+1}',exact=True).click()
            expect(registre.get_by_role('article')).to_have_count(0)
            expect(registre.get_by_text('Aucune capture TVA guidée tracée pour cette année.',exact=True)).to_be_visible()
            choix.select_option(str(annee))
            page.get_by_text(f'Registre des retenues TVA · {annee}',exact=True).click()
            expect(registre.get_by_role('article')).to_have_count(3)
            assert donnees_metier(application) == avant
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:
            browser.close()
