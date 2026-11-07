"""Éditeur réel : diagnostic historique et choix explicite, jamais zéro implicite."""
from contextlib import closing
import math

import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import connexion
from test_ras_lecture_conservation import client, lire
from test_ras_taux_finis import facture


@pytest.mark.parametrize('valide', [False, True])
def test_ras_historique_invalide_visible_sans_patch_implicite(application, valide):
    playwright = pytest.importorskip('playwright.sync_api')
    api, email, password = client(application)
    with closing(api):
        tiers = api.post('/api/tiers', json={'nom': 'Client RAS historique fictif', 'type': 'client'})
        assert tiers.status_code == 201, tiers.text
        r = api.post('/api/factures', json=facture(tiers=tiers.json()['nom'], tiers_id=tiers.json()['id']))
        assert r.status_code == 201, r.text
        fid = r.json()['id']
        with Session(application['engine']) as db:
            f = db.get(models.Facture, fid)
            sid = f.societe_id
            if valide:
                # Pièce historique synthétique préparée avant de figer son état :
                # aucune modification d'une facture déjà validée ni trigger désactivé.
                colonnes = {c.name: getattr(f, c.name) for c in f.__table__.columns if c.name != 'id'}
                colonnes.update(numero='HIST-RAS-FICTIF', est_validee=False, ras_taux=float('nan'))
                historique = models.Facture(**colonnes)
                historique.lignes = [models.LigneFacture(**{c.name: getattr(l, c.name) for c in l.__table__.columns if c.name not in ('id', 'facture_id')}) for l in f.lignes]
                db.add(historique)
                db.flush()
                historique.est_validee = True
                db.flush()
                fid = historique.id
                f.tiers = 'Brouillon source distinct fictif'
            else:
                f.ras_taux = float('nan')
            db.commit()
            compte_ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).count()
        assert lire(api, fid)['ras_taux'] is None
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': 1440, 'height': 1000})
                patches = []
                page.on('request', lambda request: patches.append(request.post_data) if request.method == 'PATCH' and request.url.endswith(f'/api/factures/{fid}') else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/factures')
                row = page.locator('tbody tr').filter(has_text='Client RAS historique fictif')
                playwright.expect(row.get_by_text('RAS à vérifier', exact=True)).to_be_visible()
                playwright.expect(row.locator('button[title="RAS historique invalide : vérifier avant duplication"]')).to_be_disabled()
                if valide:
                    assert row.locator('button[title="Modifier le brouillon"]').count() == 0
                    playwright.expect(row.locator('button[title="Facture validée : correction uniquement par avoir/document correctif"]')).to_be_disabled()
                    r = api.get(f'/api/factures/{fid}/pdf')
                    assert r.status_code == 409, r.text
                else:
                    row.locator('button[title="Modifier le brouillon"]').click()
                    modal = page.get_by_role('dialog')
                    choix = modal.get_by_label('Retenue à la source de la facture', exact=True)
                    playwright.expect(choix).to_have_value('')
                    playwright.expect(modal.get_by_role('alert')).to_contain_text('historique invalide')
                    modal.get_by_role('button', name='Enregistrer les modifications', exact=False).click()
                    playwright.expect(modal.get_by_text('Choisissez explicitement une retenue à la source valide avant de sauvegarder ce brouillon.', exact=True)).to_be_visible()
                    assert not patches
                    with Session(application['engine']) as db:
                        assert math.isnan(db.get(models.Facture, fid).ras_taux)
                    choix.select_option('0')  # Zéro est un choix explicite, pas un défaut.
                    with page.expect_response(lambda response: response.request.method == 'PATCH' and response.url.endswith(f'/api/factures/{fid}')) as reponse:
                        modal.get_by_role('button', name='Enregistrer les modifications', exact=False).click()
                    assert reponse.value.status == 200, reponse.value.text()
                    modal.wait_for(state='hidden')
                    sortie = lire(api, fid)
                    assert sortie['ras_taux'] == 0 and sortie['ras_anomalie'] is None
                    assert len(patches) == 1
                with Session(application['engine']) as db:
                    f = db.get(models.Facture, fid)
                    assert math.isnan(f.ras_taux) if valide else f.ras_taux == 0
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == compte_ecritures
                if valide:
                    assert not patches
            finally:
                browser.close()


def test_ras_existante_hors_presets_conservee_editeur(application):
    playwright = pytest.importorskip('playwright.sync_api')
    api, email, password = client(application)
    with closing(api):
        r = api.post('/api/factures', json=facture(tiers='Client RAS existante sept', ras_taux=7))
        assert r.status_code == 201, r.text
        fid = r.json()['id']
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page()
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/factures')
                page.locator('tbody tr').filter(has_text='Client RAS existante sept').locator('button[title="Modifier le brouillon"]').click()
                modal = page.get_by_role('dialog')
                playwright.expect(modal.get_by_label('Retenue à la source de la facture', exact=True)).to_have_value('7')
                with page.expect_response(lambda response: response.request.method == 'PATCH' and response.url.endswith(f'/api/factures/{fid}')) as reponse:
                    modal.get_by_role('button', name='Enregistrer les modifications', exact=False).click()
                assert reponse.value.status == 200, reponse.value.text()
                modal.wait_for(state='hidden')
                assert lire(api, fid)['ras_taux'] == 7
            finally:
                browser.close()
