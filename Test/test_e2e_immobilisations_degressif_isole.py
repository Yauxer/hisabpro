"""Dégressif déjà implémenté : cinq exercices réels sur une cible nonce."""
from datetime import date
from decimal import Decimal
from pathlib import Path
import json
import pytest
from sqlalchemy.orm import Session
import models
from test_e2e_facturation_isole import application, champ
from test_ras_lecture_conservation import client
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable

ORACLE = Path(__file__).resolve().parents[1]/'docs/recette/oracle_degressif_60000_5_ans.json'


def test_oracle_degressif_bascule_lineaire_independant():
    o = json.loads(ORACLE.read_text(encoding='utf-8'))
    brute = Decimal(o['prix_ht']); reste = brute
    dots = []
    for restant in range(5, 0, -1):
        dot = max(reste*Decimal('0.40'), reste/Decimal(restant)).quantize(Decimal('0.01'))
        dots.append(dot); reste -= dot
    assert dots == list(map(Decimal, o['dotations']))
    assert sum(dots) == brute and reste == 0
    assert Decimal(o['tva']) == brute*Decimal('0.20')
    assert Decimal(o['ttc']) == brute+Decimal(o['tva'])


@pytest.mark.parametrize('latence_ms', [0, 250], ids=['reseau-normal', 'reseau-ralenti'])
def test_edge_cinq_dotations_degressives_et_acquisition_definitive_conservee(application, latence_ms):
    from playwright.sync_api import sync_playwright, expect
    o = json.loads(ORACLE.read_text(encoding='utf-8'))
    annees = list(range(date.today().year-5, date.today().year))
    api, email, password = client(application)
    try:
        for annee in annees:
            r = api.post('/api/exercices', json={'annee': annee, 'date_debut': f'{annee}-01-01', 'date_fin': f'{annee}-12-31'})
            assert r.status_code == 201, r.text
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': 1365, 'height': 1000})
                if latence_ms:
                    session = page.context.new_cdp_session(page)
                    session.send('Network.enable')
                    session.send('Network.emulateNetworkConditions', {
                        'offline': False, 'latency': latence_ms,
                        'downloadThroughput': -1, 'uploadThroughput': -1})
                page.set_default_timeout(20000)
                page.on('dialog', lambda d: d.accept())
                erreurs, serveurs = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/immobilisations')
                page.get_by_role('button', name='Nouvelle immobilisation', exact=True).click()
                modal = page.locator('[class*="modalOverlay"]').first
                designation = 'Materiel fictif degressif 60000'
                modal.get_by_placeholder('Ex: Serveur Dell PowerEdge', exact=True).fill(designation)
                champ(modal, 'Catégorie', 'select').select_option('Matériel informatique')
                champ(modal, 'Date d’acquisition *').fill(f'{annees[0]}-01-01')
                champ(modal, 'Prix d’acquisition HT *').fill('60000')
                champ(modal, 'Durée (années)').fill('5')
                champ(modal, 'Méthode', 'select').select_option('degressif')
                with page.expect_response(lambda r: r.url.endswith('/api/immobilisations') and r.request.method == 'POST') as creation:
                    modal.get_by_role('button', name='Créer', exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                immo = creation.value.json(); iid = immo['id']; aid = immo['ecriture_acquisition_id']
                assert Decimal(str(immo['valeur_brute'])) == 60000 and Decimal(str(immo['total_ttc'])) == 72000
                modal.wait_for(state='hidden')
                r = api.post(f'/api/ecritures/{aid}/valider', json={})
                assert r.status_code == 200, r.text
                with Session(application['engine']) as db:
                    acquisition = db.get(models.Ecriture, aid); sid = acquisition.societe_id
                    original = [(l.id, l.compte, l.debit, l.credit) for l in acquisition.lignes]
                    assert {l.compte: (l.debit, l.credit) for l in acquisition.lignes} == {
                        '2355': (60000, 0), '34551': (12000, 0), '4481': (0, 72000)}
                registre = page.locator('tr').filter(has=page.get_by_text(designation, exact=True)).first
                registre.click()
                tableau = page.locator('table').filter(has=page.get_by_role('columnheader', name='Prorata', exact=True)).last
                for annee, dot, cumul, vnc in zip(annees, o['dotations'], o['cumul'], o['vnc']):
                    ligne = tableau.locator('tbody tr').filter(has=page.get_by_role('cell', name=str(annee), exact=True))
                    def mad(v): return f'{Decimal(v):,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')+' MAD'
                    # La génération précédente recharge le tableau ; attendre
                    # ses cellules au lieu de lire immédiatement un DOM vide.
                    for colonne, montant in enumerate((dot, cumul, vnc), start=3):
                        expect(ligne.locator('td').nth(colonne)).to_have_text(mad(montant))
                    with page.expect_response(lambda r: f'/api/immobilisations/{iid}/generer-ecriture?annee={annee}' in r.url) as generation:
                        ligne.get_by_role('button', name='Générer', exact=True).click()
                    assert generation.value.status == 200, generation.value.text()
                    assert Decimal(str(generation.value.json()['dotation'])) == Decimal(dot)
                    registre.wait_for()
                page.goto(application['web_url']+'/journal')
                for annee in annees:
                    page.locator('select').filter(has=page.locator(f'option[value="{annee}"]')).first.select_option(str(annee))
                    expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(1)
                    with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as validation:
                        page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                    assert validation.value.status == 200, validation.value.text()
                    assert validation.value.json()['nb_validees'] == 1
                with Session(application['engine']) as db:
                    entries = db.query(models.Ecriture).filter_by(societe_id=sid).all()
                    assert len(entries) == 6 and all(e.est_validee for e in entries)
                    assert all(sum(l.debit for l in e.lignes) == sum(l.credit for l in e.lignes) for e in entries)
                    assert [(l.id, l.compte, l.debit, l.credit) for l in db.get(models.Ecriture, aid).lignes] == original
                    assert sum(l.debit for e in entries for l in e.lignes) == sum(l.credit for e in entries for l in e.lignes) == 132000
                    assert sum(l.credit for e in entries for l in e.lignes if l.compte == '28355') == 60000
                    avant = [(e.id, e.est_validee, [(l.id, l.compte, l.debit, l.credit) for l in e.lignes]) for e in entries]
                r = api.post(f'/api/immobilisations/generer-dotations-annee?annee={annees[-1]}', json={})
                assert r.status_code == 200, r.text
                assert r.json()['nb_generees'] == 0 and r.json()['total_dotation'] == 0
                with Session(application['engine']) as db:
                    assert [(e.id, e.est_validee, [(l.id, l.compte, l.debit, l.credit) for l in e.lignes]) for e in db.query(models.Ecriture).filter_by(societe_id=sid)] == avant
                assert not erreurs and not serveurs, (erreurs, serveurs)
            finally:
                browser.close()
    finally:
        api.close()
