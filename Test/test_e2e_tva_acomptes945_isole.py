"""Date effective saisie dans le vrai détail d'acompte, puis déclaration mensuelle."""
from pathlib import Path
from contextlib import closing
import json

import pytest
from playwright.sync_api import sync_playwright, expect
from test_tva_acomptes945_isole import (
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, dossier, acompte, declaration, montant, core, ok, ROOT,
)
from test_e2e_administration_isole import connexion, observer
from test_e2e_tva_isole import choisir_mois
from browser_support import chromium_executable


@pytest.mark.parametrize('role,largeur', [('admin', 1440), ('comptable', 390), ('lecture', 390)])
def test_945_date_effective_interface_droits_et_tva(application, role, largeur, tmp_path):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        sid, tiers, banque = dossier(api, application)
        ac = acompte(api, tiers, banque)
        if role != 'admin':
            email = f'{role}-{ac["id"]}-945@hisabpro-recette.example'
            ok(api.post('/api/utilisateurs', json={'nom': 'Rôle FICTIF945', 'email': email,
                'mot_de_passe': password, 'role': role}), 201)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        preuve = {'role': role, 'largeur': largeur, 'nonce': application['cluster']['nonce'], 'erreur': None}
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 1050})
            page.set_default_timeout(15000)
            errors, serveur = observer(page, application['api_url'])
            page.on('dialog', lambda d: d.accept())
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/cloture')
            page.get_by_label('Exercice actif', exact=True).select_option('2025')
            page.goto(application['web_url'] + '/acomptes')
            ligne = page.locator('tbody tr').filter(has_text=ac['numero'])
            ligne.get_by_role('button', name="Voir le détail et l'historique", exact=True).click()
            modal = page.get_by_role('dialog')
            date = modal.get_by_label('Date de l’opération', exact=True)
            if role == 'lecture':
                expect(date).to_have_count(0)
                expect(modal.get_by_role('button', name="Confirmer l'encaissement", exact=True)).to_have_count(0)
                auth = ok(api.post('/api/auth/login', json={'email': email, 'password': password}))
                refus = api.post(f'/api/acomptes/{ac["id"]}/statut-paiement',
                    headers={'Authorization': 'Bearer ' + auth['access_token']},
                    json={'statut': 'encaisse', 'date_operation': '2025-07-05'})
                assert refus.status_code == 403, refus.text
                preuve['refus_role_lecture'] = 403
                assert montant(declaration(api, 6)) == montant(declaration(api, 7)) == 0
            else:
                date.fill('2025-07-05')
                with page.expect_response(lambda r: r.request.method == 'POST' and
                        r.url.endswith(f'/api/acomptes/{ac["id"]}/statut-paiement')) as mutation:
                    modal.get_by_role('button', name="Confirmer l'encaissement", exact=True).click()
                ok(mutation.value)
                assert mutation.value.request.post_data_json['date_operation'] == '2025-07-05'
                modal.wait_for(state='hidden')
                # La liste est rafraîchie par la mutation sans F5.
                expect(ligne).not_to_contain_text('En attente')
                ligne.get_by_role('button', name="Voir le détail et l'historique", exact=True).click()
                expect(page.get_by_role('dialog')).to_contain_text('Date effective05/07/25')
                page.goto(application['web_url'] + '/declaration-tva')
                expect(page.get_by_role('heading', name='Déclaration TVA', exact=True)).to_be_visible()
                livre = core(application, sid)
                choisir_mois(page, 6, lambda v: verifier(v, 0))
                choisir_mois(page, 7, lambda v: verifier(v, 4000))
                assert core(application, sid) == livre
                preuve.update(date_effective='2025-07-05', juin=0, juillet=4000, refresh_sans_F5=True)
            assert not errors and not serveur, (errors, serveur)
            page.screenshot(path=str(ROOT/f'.codex-tests/tva945_{role}_{largeur}.png'), full_page=True)
        except BaseException as exc:
            preuve['erreur'] = repr(exc)
            raise
        finally:
            (ROOT/f'.codex-tests/tva945_ui_{role}.json').write_text(json.dumps(preuve, ensure_ascii=False, indent=2), encoding='utf8')
            browser.close()


def verifier(data, attendu):
    assert montant(data) == attendu
