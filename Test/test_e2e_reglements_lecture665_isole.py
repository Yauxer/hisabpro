"""Commandes selon le rôle : vrai Edge/API et PostgreSQL102 nonce, données conservées."""
from contextlib import closing
from datetime import date
from uuid import uuid4
import httpx
import pytest
from sqlalchemy import text
from playwright.sync_api import sync_playwright, expect
from test_ras_documents647_isole import (
    application, application101, application100, application099, application098,
    application097, application093, application092, application091, application090,
    application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_lecture_reglements_historiques import photo
from test_e2e_administration_isole import connexion, observer
from test_e2e_ras_capture_isole import ouvrir
from browser_support import chromium_executable


@pytest.mark.parametrize('role,sens,largeur', [
    ('lecture', 'vente', 1440), ('lecture', 'achat', 390),
    ('comptable', 'achat', 1440), ('comptable', 'vente', 390),
])
def test_665_commandes_selon_role_ras_lisible_et403(application, role, sens, largeur, tmp_path):
    api, _, _ = client(application)
    with closing(api), sync_playwright() as p:
        nom = 'TIERS FICTIF665 '+uuid4().hex[:8]
        tiers = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'client' if sens == 'vente' else 'fournisseur'}), 201)
        f = ok(api.post('/api/factures', json={'type': sens, 'date': date.today().isoformat(),
            'tiers': nom, 'tiers_id': tiers['id'], 'reference': 'FACTURE-FICTIVE665',
            'lignes': [{'description': 'Service fictif665', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
        ok(api.post(f"/api/factures/{f['id']}/valider"))
        achat = ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))['ecriture_id']
        ok(api.post(f'/api/ecritures/{achat}/valider'))
        rows = []
        for comptabiliser, montant in ((False, 100), (True, 200)):
            rows.append(ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': nom,
                'tiers_id': tiers['id'], 'date': date.today().isoformat(), 'montant': montant,
                'mode': 'virement', 'reference': 'REGLEMENT-FICTIF665-'+str(montant),
                'comptabiliser': comptabiliser}), 201))
        with application['engine'].connect() as db:
            eid = db.scalar(text('SELECT ecriture_id FROM reglements WHERE id=:r'), {'r': rows[1]['id']})
        ok(api.post(f'/api/ecritures/{eid}/valider'))
        email, password = f'{role}665-{uuid4().hex[:8]}@example.com', 'ReglementsLecture665!'
        ok(api.post('/api/utilisateurs', json={'nom': role+' fictif665', 'email': email,
            'mot_de_passe': password, 'role': role}), 201)
        avant = photo(application)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(15000)
            erreurs, serveurs = observer(page, application['api_url'])
            mutations = []
            page.on('request', lambda r: mutations.append(r.url) if '/api/reglements' in r.url and r.method in ('POST','PATCH','DELETE') else None)
            connexion(page, application['web_url'], email, password)
            ouvrir(page, application, sens)
            expect(page.locator('tbody tr')).to_have_count(2)
            lecture = role == 'lecture'
            for titre in ('Modifier', 'Supprimer', 'Annuler par contrepassation'):
                expect(page.get_by_title(titre, exact=True)).to_have_count(0 if lecture else 1)
            expect(page.get_by_role('button', name='Ventiler par tiers', exact=True)).to_have_count(0 if lecture else 1)
            expect(page.get_by_title('Consulter ou déclarer la RAS', exact=True)).to_have_count(2)
            with page.expect_response(lambda r: '/api/reglements?' in r.url) as actualisation:
                page.get_by_role('button', name='Actualiser les règlements', exact=True).click()
            assert actualisation.value.status == 200
            expect(page.locator('tbody tr')).to_have_count(2)
            page.screenshot(path=str(tmp_path/f'reglements665_{role}_{largeur}.png'), full_page=True)
            book = page.locator('tbody tr').filter(has_text='REGLEMENT-FICTIF665-200')
            with page.expect_response(lambda r: r.url.endswith(f"/api/reglements/{rows[1]['id']}/ras")) as consultation:
                book.get_by_title('Consulter ou déclarer la RAS', exact=True).click()
            assert consultation.value.status == 200
            modal = page.get_by_role('dialog', name='RAS déclarée sur règlement', exact=True)
            expect(modal.get_by_text('Fermer', exact=True)).to_be_visible()
            if lecture:
                expect(modal.get_by_text('La saisie exige un règlement immédiat comptabilisé et complet', exact=False)).to_be_visible()
                expect(modal.get_by_role('button', name='Préparer la RAS déclarée', exact=True)).to_have_count(0)
                expect(modal.get_by_role('button', name='RAS TVA guidée', exact=True)).to_have_count(0)
            else:
                expect(modal.get_by_role('button', name='Préparer la RAS déclarée', exact=True)).to_be_visible()
            page.screenshot(path=str(tmp_path/f'lecture665_{role}_{largeur}.png'), full_page=True)
            modal.get_by_text('Fermer', exact=True).click()
            if lecture:
                with httpx.Client(base_url=application['api_url']) as lecteur:
                    auth = ok(lecteur.post('/api/auth/login', json={'email': email, 'password': password}))
                    lecteur.headers['Authorization'] = 'Bearer '+auth['access_token']
                    assert lecteur.patch(f"/api/reglements/{rows[0]['id']}", json={'montant': 50}).status_code == 403
                    assert lecteur.delete(f"/api/reglements/{rows[0]['id']}").status_code == 403
                    assert lecteur.post(f"/api/reglements/{rows[1]['id']}/annuler", json={'motif': 'INTERDIT FICTIF665'}).status_code == 403
            assert photo(application) == avant
            assert not mutations and not erreurs and not serveurs, (mutations, erreurs, serveurs)
        finally:
            browser.close()
