from pathlib import Path
from contextlib import closing
from io import BytesIO
import pytest
from playwright.sync_api import sync_playwright,expect
from pypdf import PdfReader
from openpyxl import load_workbook
from browser_support import chromium_executable
from test_paie917_documents_isole import (
    application,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,source_annuelle,demande,S,I,image_data)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('largeur',[1440,390])
def test_917_telechargements_pdf_excel_logo_et_revocation_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,_,_=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            droit=None
            for uid in [u['id'],v['id']]:
                for cap in CAPS:
                    g=grant(admin,uid,cap)
                    if uid==u['id'] and cap=='personnel.lire_remuneration':droit=g['id']
            activer(admin);sid=ok(admin.get('/api/auth/me'))['societe_id'];eq={'a':prep,'b':valid,'admin':admin,'uid':u['id'],'bid':v['id'],'sid':sid}
            ok(admin.patch('/api/societe/moi',json={'logo_url':image_data()}));_,_,source=source_annuelle(eq)
            r=ok(prep.post(S,json=demande(source['id'])),201);avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    ctx=browser.new_context(viewport={'width':largeur,'height':1000},accept_downloads=True);page=ctx.new_page();erreurs,serveur=observer(page,app['api_url'])
                    connexion_personnel(page,app,mail,secret);page.goto(app['web_url']+'/personnel-paie/fiscalite')
                    page.get_by_role('button',name=f'Consulter le contrôle {r["id"]}',exact=True).click()
                    expect(page.get_by_test_id('ir-annuel-arithmetique')).to_have_text('5.967,00 MAD')
                    for fmt,titre in [('pdf','PDF'),('xlsx','Excel')]:
                        with page.expect_download() as action:page.get_by_role('button',name='Télécharger le contrôle IR en '+titre,exact=True).click()
                        fichier=action.value;assert fichier.suggested_filename==f'controle_ir_annuel_{r["id"]}.{fmt}'
                        contenu=Path(fichier.path()).read_bytes()
                        if fmt=='pdf':
                            d=PdfReader(BytesIO(contenu));t='\n'.join(x.extract_text() or '' for x in d.pages)
                            assert '83881.0200' in t and '5967.0000' in t and sum(len(x.images) for x in d.pages)==1
                        else:
                            w=load_workbook(BytesIO(contenu));assert len(w['Logo société']._images)==1 and w['Sources mensuelles'].max_row==13
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    page.screenshot(path=str(R/f'docs/personnel-paie/preuves/917_{largeur}_documents.png'))
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès export FICTIF917'}));page.get_by_role('button',name='Actualiser',exact=True).click()
                    expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération')
                    expect(page.get_by_role('button',name='Télécharger le contrôle IR en PDF',exact=True)).to_have_count(0)
                    assert prep.get(f'{I}/{r["id"]}/export/pdf').status_code==403
                    assert '83881.0200' not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)') and comptabilite(app,sid)==avant
                    assert not erreurs and not serveur,(erreurs,serveur)
                finally:browser.close()
