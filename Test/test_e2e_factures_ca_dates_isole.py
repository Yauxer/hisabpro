"""Indicateurs et période : vraie API/UI, 100/101 factures, PG éphémère."""
from datetime import date
from decimal import Decimal
import re
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


@pytest.mark.parametrize('nombre', [100, 101])
def test_fenetre_facturation_complete_avoirs_date_propre_et_export(application, nombre, tmp_path):
    suffix = uuid.uuid4().hex[:8]
    email, password = f'ca-{suffix}@example.com', 'FacturationCA132!'
    year = date.today().year
    with httpx.Client(base_url=application['api_url'], timeout=30) as api:
        admin = ok(api.post('/api/auth/register', json={'nom': 'Admin CA fictif', 'email': email,
            'password': password, 'raison_sociale': 'Facturation fictive ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + admin['access_token']
        sid = ok(api.get('/api/societe/moi'))['id']
        tiers = ok(api.post('/api/tiers', json={'nom': 'Client CA fictif', 'type': 'client'}), 201)

        def facture(jour, pu, description, **options):
            ligne = {'description': description, 'quantite': 1, 'prix_unitaire': pu, 'tva': 20}
            ligne.update(options.pop('ligne', {}))
            data = ok(api.post('/api/factures', json={'type': 'vente', 'date': f'{year}-{jour}',
                'tiers': tiers['nom'], 'tiers_id': tiers['id'], 'lignes': [ligne], **options}), 201)
            ok(api.post(f"/api/factures/{data['id']}/valider"))
            return data

        ancien = facture('01-01', 100, 'Ancien service')
        borne_du = facture('02-01', 200, 'Service remisé', ligne={'remise': 10}, remise_globale=10, frais_transport_ht=20)
        facture('02-28', 300, 'Service borne fin')
        facture('03-01', 400, 'Service hors fenêtre')
        av = ok(api.post('/api/avoirs', json={'facture_id': ancien['id'], 'date': f'{year}-02-10',
            'lignes': [{'facture_ligne_id': ancien['lignes'][0]['id'], 'quantite': .25}]}), 201)
        av_hors = ok(api.post('/api/avoirs', json={'facture_id': borne_du['id'], 'date': f'{year}-03-01',
            'lignes': [{'facture_ligne_id': borne_du['lignes'][0]['id'], 'quantite': .1}]}), 201)
        av_annule = ok(api.post('/api/avoirs', json={'facture_id': ancien['id'], 'date': f'{year}-02-10',
            'lignes': [{'facture_ligne_id': ancien['lignes'][0]['id'], 'quantite': .1}]}), 201)
        ok(api.post(f"/api/avoirs/{av_annule['id']}/annuler"))
        assert Decimal(str(av['total_ht'])) == 25
        assert Decimal(str(av_hors['total_ht'])) == Decimal('16.20')
        with Session(application['engine']) as db:
            # Cas exclus et remplissage synthétiques : aucune écriture générée.
            for i in range(nombre - 4):
                negatifs = i < 3
                statut = 'annulee' if i == 2 else 'en_attente'
                db.add(models.Facture(societe_id=sid, numero=f'EXCLU-{suffix}-{i}', type='vente',
                    date=date(year, 2, 15) if negatifs else date(year, 4, 1), exercice=year,
                    tiers='Pièce exclue ou brouillon fictif', est_validee=False, est_proforma=i == 1,
                    statut=statut, lignes=[models.LigneFacture(description='Brouillon ou proforma ou annulée',
                        quantite=1, prix_unitaire=1000, tva=20)]))
            db.commit()
            assert db.query(models.Facture).filter_by(societe_id=sid, exercice=year).count() == nombre
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium/Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(accept_downloads=True); page.set_default_timeout(30000)
                errors, server_errors = observer(page, application['api_url'])
                lectures = []
                page.on('request', lambda request: lectures.append(request.url) if '/api/factures?' in request.url else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/factures')
                ht = page.get_by_test_id('facturation-nette-ht')
                playwright.expect(ht).to_contain_text('940,80')
                assert any('skip=100' in url for url in lectures), lectures
                table = page.locator('table').filter(has=page.get_by_role('columnheader', name='N° Facture', exact=True))
                playwright.expect(table.locator('tbody tr')).to_have_count(nombre)
                du = page.get_by_label('Date de début des factures et indicateurs', exact=True)
                au = page.get_by_label('Date de fin des factures et indicateurs', exact=True)
                du.fill(f'{year}-02-01'); au.fill(f'{year}-02-28')
                playwright.expect(ht).to_contain_text('457,00')
                playwright.expect(table.locator('tbody tr')).to_have_count(5)
                ventes = page.get_by_test_id('ventes-nettes-ttc')
                playwright.expect(ventes).to_contain_text('548,40')
                ventes.click()
                drill = page.locator('table').filter(has=page.get_by_role('columnheader', name='Net HT', exact=True))
                playwright.expect(drill.locator('tbody tr').filter(has_text='Ancien service')).to_contain_text('-25,00')
                playwright.expect(drill.locator('tbody tr').filter(has_text='Service remisé')).to_contain_text('162,00')
                with page.expect_download() as csv:
                    page.get_by_role('button', name='Exporter CSV', exact=True).click()
                csv_path = tmp_path / 'factures-periode.csv'; csv.value.save_as(csv_path)
                text = csv_path.read_text(encoding='utf-8-sig')
                assert f'{year}-01-01' not in text and f'{year}-03-01' not in text and f'{year}-04-01' not in text
                assert f'{year}-02-01' in text and f'{year}-02-28' in text
                au.fill(f'{year}-02-01'); playwright.expect(ht).to_contain_text('182,00')
                du.fill(f'{year}-02-28'); au.fill(f'{year}-02-28'); playwright.expect(ht).to_contain_text('300,00')
                du.fill(f'{year}-02-10'); au.fill(f'{year}-02-10'); playwright.expect(ht).to_contain_text('-25,00')
                playwright.expect(page.get_by_text('Aucune facture trouvée', exact=True)).to_be_visible()
                playwright.expect(table.locator('tbody tr').filter(has=page.locator('td').filter(has_text='EXCLU-'))).to_have_count(0)
                du.fill(f'{year}-02-28'); au.fill(f'{year}-02-01')
                page.get_by_role('alert').filter(has_text='supérieure ou égale').wait_for()
                playwright.expect(ht).to_contain_text('—')
                page.get_by_role('button', name='Effacer la période', exact=True).click()
                playwright.expect(ht).to_contain_text('940,80')
                assert not errors, errors
                assert not server_errors, server_errors
            finally:
                browser.close()
