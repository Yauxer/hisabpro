"""Délai explicite et échéance manuelle : navigateur + API réels, fin de mois."""
from datetime import date, timedelta
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_facturation_isole import application, champ
from test_e2e_administration_isole import connexion, observer


@pytest.mark.parametrize('jour', ['01-31', '02-28'])
def test_creation_edition_delais_et_echeances_manuelles(application, jour):
    playwright = pytest.importorskip('playwright.sync_api')
    suffix = uuid.uuid4().hex[:8]
    email, password = suffix + '@example.com', 'Echeance2026!'
    base = date.fromisoformat(f'{date.today().year}-{jour}')
    echeance = lambda d, jours: (d + timedelta(days=jours)).isoformat()
    with httpx.Client(base_url=application['api_url']) as api:
        r = api.post('/api/auth/register', json={'nom': 'Administrateur fictif', 'email': email,
            'password': password, 'raison_sociale': 'Échéances fictives ' + suffix})
        assert r.status_code == 200, r.text
        api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        nom = 'Client délai fictif ' + suffix
        r = api.post('/api/tiers', json={'nom': nom, 'type': 'client', 'delai_paiement': 60})
        assert r.status_code == 201, r.text
        autre = nom + ' comptant'
        r = api.post('/api/tiers', json={'nom': autre, 'type': 'client', 'delai_paiement': 0})
        assert r.status_code == 201, r.text
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': 1440, 'height': 1000})
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/factures')
                page.get_by_role('button', name='Nouvelle facture', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouvelle facture', exact=True)
                date_input = champ(modal, 'Date *')
                date_input.fill(base.isoformat())
                tiers = modal.get_by_placeholder('Rechercher un', exact=False)
                tiers.fill(nom); modal.get_by_text(nom, exact=True).click()
                delai = modal.get_by_label('Délai de paiement de la nouvelle facture', exact=True)
                fin = modal.get_by_label('Échéance de la nouvelle facture', exact=True)
                playwright.expect(fin).to_have_value(echeance(base, 60))
                tiers.fill(autre); modal.get_by_text(autre, exact=True).click()
                playwright.expect(fin).to_have_value(base.isoformat())
                tiers.fill(nom); modal.get_by_text(nom, exact=True).click()
                playwright.expect(fin).to_have_value(echeance(base, 60))
                manuelle = echeance(base, 90)
                fin.fill(manuelle)
                base_modifiee = base + timedelta(days=1)
                date_input.fill(base_modifiee.isoformat())
                playwright.expect(fin).to_have_value(manuelle)
                for jours in [30, 0, 60]:
                    delai.fill(str(jours))
                    playwright.expect(fin).to_have_value(echeance(base_modifiee, jours))
                fin.fill(manuelle)
                tiers.fill(autre); modal.get_by_text(autre, exact=True).click()
                playwright.expect(fin).to_have_value(manuelle)
                delai.fill('30')
                playwright.expect(fin).to_have_value(echeance(base_modifiee, 30))
                modal.get_by_placeholder('Description ou article...').fill('Service fictif délai')
                editor = modal.locator('.hp-invoice-line-editor')
                editor.locator('input[type="number"]').nth(0).fill('1')
                editor.locator('input[type="number"]').nth(1).fill('100')
                modal.get_by_role('button', name='Enregistrer en brouillon', exact=False).click()
                with page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/api/factures')) as creation:
                    modal.get_by_role('button', name='Enregistrer le brouillon', exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                fid = creation.value.json()['id']
                modal.wait_for(state='hidden')
                assert creation.value.json()['date_echeance'] == echeance(base_modifiee, 30)
                page.locator('tbody tr').filter(has_text=autre).locator('button[title="Modifier le brouillon"]').click()
                modal = page.get_by_role('dialog')
                delai = modal.get_by_label('Délai de paiement de la facture', exact=True)
                fin = modal.get_by_label('Échéance de la facture', exact=True)
                # L'échéance enregistrée n'est pas réinterprétée au montage.
                playwright.expect(fin).to_have_value(echeance(base_modifiee, 30))
                manuel_edit = echeance(base_modifiee, 100)
                fin.fill(manuel_edit)
                date_edit = base_modifiee + timedelta(days=1)
                champ(modal, 'Date *').fill(date_edit.isoformat())
                playwright.expect(fin).to_have_value(manuel_edit)
                for jours in [60, 30, 0]:
                    delai.fill(str(jours))
                    playwright.expect(fin).to_have_value(echeance(date_edit, jours))
                with page.expect_response(lambda r: r.request.method == 'PATCH' and r.url.endswith(f'/api/factures/{fid}')) as sauvegarde:
                    modal.get_by_role('button', name='Enregistrer les modifications', exact=False).click()
                assert sauvegarde.value.status == 200, sauvegarde.value.text()
                modal.wait_for(state='hidden')
                r = api.get('/api/factures', params={'exercice': base.year})
                assert r.status_code == 200, r.text
                f = next(f for f in r.json() if f['id'] == fid)
                assert f['date'] == f['date_echeance'] == date_edit.isoformat()
                assert f['delai_paiement'] == 0 and not f['est_validee']
                with Session(application['engine']) as db:
                    assert db.query(models.Ecriture).filter_by(societe_id=db.get(models.Facture, fid).societe_id).count() == 0
                assert not errors and not server_errors, (errors, server_errors)
            finally:
                browser.close()
