"""Achat fournisseur, avoir physique partiel, règlement et lettrage : recette isolée réelle."""
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
from test_e2e_facturation_isole import champ
from test_e2e_acompte_fournisseur_isole import ok

PHASES = [
    {'6111': (1000, 0), '34552': (200, 0), '4411': (0, 1200)},
    {'4411': (600, 0), '6111': (0, 500), '34552': (0, 100)},
    {'4411': (600, 0), '5141': (0, 600)},
]


def originaux(app, sid):
    """Toutes les colonnes persistées ; le lettrage est une table séparée."""
    with Session(app['engine']) as db:
        ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).order_by(models.Ecriture.id).all()
        return tuple((tuple((c.name, getattr(e, c.name)) for c in e.__table__.columns),
            tuple(tuple((c.name, getattr(l, c.name)) for c in l.__table__.columns)
                  for l in sorted(e.lignes, key=lambda l: l.id))) for e in ecritures)

def verifier(app, sid, tid, n, stock):
    with Session(app['engine']) as db:
        ecs = db.query(models.Ecriture).filter_by(societe_id=sid).order_by(models.Ecriture.id).all()
        assert len(ecs) == n
        for ec, attendu in zip(ecs, PHASES):
            assert {l.compte: (Decimal(str(l.debit)), Decimal(str(l.credit))) for l in ec.lignes} == attendu
            assert sum(l.debit for l in ec.lignes) == sum(l.credit for l in ec.lignes)
            assert all(l.tiers_id == tid and l.compte_auxiliaire_snapshot for l in ec.lignes if l.compte == '4411')
        assert db.query(models.Article).filter_by(societe_id=sid).one().stock_actuel == stock

@pytest.mark.parametrize('largeur', [1365, 390])
def test_achat_avoir_retour_reglement_lettrage(application, largeur):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    suffix = uuid.uuid4().hex[:8]
    email, password = 'avoir-fourn-' + suffix + '@example.com', 'AvoirFournFictif2026!'
    nom, article = 'Fournisseur retour fictif ' + suffix, 'Marchandise retour fictive ' + suffix
    with httpx.Client(base_url=application['api_url']) as api:
        auth = ok(api.post('/api/auth/register', json={'nom': 'Admin fictif', 'email': email,
            'password': password, 'raison_sociale': 'Retour fournisseur fictif ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + auth['access_token']
        sid = ok(api.get('/api/societe/moi'))['id']
        tid = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'fournisseur', 'compte_fournisseur': '4411'}), 201)['id']
        aid = ok(api.post('/api/articles', json={'code': 'RET-FR-' + suffix, 'designation': article,
            'prix_achat_ht': 500, 'prix_vente_ht': 700, 'tva': 20, 'compte_achat': '6111',
            'stock_actuel': 0, 'is_stockable': True}), 201)['id']
        executable = chromium_executable()
        if not executable: pytest.skip('Edge/Chromium requis')
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                page.on('dialog', lambda d: d.accept())
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/factures')
                page.get_by_role('button', name='Nouvelle facture', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouvelle facture', exact=True)
                modal.get_by_role('button', name='Achat', exact=True).click()
                champ(modal, 'Date *').fill(date.today().isoformat())
                modal.get_by_placeholder('Rechercher un', exact=False).fill(nom)
                modal.get_by_text(nom, exact=True).click()
                modal.get_by_placeholder('Description ou article...').fill(article)
                modal.get_by_text(article, exact=True).click()
                editor = modal.locator('.hp-invoice-line-editor')
                editor.locator('input[type="number"]').nth(0).fill('2')
                editor.locator('input[type="number"]').nth(1).fill('500')
                modal.locator('summary').filter(has_text='Options commerciales & fiscales').click()
                modal.locator('select:has(option[value="charge"])').select_option('charge')
                modal.locator('label').filter(has_text='Déductible').locator('input').fill('100')
                modal.get_by_placeholder('N° porté sur la facture du fournisseur').fill('FR-RETOUR-' + suffix)
                modal.get_by_role('button', name='Enregistrer en brouillon', exact=False).click()
                with page.expect_response(lambda r: r.url.endswith('/api/factures') and r.request.method == 'POST') as created:
                    modal.get_by_role('button', name='Enregistrer le brouillon', exact=True).click()
                assert created.value.status == 201, created.value.text()
                facture = created.value.json(); fid = facture['id']
                assert facture['total_ttc'] == 1200 and facture['nature_tva_achat'] == 'charge' and facture['tva_deductible_pct'] == 100
                modal.wait_for(state='hidden')
                with Session(application['engine']) as db: assert db.get(models.Article, aid).stock_actuel == 0
                row = page.locator('tbody tr').filter(has_text=nom)
                with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/valider')) as validated:
                    row.get_by_title('Valider définitivement', exact=True).click()
                assert validated.value.status == 200, validated.value.text()
                with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/comptabiliser')) as posted:
                    row.get_by_title("Générer l'écriture comptable de cette facture", exact=True).click()
                assert posted.value.status == 200, posted.value.text()
                verifier(application, sid, tid, 1, 2)
                page.goto(application['web_url'] + '/journal')
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(1)
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as valid_ec:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert valid_ec.value.status == 200 and valid_ec.value.json()['nb_validees'] == 1
                original = originaux(application, sid)
                page.goto(application['web_url'] + '/factures')
                page.locator('tbody tr').filter(has_text=nom).click()
                page.get_by_role('button', name='Créer un avoir', exact=True).click()
                modal = page.get_by_role('dialog', name='Créer un avoir', exact=False)
                modal.get_by_placeholder('Retour marchandise, remise après facture...').fill('Retour fournisseur fictif partiel')
                modal.get_by_role('checkbox', name='Retour physique de marchandise', exact=False).check()
                l = modal.locator('tbody tr').filter(has_text=article)
                l.get_by_role('checkbox').check(); l.locator('input[type="number"]').fill('1')
                with page.expect_response(lambda r: r.url.endswith('/api/avoirs') and r.request.method == 'POST') as credited:
                    modal.get_by_role('button', name="Créer l'avoir", exact=False).click()
                assert credited.value.status == 201, credited.value.text()
                avoir = credited.value.json(); avid = avoir['id']
                assert avoir['type'] == 'achat' and avoir['retour_stock'] and avoir['total_ttc'] == 600
                modal.wait_for(state='hidden')
                verifier(application, sid, tid, 1, 2)
                assert originaux(application, sid) == original
                page.goto(application['web_url'] + '/avoirs')
                page.locator('tbody tr').filter(has_text=nom).click()
                with page.expect_response(lambda r: r.url.endswith(f'/api/avoirs/{avid}/comptabiliser')) as posted_av:
                    page.get_by_role('button', name='Comptabiliser', exact=True).last.click()
                assert posted_av.value.status == 200, posted_av.value.text()
                verifier(application, sid, tid, 2, 1)
                page.goto(application['web_url'] + '/journal')
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(1)
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as valid_av:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert valid_av.value.status == 200 and valid_av.value.json()['nb_validees'] == 1
                avant_refus = originaux(application, sid)
                assert api.post(f'/api/avoirs/{avid}/comptabiliser').status_code == 409
                avoir_exces = {'type': 'achat', 'date': date.today().isoformat(), 'tiers': nom, 'tiers_id': tid,
                    'facture_id': fid, 'retour_stock': True, 'lignes': [{'facture_ligne_id': avoir['lignes'][0]['facture_ligne_id'], 'quantite': 2}]}
                assert api.post('/api/avoirs', json=avoir_exces).status_code == 409
                assert originaux(application, sid) == avant_refus
                situation = ok(api.get(f'/api/factures/{fid}/reglements'))
                assert situation['total_avoirs'] == 600 and situation['solde_restant'] == 600
                page.goto(application['web_url'] + '/factures')
                row = page.locator('tbody tr').filter(has_text=nom)
                row.get_by_title('Payer le fournisseur', exact=True).click()
                modal = page.get_by_role('dialog')
                assert Decimal(champ(modal, 'Montant *').input_value()) == 600
                modal.get_by_placeholder('N° chèque, virement...').fill('PAIEMENT-RETOUR-' + suffix)
                with page.expect_response(lambda r: r.url.endswith('/api/reglements') and r.request.method == 'POST') as paid:
                    modal.get_by_role('button', name='Enregistrer', exact=True).click()
                assert paid.value.status == 201, paid.value.text()
                modal.wait_for(state='hidden')
                verifier(application, sid, tid, 3, 1)
                situation = ok(api.get(f'/api/factures/{fid}/reglements'))
                assert situation['total_regle'] == 600 and situation['solde_restant'] == 0
                page.goto(application['web_url'] + '/journal')
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(1)
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as valid_pay:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert valid_pay.value.status == 200 and valid_pay.value.json()['nb_validees'] == 1
                avant_lettrage = originaux(application, sid)
                assert avant_lettrage[0] == original[0]
                page.goto(application['web_url'] + '/lettrage')
                champ(page, 'Compte', 'select').select_option('4411')
                champ(page, 'Tiers', 'select').select_option(label=nom)
                playwright.expect(page.locator('tbody input[type="checkbox"]')).to_have_count(3)
                for box in page.locator('tbody input[type="checkbox"]').all(): box.check()
                with page.expect_response(lambda r: '/api/lettrage' in r.url and r.request.method == 'POST') as lettered:
                    page.get_by_role('button', name='Lettrer 3 lignes', exact=True).click()
                assert lettered.value.status == 200 and lettered.value.json()['code'] == 'AAA', lettered.value.text()
                assert originaux(application, sid) == avant_lettrage
                page.reload(); champ(page, 'Compte', 'select').select_option('4411'); champ(page, 'Tiers', 'select').select_option(label=nom)
                page.get_by_text('3 lettrée(s)', exact=True).wait_for()
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                print('Avoir fournisseur fictif :', page.url, page.locator('body').inner_text()[:5000])
                print('Erreurs navigateur/API :', errors, server_errors)
                raise
            finally: browser.close()
        with Session(application['engine']) as db:
            ecs = db.query(models.Ecriture).filter_by(societe_id=sid).all()
            lignes = [l for e in ecs for l in e.lignes]
            assert len(ecs) == 3 and len(lignes) == 8 and all(e.est_validee for e in ecs)
            assert sum(Decimal(str(l.debit)) for l in lignes) == 2400
            assert sum(Decimal(str(l.credit)) for l in lignes) == 2400
            assert {c: sum(Decimal(str(l.debit-l.credit)) for l in lignes if l.compte == c) for c in ('6111','34552','4411','5141')} == {'6111':500,'34552':100,'4411':0,'5141':-600}
            assert all(l.code_lettrage == 'AAA' for l in lignes if l.compte == '4411')
            mouvements = db.query(models.MouvementStock).filter_by(article_id=aid).order_by(models.MouvementStock.id).all()
            assert len(mouvements) == 2
            assert [(m.type, m.quantite, m.stock_avant, m.stock_apres) for m in mouvements] == [
                ('entree', 2, 0, 2), ('sortie', 1, 2, 1)]
            assert [(m.source_type, m.source_id) for m in mouvements] == [('facture', fid), ('avoir', avid)]
        ok(api.post('/api/utilisateurs', json={'nom':'Lecteur fictif','email':'lecture-'+email,'mot_de_passe':password,'role':'lecture'}),201)
        auth = ok(api.post('/api/auth/login',json={'email':'lecture-'+email,'password':password}))
        assert api.post(f'/api/avoirs/{avid}/comptabiliser',headers={'Authorization':'Bearer '+auth['access_token']}).status_code == 403
        with httpx.Client(base_url=application['api_url']) as autre:
            auth = ok(autre.post('/api/auth/register',json={'nom':'Autre fictif','email':'autre-'+email,'password':password,'raison_sociale':'Autre retour fictif '+suffix}))
            autre.headers['Authorization']='Bearer '+auth['access_token']
            assert autre.post(f'/api/avoirs/{avid}/comptabiliser').status_code == 404
        assert originaux(application,sid) == avant_lettrage

