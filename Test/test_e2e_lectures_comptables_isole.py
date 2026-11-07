"""Erreurs réelles de lecture : brouillon fictif et filtre inversé, sans faux zéro."""
from contextlib import closing
from datetime import date
import pytest
from playwright.sync_api import sync_playwright,expect
from test_lecture_ecritures_invalides_isole import (
    application,application090,application089,application087,migration,historique,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_justificatifs_modeles_runtime_isole import ecriture,original
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


@pytest.mark.parametrize('largeur',[1440,390])
def test_accueil_erreur_brouillons_sans_fausse_liste_vide(application,largeur):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        valide=ecriture(api,validee=True,reference='DEFINITIVE-FICTIVE474')
        avant_valide=original(application,valide)
        eid,avant=historique(application,api,'NaN')
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':largeur,'height':1000})
            page.set_default_timeout(15000)
            erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            bloc=page.get_by_role('region',name='Écritures à valider',exact=True)
            expect(bloc.get_by_role('alert')).to_contain_text(str(eid))
            expect(bloc.get_by_role('table')).to_have_count(0)
            expect(page.get_by_text('Résultat net',exact=True)).to_be_visible()
            with page.expect_response(lambda r:'/api/ecritures?' in r.url and r.request.method=='GET') as refus:
                bloc.get_by_role('button',name='Réessayer',exact=True).click()
            assert refus.value.status==409
            expect(bloc.get_by_role('alert')).to_contain_text(str(eid))
            assert original(application,eid)==avant
            assert original(application,valide)==avant_valide
            rapport=ok(api.get('/api/ecritures/reporting/grand-livre',params={'exercice':date.today().year}))
            assert rapport['nb_ecritures']==1
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()


@pytest.mark.parametrize('largeur',[1440,390])
def test_grand_livre_filtre_invalide_ne_devient_pas_un_rapport_vide(application,largeur):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        eid=ecriture(api,validee=True,reference='GRAND-LIVRE-FICTIF474')
        avant=original(application,eid);annee=date.today().year
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':largeur,'height':1000})
            page.set_default_timeout(15000)
            erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/grand-livre')
            expect(page.get_by_text('2 comptes mouvementés · 1 écriture(s) définitive(s)',exact=True)).to_be_visible()
            dates=page.locator('main input[type="date"]')
            dates.nth(0).fill(f'{annee}-12-31')
            dates.nth(1).fill(f'{annee}-01-01')
            expect(page.get_by_role('alert')).to_contain_text('La date de début')
            expect(page.get_by_role('table')).to_have_count(0)
            expect(page.get_by_text('0 comptes mouvementés',exact=False)).to_have_count(0)
            expect(page.get_by_role('button',name='Exporter CSV',exact=False)).to_be_disabled()
            dates.nth(0).fill(f'{annee}-01-01')
            dates.nth(1).fill(f'{annee}-12-31')
            expect(page.get_by_role('alert')).to_have_count(0)
            expect(page.get_by_text('2 comptes mouvementés · 1 écriture(s) définitive(s)',exact=True)).to_be_visible()
            expect(page.get_by_role('button',name='Exporter CSV',exact=False)).to_be_enabled()
            assert original(application,eid)==avant
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()
