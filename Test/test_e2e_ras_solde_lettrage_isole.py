"""Estimation RAS, deux règlements, validation et lettrage réels sans DB utilisateur."""
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from test_e2e_facturation_isole import application, champ
from test_e2e_administration_isole import connexion, observer
from test_e2e_ras_situation_isole import preparer, photo, ok
from test_e2e_avoir_fournisseur_isole import originaux


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('largeur', [1365, 390])
def test_solde_brut_reel_et_lettrage_sans_ras_operee(application, sens, largeur):
    api, email, password, tiers, facture, ids, sid = preparer(application, sens)
    try:
        original = photo(application, ids)
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(20000)
                # L'opérateur confirme la validation des brouillons fictifs.
                page.on('dialog', lambda dialog: dialog.accept())
                erreurs, serveur = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/factures')
                row = page.locator('tbody tr').filter(has_text=tiers['nom'])
                for montant, reste in [('1100', 100), ('100', 0)]:
                    row.get_by_title('Payer le fournisseur' if sens == 'achat' else 'Encaisser le client', exact=True).click()
                    modal = page.get_by_role('dialog')
                    pw.expect(champ(modal, 'Montant *')).to_have_value('1200.00' if montant == '1100' else '100.00')
                    pw.expect(modal.get_by_text('RAS estimée :', exact=False)).to_contain_text('100,00 MAD')
                    champ(modal, 'Montant *').fill(montant)
                    modal.get_by_placeholder('N° chèque, virement...').fill('RAS-SANS-RETENUE-' + montant)
                    with page.expect_response(lambda r: r.url.endswith('/api/reglements') and r.request.method == 'POST') as paid:
                        modal.get_by_role('button', name='Enregistrer', exact=True).click()
                    assert paid.value.status == 201, paid.value.text()
                    modal.wait_for(state='hidden')
                    pw.expect(row).to_contain_text('Part. payée' if reste else 'Payée')
                    situation = ok(api.get(f"/api/factures/{facture['id']}/reglements"))
                    assert situation['solde_restant'] == reste
                    assert situation['montant_ras_estime'] == 100
                    assert situation['montant_ras_impute'] == 0
                    assert photo(application, ids) == original
                page.goto(application['web_url'] + '/journal')
                pw.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(2)
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as validated:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert validated.value.status == 200, validated.value.text()
                assert validated.value.json()['nb_validees'] == 2
                avant = originaux(application, sid)
                page.goto(application['web_url'] + '/lettrage')
                compte = '3421' if sens == 'vente' else '4411'
                champ(page, 'Compte', 'select').select_option(compte)
                champ(page, 'Tiers', 'select').select_option(label=tiers['nom'])
                pw.expect(page.locator('tbody input[type="checkbox"]')).to_have_count(3)
                for box in page.locator('tbody input[type="checkbox"]').all():
                    box.check()
                with page.expect_response(lambda r: '/api/lettrage' in r.url and r.request.method == 'POST') as lettered:
                    page.get_by_role('button', name='Lettrer 3 lignes', exact=True).click()
                assert lettered.value.status == 200, lettered.value.text()
                assert lettered.value.json()['code'] == 'AAA'
                page.get_by_text('3 lettrée(s)', exact=True).wait_for()
                assert originaux(application, sid) == avant
                page.reload()
                champ(page, 'Compte', 'select').select_option(compte)
                champ(page, 'Tiers', 'select').select_option(label=tiers['nom'])
                page.get_by_text('3 lettrée(s)', exact=True).wait_for()
                assert not erreurs and not serveur, (erreurs, serveur)
            finally:
                browser.close()
        with Session(application['engine']) as db:
            entries = db.query(models.Ecriture).filter_by(societe_id=sid).all()
            lignes = [l for e in entries for l in e.lignes]
            assert len(entries) == 3 and len(lignes) == 7 and all(e.est_validee for e in entries)
            assert sum(Decimal(str(l.debit)) for l in lignes) == Decimal('2400')
            assert sum(Decimal(str(l.credit)) for l in lignes) == Decimal('2400')
            assert sum(Decimal(str(l.debit)) - Decimal(str(l.credit)) for l in lignes if l.compte == compte) == 0
            assert sum(Decimal(str(l.debit)) - Decimal(str(l.credit)) for l in lignes if l.compte == '5141') == (1200 if sens == 'vente' else -1200)
            assert all(l.code_lettrage == 'AAA' and l.tiers_id == tiers['id'] for l in lignes if l.compte == compte)
            assert all(l.compte not in ('3453', '4457') for l in lignes)
            assert not db.get(models.Facture, facture['id']).ras_comptabilisee
    finally:
        api.close()
