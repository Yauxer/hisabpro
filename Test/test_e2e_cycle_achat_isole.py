"""BC achat → réception → facture, navigateur et PostgreSQL nonce réels."""
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

HT = Decimal('2') * Decimal('500')
TVA = HT * Decimal('0.20')
TTC = HT + TVA


@pytest.mark.parametrize('largeur', [1365, 390])
def test_cycle_achat_bc_reception_facture(application, largeur):
    cluster = application['cluster']
    verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
    suffix = uuid.uuid4().hex[:8]
    email, password = f'cycle-achat-{suffix}@example.com', 'CycleAchatFictif2026!'
    nom, article = 'Fournisseur cycle fictif ' + suffix, 'Marchandise cycle achat ' + suffix
    with httpx.Client(base_url=application['api_url']) as api:
        auth = ok(api.post('/api/auth/register', json={'nom': 'Recette achat', 'email': email,
            'password': password, 'raison_sociale': 'Cycle achat fictif ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + auth['access_token']
        sid = ok(api.get('/api/societe/moi'))['id']
        tid = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'fournisseur', 'compte_fournisseur': '4411'}), 201)['id']
        aid = ok(api.post('/api/articles', json={'code': 'CYCLE-FR-' + suffix, 'designation': article,
            'prix_achat_ht': 500, 'prix_vente_ht': 700, 'tva': 20, 'compte_achat': '6111',
            'stock_actuel': 0, 'is_stockable': True}), 201)['id']
        with Session(application['engine']) as db:
            assert (db.get(models.Societe, sid).stock_declencheur_achat or 'facture') == 'facture'
        stock_et_ecritures(application, aid, sid, 0, 0, 0)
        executable = chromium_executable()
        if not executable:
            pytest.skip('Edge/Chromium requis')
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            page = browser.new_page(viewport={'width': largeur, 'height': 900})
            page.set_default_timeout(20000)
            errors, server_errors = observer(page, application['api_url'])
            page.on('dialog', lambda dialog: dialog.accept())
            try:
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/commercial')
                page.get_by_role('button', name='Achat', exact=True).click()
                page.get_by_role('button', name='Nouveau BC', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouveau bon de commande', exact=True)
                modal.get_by_placeholder('Nom du fournisseur...', exact=True).fill(nom)
                modal.get_by_role('option').filter(has_text=nom).click()
                modal.get_by_placeholder('Article ou description...', exact=True).fill(article)
                modal.locator('li').filter(has_text=article).click()
                modal.get_by_label('Quantité', exact=True).fill('2')
                with page.expect_response(lambda r: r.url.endswith('/api/bons-commande') and r.request.method == 'POST') as created:
                    modal.get_by_role('button', name='Créer la commande', exact=True).click()
                assert created.value.status == 201, created.value.text()
                bc = created.value.json(); bcid = bc['id']
                assert bc['type'] == 'achat' and Decimal(str(bc['total_ht'])) == HT
                modal.wait_for(state='hidden')
                row = page.locator('tbody tr').filter(has_text=nom)
                row.get_by_title('Créer un bon de réception sur le reliquat', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouveau bon de réception', exact=True)
                playwright.expect(modal.locator('input[type="number"]')).to_have_value('2')
                with page.expect_response(lambda r: r.url.endswith(f'/api/bons-commande/{bcid}/convertir-bl')) as received:
                    modal.get_by_role('button', name='Créer le bon de réception', exact=True).click()
                assert received.value.status == 200, received.value.text()
                br = received.value.json(); brid = br['id']
                assert br['type'] == 'achat' and br['bon_commande_id'] == bcid
                modal.wait_for(state='hidden')
                page.get_by_role('button', name='Bons de réception', exact=True).click()
                for titre in ('Marquer en cours', 'Marquer réceptionné'):
                    with page.expect_response(lambda r: r.url.endswith(f'/api/bons-reception/{brid}') and r.request.method == 'PATCH') as logistics:
                        row.get_by_title(titre, exact=True).click()
                    assert logistics.value.status == 200, logistics.value.text()
                stock_et_ecritures(application, aid, sid, 0, 0, 0)
                row.get_by_title('Créer la facture fournisseur depuis ce bon de réception', exact=True).click()
                modal = page.get_by_role('dialog', name='Facturer le bon de réception ' + br['numero'], exact=True)
                playwright.expect(modal.locator('input[type="number"]')).to_have_value('2')
                with page.expect_response(lambda r: r.url.endswith(f'/api/bons-livraison/{brid}/convertir-facture')) as invoiced:
                    modal.get_by_role('button', name='Créer la facture en brouillon', exact=True).click()
                assert invoiced.value.status == 200, invoiced.value.text()
                facture = invoiced.value.json(); fid = facture['id']
                assert not facture['est_validee'] and not facture['numero']
                assert Decimal(str(facture['total_ttc'])) == TTC
                modal.wait_for(state='hidden')
                page.get_by_role('button', name='Factures', exact=True).click()
                playwright.expect(row).to_contain_text(nom)
                stock_et_ecritures(application, aid, sid, 0, 0, 0)
                # Qualification explicite par l'API réelle, sur le seul brouillon fictif.
                ok(api.patch(f'/api/factures/{fid}', json={'reference': 'FR-CYCLE-' + suffix,
                    'nature_tva_achat': 'charge', 'tva_deductible_pct': 100}))
                with Session(application['engine']) as db:
                    qualified = db.get(models.Facture, fid)
                    assert qualified.nature_tva_achat == 'charge' and qualified.tva_deductible_pct == 100
                    assert qualified.reference == 'FR-CYCLE-' + suffix
                page.goto(application['web_url'] + '/factures')
                with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/valider')) as validated:
                    row.get_by_title('Valider définitivement', exact=True).click()
                assert validated.value.status == 200, validated.value.text()
                stock_et_ecritures(application, aid, sid, 2, 1, 0)
                with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/comptabiliser')) as posted:
                    row.get_by_title("Générer l'écriture comptable de cette facture", exact=True).click()
                assert posted.value.status == 200, posted.value.text()
                stock_et_ecritures(application, aid, sid, 2, 1, 1)
                page.goto(application['web_url'] + '/journal')
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(1)
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as definitive:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert definitive.value.status == 200 and definitive.value.json()['nb_validees'] == 1
                with Session(application['engine']) as db:
                    bc_db, br_db, f = db.get(models.BonCommande, bcid), db.get(models.BonLivraison, brid), db.get(models.Facture, fid)
                    assert br_db.bon_commande_id == bcid and br_db.facture_id == fid and br_db.statut == 'livre'
                    assert br_db.lignes[0].source_ligne_bc_id == bc_db.lignes[0].id
                    ligne = f.lignes[0]
                    assert ligne.source_ligne_bc_id == bc_db.lignes[0].id and ligne.source_ligne_bl_id == br_db.lignes[0].id
                    assert ligne.article_id == aid and ligne.quantite == 2 and ligne.prix_unitaire == 500
                    ec = db.query(models.Ecriture).filter_by(societe_id=sid).one()
                    assert ec.est_validee and f.est_validee and f.est_comptabilisee
                    assert {l.compte: (Decimal(str(l.debit)), Decimal(str(l.credit))) for l in ec.lignes} == {
                        '6111': (HT, 0), '34552': (TVA, 0), '4411': (0, TTC)}
                    assert sum(l.debit for l in ec.lignes) == sum(l.credit for l in ec.lignes) == TTC
                    fournisseur = next(l for l in ec.lignes if l.compte == '4411')
                    assert fournisseur.tiers_id == tid and fournisseur.compte_auxiliaire_snapshot
                    mouvement = db.query(models.MouvementStock).filter_by(article_id=aid).one()
                    assert mouvement.type == 'entree' and mouvement.quantite == 2
                    assert mouvement.stock_avant == 0 and mouvement.stock_apres == 2
                    assert mouvement.source_type == 'facture' and mouvement.source_id == fid
                    assert mouvement.source_ligne_id == ligne.id and mouvement.cle_idempotence
                avant = originaux(application, sid)
                assert api.post(f'/api/bons-commande/{bcid}/convertir-bl', json={}).status_code == 400
                assert api.post(f'/api/bons-livraison/{brid}/convertir-facture', json={}).status_code == 409
                assert api.post(f'/api/factures/{fid}/comptabiliser').status_code == 409
                page.goto(application['web_url'] + '/commercial')
                page.get_by_role('button', name='Achat', exact=True).click()
                page.get_by_role('button', name='Factures', exact=True).click()
                playwright.expect(row).to_contain_text(nom)
                page.reload()
                page.get_by_role('button', name='Achat', exact=True).click()
                page.get_by_role('button', name='Factures', exact=True).click()
                playwright.expect(row).to_contain_text(nom)
                assert originaux(application, sid) == avant
                stock_et_ecritures(application, aid, sid, 2, 1, 1)
                with Session(application['engine']) as db:
                    for modele in (models.BonCommande, models.BonLivraison, models.Facture):
                        assert db.query(modele).filter_by(societe_id=sid).count() == 1
                    assert db.get(models.BonLivraison, brid).facture_id == fid
                    assert db.get(models.Facture, fid).lignes[0].source_ligne_bl_id == br_db.lignes[0].id
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                print('Cycle achat fictif:', page.url, page.locator('body').inner_text()[:6500])
                print('Erreurs JavaScript/API:', errors, server_errors)
                print(application['api_log'].read_text(encoding='utf-8', errors='replace')[-6000:])
                raise
            finally:
                browser.close()
