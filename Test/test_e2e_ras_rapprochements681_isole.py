"""Rapprochement puis retrait dans Edge réel, sans écritures générées."""
from contextlib import closing
from pypdf import PdfReader
from test_logo_societe import image_data
import pytest
from playwright.sync_api import sync_playwright,expect
from test_ras_rapprochements681_isole import (
    application,application102,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,application089,application087,migration,
    client,ok,capture,versement,corps,photo,chemin)
from test_e2e_administration_isole import connexion,observer
from test_e2e_ras_tva_registre_isole import ouvrir
from browser_support import chromium_executable
from test_permissions_tva_runtime_isole import donnees_metier


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_681_rapprochement_partiel_retrait_et_roles_edge(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        _,_,c=capture(api);cid=c['capture']['id'];e=versement(api)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        if role=='lecture':ok(api.post(chemin(cid),json=corps(e,'30.00')),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Rapprochement fictif681','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            avant=photo(application)
            registre=ouvrir(page,application)
            article=registre.get_by_role('article',name=f'Capture TVA {cid}',exact=True)
            article.get_by_text('Rapprochement comptable d’un versement',exact=True).click()
            panel=article.get_by_role('region',name=f'Rapprochements de la capture {cid}',exact=True)
            if role=='lecture':
                expect(panel.get_by_text('Actif · 30,00 MAD',exact=True)).to_be_visible()
                assert panel.get_by_role('button',name='Enregistrer le rapprochement documentaire',exact=True).count()==0
                assert panel.get_by_role('button',name='Retirer le rapprochement',exact=False).count()==0
                donnees=donnees_metier(application)
                panel.get_by_role('button',name='Actualiser les rapprochements',exact=True).click()
                expect(panel.get_by_text('Actif · 30,00 MAD',exact=True)).to_be_visible()
                assert donnees_metier(application)==donnees
            else:
                panel.get_by_label('Référence de la pièce à chercher',exact=True).fill(e['reference'])
                panel.get_by_role('button',name='Chercher une pièce validée',exact=True).click()
                expect(panel.get_by_label('Pièce comptable validée',exact=True).locator('option')).to_have_count(2)
                panel.get_by_label('Pièce comptable validée',exact=True).select_option(str(e['id']))
                panel.get_by_label('Montant à rapprocher MAD',exact=True).fill('30,00')
                panel.get_by_role('checkbox').check()
                with page.expect_response(lambda r:r.url.endswith(chemin(cid)) and r.request.method=='POST') as reponse:
                    panel.get_by_role('button',name='Enregistrer le rapprochement documentaire',exact=True).click()
                assert reponse.value.status==201,reponse.value.text()
                expect(panel.get_by_text('Actif · 30,00 MAD',exact=True)).to_be_visible()
                expect(panel.get_by_text('Capacité documentaire non rapprochée',exact=False)).to_contain_text('45,00 MAD')
                rid=reponse.value.json()['items'][0]['id']
                panel.get_by_role('button',name=f'Retirer le rapprochement #{rid}',exact=True).click()
                panel.get_by_label('Motif du retrait',exact=True).fill('Révision documentaire fictive681')
                with page.expect_response(lambda r:r.url.endswith(chemin(cid)+f'/{rid}/retirer')) as retrait:
                    panel.get_by_role('button',name='Confirmer le retrait documentaire',exact=True).click()
                assert retrait.value.status==200,retrait.value.text()
                expect(panel.get_by_text('Retiré · 30,00 MAD',exact=True)).to_be_visible()
                expect(panel.get_by_text('Capacité documentaire non rapprochée',exact=False)).to_contain_text('75,00 MAD')
            panel.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'rapprochement681-{role}-{largeur}.png'))
            with page.expect_download() as export:
                panel.get_by_role('button',name='PDF des rapprochements documentaires',exact=True).click()
            assert export.value.suggested_filename==f'Rapprochements_RAS_capture_{cid}.pdf'
            pdf=PdfReader(export.value.path());texte=' '.join(p.extract_text() for p in pdf.pages)
            assert e['reference'] in texte and '30,00 MAD' in texte and any(p.images for p in pdf.pages)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert photo(application)==avant and not errors and not serveur,(errors,serveur)
        finally:browser.close()
