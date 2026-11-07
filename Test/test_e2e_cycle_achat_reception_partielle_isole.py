"""Réceptions partielles avec stock au BR, interface/API et PostgreSQL nonce."""
from datetime import date
from decimal import Decimal
import uuid
import httpx
import pytest
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_acompte_imputation_isole import application, application_base
from test_e2e_acompte_fournisseur_isole import ok
from test_e2e_avoir_fournisseur_isole import originaux
from test_e2e_cycle_commercial_isole import stock_et_ecritures
from test_e2e_facturation_isole import champ


@pytest.mark.parametrize('largeur', [1365, 390])
def test_cycle_reception_partielle_stock_br(application, largeur):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    suffix = uuid.uuid4().hex[:8]
    email, password = f'partiel-br-{suffix}@example.com', 'ReceptionFictive2026!'
    nom, article = 'Fournisseur BR partiel ' + suffix, 'Article BR partiel ' + suffix
    with httpx.Client(base_url=application['api_url']) as api:
        auth = ok(api.post('/api/auth/register', json={'nom': 'Recette BR', 'email': email,
            'password': password, 'raison_sociale': 'Réceptions partielles fictives ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + auth['access_token']
        sid = ok(api.get('/api/societe/moi'))['id']
        assert ok(api.patch('/api/societe/moi', json={'stock_declencheur_achat': 'br'}))['stock_declencheur_achat'] == 'br'
        tid = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'fournisseur', 'compte_fournisseur': '4411'}), 201)['id']
        aid = ok(api.post('/api/articles', json={'code': 'PART-BR-' + suffix, 'designation': article,
            'prix_achat_ht': 500, 'prix_vente_ht': 700, 'tva': 20, 'compte_achat': '6111',
            'stock_actuel': 0, 'is_stockable': True}), 201)['id']
        bc = ok(api.post('/api/bons-commande', json={'type': 'achat', 'date': date.today().isoformat(),
            'tiers': nom, 'tiers_id': tid, 'lignes': [{'article_id': aid, 'description': article,
                'quantite': 4, 'prix_unitaire': 500, 'tva': 20, 'qualification_tva': 'taxable'}]}), 201)
        bcid, bclid = bc['id'], bc['lignes'][0]['id']
        assert Decimal(str(bc['total_ttc'])) == Decimal(4) * Decimal(500) * Decimal('1.20')
        stock_et_ecritures(application, aid, sid, 0, 0, 0)
        executable = chromium_executable()
        if not executable: pytest.skip('Edge/Chromium requis')
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            page = browser.new_page(viewport={'width': largeur, 'height': 900})
            page.set_default_timeout(20000)
            errors, server_errors = observer(page, application['api_url'])
            page.on('dialog', lambda d: d.accept())
            try:
                connexion(page, application['web_url'], email, password)
                brs, factures, cumul, premier_original = [], [], 0, None
                for n, qte in enumerate((1, 3), start=1):
                    page.goto(application['web_url'] + '/commercial')
                    page.get_by_role('button', name='Achat', exact=True).click()
                    page.get_by_role('button', name='Bons de commande', exact=True).click()
                    row = page.locator('tbody tr').filter(has_text=bc['numero'])
                    row.get_by_title('Créer un bon de réception sur le reliquat', exact=True).click()
                    modal = page.get_by_role('dialog', name='Nouveau bon de réception', exact=True)
                    qty = modal.locator('input[type="number"]')
                    playwright.expect(qty).to_have_value(str(4 - cumul))
                    qty.fill(str(qte))
                    with page.expect_response(lambda r: r.url.endswith(f'/api/bons-commande/{bcid}/convertir-bl')) as received:
                        modal.get_by_role('button', name='Créer le bon de réception', exact=True).click()
                    assert received.value.status == 200, received.value.text()
                    br = received.value.json(); brid = br['id']; brs.append(brid)
                    modal.wait_for(state='hidden')
                    stock_et_ecritures(application, aid, sid, cumul, n-1, n-1)
                    page.get_by_role('button', name='Bons de réception', exact=True).click()
                    row = page.locator('tbody tr').filter(has_text=br['numero'])
                    for titre in ('Marquer en cours', 'Marquer réceptionné'):
                        with page.expect_response(lambda r: r.url.endswith(f'/api/bons-reception/{brid}') and r.request.method == 'PATCH') as logistics:
                            row.get_by_title(titre, exact=True).click()
                        assert logistics.value.status == 200, logistics.value.text()
                    cumul += qte
                    stock_et_ecritures(application, aid, sid, cumul, n, n-1)
                    restant = ok(api.get(f'/api/bons-commande/{bcid}/reliquat'))
                    assert restant['total_reliquat'] == 4-cumul and restant['total_livre'] == cumul
                    if n == 1:
                        refuse = api.post(f'/api/bons-commande/{bcid}/convertir-bl', json={
                            'lignes': [{'ligne_bc_id': bclid, 'description': article, 'quantite': 4}]})
                        assert refuse.status_code == 400, refuse.text
                    row.get_by_title('Créer la facture fournisseur depuis ce bon de réception', exact=True).click()
                    modal = page.get_by_role('dialog', name='Facturer le bon de réception ' + br['numero'], exact=True)
                    playwright.expect(modal.locator('input[type="number"]')).to_have_value(str(qte))
                    with page.expect_response(lambda r: r.url.endswith(f'/api/bons-livraison/{brid}/convertir-facture')) as invoiced:
                        modal.get_by_role('button', name='Créer la facture en brouillon', exact=True).click()
                    assert invoiced.value.status == 200, invoiced.value.text()
                    facture = invoiced.value.json(); fid = facture['id']; factures.append(fid)
                    assert Decimal(str(facture['total_ttc'])) == Decimal(qte) * Decimal(500) * Decimal('1.20')
                    modal.wait_for(state='hidden')
                    page.goto(application['web_url'] + '/factures')
                    row = page.locator('tbody tr').filter(has_text=f'Brouillon #{fid}')
                    row.get_by_title('Modifier le brouillon', exact=True).click()
                    modal = page.get_by_role('dialog', name=f'Modifier — Brouillon #{fid}', exact=True)
                    champ(modal, 'N° facture fournisseur').fill(f'FR-PART-{suffix}-{n}')
                    modal.get_by_label('Qualification TVA de l’achat', exact=True).select_option('charge')
                    modal.get_by_label('TVA déductible (%)', exact=True).fill('100')
                    with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}') and r.request.method == 'PATCH') as edited:
                        modal.get_by_role('button', name='Enregistrer les modifications', exact=True).click()
                    assert edited.value.status == 200, edited.value.text()
                    payload = edited.value.request.post_data_json
                    assert payload['nature_tva_achat'] == 'charge' and payload['tva_deductible_pct'] == 100
                    modal.wait_for(state='hidden')
                    with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/valider')) as validated:
                        row.get_by_title('Valider définitivement', exact=True).click()
                    assert validated.value.status == 200, validated.value.text()
                    numero = validated.value.json()['numero']
                    stock_et_ecritures(application, aid, sid, cumul, n, n-1)
                    row = page.locator('tbody tr').filter(has_text=numero)
                    with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/comptabiliser')) as posted:
                        row.get_by_title("Générer l'écriture comptable de cette facture", exact=True).click()
                    assert posted.value.status == 200, posted.value.text()
                    stock_et_ecritures(application, aid, sid, cumul, n, n)
                    page.goto(application['web_url'] + '/journal')
                    playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(1)
                    with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as definitive:
                        page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                    assert definitive.value.status == 200 and definitive.value.json()['nb_validees'] == 1
                    originaux_phase = originaux(application, sid)
                    if premier_original is None:
                        premier_original = originaux_phase[0]
                    else:
                        assert originaux_phase[0] == premier_original
                    assert api.post(f'/api/bons-livraison/{brid}/convertir-facture', json={}).status_code == 409
                    assert api.post(f'/api/factures/{fid}/comptabiliser').status_code == 409
                    assert originaux(application, sid) == originaux_phase
                avant = originaux(application, sid)
                assert api.post(f'/api/bons-commande/{bcid}/convertir-bl', json={}).status_code == 400
                with Session(application['engine']) as db:
                    assert db.query(models.BonCommande).filter_by(societe_id=sid).count() == 1
                    assert db.query(models.BonLivraison).filter_by(societe_id=sid).count() == 2
                    assert db.query(models.Facture).filter_by(societe_id=sid).count() == 2
                    for brid, fid, quantite in zip(brs, factures, (1, 3)):
                        br, f = db.get(models.BonLivraison, brid), db.get(models.Facture, fid)
                        assert br.bon_commande_id == bcid and br.facture_id == fid
                        assert br.lignes[0].source_ligne_bc_id == bclid
                        assert f.lignes[0].source_ligne_bc_id == bclid and f.lignes[0].source_ligne_bl_id == br.lignes[0].id
                        assert f.lignes[0].quantite == quantite and f.lignes[0].article_id == aid
                        assert f.est_validee and f.est_comptabilisee and f.nature_tva_achat == 'charge' and f.tva_deductible_pct == 100
                    mouvements = db.query(models.MouvementStock).filter_by(article_id=aid).order_by(models.MouvementStock.id).all()
                    assert [(m.quantite, m.stock_avant, m.stock_apres) for m in mouvements] == [(1, 0, 1), (3, 1, 4)]
                    for m, brid in zip(mouvements, brs):
                        assert m.type == 'entree' and m.source_type == 'bon_reception' and m.source_id == brid
                        assert m.source_ligne_id == db.get(models.BonLivraison, brid).lignes[0].id
                        assert m.cout_unitaire == 500 and m.cle_idempotence
                    ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).all()
                    assert len(ecritures) == 2 and all(e.est_validee for e in ecritures)
                    sommes = {}
                    for e in ecritures:
                        assert sum(l.debit for l in e.lignes) == sum(l.credit for l in e.lignes)
                        for l in e.lignes:
                            d, c = sommes.get(l.compte, (Decimal(0), Decimal(0)))
                            sommes[l.compte] = d+Decimal(str(l.debit)), c+Decimal(str(l.credit))
                            if l.compte == '4411': assert l.tiers_id == tid and l.compte_auxiliaire_snapshot
                    assert sommes == {'6111': (2000, 0), '34552': (400, 0), '4411': (0, 2400)}
                page.goto(application['web_url'] + '/commercial')
                page.get_by_role('button', name='Achat', exact=True).click()
                page.get_by_role('button', name='Factures', exact=True).click()
                playwright.expect(page.locator('tbody tr').filter(has_text=nom)).to_have_count(2)
                page.reload()
                page.get_by_role('button', name='Achat', exact=True).click()
                page.get_by_role('button', name='Factures', exact=True).click()
                playwright.expect(page.locator('tbody tr').filter(has_text=nom)).to_have_count(2)
                stock_et_ecritures(application, aid, sid, 4, 2, 2)
                assert originaux(application, sid) == avant
                # Prolongement connecté : régler séparément les deux pièces du même fournisseur.
                for n, (fid, montant) in enumerate(zip(factures, (600, 1800)), start=1):
                    with Session(application['engine']) as db:
                        numero = db.get(models.Facture, fid).numero
                    page.goto(application['web_url'] + '/factures')
                    row = page.locator('tbody tr').filter(has_text=numero)
                    row.get_by_title('Payer le fournisseur', exact=True).click()
                    modal = page.get_by_role('dialog')
                    assert Decimal(champ(modal, 'Montant *').input_value()) == montant
                    modal.get_by_placeholder('N° chèque, virement...').fill(f'PAY-PART-{suffix}-{n}')
                    with page.expect_response(lambda r: r.url.endswith('/api/reglements') and r.request.method == 'POST') as paid:
                        modal.get_by_role('button', name='Enregistrer', exact=True).click()
                    assert paid.value.status == 201, paid.value.text()
                    assert paid.value.json()['facture_id'] == fid
                    modal.wait_for(state='hidden')
                    situation = ok(api.get(f'/api/factures/{fid}/reglements'))
                    assert situation['total_regle'] == montant and situation['solde_restant'] == 0
                    stock_et_ecritures(application, aid, sid, 4, 2, 2+n)
                    assert originaux(application, sid)[:2] == avant
                page.goto(application['web_url'] + '/journal')
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(2)
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as paiements_valides:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert paiements_valides.value.status == 200 and paiements_valides.value.json()['nb_validees'] == 2
                avant_lettrage = originaux(application, sid)
                assert avant_lettrage[:2] == avant
                page.goto(application['web_url'] + '/lettrage')
                champ(page, 'Compte', 'select').select_option('4411')
                champ(page, 'Tiers', 'select').select_option(label=nom)
                playwright.expect(page.locator('tbody input[type="checkbox"]')).to_have_count(4)
                for box in page.locator('tbody input[type="checkbox"]').all(): box.check()
                with page.expect_response(lambda r: '/api/lettrage' in r.url and r.request.method == 'POST') as lettered:
                    page.get_by_role('button', name='Lettrer 4 lignes', exact=True).click()
                assert lettered.value.status == 200 and lettered.value.json()['code'] == 'AAA', lettered.value.text()
                assert originaux(application, sid) == avant_lettrage
                page.reload()
                champ(page, 'Compte', 'select').select_option('4411')
                champ(page, 'Tiers', 'select').select_option(label=nom)
                page.get_by_text('4 lettrée(s)', exact=True).wait_for()
                stock_et_ecritures(application, aid, sid, 4, 2, 4)
                with Session(application['engine']) as db:
                    ecs = db.query(models.Ecriture).filter_by(societe_id=sid).all()
                    assert len(ecs) == 4 and all(e.est_validee for e in ecs)
                    ls = [l for e in ecs for l in e.lignes]
                    assert len(ls) == 10
                    assert sum(Decimal(str(l.debit)) for l in ls) == sum(Decimal(str(l.credit)) for l in ls) == 4800
                    soldes = {}
                    for l in ls:
                        soldes[l.compte] = soldes.get(l.compte, Decimal(0)) + Decimal(str(l.debit)) - Decimal(str(l.credit))
                    assert soldes == {'6111': 2000, '34552': 400, '4411': 0, '5141': -2400}
                    fournisseurs = [l for l in ls if l.compte == '4411']
                    assert len(fournisseurs) == 4 and all(l.tiers_id == tid and l.code_lettrage == 'AAA' for l in fournisseurs)
                    assert db.query(models.Reglement).filter_by(societe_id=sid).count() == 2
                assert originaux(application, sid) == avant_lettrage
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                try:
                    print('Réception partielle fictive:', page.url, page.locator('body').inner_text(timeout=2000)[:6500])
                    print('Erreurs JS/API:', errors, server_errors)
                    print(application['api_log'].read_text(encoding='utf-8', errors='replace')[-6000:])
                except Exception as diagnostic:
                    print('Diagnostic secondaire indisponible:', type(diagnostic).__name__)
                raise
            finally:
                browser.close()
