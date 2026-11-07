"""Vrais Edge/API/PostgreSQL099 : parcours guidé et dossier conservé."""
from contextlib import closing
from datetime import date
from pathlib import Path
import uuid
import pytest
from playwright.sync_api import sync_playwright, expect
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    preparer, paiement, capturer,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_ras_capture_isole import ouvrir
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable
from test_permissions_tva_runtime_isole import donnees_metier


def ouvrir_capture(page, app, nature, cash):
    ouvrir(page, app, nature)
    row=page.locator('tbody tr').filter(has_text=f'{cash},00 MAD')
    row.get_by_title('Consulter ou déclarer la RAS',exact=True).click()
    modal=page.get_by_role('dialog')
    modal.get_by_role('button',name='RAS TVA guidée',exact=True).click()
    return modal,row


def remplir(modal, quote='400', tva='66.67', nature='vente'):
    modal.get_by_text('Assistant RAS TVA · 2026',exact=True).click()
    expect(modal.get_by_label('Date réelle du paiement',exact=True)).to_be_disabled()
    modal.get_by_label('Situation du payeur',exact=True).select_option('pm_privee_assujettie')
    modal.get_by_label('Situation du prestataire',exact=True).select_option('pp_assujettie')
    modal.get_by_label('Service relevant de la liste B',exact=True).select_option('oui')
    modal.get_by_label('Exclusions de l’article 117',exact=True).select_option('aucune_apres_controle')
    modal.get_by_label('Attestation de régularité fiscale',exact=True).select_option('presentee')
    modal.get_by_label('Date de délivrance de l’attestation',exact=True).fill('2026-09-01')
    modal.get_by_label('Référence de l’attestation',exact=True).fill('ATTESTATION-FICTIVE573')
    modal.get_by_label('Quote-part TTC payée avant retenues (MAD)',exact=True).fill(quote)
    modal.get_by_label('TVA correspondant à cette quote-part (MAD)',exact=True).fill(tva)
    modal.get_by_role('button',name='Simuler la RAS TVA',exact=True).click()
    expect(modal.get_by_role('region',name='Résultat de la simulation RAS TVA')).to_contain_text('Calcul de préparation')
    modal.get_by_label('Justificatif de ventilation TVA',exact=True).fill('VENTILATION-FICTIVE573-'+quote)
    modal.get_by_label('Référence RAS TVA',exact=True).fill('RAS-FICTIVE573-'+quote)
    compte=modal.get_by_label('Compte destination RAS TVA',exact=True)
    expect(compte).to_have_value('')
    compte.select_option('3453' if nature=='vente' else '4457')


@pytest.mark.parametrize('nature,largeur,role',[
    ('vente',1440,'admin'),('achat',390,'comptable'),('vente',390,'comptable'),('achat',1440,'admin'),
])
def test_573_partiels_guides_refresh_dossier_et_garde_declaration(application,nature,largeur,role,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        f,r=preparer(api,nature,cash='350.00')
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Comptable fictif573','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            for cash,quote,tva,ras,solde in [(350,'400','66.67','50,00',800),(700,'800','133.33','100,00',0)]:
                if cash==700:r=paiement(api,f,str(cash))
                modal,row=ouvrir_capture(page,application,nature,cash)
                remplir(modal,quote,tva,nature)
                modal.get_by_role('button',name='Vérifier le règlement et afficher l’aperçu',exact=True).click()
                apercu=modal.get_by_role('region',name='Aperçu de la capture RAS TVA',exact=True)
                expect(apercu).to_contain_text(ras+' MAD')
                bouton=apercu.get_by_role('button',name='Préparer la capture RAS TVA et son OD',exact=True)
                expect(bouton).to_be_disabled()
                apercu.get_by_role('checkbox').check()
                expect(bouton).to_be_enabled()
                # La vraie réponse POST est retenue après transaction pour vérifier les contrôles occupés.
                retenues=[]
                def retarder(route):
                    reponse=route.fetch();assert reponse.status==200
                    retenues.append((route,reponse));page.evaluate('window.__capture573Terminee=true')
                page.route(f'**/api/reglements/{r["id"]}/ras-tva',retarder)
                bouton.click()
                page.wait_for_function('window.__capture573Terminee===true')
                expect(modal.get_by_role('button',name='Saisie déclarative libre',exact=True)).to_be_disabled()
                expect(modal.get_by_label('Justificatif de ventilation TVA',exact=True)).to_be_disabled()
                page.keyboard.press('Escape');expect(modal).to_be_visible()
                retenues[0][0].fulfill(response=retenues[0][1]);page.unroute(f'**/api/reglements/{r["id"]}/ras-tva',retarder)
                page.evaluate('window.__capture573Terminee=false')
                modal.wait_for(state='hidden')
                expect(row).to_contain_text('Soldée' if solde==0 else 'Partiel')
                assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant']==solde
                row.get_by_title('Consulter ou déclarer la RAS',exact=True).click()
                modal=page.get_by_role('dialog')
                dossier=modal.get_by_role('region',name='Dossier RAS TVA conservé',exact=True)
                expect(dossier).to_contain_text(ras+' MAD')
                expect(dossier).to_contain_text('VENTILATION-FICTIVE573-'+quote)
                expect(dossier).not_to_contain_text('À vérifier')
                expect(dossier).to_contain_text(quote+',00 MAD')
                expect(modal.get_by_role('button',name='RAS TVA guidée',exact=True)).to_have_count(0)
                dossier.scroll_into_view_if_needed()
                page.screenshot(path=str(tmp_path/f'ras573_{nature}_{largeur}.png'))
                assert modal.evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
                modal.get_by_text('Fermer',exact=True).click()
            page.goto(application['web_url']+'/declaration-tva')
            expect(page.get_by_text('Déclaration TVA automatique à compléter',exact=False)).to_be_visible()
            # Une déclaration échouée ne conserve pas un ancien montant et ne s'imprime pas.
            expect(page.get_by_role('button',name='Imprimer',exact=False)).to_be_disabled()
            expect(page.get_by_text('TVA collectée',exact=True)).to_have_count(0)
            expect(page.get_by_text('Calcul indisponible',exact=True)).to_be_visible()
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:browser.close()


def test_573_apercu_retarde_ignore_apres_changement(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        _,r=preparer(api,cash='350.00')
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(20000)
            connexion(page,application['web_url'],email,password)
            modal,_=ouvrir_capture(page,application,'vente',350);remplir(modal)
            avant=donnees_metier(application);retenues=[]
            def retarder(route):
                reponse=route.fetch();assert reponse.status==200
                retenues.append((route,reponse));page.evaluate('window.__apercu573Retarde=true')
            page.route('**/ras-tva/apercu',retarder)
            modal.get_by_role('button',name='Vérifier le règlement et afficher l’aperçu',exact=True).click()
            page.wait_for_function('window.__apercu573Retarde===true')
            modal.get_by_label('Justificatif de ventilation TVA',exact=True).fill('NOUVELLE-VENTILATION573')
            retenues[0][0].fulfill(response=retenues[0][1]);page.unroute('**/ras-tva/apercu',retarder)
            page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            expect(modal.get_by_role('region',name='Aperçu de la capture RAS TVA')).to_have_count(0)
            assert donnees_metier(application)==avant
            modal.get_by_role('button',name='Vérifier le règlement et afficher l’aperçu',exact=True).click()
            apercu=modal.get_by_role('region',name='Aperçu de la capture RAS TVA')
            expect(apercu).to_be_visible();apercu.get_by_role('checkbox').check()
            # Une nouvelle simulation invalide également le consentement et l'aperçu.
            modal.get_by_label('TVA correspondant à cette quote-part (MAD)',exact=True).fill('60')
            expect(apercu).to_have_count(0)
            assert donnees_metier(application)==avant
        finally:browser.close()


def test_573_lecture_dossier_sans_formulaire_de_capture(application,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        _,r=preparer(api);capturer(api,r)
        email='lecture573-'+uuid.uuid4().hex[:8]+'@example.com'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecture fictive573','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(20000)
            connexion(page,application['web_url'],email,password)
            ouvrir(page,application,'vente')
            page.get_by_title('Consulter ou déclarer la RAS',exact=True).click()
            modal=page.get_by_role('dialog');dossier=modal.get_by_role('region',name='Dossier RAS TVA conservé')
            expect(dossier).to_contain_text('75,00 MAD')
            expect(modal.get_by_role('button',name='RAS TVA guidée',exact=True)).to_have_count(0)
            expect(modal.locator('input,select')).to_have_count(0)
            avant=donnees_metier(application)
            dossier.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/'ras573_lecture390.png'))
            assert donnees_metier(application)==avant
        finally:browser.close()
