"""971 — page « Paie du mois » : étapes dans l'ordre, état réel, liens vers les bons écrans. PG nonce, données fictives."""
from contextlib import closing
from pathlib import Path
from uuid import uuid4
import pytest
from playwright.sync_api import sync_playwright, expect
from browser_support import chromium_executable
from test_paie968_bulletins_isole import (
    application, application124, application123, application122, application121, application120, application119, application118, application117,
    application116, application115, application114, application113, application112, application111, application110, application109, application108,
    application107, application875, application873, application093, application092, application091, application090, application089, application087,
    migration, cles_coffre885, B, source, corps)
from test_paie919_rattachement_isole import client, ok, role_client, grant, activer, CAPS
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R = Path(__file__).resolve().parents[1]
ETAPES = ['Salariés', 'Paramètres de paie', 'Primes et variables du mois', 'Calcul du brut', 'Cotisations sociales', 'Bases fiscales',
          'Impôt sur le revenu (IR)', 'Bulletins de paie', 'Comptabilisation', 'Paiement des salaires']


def etat(page, titre):
    return page.get_by_role('list', name='Étapes de la paie du mois').locator('li').filter(
        has=page.get_by_role('heading', name=titre, exact=True))


@pytest.mark.parametrize('largeur', [1440, 390])
def test_971_paie_du_mois_suit_la_chaine_et_ouvre_les_bons_ecrans(application, largeur):
    app = application
    with closing(client(app)[0]) as admin:
        prep, u, mail, secret = role_client(app, admin, 'personnel')
        valid, v, _, _ = role_client(app, admin, 'personnel')
        with closing(prep), closing(valid):
            for uid in [u['id'], v['id']]:
                for cap in CAPS:
                    grant(admin, uid, cap)
            activer(admin)
            sid = ok(admin.get('/api/auth/me'))['societe_id']
            eq = {'a': prep, 'b': valid, 'admin': admin, 'uid': u['id'], 'bid': v['id'], 'sid': sid}
            eid, controle = source(eq)  # brut, cotisations, bases fiscales et contrôle IR de novembre 2026
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
                try:
                    page = browser.new_context(viewport={'width': largeur, 'height': 1000}).new_page()
                    page.set_default_timeout(20000)
                    erreurs, serveur = observer(page, app['api_url'])
                    connexion_personnel(page, app, mail, secret)
                    page.goto(app['web_url'] + '/personnel-paie/paie-du-mois')
                    page.get_by_label('Mois de paie', exact=True).fill('2026-11')
                    liste = page.get_by_role('list', name='Étapes de la paie du mois')
                    expect(liste.locator('li')).to_have_count(len(ETAPES))
                    for titre in ETAPES:
                        expect(etat(page, titre)).to_have_count(1)
                    for titre in ['Calcul du brut', 'Cotisations sociales', 'Bases fiscales']:
                        expect(etat(page, titre)).to_contain_text('Fait')
                    expect(etat(page, 'Bulletins de paie')).to_contain_text('À faire')
                    expect(etat(page, 'Comptabilisation')).to_contain_text('Après l’étape précédente')
                    expect(page.get_by_role('link', name='Étape suivante', exact=False)).to_be_visible()
                    # Chaque bouton ouvre un écran réel, jamais « Rubrique à venir ».
                    for titre in ETAPES:
                        page.goto(app['web_url'] + '/personnel-paie/paie-du-mois')
                        page.get_by_label('Mois de paie', exact=True).fill('2026-11')
                        lien = etat(page, titre).get_by_role('link')
                        if not lien.count():
                            continue
                        lien.click()
                        page.get_by_role('main').wait_for()
                        expect(page.get_by_role('heading', name='Rubrique à venir', exact=True)).to_have_count(0)
                        expect(page.get_by_role('region', name='Mise en service de la paie')).to_have_count(0)
                    # Le bulletin établi fait avancer la page.
                    ok(prep.post(B + '/bulletins', json=corps(controle['id'])), 201)
                    page.goto(app['web_url'] + '/personnel-paie/paie-du-mois')
                    page.get_by_label('Mois de paie', exact=True).fill('2026-11')
                    expect(etat(page, 'Comptabilisation')).to_contain_text('À faire')
                    page.screenshot(path=str(R / f'.codex-tests/paie971_{largeur}.png'), full_page=True)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    assert not erreurs and not serveur, (erreurs, serveur)
                finally:
                    browser.close()
