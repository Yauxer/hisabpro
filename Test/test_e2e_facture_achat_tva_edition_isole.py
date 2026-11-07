"""Édition de TVA achat par navigateur réel sur PostgreSQL nonce."""
from datetime import date
from decimal import Decimal
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import models
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_acompte_imputation_isole import application, application_base
from test_e2e_acompte_fournisseur_isole import ok
from test_e2e_avoir_fournisseur_isole import originaux
from test_e2e_facturation_isole import champ


@pytest.mark.parametrize('largeur', [1365, 390])
def test_edition_qualification_tva_achat(application, largeur):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    suffix = uuid.uuid4().hex[:8]
    email, password = f'tva-edit-{suffix}@example.com', 'TvaEditionFictive2026!'
    nom = 'Fournisseur TVA fictif ' + suffix
    with httpx.Client(base_url=application['api_url']) as api:
        auth = ok(api.post('/api/auth/register', json={'nom': 'Recette TVA', 'email': email,
            'password': password, 'raison_sociale': 'TVA édition fictive ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + auth['access_token']
        sid = ok(api.get('/api/societe/moi'))['id']
        tid = ok(api.post('/api/tiers', json={'nom': nom, 'type': 'les_deux'}), 201)['id']
        def creer(type_doc='achat'):
            return ok(api.post('/api/factures', json={'type': type_doc, 'date': date.today().isoformat(),
                'tiers': nom, 'tiers_id': tid, 'nature_tva_achat': 'charge', 'tva_deductible_pct': 100,
                'lignes': [{'description': 'Service fictif TVA', 'quantite': 2, 'prix_unitaire': 500,
                    'tva': 20, 'qualification_tva': 'taxable'}]}), 201)['id']
        fid = creer()
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
                def ouvrir(id_facture):
                    page.goto(application['web_url'] + '/factures')
                    row = page.locator('tbody tr').filter(has_text=f'Brouillon #{id_facture}')
                    row.get_by_title('Modifier le brouillon', exact=True).click()
                    return page.get_by_role('dialog', name=f'Modifier — Brouillon #{id_facture}', exact=True)
                def sauvegarder(modal, id_facture):
                    with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{id_facture}') and r.request.method == 'PATCH') as saved:
                        modal.get_by_role('button', name='Enregistrer les modifications', exact=True).click()
                    assert saved.value.status == 200, saved.value.text()
                    payload = saved.value.request.post_data_json
                    modal.wait_for(state='hidden')
                    return payload
                modal = ouvrir(fid)
                nature = modal.get_by_label('Qualification TVA de l’achat', exact=True)
                pct = modal.get_by_label('TVA déductible (%)', exact=True)
                playwright.expect(nature).to_have_value('charge')
                playwright.expect(pct).to_have_value('100')
                nature.select_option('charge'); pct.fill('80')
                champ(modal, 'N° facture fournisseur').fill('FR-TVA-' + suffix)
                payload = sauvegarder(modal, fid)
                assert payload['nature_tva_achat'] == 'charge' and payload['tva_deductible_pct'] == 80
                modal = ouvrir(fid)
                playwright.expect(modal.get_by_label('TVA déductible (%)', exact=True)).to_have_value('80')
                requests = []
                page.on('request', lambda r: requests.append(r.url) if r.method == 'PATCH' else None)
                pct = modal.get_by_label('TVA déductible (%)', exact=True)
                pct.fill('1e309')
                modal.get_by_role('button', name='Enregistrer les modifications', exact=True).click()
                playwright.expect(modal).to_contain_text('pourcentage fini entre 0 et 100')
                assert requests == []
                pct.fill('80')
                modal.get_by_role('button', name='Annuler', exact=True).click()
                row = page.locator('tbody tr').filter(has_text=f'Brouillon #{fid}')
                with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/valider')) as validated:
                    row.get_by_title('Valider définitivement', exact=True).click()
                assert validated.value.status == 200, validated.value.text()
                with page.expect_response(lambda r: r.url.endswith(f'/api/factures/{fid}/comptabiliser')) as posted:
                    page.locator('tbody tr').filter(has_text=nom).get_by_title("Générer l'écriture comptable de cette facture", exact=True).click()
                assert posted.value.status == 200, posted.value.text()
                page.goto(application['web_url'] + '/journal')
                playwright.expect(page.get_by_role('button', name='Valider', exact=True)).to_have_count(1)
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures/valider-lot')) as valid_ec:
                    page.get_by_role('button', name='Valider les brouillons', exact=True).click()
                assert valid_ec.value.status == 200 and valid_ec.value.json()['nb_validees'] == 1
                with Session(application['engine']) as db:
                    ec = db.query(models.Ecriture).filter_by(societe_id=sid).one()
                    totals = {}
                    for l in ec.lignes:
                        debit, credit = totals.get(l.compte, (Decimal(0), Decimal(0)))
                        totals[l.compte] = debit + Decimal(str(l.debit)), credit + Decimal(str(l.credit))
                    assert totals == {'6111': (Decimal('1040'), 0), '34552': (Decimal('160'), 0), '4411': (0, Decimal('1200'))}
                    assert ec.est_validee
                original = originaux(application, sid)
                assert api.patch(f'/api/factures/{fid}', json={'nature_tva_achat': 'non_deductible', 'tva_deductible_pct': 0}).status_code == 409
                assert originaux(application, sid) == original
                page.goto(application['web_url'] + '/factures')
                assert page.locator('tbody tr').filter(has_text=nom).get_by_title('Modifier le brouillon', exact=True).count() == 0
                # Nouveau brouillon : choix explicite non déductible impose le zéro existant.
                non_ded = creer()
                modal = ouvrir(non_ded)
                modal.get_by_label('Qualification TVA de l’achat', exact=True).select_option('non_deductible')
                pct = modal.get_by_label('TVA déductible (%)', exact=True)
                playwright.expect(pct).to_have_value('0'); playwright.expect(pct).to_be_disabled()
                payload = sauvegarder(modal, non_ded)
                assert payload['nature_tva_achat'] == 'non_deductible' and payload['tva_deductible_pct'] == 0
                with Session(application['engine']) as db:
                    f = db.get(models.Facture, non_ded)
                    assert f.nature_tva_achat == 'non_deductible' and f.tva_deductible_pct == 0
                # Historique incomplet uniquement dans le cluster gardé, sans donnée réelle.
                historique = creer()
                with Session(application['engine']) as db:
                    f = db.get(models.Facture, historique)
                    f.nature_tva_achat = None; f.tva_deductible_pct = None; db.commit()
                modal = ouvrir(historique)
                playwright.expect(modal).to_contain_text('Qualification historique inconnue')
                playwright.expect(modal.get_by_label('TVA déductible (%)', exact=True)).to_have_value('')
                champ(modal, 'N° facture fournisseur').fill('HIST-TVA-' + suffix)
                payload = sauvegarder(modal, historique)
                assert 'nature_tva_achat' not in payload and 'tva_deductible_pct' not in payload
                with Session(application['engine']) as db:
                    f = db.get(models.Facture, historique)
                    assert f.nature_tva_achat is None and f.tva_deductible_pct is None
                # Valeurs historiques finies mais invalides : ni faux zéro ni clamp.
                invalide = creer()
                with Session(application['engine']) as db:
                    f = db.get(models.Facture, invalide)
                    controle_sql = db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='public.factures'::regclass AND conname='ck_facture_tva_deductible_pct')"))
                    if controle_sql:
                        # Depuis094, cette injection n'est plus un historique
                        # constructible : exiger son refus et son rollback.
                        # Le casNULL historique est réellement parcouru ci-dessus.
                        with pytest.raises(IntegrityError):
                            f.nature_tva_achat = 'ancienne_inconnue'; f.tva_deductible_pct = 150; db.commit()
                        db.rollback();db.refresh(f)
                        assert f.nature_tva_achat=='charge' and f.tva_deductible_pct==100
                    else:
                        f.nature_tva_achat = 'ancienne_inconnue'; f.tva_deductible_pct = 150; db.commit()
                if not controle_sql:
                    modal = ouvrir(invalide)
                    playwright.expect(modal).to_contain_text('Qualification historique inconnue')
                    playwright.expect(modal.get_by_label('Qualification TVA de l’achat', exact=True)).to_have_value('')
                    playwright.expect(modal.get_by_label('TVA déductible (%)', exact=True)).to_have_value('')
                    champ(modal, 'N° facture fournisseur').fill('INVALID-TVA-' + suffix)
                    payload = sauvegarder(modal, invalide)
                    assert 'nature_tva_achat' not in payload and 'tva_deductible_pct' not in payload
                    with Session(application['engine']) as db:
                        f = db.get(models.Facture, invalide)
                        assert f.nature_tva_achat == 'ancienne_inconnue' and f.tva_deductible_pct == 150
                vente = creer('vente')
                modal = ouvrir(vente)
                assert modal.get_by_label('Qualification TVA de l’achat', exact=True).count() == 0
                modal.get_by_role('button', name='Annuler', exact=True).click()
                assert originaux(application, sid) == original
                assert not errors and not server_errors, (errors, server_errors)
            finally:
                browser.close()

