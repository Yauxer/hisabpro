"""IS : Edge reel/API/PG ephemere, hypothese chiffree non normative."""
from decimal import Decimal
from pathlib import Path
import re
import uuid

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def ecriture(api, reference, lignes):
    data = ok(api.post('/api/ecritures', json={'date': '2025-12-01', 'journal': 'OD',
        'reference': reference, 'libelle': reference + ' fictif', 'lignes': lignes}), 201)
    ok(api.post(f"/api/ecritures/{data['id']}/valider"))
    return data


def test_is_retraitements_credits_acompte_cloture_et_snapshot_ui(application):
    cible = application['cluster']
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    raw = application['engine'].raw_connection()
    try:
        raw.autocommit = True
        with raw.cursor() as cursor:
            for nom in ('021_fiscalite_is.sql', '021b_fiscalite_permissions.sql',
                        '022_deficits_fiscaux_millesimes.sql', '023_cotisation_minimale.sql',
                        '024_acomptes_liquidation_is.sql', '025_css_credits_is.sql',
                        '066_liquidation_is_snapshot_detail.sql'):
                verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
                cursor.execute((Path(__file__).resolve().parents[1] / 'hisabpro-backend' / nom).read_text(encoding='utf-8'))
    finally:
        raw.close()
    suffix = uuid.uuid4().hex[:8]
    email, password = 'is-' + suffix + '@example.com', 'ISE2E132!Sure'
    resultat = Decimal('20000.00')
    reintegration, deduction = Decimal('1000.00'), Decimal('500.00')
    base = resultat + reintegration - deduction
    impot = (base * Decimal('0.20')).quantize(Decimal('0.01'))
    credit, deja_impute, verse = Decimal('300.00'), Decimal('100.00'), Decimal('1000.00')
    solde = impot - (credit - deja_impute) - (verse + deja_impute)
    assert (base, impot, solde) == (Decimal('20500.00'), Decimal('4100.00'), Decimal('2800.00'))
    with httpx.Client(base_url=application['api_url'], timeout=30) as api:
        inscription = ok(api.post('/api/auth/register', json={'nom': 'Admin IS fictif', 'email': email,
            'password': password, 'raison_sociale': 'IS fictive ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + inscription['access_token']
        sid = ok(api.patch('/api/societe/moi', json={'exercice_debut': 2025}))['id']
        ecriture(api, 'PRODUIT-IS-FICTIF', [{'compte': '5141', 'debit': 19700},
            {'compte': '3453', 'debit': 300}, {'compte': '7111', 'credit': 20000}])
        ecriture(api, 'ACOMPTE-IS-FICTIF', [{'compte': '3453', 'debit': 1000},
            {'compte': '5141', 'credit': 1000}])
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Edge/Chromium requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': 1400, 'height': 1100})
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                page.on('dialog', lambda dialog: dialog.accept())
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/cloture')
                page.get_by_label('Exercice actif', exact=True).select_option('2025')
                page.goto(application['web_url'] + '/fiscalite-is')
                page.get_by_label('Taux dérogatoire (optionnel)', exact=True).fill('20')
                page.get_by_label('Justification du taux dérogatoire', exact=True).fill('Hypothese synthetique du laboratoire, sans portee reglementaire')
                page.get_by_label('Référence annuelle forcée (optionnel)', exact=True).fill('4000')
                page.get_by_label('Justification de la référence forcée', exact=True).fill('Base annuelle fictive explicite de recette')
                parametres = page.locator('section').filter(has=page.get_by_label('Taux dérogatoire (optionnel)', exact=True))
                with page.expect_response(lambda r: r.request.method == 'PUT' and r.url.endswith('/api/fiscalite/is/2025/parametres')) as sauvegarde:
                    parametres.get_by_role('button', name='Enregistrer', exact=True).click()
                assert sauvegarde.value.status == 200, sauvegarde.value.text()
                retraitements = page.locator('form').filter(has=page.get_by_placeholder('Libellé du retraitement', exact=True))
                for nature, libelle, montant in [('reintegration', 'Reintegration fictive explicite', '1000'),
                                                  ('deduction', 'Deduction fictive explicite', '500')]:
                    retraitements.locator('select').first.select_option(nature)
                    retraitements.get_by_placeholder('Libellé du retraitement', exact=True).fill(libelle)
                    retraitements.get_by_placeholder('Montant MAD', exact=True).fill(montant)
                    with page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/api/fiscalite/is/2025/retraitements')) as ajout:
                        retraitements.get_by_role('button', name='Ajouter', exact=True).click()
                    assert ajout.value.status == 200, ajout.value.text()
                    page.get_by_text(libelle, exact=True).wait_for()
                formulaire_credit = page.locator('form').filter(has=page.get_by_placeholder('Montant retenu', exact=True))
                formulaire_credit.locator('select').select_option('pprf')
                formulaire_credit.get_by_placeholder('Montant retenu', exact=True).fill('300')
                formulaire_credit.get_by_placeholder('Déjà imputé acomptes', exact=True).fill('100')
                formulaire_credit.locator('input[type=date]').fill('2025-12-01')
                formulaire_credit.get_by_placeholder('Référence justificative', exact=True).fill('PPRF-FICTIF-300')
                with page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/api/fiscalite/is/2025/credits')) as ajout_credit:
                    formulaire_credit.get_by_role('button', name='Ajouter', exact=True).click()
                assert ajout_credit.value.status == 200, ajout_credit.value.text()
                page.get_by_text('PPRF-FICTIF-300', exact=True).wait_for()
                ligne_acompte = page.locator('tr').filter(has=page.get_by_placeholder('Réf. paiement', exact=True)).first
                ligne_acompte.get_by_placeholder('Montant', exact=True).fill('1000')
                ligne_acompte.locator('input[type=date]').fill('2025-12-01')
                ligne_acompte.get_by_placeholder('Réf. paiement', exact=True).fill('ACOMPTE-FICTIF-1000')
                with page.expect_response(lambda r: r.request.method == 'PUT' and r.url.endswith('/api/fiscalite/is/2025/acomptes/1')) as acompte:
                    ligne_acompte.get_by_role('button', name='Enregistrer', exact=True).click()
                assert acompte.value.status == 200, acompte.value.text()
                situation = ok(api.get('/api/fiscalite/is/2025'))
                assert Decimal(str(situation['calcul']['resultat_comptable_avant_is'])) == resultat
                assert Decimal(str(situation['calcul']['benefice_fiscal_imposable'])) == base
                assert Decimal(str(situation['liquidation']['is_theorique'])) == impot
                assert Decimal(str(situation['liquidation']['solde_a_payer'])) == solde
                # Incoherence atteinte par operations normales, jamais en modifiant une definitive.
                mauvaise = ecriture(api, 'IS-INCORRECT-FICTIF', [{'compte': '6701', 'debit': 2000},
                    {'compte': '4453', 'credit': 2000}])
                incoherente = ok(api.get('/api/fiscalite/is/2025'))
                assert not incoherente['comptabilisation_is']['coherente']
                refus = api.post('/api/cloture/cloturer?exercice=2025')
                assert refus.status_code == 409 and 'comptabilisation' in refus.text, refus.text
                confirmation_precoce = api.post('/api/fiscalite/is/2025/liquidation/confirmer')
                assert confirmation_precoce.status_code == 409 and 'exercice comptable' in confirmation_precoce.text
                correction = ok(api.post(f"/api/ecritures/{mauvaise['id']}/contrepasser", json={
                    'date_correction': '2025-12-02', 'motif': 'Contrepassation explicite de la charge fictive erronee'}))
                assert correction['id'] != mauvaise['id']
                ok(api.post('/api/cloture/cloturer?exercice=2025'))
                coherente = ok(api.get('/api/fiscalite/is/2025'))
                assert coherente['comptabilisation_is']['coherente']
                assert Decimal(str(coherente['comptabilisation_is']['comptabilise'])) == impot
                page.reload()
                with page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/api/fiscalite/is/2025/liquidation/confirmer')) as confirmation:
                    page.get_by_role('button', name='Confirmer la liquidation', exact=True).click()
                assert confirmation.value.status == 200, confirmation.value.text()
                snapshot = confirmation.value.json()
                assert Decimal(str(snapshot['solde_a_payer'])) == solde
                page.get_by_text('Photographie confirmée le', exact=False).wait_for()
                texte_snapshot = re.sub(r'\s+', '', page.get_by_text('Photographie confirmée le', exact=False).inner_text())
                assert 'solde2800,00' in texte_snapshot.replace('.', ''), texte_snapshot
                page.reload()
                page.get_by_text('Photographie confirmée le', exact=False).wait_for()
                assert page.get_by_role('button', name='Confirmer la liquidation', exact=True).count() == 0
                apres = ok(api.get('/api/fiscalite/is/2025'))
                assert apres['liquidation']['confirmee']
                detail = apres['liquidation']['snapshot']['detail']
                assert Decimal(detail['liquidation']['solde_a_payer']) == solde
                assert detail['acomptes'][0]['reference_paiement'] == 'ACOMPTE-FICTIF-1000'
                assert api.post('/api/fiscalite/is/2025/liquidation/confirmer').status_code == 409
                assert api.post('/api/fiscalite/is/2025/credits', json={'type': 'pprf', 'montant': 1,
                    'reference': 'Interdit apres confirmation'}).status_code == 409
                verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
                with Session(application['engine']) as db:
                    archive = db.query(models.FiscalLiquidationIS).filter_by(societe_id=sid, exercice=2025).one()
                    assert archive.solde_a_payer == solde and archive.impot_du == impot
                    assert archive.snapshot_detail == detail
                    original = db.get(models.Ecriture, mauvaise['id'])
                    assert original.est_validee
                    assert original.lignes[0].debit == Decimal('2000')
                with application['engine'].connect() as db:
                    with pytest.raises(DBAPIError):
                        db.execute(text('UPDATE fiscal_liquidations_is SET solde_a_payer=0 WHERE societe_id=:sid'), {'sid': sid})
                    db.rollback()
                assert not errors and not server_errors, (errors, server_errors)
            finally:
                browser.close()
