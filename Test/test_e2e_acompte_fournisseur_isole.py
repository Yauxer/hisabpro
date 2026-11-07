"""Avance fournisseur → facture achat → imputation → solde → lettrage réel."""
from datetime import date
from decimal import Decimal
from pathlib import Path
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_acompte_imputation_isole import application, application_base
from test_e2e_facturation_isole import champ


AVANCE = Decimal('400')
HT = Decimal('1000')
TVA = HT * Decimal('0.20')
TTC = HT + TVA
SOLDE = TTC - AVANCE
TOTAL_JOURNAL = AVANCE + TTC + AVANCE + SOLDE
PHASES = [
    {'3411': (AVANCE, Decimal(0)), '5141': (Decimal(0), AVANCE)},
    {'6111': (HT, Decimal(0)), '34552': (TVA, Decimal(0)), '4411': (Decimal(0), TTC)},
    {'4411': (AVANCE, Decimal(0)), '3411': (Decimal(0), AVANCE)},
    {'4411': (SOLDE, Decimal(0)), '5141': (Decimal(0), SOLDE)},
]


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


def verifier_phases(app, sid, tid, nombre, definitives=False):
    with Session(app['engine']) as db:
        ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).order_by(models.Ecriture.id).all()
        assert len(ecritures) == nombre
        for ec, oracle in zip(ecritures, PHASES):
            assert ec.est_validee is definitives
            assert {l.compte: (Decimal(str(l.debit)), Decimal(str(l.credit))) for l in ec.lignes} == oracle
            assert sum(Decimal(str(l.debit)) for l in ec.lignes) == sum(Decimal(str(l.credit)) for l in ec.lignes)
            assert all(l.tiers_id == tid and l.compte_auxiliaire_snapshot for l in ec.lignes if l.compte in ('3411', '4411'))


def originaux(app, sid):
    with Session(app['engine']) as db:
        rows = db.query(models.Ecriture).filter_by(societe_id=sid).order_by(models.Ecriture.id).all()
        return tuple((e.id, e.date, e.date_piece, e.reference, e.libelle, e.journal, e.exercice,
            e.source, e.est_validee, e.date_validation,
            tuple((l.id, l.compte, l.libelle, l.debit, l.credit, l.tiers_id, l.compte_auxiliaire_snapshot)
                  for l in sorted(e.lignes, key=lambda l: l.id))) for e in rows)


@pytest.mark.parametrize('largeur', [1365, 390])
def test_acompte_fournisseur_facture_solde_lettrage_permissions(application, largeur):
    suffix = uuid.uuid4().hex[:8]
    email, password = 'avance-fourn-' + suffix + '@example.com', 'AvanceFournisseurFictif!'
    nom = 'Fournisseur avances fictif ' + suffix
    with httpx.Client(base_url=application['api_url']) as api:
        reg = ok(api.post('/api/auth/register', json={'nom': 'Admin avances fournisseur', 'email': email,
            'password': password, 'raison_sociale': 'Avances fournisseur fictif ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + reg['access_token']
        sid = ok(api.get('/api/societe/moi'))['id']
        tid = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'fournisseur',
            'compte_fournisseur': '4411', 'delai_paiement': 60}), 201)['id']
        executable = chromium_executable()
        if not executable:
            pytest.skip('Microsoft Edge / Chromium requis')
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                page.on('dialog', lambda dialog: dialog.accept())
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/acomptes')
                page.get_by_role('button', name='Nouvel acompte', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouvel acompte', exact=True)
                modal.get_by_role('button', name='Acompte fournisseur versé', exact=False).click()
                modal.locator('input[role="combobox"]').fill(nom)
                modal.get_by_role('option').filter(has_text=nom).click()
                champ(modal, 'Montant (MAD)').fill(str(AVANCE))
                modal.get_by_placeholder('N° chèque, virement...').fill('AVANCE-FICTIVE-' + suffix)
                with page.expect_response(lambda r: r.url.endswith('/api/acomptes') and r.request.method == 'POST') as created:
                    modal.get_by_role('button', name='Enregistrer l’acompte', exact=True).click()
                assert created.value.status == 201, created.value.text()
                acompte = created.value.json()
                acid = acompte['id']
                assert acompte['type'] == 'fournisseur' and acompte['montant_disponible'] == float(AVANCE)
                assert acompte['est_comptabilisee']
                modal.wait_for(state='hidden')
                verifier_phases(application, sid, tid, 1)
                # Création de l'achat marchandises dans l'interface, avec compte par défaut déclaré.
                page.goto(application['web_url'] + '/factures')
                page.get_by_role('button', name='Nouvelle facture', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouvelle facture', exact=True)
                modal.get_by_role('button', name='Achat', exact=True).click()
                champ(modal, 'Date *').fill(date.today().isoformat())
                modal.get_by_placeholder('Rechercher un', exact=False).fill(nom)
                modal.get_by_text(nom, exact=True).click()
                modal.get_by_placeholder('Description ou article...').fill('Achat marchandises fictif')
                editor = modal.locator('.hp-invoice-line-editor')
                editor.locator('input[type="number"]').nth(0).fill('1')
                editor.locator('input[type="number"]').nth(1).fill(str(HT))
                modal.get_by_placeholder('N° porté sur la facture du fournisseur').fill('FR-AVANCE-FICTIVE-' + suffix)
                modal.get_by_role('button', name='Enregistrer en brouillon', exact=False).click()
                with page.expect_response(lambda r: r.url.endswith('/api/factures') and r.request.method == 'POST') as invoice:
                    modal.get_by_role('button', name='Enregistrer le brouillon', exact=True).click()
                assert invoice.value.status == 201, invoice.value.text()
                fid = invoice.value.json()['id']
                assert invoice.value.json()['total_ttc'] == float(TTC)
                modal.wait_for(state='hidden')
                row = page.locator('tbody tr').filter(has_text=nom)
                with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/valider')) as valid:
                    row.get_by_title('Valider définitivement', exact=True).click()
                assert valid.value.status == 200, valid.value.text()
                with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/comptabiliser')) as compta:
                    row.get_by_title("Générer l'écriture comptable de cette facture", exact=True).click()
                assert compta.value.status == 200, compta.value.text()
                verifier_phases(application, sid, tid, 2)
                page.goto(application['web_url'] + '/acomptes')
                row = page.locator('tbody tr').filter(has_text=nom)
                row.get_by_title('Imputer sur une facture', exact=True).click()
                modal = page.get_by_role('dialog')
                modal.locator('select').select_option(str(fid))
                playwright.expect(champ(modal, 'Montant à imputer (MAD)')).to_have_value('400.00')
                with page.expect_response(lambda r: r.url.endswith(f'/api/acomptes/{acid}/imputer')) as imputed:
                    modal.get_by_role('button', name='Imputer l’acompte', exact=True).click()
                assert imputed.value.status == 200, imputed.value.text()
                assert imputed.value.json()['montant_disponible'] == 0
                modal.wait_for(state='hidden')
                verifier_phases(application, sid, tid, 3)
                avant_doublon = originaux(application, sid)
                assert api.post(f'/api/acomptes/{acid}/imputer', json={'facture_id': fid, 'montant': 400}).status_code == 409
                assert originaux(application, sid) == avant_doublon
                page.goto(application['web_url'] + '/factures')
                row = page.locator('tbody tr').filter(has_text=nom)
                row.get_by_title('Payer le fournisseur', exact=True).click()
                modal = page.get_by_role('dialog')
                assert Decimal(champ(modal, 'Montant *').input_value()) == SOLDE
                modal.get_by_placeholder('N° chèque, virement...').fill('SOLDE-FICTIF-' + suffix)
                with page.expect_response(lambda r: r.url.endswith('/api/reglements') and r.request.method == 'POST') as paid:
                    modal.get_by_role('button', name='Enregistrer', exact=True).click()
                assert paid.value.status == 201, paid.value.text()
                modal.wait_for(state='hidden')
                verifier_phases(application, sid, tid, 4)
                situation = ok(api.get(f'/api/factures/{fid}/reglements'))
                assert situation['total_acomptes'] == float(AVANCE) and situation['total_regle'] == float(SOLDE)
                assert situation['solde_restant'] == 0
                page.goto(application['web_url'] + '/journal')
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(4)
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as official:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert official.value.status == 200 and official.value.json()['nb_validees'] == 4
                verifier_phases(application, sid, tid, 4, definitives=True)
                avant_lettrage = originaux(application, sid)
                page.goto(application['web_url'] + '/lettrage')
                champ(page, 'Compte', 'select').select_option('4411')
                champ(page, 'Tiers', 'select').select_option(label=nom)
                playwright.expect(page.locator('tbody input[type="checkbox"]')).to_have_count(3)
                for box in page.locator('tbody input[type="checkbox"]').all():
                    box.check()
                with page.expect_response(lambda r: '/api/lettrage' in r.url and r.request.method == 'POST') as lettered:
                    page.get_by_role('button', name='Lettrer 3 lignes', exact=True).click()
                assert lettered.value.status == 200, lettered.value.text()
                assert lettered.value.json()['code'] == 'AAA'
                page.get_by_text('3 lettrée(s)', exact=True).wait_for()
                assert originaux(application, sid) == avant_lettrage
                page.reload()
                champ(page, 'Compte', 'select').select_option('4411')
                champ(page, 'Tiers', 'select').select_option(label=nom)
                page.get_by_text('3 lettrée(s)', exact=True).wait_for()
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                print('Acompte fournisseur fictif :', page.url, page.locator('body').inner_text()[:8000])
                print('Erreurs :', errors, server_errors)
                preuve = Path(__file__).resolve().parents[1] / '.codex-tests' / f'acompte_fournisseur_{largeur}_{suffix}.png'
                page.screenshot(path=str(preuve))
                print('Capture fictive :', preuve)
                action = page.get_by_title('Valider définitivement', exact=True)
                if action.count() == 1:
                    print('Géométrie action :', action.evaluate("e => {const r=e.getBoundingClientRect();return {rect:{x:r.x,y:r.y,w:r.width,h:r.height},hit:document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.outerHTML.slice(0,800),parents:Array.from((function*(v){while(v){yield v;v=v.parentElement}})(e)).slice(0,7).map(v=>({tag:v.tagName,cls:v.className,scrollLeft:v.scrollLeft,clientWidth:v.clientWidth,scrollWidth:v.scrollWidth,overflow:getComputedStyle(v).overflow}))}}"))
                raise
            finally:
                browser.close()
        with Session(application['engine']) as db:
            avance_db = db.get(models.Acompte, acid)
            imputation_db = db.query(models.ImputationAcompte).filter_by(societe_id=sid, acompte_id=acid).one()
            assert avance_db.statut == 'impute' and avance_db.est_imputee_compta
            assert imputation_db.facture_id == fid and Decimal(str(imputation_db.montant)) == AVANCE
            assert imputation_db.statut == 'active' and imputation_db.est_comptabilisee
            assert db.query(models.Reglement).filter_by(societe_id=sid, facture_id=fid).count() == 1
            lignes = db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid).all()
            assert len(lignes) == 9
            assert sum(Decimal(str(l.debit)) for l in lignes) == TOTAL_JOURNAL
            assert sum(Decimal(str(l.credit)) for l in lignes) == TOTAL_JOURNAL
            soldes = {c: sum(Decimal(str(l.debit)) - Decimal(str(l.credit)) for l in lignes if l.compte == c)
                      for c in ('3411', '4411', '5141', '6111', '34552')}
            assert soldes == {'3411': 0, '4411': 0, '5141': -TTC, '6111': HT, '34552': TVA}
            assert all(l.code_lettrage == 'AAA' for l in lignes if l.compte == '4411')
        # Autorisations et périmètre société, avec même oracle comptable figé.
        ok(api.post('/api/utilisateurs', json={'nom': 'Lecteur avances', 'email': 'lecture-' + email,
            'mot_de_passe': password, 'role': 'lecture'}), 201)
        avec_lecture = ok(api.post('/api/auth/login', json={'email': 'lecture-' + email, 'password': password}))
        headers_lecture = {'Authorization': 'Bearer ' + avec_lecture['access_token']}
        assert api.get(f'/api/acomptes?exercice={date.today().year}', headers=headers_lecture).status_code == 200
        assert api.post(f'/api/acomptes/{acid}/imputer', json={'facture_id': fid, 'montant': 1}, headers=headers_lecture).status_code == 403
        with httpx.Client(base_url=application['api_url']) as autre:
            reg_b = ok(autre.post('/api/auth/register', json={'nom': 'Autre admin fictif', 'email': 'autre-' + email,
                'password': password, 'raison_sociale': 'Autre société avance ' + suffix}))
            autre.headers['Authorization'] = 'Bearer ' + reg_b['access_token']
            assert ok(autre.get(f'/api/acomptes?exercice={date.today().year}')) == []
            assert autre.get(f'/api/acomptes/{acid}/factures-imputables').status_code == 404
            assert autre.post(f'/api/acomptes/{acid}/imputer', json={'facture_id': fid, 'montant': 1}).status_code == 404
        assert originaux(application, sid) == avant_lettrage
