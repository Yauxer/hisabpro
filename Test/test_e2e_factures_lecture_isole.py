"""Factures en consultation seule, vrais comptes/HTTP/Edge sur PostgreSQL nonce."""
from contextlib import closing
from datetime import date
from pathlib import Path
import uuid
import httpx
import pytest
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from test_justificatifs_modeles_runtime_isole import pdf_fictif
from test_reglement_comptabilisation_concurrente_isole import metier
from browser_support import chromium_executable


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('role,largeur', [('lecture',390), ('lecture',1440), ('comptable',1440)])
def test_factures_commandes_documents_selon_role(application, sens, role, largeur, tmp_path):
    playwright=pytest.importorskip('playwright.sync_api')
    admin,email,password=client(application)
    with closing(admin),playwright.sync_playwright() as p:
        suffix=uuid.uuid4().hex[:8]
        tid=ok(admin.post('/api/tiers',json={'nom':'Tiers fictif540 '+suffix,
            'type':'client' if sens=='vente' else 'fournisseur'}),201)['id']
        fs=[]
        for etat in ('brouillon','validee','proforma'):
            f=ok(admin.post('/api/factures',json={'type':sens,'date':date.today().isoformat(),
                'tiers_id':tid,'tiers':'Tiers fictif540 '+suffix,
                'reference':etat+'-'+suffix,'est_proforma':etat=='proforma',
                'lignes':[{'description':'Service fictif540','quantite':1,'prix_unitaire':100,'tva':20}]}),201)
            if etat=='validee':f.update(ok(admin.post(f"/api/factures/{f['id']}/valider",json={})))
            fs.append(f)
        fid=fs[1]['id']
        if sens=='achat':
            piece=ok(admin.post(f'/api/attachments/facture/{fid}',files={
                'file':('preuve540.pdf',pdf_fictif(),'application/pdf')}))
        email=email.replace('@','-'+role+'@')
        ok(admin.post('/api/utilisateurs',json={'nom':'Utilisateur fictif540','email':email,
            'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True)
            page.set_default_timeout(15000)
            errors,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            requetes=[]
            page.on('request',lambda r:requetes.append((r.method,r.url)) if r.url.startswith(application['api_url']) else None)
            avant=metier(application)
            page.goto(application['web_url']+'/factures',wait_until='domcontentloaded')
            playwright.expect(page.locator('tbody tr').filter(has_text='Tiers fictif540 '+suffix)).to_have_count(3)
            with page.expect_download() as dl:
                page.get_by_role('button',name='Exporter CSV',exact=True).click()
            csv=Path(dl.value.path()).read_text(encoding='utf-8-sig')
            assert 'Proforma' in csv and fs[2]['numero'] in csv
            ecrire=role=='comptable'
            nouveau=page.get_by_role('button',name='Nouvelle facture',exact=True)
            if ecrire:playwright.expect(nouveau).to_be_enabled()
            else:playwright.expect(nouveau).to_be_disabled()
            for titre,nb in [('Modifier le brouillon',1),('Modifier la proforma',1),
                ('Valider définitivement',1),('Dupliquer la facture',3),
                ('Convertir en facture définitive',1),
                ("Générer l'écriture comptable de cette facture",1),
                ('Encaisser le client' if sens=='vente' else 'Payer le fournisseur',1),
                ('Créer bon de livraison',1 if sens=='vente' else 0)]:
                playwright.expect(page.get_by_title(titre,exact=True)).to_have_count(nb if ecrire else 0)
            playwright.expect(page.get_by_role('button',name='Supprimer',exact=True)).to_have_count(2 if ecrire else 0)
            row=page.locator('tbody tr').filter(has_text='Tiers fictif540 '+suffix).filter(has_text='Validée')
            if sens=='achat':
                row.get_by_title('Pièces jointes',exact=True).click()
                page.get_by_text(piece['nom'],exact=True).wait_for()
                playwright.expect(page.get_by_role('button',name='Joindre un fichier',exact=True)).to_have_count(1 if ecrire else 0)
                playwright.expect(page.get_by_title('Supprimer',exact=True)).to_have_count(1 if ecrire else 0)
                with page.expect_download() as dl:page.get_by_title('Télécharger',exact=True).click()
                assert Path(dl.value.path()).read_bytes()==pdf_fictif()
            row.click()
            playwright.expect(page.get_by_role('button',name='Créer un avoir',exact=True)).to_have_count(1 if ecrire else 0)
            with page.expect_download() as dl:
                page.get_by_role('button',name='Télécharger PDF',exact=True).click()
            assert Path(dl.value.path()).read_bytes().startswith(b'%PDF')
            if ecrire:
                page.get_by_role('button',name='Créer un avoir',exact=True).click()
                page.get_by_role('dialog',name='Créer un avoir',exact=False).wait_for()
            else:
                assert not [(m,u) for m,u in requetes if m not in ('GET','OPTIONS')],requetes
            assert metier(application)==avant
            assert not errors and not serveur,(errors,serveur)
            if not ecrire:
                with httpx.Client(base_url=application['api_url']) as lecteur:
                    lecteur.headers['Authorization']='Bearer '+ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
                    avant=metier(application)
                    assert lecteur.post(f"/api/factures/{fs[0]['id']}/valider",json={}).status_code==403
                    assert lecteur.post(f'/api/factures/{fid}/comptabiliser',json={}).status_code==403
                    assert lecteur.delete(f"/api/factures/{fs[0]['id']}").status_code==403
                    assert lecteur.post('/api/reglements',json={'facture_id':fid,'tiers':'Tiers fictif540',
                        'date':date.today().isoformat(),'montant':120,'mode':'virement'}).status_code==403
                    assert lecteur.post('/api/avoirs',json={'facture_id':fid,'date':date.today().isoformat(),
                        'lignes':[{'facture_ligne_id':fs[0]['lignes'][0]['id'],'quantite':1}]}).status_code==403
                    assert lecteur.post(f'/api/attachments/facture/{fid}',files={'file':('interdit.pdf',pdf_fictif(),'application/pdf')}).status_code==403
                    assert metier(application)==avant
        except BaseException:
            print(role,sens,page.locator('body').inner_text()[-6000:])
            page.screenshot(path=str(tmp_path/f'factures540-{role}-{sens}-{largeur}.png'),full_page=True)
            raise
        finally:browser.close()
