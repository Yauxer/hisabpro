"""Vrais uploads/téléchargements Edge et isolation des versions de balances."""
from contextlib import closing
from io import BytesIO
from zipfile import ZipFile
import hashlib,json
import pytest
from playwright.sync_api import sync_playwright,expect
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from test_balance_documents691_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,demande,chemin,BASE,donnees_metier,path,joindre,pdf_fictif)
from test_e2e_balance_echeances687_isole import ouvrir
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


def ouvrir_docs(panel):
    panel.get_by_text('Justificatifs complémentaires de cette version',exact=True).click()
    docs=panel.get_by_role('region',name='Justificatifs de la préparation',exact=True)
    expect(docs.get_by_text('Les tailles et empreintes affichées',exact=False)).to_be_visible()
    return docs


@pytest.mark.parametrize('role,largeur',[('admin',1440),('comptable',390),('lecture',390)])
def test_691_upload_document_zip_roles_et_relecture_edge(application,role,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);raw=pdf_fictif();nom='ETAT_FICTIF691_'+'x'*110+'.pdf'
        if role=='lecture':ok(joindre(api,v,raw=raw,nom=nom),201)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Pièces fictives691','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True);page.set_default_timeout(10000)
            errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            panel,_=ouvrir(page,application,v,role=='lecture');docs=ouvrir_docs(panel);avant=donnees_metier(application)
            if role=='lecture':
                assert docs.get_by_label('Fichier justificatif',exact=True).count()==0
                assert docs.get_by_role('button',name='Joindre et conserver le justificatif',exact=True).count()==0
            else:
                docs.get_by_label('Fichier justificatif',exact=True).set_input_files({'name':nom,'mimeType':'application/pdf','buffer':raw})
                docs.get_by_label('Référence documentaire facultative',exact=True).fill('État créances fictif691')
                with page.expect_response(lambda r:r.url.endswith(path(v)) and r.request.method=='POST') as rep:
                    docs.get_by_role('button',name='Joindre et conserver le justificatif',exact=True).click()
                assert rep.value.status==201,rep.value.text()
                expect(docs.get_by_text('Justificatif conservé avec sa trace et son empreinte.',exact=True)).to_be_visible()
            expect(docs.get_by_role('article')).to_have_count(1)
            r=ok(api.get(path(v)))['documents'][0]
            expect(docs.get_by_role('article')).to_contain_text(r['sha256'])
            expect(docs.get_by_role('article')).to_contain_text('Ko')
            with page.expect_download() as export:
                docs.get_by_role('button',name=f'Télécharger le justificatif #{r["id"]}',exact=True).click()
            assert export.value.path().read_bytes()==raw
            with page.expect_download() as paquet:
                panel.get_by_role('button',name='Télécharger le dossier de préparation ZIP',exact=True).click()
            with ZipFile(paquet.value.path()) as z:
                assert z.testzip() is None and z.read('justificatifs/'+r['nom_stockage'])==raw
                assert json.loads(z.read('justificatifs.json'))['documents']==[r]
            apres=donnees_metier(application)
            assert all(apres[k]==value for k,value in avant.items() if k!='liasse_balance_documents')
            assert ok(api.get(BASE+f'/{v["id"]}'))==v
            docs.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'pieces691-{role}-{largeur}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors and not serveur,(errors,serveur)
            page.reload();panel,_=ouvrir(page,application,v,role=='lecture');docs=ouvrir_docs(panel)
            expect(docs.get_by_role('article')).to_contain_text(r['sha256'])
        finally:browser.close()


def test_691_refus_fichier_puis_correction_et_erreur_lecture_reessayable(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        owner=create_engine(make_url(application['cluster']['url']))
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(10000)
            connexion(page,application['web_url'],email,password);panel,_=ouvrir(page,application,v);docs=ouvrir_docs(panel)
            docs.get_by_label('Fichier justificatif',exact=True).set_input_files({'name':'faux691.exe','mimeType':'application/octet-stream','buffer':b'fictif'})
            with page.expect_response(lambda r:r.url.endswith(path(v)) and r.request.method=='POST') as rep:
                docs.get_by_role('button',name='Joindre et conserver le justificatif',exact=True).click()
            assert rep.value.status==422;expect(docs.get_by_role('alert')).to_contain_text('Nom de justificatif valide requis')
            docs.get_by_label('Fichier justificatif',exact=True).set_input_files({'name':'preuve691.pdf','mimeType':'application/pdf','buffer':pdf_fictif()})
            docs.get_by_role('button',name='Joindre et conserver le justificatif',exact=True).click()
            expect(docs.get_by_role('article')).to_have_count(1)
            with owner.begin() as db:db.execute(text('REVOKE SELECT ON liasse_balance_documents FROM hisabpro'))
            docs.get_by_role('button',name='Actualiser les justificatifs de préparation',exact=True).click()
            expect(docs.get_by_role('alert')).to_contain_text('Accès aux justificatifs indisponible')
            with owner.begin() as db:db.execute(text('GRANT SELECT ON liasse_balance_documents TO hisabpro'))
            docs.get_by_role('button',name='Actualiser les justificatifs de préparation',exact=True).click()
            expect(docs.get_by_role('article')).to_have_count(1)
        finally:
            with owner.begin() as db:db.execute(text('GRANT SELECT ON liasse_balance_documents TO hisabpro'))
            owner.dispose();browser.close()


@pytest.mark.parametrize('methode',['GET','POST'])
def test_691_reponse_reelle_tardive_ne_melange_pas_les_versions(application,methode):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        v=creer(api);v2=ok(api.post(chemin(v),json=demande(v)),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(10000)
            connexion(page,application['web_url'],email,password);panel,_=ouvrir(page,application,v)
            pending=[]
            def retenir(route):
                if route.request.method!=methode:route.continue_();return
                rep=route.fetch();assert rep.status==(200 if methode=='GET' else 201)
                pending.append((route,rep));page.evaluate('window.__pieces691Retenues = true')
            if methode=='POST':
                docs=ouvrir_docs(panel)
                docs.get_by_label('Fichier justificatif',exact=True).set_input_files({'name':'preuve691.pdf','mimeType':'application/pdf','buffer':pdf_fictif()})
            page.route('**'+path(v),retenir)
            if methode=='GET':panel.get_by_text('Justificatifs complémentaires de cette version',exact=True).click()
            else:docs.get_by_role('button',name='Joindre et conserver le justificatif',exact=True).click()
            page.wait_for_function('window.__pieces691Retenues === true')
            # Le select global est libre pendant l'upload local, comme dans l'interface.
            panel.get_by_label('Préparations conservées',exact=True).select_option(str(v2['id']))
            expect(panel.get_by_text('Version 2 conservée',exact=False)).to_be_visible()
            docs=ouvrir_docs(panel)
            expect(docs.get_by_text('Aucun justificatif complémentaire sur cette version.',exact=True)).to_be_visible()
            route,rep=pending.pop()
            with page.expect_response(lambda r:r.url.endswith(path(v))):route.fulfill(response=rep)
            page.wait_for_load_state('networkidle')
            expect(docs.get_by_role('article')).to_have_count(0)
            assert ok(api.get(path(v2)))['documents']==[]
            if methode=='POST':assert len(ok(api.get(path(v)))['documents'])==1
        finally:browser.close()
