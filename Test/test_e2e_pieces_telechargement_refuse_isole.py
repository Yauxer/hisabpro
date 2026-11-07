"""Refus réels de téléchargement : aucune réponse API interceptée ou fabriquée."""
from contextlib import closing
from pathlib import Path
import pytest

from test_justificatifs_modeles_runtime_isole import (
    application, application090, application089, application087, migration,
    ecriture, pdf_fictif, original,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


@pytest.mark.parametrize('cas,largeur,statut', [('fichier_supprime',1440,404),('compte_desactive',390,401)])
def test_document_refuse_ne_devient_pas_un_faux_pdf(application,cas,largeur,statut,tmp_path):
    playwright=pytest.importorskip('playwright.sync_api')
    admin,email,password=client(application)
    with closing(admin),playwright.sync_playwright() as p:
        eid=ecriture(admin,validee=False,reference='FICTIF-DOWNLOAD453')
        contenu=pdf_fictif()
        fichier=ok(admin.post(f'/api/attachments/ecriture/{eid}',files={'file':('preuve453.pdf',contenu,'application/pdf')}))
        user=None
        if cas=='compte_desactive':
            email=email.replace('@','-comptable@')
            user=ok(admin.post('/api/utilisateurs',json={'nom':'Comptable fictif453','email':email,
                'mot_de_passe':password,'role':'comptable'}),201)
        avant=original(application,eid)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True)
            page.set_default_timeout(15000)
            errors,server_errors=observer(page,application['api_url'])
            downloads=[];page.on('download',lambda download:downloads.append(download))
            connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/journal',wait_until='domcontentloaded')
            page.locator('tbody tr').filter(has_text='FICTIF-DOWNLOAD453').first.locator('button[title^="Justificatifs"]').click()
            page.get_by_text(fichier['nom'],exact=True).wait_for()
            # Terminer les lectures initiales avant de révoquer le compte :
            # leur 401 redirigerait légitimement vers la connexion avant le clic.
            # Le refus à exercer ici doit provenir du téléchargement lui-même.
            page.wait_for_load_state('networkidle')
            # Mutation autorisée par un autre client, après affichage du document.
            if cas=='fichier_supprime':
                assert admin.delete(f"/api/attachments/ecriture/{eid}/{fichier['nom']}").status_code==204
            else:ok(admin.patch(f"/api/utilisateurs/{user['id']}",json={'actif':False}))
            with page.expect_response(lambda r:r.url.endswith('/download/'+fichier['nom'])) as refus:
                page.get_by_role('button',name='Télécharger',exact=True).click()
            assert refus.value.status==statut,refus.value.text()
            playwright.expect(page.get_by_text('Téléchargement impossible',exact=False)).to_be_visible()
            assert not downloads,'Une réponse de refus ne doit pas être enregistrée comme document.'
            assert original(application,eid)==avant
            assert not errors and not server_errors,(errors,server_errors)
        except BaseException:
            print('Refus réel :',cas,'; téléchargements déclenchés :',len(downloads))
            for d in downloads:
                print('Contenu reçu à tort :',Path(d.path()).read_text(encoding='utf-8',errors='replace')[:250])
            page.screenshot(path=str(tmp_path/f'refus453-{cas}.png'),full_page=True)
            raise
        finally:browser.close()
