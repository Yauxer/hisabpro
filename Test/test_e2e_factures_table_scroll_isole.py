"""Le tableau des factures reste accessible quand KPI/filtres occupent la hauteur."""
from datetime import date
from decimal import Decimal
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


@pytest.mark.parametrize('largeur,hauteur', [(390, 1000), (1365, 600), (1365, 1000)])
def test_tableau_factures_hauteur_scroll_et_validation_native(application, largeur, hauteur):
    suffix = uuid.uuid4().hex[:8]
    email, password = 'facture-scroll-' + suffix + '@example.com', 'FactureScrollFictif!'
    nom = 'Client hauteur fictif ' + suffix
    reference = 'REF-SCROLL-FICTIVE-' + suffix
    ht = Decimal('100')
    tva = ht * Decimal('0.20')
    ttc = ht + tva
    with httpx.Client(base_url=application['api_url']) as api:
        reg = api.post('/api/auth/register', json={'nom': 'Admin scroll fictif', 'email': email,
             'password': password, 'raison_sociale': 'Recette hauteur factures ' + suffix})
        assert reg.status_code == 200, reg.text
        api.headers['Authorization'] = 'Bearer ' + reg.json()['access_token']
        sid = api.get('/api/societe/moi').json()['id']
        tiers = api.post('/api/tiers', json={'nom': nom, 'type': 'client'})
        assert tiers.status_code == 201, tiers.text
        facture = api.post('/api/factures', json={'type': 'vente', 'date': date.today().isoformat(),
            'tiers': nom, 'tiers_id': tiers.json()['id'], 'reference': reference,
            'lignes': [{'description': 'Prestation fictive contrôle tableau', 'quantite': 1,
                'prix_unitaire': float(ht), 'tva': 20}]})
        assert facture.status_code == 201, facture.text
        fid = facture.json()['id']
        assert facture.json()['total_ht'] == float(ht) and facture.json()['total_ttc'] == float(ttc)
        executable = chromium_executable()
        if not executable:
            pytest.skip('Microsoft Edge / Chromium requis')
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': hauteur})
                page.set_default_timeout(15000)
                errors, server_errors = observer(page, application['api_url'])
                page.on('dialog', lambda dialog: dialog.accept())
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/factures')
                row = page.locator('tbody tr').filter(has_text=nom)
                row.wait_for()
                for label in ['Facturation nette HT', 'Achats nets TTC', 'En attente', 'En retard']:
                    assert page.get_by_text(label, exact=True).first.is_visible()
                assert page.locator('input[type="date"]').count() == 2
                wrapper = page.locator('table').locator('..')
                geometrie = wrapper.evaluate('e => ({height:e.clientHeight,scrollHeight:e.scrollHeight,width:e.clientWidth,scrollWidth:e.scrollWidth})')
                print('Tableau réel', largeur, hauteur, geometrie)
                assert geometrie['height'] > 0, geometrie
                with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/valider') and r.request.method == 'POST') as validation:
                    row.get_by_title('Valider définitivement', exact=True).click()
                assert validation.value.status == 200, validation.value.text()
                row.get_by_title("Générer l'écriture comptable de cette facture", exact=True).wait_for()
                with Session(application['engine']) as db:
                    piece = db.get(models.Facture, fid)
                    assert piece.est_validee and piece.numero and piece.reference == reference
                    assert len(piece.lignes) == 1
                    assert Decimal(str(piece.lignes[0].quantite)) == 1
                    assert Decimal(str(piece.lignes[0].prix_unitaire)) == ht
                    assert Decimal(str(piece.lignes[0].tva)) == 20
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
                resultat = api.get(f'/api/factures?exercice={date.today().year}')
                assert resultat.status_code == 200, resultat.text
                finale = next(f for f in resultat.json() if f['id'] == fid)
                assert Decimal(str(finale['total_ht'])) == ht and Decimal(str(finale['total_tva'])) == tva
                assert Decimal(str(finale['total_ttc'])) == ttc
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                print('Écran facture fictive :', page.url, page.locator('body').inner_text()[:6500])
                raise
            finally:
                browser.close()
