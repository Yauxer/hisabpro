from contextlib import closing
import pytest
from playwright.sync_api import sync_playwright, expect
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ajustements_inventaire_isole import exercice
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_e2e_administration_isole import connexion, observer
from test_e2e_annee_connectee_isole import valider_brouillons_ui
from browser_support import chromium_executable


@pytest.mark.parametrize('largeur',[1440,390])
def test_603_suggestions_et_refus_reels_puis_creation(application,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        exercice(api)
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            page.on('dialog',lambda d:d.accept())
            erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/cloture')
            page.get_by_label('Exercice actif',exact=True).select_option('2025')
            expect(page.get_by_role('heading',name='Clôture de l\'exercice 2025',exact=True)).to_be_visible()
            for type_,mauvais,correct,prefixes in [
                ('provision_risque','3942','4508',('15','45')),
                ('depreciation_client','3911','3942',('3942',)),
                ('depreciation_stock','3942','3915',('391',)),
            ]:
                ajouter=page.get_by_role('button',name='Ajouter un ajustement',exact=True)
                expect(ajouter).to_be_enabled();ajouter.click()
                formulaire=page.locator('form').filter(has=page.get_by_role('button',name='Vérifier l’écriture',exact=True))
                formulaire.get_by_label('Type d’ajustement',exact=True).select_option(type_)
                options=formulaire.locator('#comptes-provision-cloture option').evaluate_all('(es)=>es.map(e=>e.value)')
                assert options and correct in options and all(c.startswith(prefixes) for c in options)
                assert mauvais not in options
                formulaire.get_by_label('Libellé / justification',exact=True).fill('Justification fictive603 '+type_)
                formulaire.get_by_label('Montant HT / comptable (MAD)',exact=True).fill('123.45')
                formulaire.get_by_label('Compte de contrepartie',exact=True).fill(mauvais)
                avant=donnees_metier(application)
                with page.expect_response(lambda r:r.request.method=='POST' and '/ajustements/apercu?exercice=2025' in r.url) as rep:
                    formulaire.get_by_role('button',name='Vérifier l’écriture',exact=True).click()
                assert rep.value.status==400,rep.value.text()
                expect(formulaire.get_by_role('alert')).to_contain_text('Compte de provision/dépréciation')
                expect(formulaire.get_by_role('button',name='Créer l’écriture',exact=True)).to_be_disabled()
                assert donnees_metier(application)==avant
                formulaire.get_by_label('Compte de contrepartie',exact=True).fill(correct)
                formulaire.get_by_role('button',name='Vérifier l’écriture',exact=True).click()
                creer=formulaire.get_by_role('button',name='Créer l’écriture',exact=True)
                expect(creer).to_be_enabled()
                with page.expect_response(lambda r:r.request.method=='POST' and '/ajustements?exercice=2025' in r.url) as rep:
                    creer.click()
                assert rep.value.status==200,rep.value.text()
                assert rep.value.json()['contrepassation_id'] is None
                expect(formulaire).to_have_count(0)
            valider_brouillons_ui(page,application,3)
            assert all(a['est_validee'] for a in ok(api.get('/api/cloture/ajustements?exercice=2025')))
            page.goto(application['web_url']+'/cloture')
            expect(page.get_by_text('61961 / 3915',exact=False)).to_be_visible()
            page.screenshot(path=str(tmp_path/f'provisions603_{largeur}.png'))
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()
