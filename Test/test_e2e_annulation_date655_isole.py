"""Annulation datée : vrai Edge, API et PostgreSQL102 nonce ; aucun compte réel."""
from contextlib import closing
from datetime import date, timedelta
import pytest
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import text
from test_ras_documents647_isole import (
    application, application101, application100, application099, application098,
    application097, application093, application092, application091, application090,
    application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_prorata_inventaire_isole import photo
from test_permissions_tva_runtime_isole import donnees_metier
from test_e2e_administration_isole import connexion, observer
from test_e2e_ras_capture_isole import ouvrir
from browser_support import chromium_executable
from generer_annexe_ras_documents649 import jeu


@pytest.mark.parametrize('largeur', [1440, 390])
def test_655_refus_futur_date_choisie_motif_et_originaux(application, largeur, tmp_path):
    d = jeu()
    source = (date.today() - timedelta(days=2)).isoformat()
    choisie = (date.today() - timedelta(days=1)).isoformat()
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        tiers = ok(api.post('/api/tiers', json={'nom': 'Fournisseur fictif655', 'type': 'fournisseur'}), 201)
        f = ok(api.post('/api/factures', json={**d['facture'], 'date': source,
            'tiers': tiers['nom'], 'tiers_id': tiers['id']}), 201)
        ok(api.post(f"/api/factures/{f['id']}/valider"))
        achat = ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))['ecriture_id']
        r = ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': tiers['nom'],
            'tiers_id': tiers['id'], 'date': source, 'montant': '5250.00', 'mode': 'virement',
            'reference': 'VIR-FICTIF655', 'comptabiliser': True}), 201)
        with application['engine'].connect() as db:
            cash = db.scalar(text('SELECT ecriture_id FROM reglements WHERE id=:r'), {'r': r['id']})
        corps = {'simulation': {**d['simulation'], 'date_paiement': source},
            'justification_quote_part': d['justification_quote_part']}
        apercu = ok(api.post(f"/api/reglements/{r['id']}/ras-tva/apercu", json=corps))
        capture = ok(api.post(f"/api/reglements/{r['id']}/ras-tva", json={**corps,
            'reference': 'RAS-FICTIVE655', 'compte_destination': '4457',
            'empreinte_apercu': apercu['empreinte_apercu'], 'pieces_verifiees': True}))
        ras = capture['capture']['ecriture_id']
        for eid in (achat, cash, ras):
            ok(api.post(f'/api/ecritures/{eid}/valider'))
        originaux = photo(application, [achat, cash, ras])
        avant = donnees_metier(application)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            erreurs, serveurs = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            ouvrir(page, application, 'achat')
            row = page.locator('tbody tr').filter(has_text='VIR-FICTIF655')
            row.get_by_title('Annuler par contrepassation', exact=True).click()
            modal = page.get_by_role('dialog', name='Annuler le règlement', exact=True)
            expect(modal.get_by_label('Date d’annulation *', exact=True)).to_have_value(date.today().isoformat())
            expect(modal.get_by_label('Motif (facultatif)', exact=True)).to_have_value('')
            modal.get_by_label('Date d’annulation *', exact=True).fill((date.today()+timedelta(days=1)).isoformat())
            motif = 'ANNULATION FICTIVE655 — date choisie pour recette'
            modal.get_by_label('Motif (facultatif)', exact=True).fill(motif)
            with page.expect_response(lambda rr: rr.url.endswith(f"/api/reglements/{r['id']}/annuler")) as refus:
                modal.get_by_role('button', name='Confirmer l’annulation', exact=True).click()
            assert refus.value.status == 422, refus.value.text()
            expect(modal.get_by_role('alert')).to_contain_text('future')
            expect(modal.get_by_label('Motif (facultatif)', exact=True)).to_have_value(motif)
            assert donnees_metier(application) == avant
            modal.get_by_label('Date d’annulation *', exact=True).fill(choisie)
            page.screenshot(path=str(tmp_path/f'annulation655_{largeur}.png'), full_page=True)
            with page.expect_response(lambda rr: rr.url.endswith(f"/api/reglements/{r['id']}/annuler")) as annulation:
                modal.get_by_role('button', name='Confirmer l’annulation', exact=True).click()
            assert annulation.value.status == 200, annulation.value.text()
            assert annulation.value.request.post_data_json == {'date_annulation': choisie, 'motif': motif}
            modal.wait_for(state='hidden')
            expect(row).to_contain_text('annule')
            assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant'] == 12000
            assert photo(application, [achat, cash, ras]) == originaux
            with application['engine'].connect() as db:
                inverse_cash = db.scalar(text('SELECT ecriture_annulation_id FROM reglements WHERE id=:r'), {'r': r['id']})
                inverse_ras = db.scalar(text('SELECT ecriture_id FROM ras_reglement_annulations WHERE capture_id=:c'), {'c': capture['capture']['id']})
                for eid, montant in ((inverse_cash, 5250), (inverse_ras, 750)):
                    e = db.execute(text('SELECT date,date_piece,motif_correction,est_validee FROM ecritures WHERE id=:e'), {'e': eid}).one()
                    assert e[0].isoformat() == e[1].isoformat() == choisie
                    assert e[2] == motif and e[3] is False
                    assert db.execute(text('SELECT sum(debit),sum(credit) FROM lignes_ecriture WHERE ecriture_id=:e'), {'e': eid}).one() == (montant, montant)
            assert not erreurs and not serveurs, (erreurs, serveurs)
        finally:
            browser.close()
