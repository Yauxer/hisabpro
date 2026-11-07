"""Correspondance puis validation/comptabilisation ordinaires dans Edge réel."""
from pathlib import Path
from datetime import date
import re
import pytest
from sqlalchemy import text
from test_factures_liees635_isole import (
    application,application101,application100,application099,application098,application097,application093,
    application092,application091,application090,application089,application087,migration,vente,chemin,demande,PATH)
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion,observer
from test_e2e_annee_connectee_isole import valider_brouillons_ui
from test_permissions_tva_runtime_isole import donnees_metier
from browser_support import chromium_executable


@pytest.mark.parametrize('largeur,decale',[(1440,False),(390,False),(390,True)])
def test_635_transfert_switch_validation_et_deux_journaux_edge(application,largeur,decale,tmp_path):
    from playwright.sync_api import sync_playwright,expect
    a,b,ids=vente(application)
    annee_cible=date.today().year+int(decale and date.today().month>=7)
    if decale:
        y=date.today().year
        ok(b.patch(f'/api/exercices/{y}',json={'date_debut':f'{y-1}-07-01','date_fin':f'{y}-06-30'}))
        ok(b.post('/api/exercices',json={'annee':y+1,'date_debut':f'{y}-07-01','date_fin':f'{y+1}-06-30'}),201)
    vendeur=ok(a.get('/api/societe/moi'))['raison_sociale'];acheteur=ok(b.get('/api/societe/moi'))['raison_sociale']
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
            errors,serveur=observer(page,application['api_url']);page.on('dialog',lambda d:d.accept())
            try:
                connexion(page,application['web_url'],ids['email'],ids['password'])
                page.goto(application['web_url']+'/factures')
                row=page.locator('tbody tr').filter(has_text='Acheteur représenté fictif633');expect(row).to_have_count(1)
                # Vente comptabilisée par sa commande ordinaire, pas par le pont.
                with page.expect_response(lambda r:r.url.endswith(f'/api/factures/{ids["fid"]}/comptabiliser')) as r:
                    row.get_by_title("Générer l'écriture comptable de cette facture",exact=True).click()
                assert r.value.status==200,r.value.text()
                row.click()
                page.locator('summary').filter(has_text='Correspondance entre sociétés').click()
                panel=page.get_by_role('region',name='Correspondance entre sociétés')
                panel.get_by_label('Liaison de vente',exact=True).select_option(str(ids['liaison']))
                for x in ids['corps']['lignes']:panel.get_by_label(f'Article acheteur pour la ligne {x["source_ligne_id"]}',exact=True).select_option(str(ids['aa']))
                panel.get_by_label('Nature TVA de l’achat',exact=True).select_option('charge')
                panel.get_by_label('TVA déductible propre à la facture (%)',exact=True).fill('100')
                with page.expect_response(lambda r:r.url.endswith(chemin(ids,'/apercu'))) as r:
                    panel.get_by_role('button',name='Vérifier le brouillon d’achat',exact=True).click()
                assert r.value.status==200,r.value.text()
                expect(panel.get_by_text(re.compile('TTC 600,00 MAD'))).to_be_visible()
                panel.get_by_role('checkbox').check()
                with page.expect_response(lambda r:r.url.endswith(chemin(ids)) and r.request.method=='POST') as r:
                    panel.get_by_role('button',name='Créer le brouillon chez l’acheteur',exact=True).click()
                assert r.value.status==201,r.value.text()
                suivi=r.value.json();fid=suivi['facture_achat_id']
                assert suivi['achat']['exercice']==annee_cible
                expect(panel.get_by_text(re.compile(f'Achat lié #{fid}'))).to_be_visible()
                expect(panel.get_by_text('Aucun écart documentaire détecté entre les deux factures.',exact=True)).to_be_visible()
                page.screenshot(path=str(tmp_path/f'correspondance635-{largeur}.png'),full_page=True)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
                page.get_by_role('dialog').get_by_role('button',name='Fermer',exact=True).click()
                page.get_by_role('button',name=vendeur,exact=True).click()
                with page.expect_response(lambda r:r.url.endswith(f'/api/societes/switcher/{ids["bid"]}')) as r:
                    page.get_by_role('button').filter(has_text=acheteur).click()
                assert r.value.status==200
                expect(page.get_by_role('button',name=acheteur,exact=True)).to_be_visible()
                page.get_by_label('Exercice comptable',exact=True).select_option(str(annee_cible))
                page.goto(application['web_url']+'/factures')
                row=page.locator('tbody tr').filter(has_text='Vendeur représenté fictif633');expect(row).to_have_count(1)
                with page.expect_response(lambda r:r.url.endswith(f'/api/factures/{fid}/valider')) as r:
                    row.get_by_title('Valider définitivement',exact=True).click()
                assert r.value.status==200,r.value.text()
                with page.expect_response(lambda r:r.url.endswith(f'/api/factures/{fid}/comptabiliser')) as r:
                    row.get_by_title("Générer l'écriture comptable de cette facture",exact=True).click()
                assert r.value.status==200,r.value.text()
                valider_brouillons_ui(page,application,1)
                page.goto(application['web_url']+'/factures');row=page.locator('tbody tr').filter(has_text='Vendeur représenté fictif633');row.click()
                page.locator('summary').filter(has_text='Correspondance entre sociétés').click()
                panel=page.get_by_role('region',name='Correspondance entre sociétés')
                expect(panel.get_by_text(re.compile('Achat : validé, comptabilisé'))).to_be_visible()
                assert panel.locator('form').count()==0
                assert not errors and not serveur,(errors,serveur)
            except BaseException:
                print(page.locator('body').inner_text()[-6000:]);page.screenshot(path=str(tmp_path/f'echec635-{largeur}.png'),full_page=True);raise
            finally:browser.close()
        suivi=ok(a.get(f'{PATH}/factures/{ids["fid"]}/correspondance'))
        assert suivi['ecarts']==[] and suivi['vente']['comptabilisee'] and suivi['achat']['comptabilisee']
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id IN (:a,:b)'),{'a':ids['sid'],'b':ids['bid']})==2
            assert db.scalar(text('SELECT count(*) FROM factures_correspondantes WHERE facture_vente_id=:f'),{'f':ids['fid']})==1
    finally:a.close();b.close()


def test_635_lecteur_aucune_creation_et_pas_de_mutation_edge(application):
    from playwright.sync_api import sync_playwright,expect
    a,b,ids=vente(application)
    try:
        with application['engine'].begin() as db:db.execute(text("UPDATE utilisateurs SET role='lecture' WHERE id=:id"),{'id':ids['uid']})
        avant=donnees_metier(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':390,'height':1000});errors,serveur=observer(page,application['api_url'])
                connexion(page,application['web_url'],ids['email'],ids['password'])
                page.goto(application['web_url']+'/factures');page.locator('tbody tr').filter(has_text='Acheteur représenté fictif633').click()
                page.locator('summary').filter(has_text='Correspondance entre sociétés').click()
                panel=page.get_by_role('region',name='Correspondance entre sociétés')
                expect(panel.get_by_text('Consultation seule : aucune commande de création disponible.',exact=True)).to_be_visible()
                assert panel.locator('form').count()==0 and panel.locator('select').count()==0
                assert not errors and not serveur,(errors,serveur)
            finally:browser.close()
        assert donnees_metier(application)==avant
    finally:a.close();b.close()
