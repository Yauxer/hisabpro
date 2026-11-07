"""Préparation ventes et CSV vus dans Edge : API/PGnonce réels."""
from datetime import date
import csv,io
from pathlib import Path
import pytest
from sqlalchemy import text
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion,observer
from test_ventes_preparation_isole import application,facture,ok
from test_ras_lecture_conservation import client
from test_articles_alertes_stock_historique_postgres import cible
from test_validation_facture_montants_historiques_postgres import photographie


def ouvrir(page,app,email,password):
    connexion(page,app['web_url'],email,password)
    page.goto(app['web_url']+'/liasse-fiscale',wait_until='domcontentloaded')
    page.get_by_role('button',name='Préparation ventes',exact=True).click()
    return page.get_by_role('region',name='Préparation annuelle des ventes',exact=True)


@pytest.mark.parametrize('largeur',[1365,390])
def test_preparation_interface_export_exact_inconnu_sans_reparation(application,largeur,tmp_path):
    api,email,password=client(application)
    try:
        f,_=facture(api,100)
        facture(api,200)
        ok(api.post('/api/avoirs',json={'facture_id':f['id'],'date':f'{date.today().year}-03-15',
            'motif':'Correction fictive','lignes':[{'facture_ligne_id':f['lignes'][0]['id'],'quantite':0.3}]}),201)
        avant=photographie(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
                errors,server=observer(page,application['api_url'])
                region=ouvrir(page,application,email,password)
                expect(region.get_by_role('button',name='Exporter les ventes CSV',exact=True)).to_be_disabled()
                with page.expect_response(lambda r:'/api/etats/ventes/preparation/' in r.url) as lecture:
                    region.get_by_role('button',name='Préparer les ventes',exact=True).click()
                assert lecture.value.status==200,lecture.value.text()
                data=lecture.value.json()
                expect(region.locator('tbody tr')).to_have_count(3)
                expect(region).to_contain_text('270,00')
                expect(region).to_contain_text('324,00')
                expect(region).to_contain_text('extérieure à l’archive')
                with page.expect_download() as fichier:
                    region.get_by_role('button',name='Exporter les ventes CSV',exact=True).click()
                fichier.value.save_as(tmp_path/'ventes.csv')
                contenu=(tmp_path/'ventes.csv').read_bytes().decode('utf-8-sig')
                assert contenu==data['csv']
                assert any(r[0]=='Total complet' and r[7:10]==['270.00','54.00','324.00']
                           for r in csv.reader(io.StringIO(contenu),delimiter=';'))
                assert photographie(application)==avant
                # Corruption historique synthétique, uniquement dans le nonce.
                inconnu,_=facture(api,50,valider=False)
                cible(application)
                with application['engine'].begin() as db:
                    db.execute(text("UPDATE lignes_facture SET prix_unitaire='NaN' WHERE facture_id=:id"),{'id':inconnu['id']})
                    db.execute(text('UPDATE factures SET est_validee=true,numero=:n WHERE id=:id'),
                        {'id':inconnu['id'],'n':f"HIST-FICT-{inconnu['id']}"})
                apres_preparation=photographie(application)
                with page.expect_response(lambda r:'/api/etats/ventes/preparation/' in r.url) as relu:
                    region.get_by_role('button',name='Actualiser les ventes',exact=True).click()
                assert relu.value.status==200 and relu.value.json()['totaux'] is None
                expect(region.get_by_role('alert')).to_contain_text('Total complet à vérifier')
                expect(region.locator('tbody tr')).to_have_count(4)
                expect(region.locator('tbody tr').filter(has_text=f"HIST-FICT-{inconnu['id']}")).to_contain_text('À vérifier')
                page.screenshot(path=str(Path(__file__).resolve().parents[1]/f'.codex-tests/ventes418_{largeur}.png'),full_page=True)
                assert photographie(application)==apres_preparation
                assert not errors and not server,(errors,server)
            finally:browser.close()
    finally:api.close()


def test_preparation_tardive_ancienne_annee_ignoree(application):
    api,email,password=client(application)
    try:
        annee=date.today().year
        facture(api,100)
        ok(api.post('/api/exercices',json={'annee':annee-1,'date_debut':f'{annee-1}-01-01','date_fin':f'{annee-1}-12-31'}),201)
        avant=photographie(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            retenues=[]
            try:
                page=browser.new_page();page.set_default_timeout(20000)
                region=ouvrir(page,application,email,password)
                def retenir(route):
                    reponse=route.fetch();assert reponse.status==200
                    retenues.append((route,reponse))
                    page.evaluate("console.log('VENTES418_SOURCE_RETENUE')")
                motif=f'**/api/etats/ventes/preparation/{annee}'
                page.route(motif,retenir)
                with page.expect_console_message(lambda m:m.text=='VENTES418_SOURCE_RETENUE'):
                    region.get_by_role('button',name='Préparer les ventes',exact=True).click()
                assert len(retenues)==1
                page.locator('select').filter(has=page.locator(f'option[value="{annee-1}"]')).first.select_option(str(annee-1))
                region=page.get_by_role('region',name='Préparation annuelle des ventes',exact=True)
                expect(region.get_by_role('button',name='Préparer les ventes',exact=True)).to_be_enabled()
                with page.expect_response(lambda r:r.url.endswith(f'/ventes/preparation/{annee-1}')) as courant:
                    region.get_by_role('button',name='Préparer les ventes',exact=True).click()
                assert courant.value.status==200 and courant.value.json()['documents']==[]
                with page.expect_response(lambda r:r.url.endswith(f'/ventes/preparation/{annee}')):
                    for route,reponse in retenues:route.fulfill(response=reponse)
                retenues.clear();page.unroute(motif)
                expect(region).to_contain_text('Aucune pièce de vente définitive')
                expect(region.locator('tbody tr')).to_have_count(0)
                assert photographie(application)==avant
            finally:
                for route,reponse in retenues:route.fulfill(response=reponse)
                browser.close()
    finally:api.close()
