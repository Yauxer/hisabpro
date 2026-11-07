"""Parcours annuel réduit : même société, API/Edge/PG réellement connectés.

Oracle figé avant le premier run, indépendant des calculs de l'application.
Toutes les mutations passent par les routes normales, sur PG éphémère nonce.
"""
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import hashlib
import json
import uuid

import httpx
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_balances_exports_isole import telecharger, pdf_texte
from test_e2e_facturation_isole import application, champ
from test_e2e_tva_isole import choisir_mois

ORACLE_PATH = Path(__file__).resolve().parents[1] / 'docs/recette/oracle_annee_connectee_2025.json'
ORACLE = json.loads(ORACLE_PATH.read_text(encoding='utf-8'))
D = Decimal


def ok(r, statut=200):
    assert r.status_code == statut, r.text
    return r.json()


def oracle_soldes():
    soldes, debit, credit = defaultdict(lambda: D(0)), D(0), D(0)
    for ecriture in ORACLE['ecritures_avant_impot']:
        total_d = sum(D(l[1]) for l in ecriture['lignes'])
        total_c = sum(D(l[2]) for l in ecriture['lignes'])
        assert total_d == total_c
        debit += total_d; credit += total_c
        for compte, montant_d, montant_c in ecriture['lignes']:
            soldes[compte] += D(montant_d) - D(montant_c)
    return dict(soldes), debit, credit


def test_oracle_annuel_independant_equilibre_et_resultats():
    soldes, debit, credit = oracle_soldes()
    assert soldes == {c: D(s) for c, s in ORACLE['soldes_avant_impot'].items()}
    assert debit == credit == D(ORACLE['totaux_journal_avant_impot']['debit'])
    assert len(ORACLE['ecritures_avant_impot']) == 10
    assert sum(len(e['lignes']) for e in ORACLE['ecritures_avant_impot']) == 23
    resultat = -sum(s for c, s in soldes.items() if c.startswith(('6', '7')))
    assert resultat == D(ORACLE['resultat_avant_impot']) == 0
    base = -sum(s for c, s in soldes.items() if c.startswith('711'))
    proportionnelle = (base * D('0.25') / 100).quantize(D('.01'))
    assert base == 800 and proportionnelle == 2
    impot = max(proportionnelle, D('3000'))
    assert impot == D(ORACLE['impot_laboratoire']['impot_attendu'])
    assert resultat - impot == D(ORACLE['impot_laboratoire']['resultat_net'])
    an = {c: D(s) for c, s in ORACLE['soldes_a_nouveaux_2026'].items()}
    assert sum(an.values()) == 0
    assert sum(s for s in an.values() if s > 0) == D('25000')
    assert -sum(s for s in an.values() if s < 0) == D('25000')


def lignes_comptables(application, sid):
    with Session(application['engine']) as db:
        return {(l.id, l.ecriture_id, l.compte, l.debit, l.credit, l.tiers_id,
                 l.compte_auxiliaire_snapshot, l.libelle_auxiliaire_snapshot)
                for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid)}


def valider_brouillons_ui(page, application, nb):
    page.goto(application['web_url'] + '/journal')
    expect = pytest.importorskip('playwright.sync_api').expect
    expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(nb)
    with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as sortie:
        page.get_by_role('button', name='Valider les brouillons', exact=True).click()
    assert sortie.value.status == 200, sortie.value.text()
    assert sortie.value.json()['nb_validees'] == nb


def verifier_tva(data, periode):
    attendu = ORACLE['tva'][periode]
    assert D(str(data['collectee']['total'])) == D(attendu['collectee'])
    assert D(str(data['recuperable']['total'])) == D(attendu['recuperable'])
    assert D(str(data['tva_due'])) == D(attendu['due'])
    assert D(str(data['credit_tva'])) == D(attendu['credit'])
    if 'credit_anterieur' in attendu:
        assert D(str(data['credit_tva_anterieur'])) == D(attendu['credit_anterieur'])
    assert D(str(data['recuperable_immobilisations']['total'])) == 0
    assert any('acquisition non payée' in a and 'non déduite' in a for a in data['alertes'])


def test_annee_connectee_stock_paiements_lettrage_tva_immo_cloture_an(application, tmp_path):
    suffix = uuid.uuid4().hex[:8]
    email, password = f'annee-connectee-{suffix}@example.com', 'AnneeConnectee2025!'
    noms = {'achat': 'Fournisseur annuel fictif ' + suffix, 'vente': 'Client annuel fictif ' + suffix}
    with httpx.Client(base_url=application['api_url'], timeout=40) as api:
        inscription = ok(api.post('/api/auth/register', json={'nom': 'Administrateur annuel fictif', 'email': email, 'password': password, 'raison_sociale': 'Année connectée fictive ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + inscription['access_token']
        societe = ok(api.patch('/api/societe/moi', json={'forme_juridique': 'SARL', 'regime_fiscal': 'is', 'regime_tva': 'encaissement', 'periodicite_tva': 'mensuelle', 'devise': 'MAD', 'capital_social': 20000, 'exercice_debut': 2020, 'stock_declencheur_vente': 'facture', 'stock_declencheur_achat': 'facture'}))
        sid = societe['id']
        exercices = ok(api.get('/api/exercices'))
        if not any(e['annee'] == 2025 for e in exercices):
            ok(api.post('/api/exercices', json={'annee': 2025, 'date_debut': '2025-01-01', 'date_fin': '2025-12-31'}), 201)
        ok(api.put('/api/fiscalite/is/2025/parametres', json=ORACLE['profil']['parametres_is']))
        capital = ORACLE['ecritures_avant_impot'][0]
        ok(api.post('/api/ecritures', json={'date': capital['date'], 'journal': 'BQ', 'reference': capital['reference'], 'libelle': 'Apport bancaire fictif annuel', 'lignes': [{'compte': c, 'debit': d, 'credit': cr} for c, d, cr in capital['lignes']]}), 201)
        article = ok(api.post('/api/articles', json={'code': 'ANNUEL-' + suffix, 'designation': 'Marchandise annuelle fictive', 'prix_achat_ht': 100, 'prix_vente_ht': 200, 'stock_actuel': 0, 'is_stockable': True, 'compte_achat': '6111', 'compte_vente': '7111'}), 201)
        tiers = {}
        factures = {}
        for nature, quantite, prix, date_facture in [('achat', 10, 100, '2025-03-01'), ('vente', 4, 200, '2025-03-02')]:
            tiers[nature] = ok(api.post('/api/tiers', json={'nom': noms[nature], 'type': 'client' if nature == 'vente' else 'fournisseur', 'categorie_fiscale': 'particulier' if nature == 'vente' else 'professionnel'}), 201)
            factures[nature] = ok(api.post('/api/factures', json={'type': nature, 'date': date_facture, 'tiers': noms[nature], 'tiers_id': tiers[nature]['id'], 'reference': 'ANNUEL-' + nature, 'date_echeance': '2025-06-15', 'lignes': [{'article_id': article['id'], 'description': article['designation'], 'quantite': quantite, 'prix_unitaire': prix, 'tva': 20}]}), 201)
        immo_nom = 'Serveur annuel fictif ' + suffix
        immo = ok(api.post('/api/immobilisations', json={'designation': immo_nom, 'reference': 'IMMO-ANNUEL', 'categorie': 'Matériel informatique', 'date_acquisition': '2025-01-01', 'date_mise_en_service': '2025-01-01', 'prix_acquisition_ht': '1200', 'taux_tva': '20', 'duree_amort': 3, 'methode': 'lineaire', 'date_paiement': None, 'fournisseur': noms['achat'], 'fournisseur_tiers_id': tiers['achat']['id'], 'compte_immo': '2355', 'compte_amort': '28355', 'compte_dotation': '61935'}), 201)
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(accept_downloads=True)
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                responses_lettrage = []
                page.on('response', lambda r: responses_lettrage.append((r.url, r.status)) if '/api/lettrage/' in r.url else None)
                page.on('dialog', lambda dialog: dialog.accept())
                connexion(page, application['web_url'], email, password)
                page.locator('select').filter(has=page.locator('option[value="2025"]')).first.select_option('2025')
                page.goto(application['web_url'] + '/factures')
                for nature in ('achat', 'vente'):
                    row = page.locator('tbody tr').filter(has_text=noms[nature])
                    row.locator('button[title="Valider définitivement"]').wait_for()
                    fid = factures[nature]['id']
                    with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/valider')) as sortie:
                        row.locator('button[title="Valider définitivement"]').click()
                    assert sortie.value.status == 200, sortie.value.text()
                    with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/comptabiliser')) as sortie:
                        row.locator('button[title="Générer l\'écriture comptable de cette facture"]').click()
                    assert sortie.value.status == 200, sortie.value.text()
                for nature, montant, date_reglement, reference in [
                    ('vente', 360, '2025-03-03', 'CLI-PARTIEL'), ('achat', 600, '2025-03-04', 'FOU-PARTIEL'),
                    ('vente', 600, '2025-06-03', 'CLI-SOLDE'), ('achat', 600, '2025-06-04', 'FOU-SOLDE'),
                ]:
                    row = page.locator('tbody tr').filter(has_text=noms[nature])
                    titre = 'Encaisser le client' if nature == 'vente' else 'Payer le fournisseur'
                    row.locator('button[title="' + titre + '"]').click()
                    modal = page.get_by_role('dialog')
                    champ(modal, 'Montant *').fill(str(montant))
                    champ(modal, 'Date *').fill(date_reglement)
                    champ(modal, 'Mode', 'select').select_option('virement')
                    modal.get_by_placeholder('N° chèque, virement...').fill(reference)
                    with page.expect_response(lambda r: r.url.endswith('/api/reglements') and r.request.method == 'POST') as sortie:
                        modal.get_by_role('button', name='Enregistrer', exact=True).click()
                    assert sortie.value.status == 201, sortie.value.text()
                    modal.wait_for(state='hidden')
                    facture_db = next(f for f in ok(api.get('/api/factures?exercice=2025')) if f['id'] == factures[nature]['id'])
                    assert facture_db['statut'] == ('partiellement_payee' if reference.endswith('PARTIEL') else 'payee')
                    assert sortie.value.json()['ecriture_id']
                assert api.post('/api/cloture/cloturer?exercice=2025').status_code == 400
                valider_brouillons_ui(page, application, 8)
                avant_lettrage = lignes_comptables(application, sid)
                for nature, compte in [('vente', '3421'), ('achat', '4411')]:
                    page.goto(application['web_url'] + '/lettrage')
                    champ(page, 'Compte', 'select').select_option(compte)
                    champ(page, 'Tiers', 'select').select_option(label=noms[nature])
                    boxes = page.locator('tbody input[type="checkbox"]')
                    playwright.expect(boxes).to_have_count(3)
                    for box in boxes.all():
                        box.check()
                    with page.expect_response(lambda r: '/api/lettrage' in r.url and r.request.method == 'POST') as sortie:
                        page.get_by_role('button', name='Lettrer 3 lignes', exact=True).click()
                    assert sortie.value.status == 200, sortie.value.text()
                    page.get_by_text('3 lettrée(s)', exact=True).wait_for()
                assert lignes_comptables(application, sid) == avant_lettrage
                with Session(application['engine']) as db:
                    for compte in ('3421', '4411'):
                        lignes = db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid, models.LigneEcriture.compte == compte).all()
                        assert len(lignes) == 3 and sum(l.debit - l.credit for l in lignes) == 0
                        codes = {l.code_lettrage for l in lignes}
                        assert len(codes) == 1 and None not in codes and len(next(iter(codes))) >= 3
                        assert all(l.tiers_id and l.compte_auxiliaire_snapshot for l in lignes)
                    physique = db.get(models.Article, article['id'])
                    assert physique.stock_actuel == 6 and physique.cmup == 100
                    assert db.query(models.MouvementStock).filter_by(article_id=article['id']).count() == 2
                page.goto(application['web_url'] + '/declaration-tva')
                page.get_by_role('heading', name='Déclaration TVA', exact=True).wait_for()
                choisir_mois(page, 3, lambda data: verifier_tva(data, 'mars'))
                choisir_mois(page, 6, lambda data: verifier_tva(data, 'juin'))
                with page.expect_response(lambda r: '/api/tva/declaration?' in r.url and 'trimestre=' not in r.url and 'mois=' not in r.url) as sortie:
                    page.get_by_role('button', name='Vue annuelle', exact=True).click()
                assert sortie.value.status == 200
                verifier_tva(sortie.value.json(), 'annuelle')
                page.get_by_text('acquisition non payée', exact=False).wait_for()
                page.goto(application['web_url'] + '/immobilisations')
                page.get_by_text(immo_nom, exact=True).wait_for()
                with page.expect_response(lambda r: '/api/immobilisations/generer-dotations-annee?annee=2025' in r.url) as sortie:
                    page.get_by_role('button', name='Dotations 2025', exact=True).click()
                assert sortie.value.status == 200, sortie.value.text()
                assert sortie.value.json()['nb_generees'] == 1
                assert D(str(sortie.value.json()['total_dotation'])) == 400
                inventaire = ok(api.post('/api/inventaire/valider', json={'date': '2025-12-31', 'reference': 'INV-ANNUEL', 'lignes': [{'article_id': article['id'], 'quantite_reelle': 6}]}))
                assert D(str(inventaire['total_valeur'])) == 600
                stock = ok(api.post('/api/inventaire/comptabiliser-stock?exercice=2025'))
                assert stock['ecriture_id']
                valider_brouillons_ui(page, application, 2)
                avant_cloture = lignes_comptables(application, sid)
                with Session(application['engine']) as db:
                    ecritures = db.query(models.Ecriture).filter_by(societe_id=sid, exercice=2025).all()
                    assert len(ecritures) == 10 and all(e.est_validee for e in ecritures)
                    lignes = [l for e in ecritures for l in e.lignes]
                    assert len(lignes) == 23
                    assert sum(l.debit for l in lignes) == sum(l.credit for l in lignes) == D('26760')
                rapport = ok(api.get('/api/ecritures/reporting/balance?exercice=2025&date_from=2025-01-01&date_to=2025-12-31'))
                assert {r['compte']: D(str(r['solde_final'])) for r in rapport['comptes']} == {c: D(s) for c, s in ORACLE['soldes_avant_impot'].items()}
                etat = ok(api.get('/api/cloture/etat?exercice=2025'))
                assert etat['resultat_net'] == 0 and etat['equilibre'] and etat['nb_ecritures_brouillon'] == 0
                assert etat['stock_cloture']['stock_rapproche'] and etat['immobilisations_rapprochement']['rapproche']
                assert etat['nb_dotations_manquantes'] == 0 and etat['fec_controle']['conforme']
                assert D(str(etat['fiscalite_is']['a_comptabiliser'])) == 3000
                page.goto(application['web_url'] + '/balances')
                page.get_by_text('Balance équilibrée', exact=False).wait_for()
                xlsx = load_workbook(telecharger(page, 'Excel', tmp_path, 'annuelle-avant-cloture'), data_only=True)
                rows = list(xlsx['Balance'].values)
                assert next(r for r in rows[7:] if r[0] == '5141')[6:] == (19760, 0)
                pdf = pdf_texte(telecharger(page, 'PDF', tmp_path, 'annuelle-avant-cloture'))
                assert '19 760,00' in pdf and '2355' in pdf and '3111' in pdf
                page.get_by_role('button', name='Balance Résultat', exact=False).click()
                xlsx = load_workbook(telecharger(page, 'Excel', tmp_path, 'resultat-annuel'), data_only=True)
                assert next(r for r in xlsx['Balance'].values if r[0] == 'Résultat net signé')[1] == 0
                page.goto(application['web_url'] + '/cloture')
                bouton = page.get_by_role('button', name="Clôturer l'exercice 2025", exact=True)
                playwright.expect(bouton).to_be_enabled()
                with page.expect_response(lambda r: '/api/cloture/cloturer?exercice=2025' in r.url) as sortie:
                    bouton.click()
                assert sortie.value.status == 200, sortie.value.text()
                assert D(str(sortie.value.json()['resultat_net'])) == D('-3000')
                assert sortie.value.json()['a_nouveaux_sur'] == 2026
                page.get_by_text('Exercice 2025 clôturé définitivement', exact=False).wait_for()
                with Session(application['engine']) as db:
                    ex = db.query(models.ExerciceComptable).filter_by(societe_id=sid, annee=2025).one()
                    assert ex.statut == 'cloture' and all(p.statut == 'fermee' for p in ex.periodes)
                    trace = db.query(models.ClotureExercice).filter_by(societe_id=sid, exercice=2025).one()
                    an = db.get(models.Ecriture, trace.ecriture_an_id)
                    assert an.est_validee and an.exercice == 2026 and an.journal == models.JournalEnum.AN
                    soldes_an = defaultdict(lambda: D(0))
                    for l in an.lignes:
                        soldes_an[l.compte] += l.debit - l.credit
                    assert dict(soldes_an) == {c: D(s) for c, s in ORACLE['soldes_a_nouveaux_2026'].items()}
                    assert sum(l.debit for l in an.lignes) == sum(l.credit for l in an.lignes) == D('25000')
                    activite = defaultdict(lambda: D(0))
                    for e in db.query(models.Ecriture).filter_by(societe_id=sid, exercice=2025):
                        for l in e.lignes:
                            if l.compte.startswith(('6', '7', '8')):
                                activite[l.compte] += l.debit - l.credit
                    assert all(v == 0 for v in activite.values())
                assert avant_cloture <= lignes_comptables(application, sid)
                refuse = api.post('/api/ecritures', json={'date': '2025-12-31', 'journal': 'BQ', 'reference': 'INTERDIT-CLOS', 'libelle': 'Tentative fictive refusée', 'lignes': [{'compte': '5141', 'debit': 1}, {'compte': '1111', 'credit': 1}]})
                assert refuse.status_code == 423, refuse.text
                assert api.post('/api/cloture/cloturer?exercice=2025').status_code == 400
                for annee in (2025, 2026):
                    controle = ok(api.get(f'/api/fec/apercu?exercice={annee}'))
                    assert controle['conforme_export'], controle
                    export = api.get(f'/api/fec/export?exercice={annee}')
                    assert export.status_code == 200, export.text
                    (tmp_path / f'FEC-{annee}.txt').write_bytes(export.content)
                    assert len(export.content.splitlines()) > 5
                page.locator('select').filter(has=page.locator('option[value="2026"]')).first.select_option('2026')
                page.goto(application['web_url'] + '/journal')
                page.get_by_text('AN-2026', exact=True).wait_for()
                page.reload(); page.get_by_text('AN-2026', exact=True).wait_for()
                page.goto(application['web_url'] + '/balances')
                page.get_by_text('Balance équilibrée', exact=False).wait_for()
                xlsx = load_workbook(telecharger(page, 'Excel', tmp_path, 'a-nouveaux-2026'), data_only=True)
                rows = list(xlsx['Balance'].values)
                assert next(r for r in rows[7:] if r[0] == '1199')[6:] == (3000, 0)
                total = next(r for r in rows if r[0] == 'TOTAL GÉNÉRAL')
                assert total[6:] == (25000, 25000)
                pdf = pdf_texte(telecharger(page, 'PDF', tmp_path, 'a-nouveaux-2026'))
                assert '25 000,00' in pdf and '1199' in pdf and '4453' in pdf
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print('Page annuelle fictive :', page.url, page.locator('body').inner_text()[:6000])
                print('API isolée :', application['api_log'].read_text(encoding='utf-8', errors='replace')[-6000:])
                print('Empreinte oracle figé :', hashlib.sha256(ORACLE_PATH.read_bytes()).hexdigest())
                print('Réponses lettrage dans ordre réel :', responses_lettrage)
                raise
            finally:
                browser.close()
