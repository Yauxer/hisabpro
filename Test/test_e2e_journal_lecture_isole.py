"""Journal : consultation seule réelle, documents accessibles et mutations403."""
from contextlib import closing
from pathlib import Path
import pytest
import httpx
from test_justificatifs_modeles_runtime_isole import (
    application, application090, application089, application087, migration,
    ecriture, original, pdf_fictif,
)
from test_multi_societes_runtime_isole import ok
from test_ras_lecture_conservation import client
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


@pytest.mark.parametrize('role,largeur',[('lecture',390),('comptable',1440)])
def test_commandes_journal_documents_et_controles_selon_role(application,role,largeur,tmp_path):
    playwright=pytest.importorskip('playwright.sync_api')
    admin,email,password=client(application)
    with closing(admin),playwright.sync_playwright() as p:
        ids=[ecriture(admin,reference='DEFINITIF-ROLE457'),
             ecriture(admin,validee=False,reference='BROUILLON-ROLE457'),
             ecriture(admin,reference=None)]
        f=ok(admin.post(f'/api/attachments/ecriture/{ids[0]}',files={'file':('role457.pdf',pdf_fictif(),'application/pdf')}))
        original_avant={eid:original(application,eid) for eid in ids}
        email=email.replace('@','-'+role+'@')
        ok(admin.post('/api/utilisateurs',json={'nom':'Utilisateur fictif rôle457','email':email,
            'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True)
            page.set_default_timeout(15000)
            errors,server_errors=observer(page,application['api_url'])
            requetes=[]
            page.on('request',lambda r:requetes.append((r.method,r.url)) if r.url.startswith(application['api_url']) else None)
            connexion(page,application['web_url'],email,password);requetes.clear()
            page.goto(application['web_url']+'/journal',wait_until='domcontentloaded')
            cree=page.get_by_role('button',name='Nouvelle écriture',exact=True)
            lot=page.get_by_role('button',name='Valider les brouillons',exact=True)
            ecrire=role=='comptable'
            if ecrire:
                playwright.expect(cree).to_be_enabled();playwright.expect(lot).to_be_enabled()
            else:
                playwright.expect(cree).to_be_disabled();playwright.expect(lot).to_be_disabled()
            for label,compte in [('Valider',1),('Modifier',1),('Supprimer',1),('Contrepasser',2)]:
                playwright.expect(page.locator(f'tbody button[aria-label="{label}"]')).to_have_count(compte if ecrire else 0)
            page.get_by_role('button',name='Export FEC',exact=True).click()
            page.get_by_text('REFERENCE_PIECE_MANQUANTE',exact=True).wait_for()
            assert page.get_by_placeholder('Référence du justificatif existant').count()==(1 if ecrire else 0)
            page.get_by_role('button',name='Fermer',exact=True).click()
            page.locator('tbody tr').filter(has_text='DEFINITIF-ROLE457').first.locator('button[title^="Justificatifs"]').click()
            page.get_by_text(f['nom'],exact=True).wait_for()
            assert page.get_by_role('button',name='Ajouter la référence',exact=True).count()==(1 if ecrire else 0)
            assert page.get_by_role('button',name='Joindre un fichier',exact=True).count()==(1 if ecrire else 0)
            with page.expect_download() as dl:page.get_by_role('button',name='Télécharger',exact=True).click()
            assert Path(dl.value.path()).read_bytes()==pdf_fictif()
            if ecrire:
                page.get_by_label('Référence du justificatif',exact=True).fill('REFERENCE-FICTIVE-COMPTABLE457')
                with page.expect_response(lambda r:r.url.endswith(f'/api/ecritures/{ids[0]}/justificatifs') and r.request.method=='POST') as ajout:
                    page.get_by_role('button',name='Ajouter la référence',exact=True).click()
                assert ajout.value.status==201,ajout.value.text()
            else:
                assert not [(m,u) for m,u in requetes if m not in ('GET','OPTIONS')],requetes
                with httpx.Client(base_url=application['api_url']) as lecteur:
                    token=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
                    lecteur.headers['Authorization']='Bearer '+token
                    assert lecteur.post(f'/api/ecritures/{ids[1]}/valider').status_code==403
                    assert lecteur.post(f'/api/ecritures/{ids[0]}/justificatifs',json={'reference':'INTERDIT'}).status_code==403
            assert {eid:original(application,eid) for eid in ids}==original_avant
            assert not errors and not server_errors,(errors,server_errors)
        except BaseException:
            print(role,page.locator('body').inner_text()[-6500:])
            page.screenshot(path=str(tmp_path/f'journal457-{role}.png'),full_page=True)
            raise
        finally:browser.close()
