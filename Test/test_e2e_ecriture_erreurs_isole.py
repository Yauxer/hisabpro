"""Erreurs réelles de saisie : aucune réponse fabriquée, aucune compta réelle."""
from datetime import date
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ


@pytest.mark.parametrize('societe', ['A', 'B'])
def test_creation_ecriture_erreurs_422_libelles_et_comptes_isoles(application, societe):
    suffix = uuid.uuid4().hex[:8]
    nom = f'Recette erreurs {societe} {suffix}'
    email, password = f'erreurs-{suffix}@example.com', 'EcritureErreurs2026!'
    label = f'Banque société {societe} — libellé exact {suffix}'
    with httpx.Client(base_url=application['api_url']) as api:
        register = api.post('/api/auth/register', json={'nom': 'Administrateur recette', 'email': email,
                          'password': password, 'raison_sociale': nom})
        assert register.status_code == 200, register.text
        api.headers['Authorization'] = 'Bearer ' + register.json()['access_token']
        company = api.get('/api/societe/moi').json()
        sid = company['id']
        modif = api.patch('/api/plan-comptable/5141', json={'libelle': label})
        assert modif.status_code == 200, modif.text
        # Un compte privé de l'autre société ne devient pas un compte autorisé.
        with httpx.Client(base_url=application['api_url']) as autre:
            compte_b = autre.post('/api/auth/register', json={'nom': 'Autre administrateur',
                'email': f'autre-erreurs-{suffix}@example.com', 'password': password, 'raison_sociale': 'Autre société ' + suffix})
            assert compte_b.status_code == 200, compte_b.text
            autre.headers['Authorization'] = 'Bearer ' + compte_b.json()['access_token']
            label_autre = 'Banque privée autre société ' + suffix
            assert autre.patch('/api/plan-comptable/5141', json={'libelle': label_autre}).status_code == 200
            subdivision = autre.post('/api/plan-comptable', json={'numero': '51419', 'libelle': 'Subdivision privée autre société', 'type_compte': 'SP'})
            assert subdivision.status_code == 201, subdivision.text
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Microsoft Edge / Chromium requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(15000)
                errors, server_errors = observer(page, application['api_url'])
                posts = []
                page.on('request', lambda r: posts.append(r.post_data_json) if r.url.endswith('/api/ecritures') and r.method == 'POST' else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/journal')
                page.get_by_role('button', name='Nouvelle écriture', exact=True).click()
                modal = page.get_by_role('dialog')
                champ(modal, 'Journal *', 'select').select_option('BQ')
                champ(modal, 'Date comptable').fill(date.today().isoformat())
                lignes = modal.locator('tbody tr')
                playwright.expect(lignes).to_have_count(3)
                lignes.nth(0).get_by_placeholder('Ex: 6111').fill('ABC')
                lignes.nth(1).get_by_placeholder('Ex: 6111').fill('DEF')
                lignes.nth(0).locator('td[data-label="Débit (MAD)"] input').fill('100')
                lignes.nth(1).locator('td[data-label="Crédit (MAD)"] input').fill('100')
                champ(modal, "Libellé de l'écriture").fill('Erreur fictive sans écriture enregistrée')
                modal.get_by_label('Valider immédiatement', exact=False).check()
                bouton = modal.get_by_role('button', name="Enregistrer l'écriture", exact=True)
                playwright.expect(bouton).to_be_enabled()
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures') and r.request.method == 'POST') as rejet:
                    bouton.click()
                assert rejet.value.status == 422, rejet.value.text()
                detail = rejet.value.json()['detail']
                assert isinstance(detail, list) and len(detail) == 2, detail
                assert {tuple(e['loc']) for e in detail} == {('body', 'lignes', 0, 'compte'), ('body', 'lignes', 1, 'compte')}
                modal.get_by_text('Numéro de compte invalide', exact=False).wait_for()
                texte = modal.inner_text()
                assert 'lignes.0.compte' in texte and 'lignes.1.compte' in texte
                assert '[object object]' not in texte.lower()
                assert posts[-1]['est_validee'] is True
                with Session(application['engine']) as db:
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
                playwright.expect(lignes.nth(0).get_by_placeholder('Ex: 6111')).to_have_value('ABC')
                playwright.expect(lignes.nth(1).locator('td[data-label="Crédit (MAD)"] input')).to_have_value('100')
                # Libellé automatique identique au plan société, sans celui du voisin.
                lignes.nth(0).get_by_placeholder('Ex: 6111').fill('5141')
                lignes.nth(1).get_by_placeholder('Ex: 6111').fill('1111')
                champ(modal, "Libellé de l'écriture").click()
                playwright.expect(lignes.nth(0).get_by_label('Libellé du compte', exact=True)).to_have_value(label)
                assert label_autre not in modal.inner_text()
                assert lignes.nth(0).get_by_label('Libellé du compte', exact=True).is_editable() is False
                lignes.nth(1).locator('td[data-label="Crédit (MAD)"] input').fill('101')
                playwright.expect(bouton).to_be_disabled()
                assert len(posts) == 1
                # Numéro valide dans le schéma mais privé à une autre société :
                # vrai rejet métier 400, jamais une création implicite dans A.
                lignes.nth(1).locator('td[data-label="Crédit (MAD)"] input').fill('100')
                lignes.nth(0).get_by_placeholder('Ex: 6111').fill('51419')
                champ(modal, "Libellé de l'écriture").fill('Compte privé étranger refusé')
                playwright.expect(bouton).to_be_enabled()
                with page.expect_response(lambda r: r.url.endswith('/api/ecritures') and r.request.method == 'POST') as refus_compte:
                    bouton.click()
                assert refus_compte.value.status == 400, refus_compte.value.text()
                modal.get_by_text('Compte(s) absent(s) ou désactivé(s)', exact=False).wait_for()
                assert '[object object]' not in modal.inner_text().lower()
                assert len(posts) == 2
                assert not errors, errors
                assert not server_errors, server_errors
                assert api.get(f'/api/ecritures?exercice={date.today().year}').json() == []
                with Session(application['engine']) as db:
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
                    assert db.query(models.CompteSociete).filter_by(societe_id=sid, numero='51419').count() == 0
            except Exception:
                print('Écran erreurs fictives :', page.url, page.locator('body').inner_text()[:7500])
                print('Erreurs :', errors, server_errors)
                raise
            finally:
                browser.close()
