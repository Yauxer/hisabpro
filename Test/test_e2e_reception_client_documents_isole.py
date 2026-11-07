"""Pièces externes du client liées au BL : Edge / API / PG et fichiers isolés."""
from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import uuid

import httpx
import pytest
from pypdf import PdfReader
from PIL import Image
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer, deconnexion
from test_e2e_facturation_isole import application


def ok(reponse, code=200):
    assert reponse.status_code == code, reponse.text
    return reponse.json()


def snapshot(app, sid, article_id, bl_id):
    with Session(app['engine']) as db:
        article = db.get(models.Article, article_id)
        bl = db.get(models.BonLivraison, bl_id)
        return (article.stock_actuel, article.cmup, bl.statut, bl.date, bl.facture_id,
                tuple((l.id, l.quantite_prevue, l.quantite_livree) for l in bl.lignes),
                db.query(models.MouvementStock).filter_by(societe_id=sid).count(),
                db.query(models.Ecriture).filter_by(societe_id=sid).count())


def ouvrir_documents(page, app, numero):
    page.goto(app['web_url'] + '/commercial')
    page.get_by_role('button', name='Réception client', exact=True).click()
    ligne = page.locator('tbody tr').filter(has_text=numero)
    ligne.locator('button[title="Documents reçus du client"]').click()
    return page.get_by_role('dialog').filter(has_text=numero)


@pytest.mark.parametrize('largeur', [1365, 390])
def test_br_client_externe_pdf_image_stock_inchange_et_permissions(application, tmp_path, largeur):
    suffix = uuid.uuid4().hex[:8]
    email, password = f'br-client-{suffix}@example.com', 'BRClientRecette2026!'
    with httpx.Client(base_url=application['api_url']) as api:
        registre = ok(api.post('/api/auth/register', json={'nom': 'Admin réception fictive', 'email': email,
                     'password': password, 'raison_sociale': 'BR client fictif ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + registre['access_token']
        sid = ok(api.get('/api/societe/moi'))['id']
        ok(api.patch('/api/societe/moi', json={'stock_declencheur_vente': 'bl'}))
        nom = 'Client BR fictif ' + suffix
        tiers = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'client'}), 201)
        article = ok(api.post('/api/articles', json={'code': 'BR-' + suffix, 'designation': 'Article réception fictif',
                     'is_stockable': True, 'stock_actuel': 5, 'prix_achat_ht': 40, 'prix_vente_ht': 100, 'tva': 20}), 201)
        bl = ok(api.post('/api/bons-livraison', json={'date': date.today().isoformat(), 'type': 'vente',
                'tiers': nom, 'tiers_id': tiers['id'], 'lignes': [{'description': article['designation'],
                'article_id': article['id'], 'quantite_prevue': 2, 'quantite_livree': 2, 'prix_unitaire': 100, 'tva': 20}]}), 201)
        assert bl['statut'] == 'en_preparation'
        avant = snapshot(application, sid, article['id'], bl['id'])
        # Interdire tout upload si le serveur n'a pas un stockage distinct de
        # hisabpro-backend/uploads. La fixture fournit sa racine privée nonce.
        racine = Path(application['uploads_dir']).resolve()
        assert racine.is_relative_to(application['directory'].resolve())
        assert not racine.is_relative_to((Path(__file__).resolve().parents[1] / 'hisabpro-backend' / 'uploads').resolve())
        preuve = tmp_path / 'BR client fictif.pdf'
        c = canvas.Canvas(str(preuve))
        c.drawString(40, 800, 'DOCUMENT FICTIF DE RECETTE — AUCUNE RECEPTION REELLE')
        c.drawString(40, 770, 'Bon de reception client rattache au BL ' + bl['numero'])
        c.drawString(40, 740, 'Marque de recette fictive, sans signature authentifiee')
        c.save()
        original = preuve.read_bytes()
        assert bl['numero'] in ''.join(p.extract_text() for p in PdfReader(BytesIO(original)).pages)
        image = tmp_path / 'BR client fictif.png'
        Image.new('RGB', (80, 40), color='white').save(image)
        with Image.open(image) as document_image:
            assert document_image.format == 'PNG'
            document_image.verify()
        lecteur_email = 'br-lecture-' + suffix + '@example.com'
        ok(api.post('/api/utilisateurs', json={'nom': 'Lecteur BR', 'email': lecteur_email, 'mot_de_passe': password, 'role': 'lecture'}), 201)
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Microsoft Edge / Chromium requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000}, accept_downloads=True)
                page.set_default_timeout(15000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                modal = ouvrir_documents(page, application, bl['numero'])
                modal.get_by_text('Aucune pièce jointe', exact=True).wait_for()
                cadre = modal.bounding_box()
                assert cadre['x'] >= 0 and cadre['x'] + cadre['width'] <= largeur + 1
                noms_uploads = []
                for fichier in [preuve, preuve, image]:
                    with page.expect_response(lambda r: r.url.endswith(f'/api/attachments/bl/{bl["id"]}') and r.request.method == 'POST') as upload:
                        modal.locator('input[type="file"]').set_input_files(str(fichier))
                    assert upload.value.status == 200, upload.value.text()
                    nom_stocke = upload.value.json()['nom']
                    noms_uploads.append(nom_stocke)
                    modal.get_by_text(nom_stocke, exact=True).wait_for()
                    assert snapshot(application, sid, article['id'], bl['id']) == avant
                assert len(set(noms_uploads)) == 3
                assert modal.get_by_role('button', name='Supprimer', exact=True).count() == 0
                fichiers = ok(api.get(f'/api/attachments/bl/{bl["id"]}'))
                assert {f['nom'] for f in fichiers} == set(noms_uploads)
                for nom_stocke, contenu in zip(noms_uploads, [original, original, image.read_bytes()]):
                    path = racine / str(sid) / 'bl' / str(bl['id']) / nom_stocke
                    assert path.is_file() and sha256(path.read_bytes()).digest() == sha256(contenu).digest()
                    row = modal.get_by_text(nom_stocke, exact=True).locator('..')
                    with page.expect_download() as download:
                        row.get_by_role('button', name='Télécharger', exact=True).click()
                    cible = tmp_path / ('telecharge-' + nom_stocke)
                    download.value.save_as(str(cible))
                    assert download.value.failure() is None
                    assert sha256(cible.read_bytes()).digest() == sha256(contenu).digest()
                page.reload()
                modal = ouvrir_documents(page, application, bl['numero'])
                for nom_stocke in noms_uploads:
                    modal.get_by_text(nom_stocke, exact=True).wait_for()
                # Le lecteur consulte/télécharge mais ne peut déposer par API.
                page.get_by_role('dialog').get_by_role('button', name='Fermer', exact=True).click()
                deconnexion(page)
                connexion(page, application['web_url'], lecteur_email, password)
                modal = ouvrir_documents(page, application, bl['numero'])
                modal.get_by_text(noms_uploads[0], exact=True).wait_for()
                assert modal.get_by_role('button', name='Joindre un fichier', exact=True).count() == 0
                with page.expect_download() as lecture_download:
                    modal.get_by_text(noms_uploads[0], exact=True).locator('..').get_by_role('button', name='Télécharger', exact=True).click()
                preuve_lecture = tmp_path / 'lecture-client.pdf'
                lecture_download.value.save_as(str(preuve_lecture))
                assert sha256(preuve_lecture.read_bytes()).digest() == sha256(original).digest()
                refuse = page.evaluate("async ({url,id}) => {const f=new FormData();f.append('file',new File(['fictif'],'refus.pdf',{type:'application/pdf'}));return (await fetch(url+'/api/attachments/bl/'+id,{method:'POST',headers:{Authorization:'Bearer '+localStorage.getItem('hisabpro_token')},body:f})).status}", {'url': application['api_url'], 'id': bl['id']})
                assert refuse == 403
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print('Écran BR fictif :', page.url, page.locator('body').inner_text()[:7500])
                print('Erreurs :', errors, server_errors)
                raise
            finally:
                browser.close()
        # Une autre société ne voit aucun fichier ni document de ce BL.
        with httpx.Client(base_url=application['api_url']) as autre:
            token_b = ok(autre.post('/api/auth/register', json={'nom': 'Autre admin BR', 'email': 'autre-br-' + suffix + '@example.com', 'password': password, 'raison_sociale': 'Autre BR ' + suffix}))
            autre.headers['Authorization'] = 'Bearer ' + token_b['access_token']
            assert autre.get(f'/api/attachments/bl/{bl["id"]}').status_code == 404
            assert autre.get(f'/api/attachments/bl/{bl["id"]}/download/{noms_uploads[0]}').status_code == 404
            assert autre.post(f'/api/attachments/bl/{bl["id"]}', files={'file': ('autre.pdf', original, 'application/pdf')}).status_code == 404
        assert snapshot(application, sid, article['id'], bl['id']) == avant
