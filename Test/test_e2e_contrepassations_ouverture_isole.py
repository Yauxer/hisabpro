from contextlib import closing
import pytest
from playwright.sync_api import sync_playwright, expect
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ajustements_inventaire_isole import exercice
from test_contrepassations_ouverture_isole import creer
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_e2e_administration_isole import connexion, observer
from test_e2e_annee_connectee_isole import valider_brouillons_ui
from browser_support import chromium_executable


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_601_suivi_statuts_et_journal_trois_roles(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        exercice(api)
        a=creer(api);b=creer(api,libelle='Source fictive601 encore en brouillon')
        ok(api.post(f"/api/ecritures/{a['ecriture_id']}/valider"))
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Fictif601','email':email,'mot_de_passe':password,'role':role}),201)
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            page.on('dialog',lambda d:d.accept())
            erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application)
            page.goto(application['web_url']+'/cloture')
            region=page.get_by_role('region',name='Contrepassations d’ouverture',exact=True)
            expect(region).to_contain_text('2 liée(s) · 2 à valider · 0 validée(s)')
            expect(region).to_contain_text('Débit 1.200,13 MAD · Crédit 1.200,13 MAD')
            expect(region).to_contain_text('Source encore en brouillon')
            expect(region).to_contain_text('2026-01-01')
            expect(region.locator('article')).to_have_count(2)
            region.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'contrepassations601_{role}_{largeur}.png'))
            assert region.evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
            assert donnees_metier(application)==avant
            # Changer d'exercice retire immédiatement les pièces de destination.
            page.get_by_label('Exercice actif',exact=True).select_option('2025')
            expect(region).to_contain_text('Aucune contrepassation liée dans cet exercice.')
            expect(region.locator('article')).to_have_count(0)
            page.get_by_label('Exercice actif',exact=True).select_option('2026')
            expect(region.locator('article')).to_have_count(2)
            region.get_by_role('button',name='Ouvrir le Journal des contrepassations',exact=True).click()
            expect(page).to_have_url(application['web_url']+'/journal')
            if role=='lecture':
                expect(page.get_by_role('button',name='Valider les brouillons',exact=True)).to_be_disabled()
                assert donnees_metier(application)==avant
            else:
                # Validation ordinaire réelle, aucune nouvelle route de mutation.
                valider_brouillons_ui(page,application,2)
                page.goto(application['web_url']+'/cloture')
                expect(region).to_contain_text('2 liée(s) · 0 à valider · 2 validée(s)')
                ok(api.post(f"/api/ecritures/{b['ecriture_id']}/valider"))
                region.get_by_role('button',name='Actualiser les contrepassations',exact=True).click()
                expect(region).not_to_contain_text('Source encore en brouillon')
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()


def test_601_pagination_navigateur(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        exercice(api)
        for i in range(21):creer(api,libelle=f'Contrat fictif pagination601 {i}')
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page();page.set_default_timeout(20000)
            connexion(page,application['web_url'],email,password);avant=donnees_metier(application)
            page.goto(application['web_url']+'/cloture')
            region=page.get_by_role('region',name='Contrepassations d’ouverture',exact=True)
            expect(region.locator('article')).to_have_count(20)
            expect(region).to_contain_text('Page 1 / 2')
            region.get_by_role('button',name='Suivantes',exact=True).click()
            expect(region.locator('article')).to_have_count(1)
            expect(region).to_contain_text('Page 2 / 2')
            region.get_by_role('button',name='Précédentes',exact=True).click()
            expect(region.locator('article')).to_have_count(20)
            assert donnees_metier(application)==avant
        finally:navigateur.close()
