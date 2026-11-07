"""Chèque encaissé puis impayé depuis l'écran Effets : vraie UI/API/PG nonce, données fictives."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ  # noqa: F401
from test_ras_lecture_conservation import client
from test_e2e_ras_capture_isole import ok


@pytest.mark.parametrize('largeur', [1365, 390])
def test_957_impaye_apres_encaissement_depuis_effets(application, largeur):
    api, email, password = client(application)
    jour = date.today().isoformat()
    nom = 'Client impayé encaissé fictif'
    try:
        tiers = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'client'}), 201)
        f = ok(api.post('/api/factures', json={'type': 'vente', 'tiers': nom, 'tiers_id': tiers['id'], 'date': jour,
            'ras_taux': 0, 'lignes': [{'description': 'Service fictif', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
        ok(api.post(f"/api/factures/{f['id']}/valider"))
        e = ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
        ok(api.post(f"/api/ecritures/{e['ecriture_id']}/valider"))
        r = ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': nom, 'date': jour, 'montant': 1200,
            'mode': 'cheque', 'reference': 'CHQ-ENC-957', 'comptabiliser': True}), 201)
        rid = r['id']
        ok(api.post(f'/api/reglements/{rid}/transition', json={'action': 'encaisser', 'date_effective': jour}))
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant'] == 0
        with Session(application['engine']) as db:
            sid = db.get(models.Facture, f['id']).societe_id
            avant = {x.id for x in db.query(models.Ecriture).filter_by(societe_id=sid)}
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000}); page.set_default_timeout(20000)
                erreurs, serveur = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/effets')
                champ(page, 'Statut', 'select').select_option('tous')
                effet = page.locator('tbody tr').filter(has_text='CHQ-ENC-957')
                effet.get_by_title('Déclarer impayé après encaissement', exact=True).click()
                modal = page.get_by_role('dialog')
                pw.expect(modal).to_contain_text('déjà crédité revient impayé')
                modal.locator('input[type="date"]').fill(jour)
                modal.get_by_placeholder('0.00', exact=True).fill('25')
                with page.expect_response(lambda rr: rr.url.endswith(f'/api/reglements/{rid}/transition')) as t:
                    modal.get_by_role('button', name="Déclarer l'impayé", exact=True).click()
                assert t.value.status == 200, t.value.text()
                assert t.value.json()['statut'] == 'rejete'
                modal.wait_for(state='hidden')
                pw.expect(effet).to_contain_text('Rejeté / Impayé')
                assert not erreurs and not serveur, (erreurs, serveur)
            finally:
                browser.close()
        s = ok(api.get(f"/api/factures/{f['id']}/reglements"))
        assert s['solde_restant'] == 1200 and s['total_regle'] == 0
        with Session(application['engine']) as db:
            nouvelles = [x for x in db.query(models.Ecriture).filter_by(societe_id=sid) if x.id not in avant]
            assert len(nouvelles) == 1 and nouvelles[0].journal == 'BQ'
            lignes = {(l.compte, Decimal(str(l.debit)), Decimal(str(l.credit))) for l in nouvelles[0].lignes}
            assert ('3421', Decimal('1225'), Decimal('0')) in lignes
            assert ('6147', Decimal('25'), Decimal('0')) in lignes and ('7127', Decimal('0'), Decimal('25')) in lignes
            assert sum(d for _, d, _ in lignes) == sum(c for _, _, c in lignes) == Decimal('1250')
            reg = db.get(models.Reglement, rid)
            assert reg.date_encaissement == date.today() and reg.date_rejet_effective == date.today()
        ok(api.post(f"/api/ecritures/{nouvelles[0].id}/valider"))
    finally:
        api.close()
