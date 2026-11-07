"""Consultation et ajout de documents RAS dans Edge, API et fichiers réels nonce."""
from contextlib import closing
from io import BytesIO
import pytest
from playwright.sync_api import sync_playwright,expect
from openpyxl import load_workbook
from test_ras_documents647_isole import (
    application,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,
    application089,application087,migration,capture,joindre,chemins,ligne,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_justificatifs_modeles_runtime_isole import pdf_fictif,original
from test_e2e_ras_tva_registre_isole import ouvrir as ouvrir_registre
from test_e2e_ras_tva_preparation_isole import ouvrir as ouvrir_preparation
from test_e2e_administration_isole import connexion,observer
from test_permissions_tva_runtime_isole import donnees_metier
from test_logo_societe import image_data
from browser_support import chromium_executable


@pytest.mark.parametrize('role,largeur,mode',[
    ('admin',1440,'registre'),('comptable',390,'preparation'),
    ('lecture',390,'registre'),('lecture',1440,'preparation'),
])
def test_647_documents_od_et_contrepassation_roles_mobile_et_export(application,role,largeur,mode,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        _,_,c=capture(api,annuler=True);cid=c['capture']['id'];eid=c['capture']['ecriture_id']
        _,r=ligne(api,chemins()[0],cid);inverse=r['od_annulation_id']
        f=joindre(api,eid);fann=joindre(api,inverse,'annulation647.pdf')
        ok(api.post(f'/api/ecritures/{eid}/justificatifs',json={'reference':'REF-DOC647','motif':'Complément fictif647'}),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        photos=[original(application,x) for x in (eid,inverse)]
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Documents fictifs647','email':email,'mot_de_passe':password,'role':role}),201)
        avant=donnees_metier(application)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True);page.set_default_timeout(20000)
            erreurs,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            region=(ouvrir_registre if mode=='registre' else ouvrir_preparation)(page,application)
            nom=('Capture TVA ' if mode=='registre' else 'Préparation capture TVA ')+str(cid)
            article=region.get_by_role('article',name=nom,exact=True)
            article.get_by_text('Documents liés aux OD',exact=True).click()
            docs=article.get_by_role('region',name=f'Documents de la capture TVA {cid}',exact=True)
            groupe=docs.get_by_role('region',name=f'Capture · OD {eid}',exact=True)
            contre=docs.get_by_role('region',name=f'Contrepassation · OD {inverse}',exact=True)
            expect(groupe.get_by_text(f['nom'],exact=True)).to_be_visible()
            expect(contre.get_by_text(fann['nom'],exact=True)).to_be_visible()
            expect(groupe.get_by_text('REF-DOC647',exact=False)).to_be_visible()
            expect(docs.get_by_role('button',name='Supprimer',exact=True)).to_have_count(0)
            with page.expect_download() as recu:contre.get_by_role('button',name='Télécharger',exact=True).click()
            with open(recu.value.path(),'rb') as h:assert h.read()==pdf_fictif()
            if role=='lecture':
                expect(docs.get_by_role('button',name='Joindre un fichier',exact=True)).to_have_count(0)
                expect(docs.locator('input[type=file]')).to_have_count(0)
                assert donnees_metier(application)==avant
            else:
                path=f'/api/attachments/ecriture/{eid}'
                with page.expect_response(lambda res:res.url.endswith(path) and res.request.method=='POST') as envoi:
                    groupe.locator('input[type=file]').set_input_files({'name':'ajout647.pdf','mimeType':'application/pdf','buffer':pdf_fictif()})
                assert envoi.value.status==200;nouveau=envoi.value.json()['nom']
                expect(groupe.get_by_text(nouveau,exact=True)).to_be_visible()
                # Le complément issu du registre et son empreinte sont relus sans F5.
                expect(groupe.locator('li').filter(has_text=nouveau)).to_be_visible()
                with page.expect_download() as fichier:region.get_by_role('button',name='Excel',exact=True).click()
                with open(fichier.value.path(),'rb') as h:w=load_workbook(BytesIO(h.read()))
                assert any(nouveau in row for row in w['Documents liés'].values)
                assert len(w['Logo société']._images)==1
                assert nouveau not in [x['nom'] for x in ok(api.get(f'/api/attachments/ecriture/{inverse}'))]
            assert [original(application,x) for x in (eid,inverse)]==photos
            docs.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'ras647_{role}_{mode}_{largeur}.png'))
            assert region.evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:browser.close()
