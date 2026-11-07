"""Média impression et PDF réels Edge ; seules sociétés PostgreSQL jetables."""
from io import BytesIO
import pytest
from pypdf import PdfReader
from playwright.sync_api import sync_playwright,expect
from sqlalchemy import text
from test_e2e_runtime_session_isole import application,application090,application089,application087,migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_logo_societe import image_data
from test_justificatifs_modeles_runtime_isole import ecriture,original
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


@pytest.mark.parametrize('largeur,logo',[(1440,'PNG'),(390,'JPEG'),(1440,None),(390,'ancien')])
def test_journal_tva_imprimes_logo_et_source_intacte(application,largeur,logo):
    api,email,password=client(application)
    try:
        soc=ok(api.get('/api/societe/moi'))
        if logo in ('PNG','JPEG'):ok(api.patch('/api/societe/moi',json={'logo_url':image_data(logo)}))
        if logo=='ancien':
            with application['engine'].begin() as db:
                db.execute(text("UPDATE societes SET logo_url='https://example.com/logo-ancien.png' WHERE id=:id"),{'id':soc['id']})
        eid=ecriture(api);avant=original(application,eid)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
                errors,server_errors=observer(page,application['api_url']);reseau_logo=[]
                page.on('request',lambda r:reseau_logo.append(r.url) if 'logo-ancien.png' in r.url else None)
                connexion(page,application['web_url'],email,password)
                for route,titre in [('journal','Journal comptable'),('declaration-tva','Déclaration TVA')]:
                    page.goto(application['web_url']+'/'+route)
                    expect(page.get_by_role('button',name='Imprimer',exact=True)).to_be_enabled()
                    if route=='journal':
                        libelles=page.get_by_text('Pièce fictive justificatifs451',exact=True)
                        expect(libelles).to_have_count(2)  # Deux lignes de la même écriture.
                        expect(libelles.first).to_be_visible()
                    page.emulate_media(media='print')
                    img=page.get_by_role('img',name='Logo de '+soc['raison_sociale'],exact=True)
                    if logo in ('PNG','JPEG'):
                        expect(img).to_be_visible()
                        expect(img).to_have_js_property('complete',True)
                        assert img.evaluate('(e)=>e.naturalWidth')>0
                    else:expect(img).to_have_count(0)
                    pdf=PdfReader(BytesIO(page.pdf(prefer_css_page_size=True,print_background=True)))
                    texte=' '.join(p.extract_text() for p in pdf.pages)
                    assert titre in texte and soc['raison_sociale'] in texte
                    assert bool(any(p.images for p in pdf.pages))==(logo in ('PNG','JPEG'))
                    page.emulate_media(media='screen')
                    if logo in ('PNG','JPEG'):expect(img).to_be_hidden()
                assert original(application,eid)==avant
                assert not errors,errors
                assert not server_errors,server_errors
                assert not reseau_logo,reseau_logo
            finally:browser.close()
    finally:api.close()
