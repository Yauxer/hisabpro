"""968 — parcours navigateur : menu Paie sans numéros, avance, bulletin, comptabilisation, paiement, états. PG nonce, données fictives."""
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
    migration, cles_coffre885, B, source)
from test_paie919_rattachement_isole import client, ok, role_client, grant, activer, CAPS
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R = Path(__file__).resolve().parents[1]
SECTIONS = ['Bulletins de paie', 'Avances & prêts', 'Paiements', 'Comptabilisation', 'États & reporting']


@pytest.mark.parametrize('largeur', [1440, 390])
def test_968_bulletin_avance_et_etats_dans_le_navigateur(application, largeur):
    app = application
    with closing(client(app)[0]) as admin:
        prep, u, mail, secret = role_client(app, admin, 'personnel')
        valid, v, _, _ = role_client(app, admin, 'personnel')
        with closing(prep), closing(valid):
            moi = ok(admin.get('/api/auth/me'))['id']  # l'admin comptabilise : habilitations Personnel requises
            for uid in [u['id'], v['id'], moi]:
                for cap in CAPS:
                    grant(admin, uid, cap)
            activer(admin)
            sid = ok(admin.get('/api/auth/me'))['societe_id']
            eq = {'a': prep, 'b': valid, 'admin': admin, 'uid': u['id'], 'bid': v['id'], 'sid': sid}
            eid, controle = source(eq)
            nom = controle['contenu']['nom']
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
                try:
                    page = browser.new_context(viewport={'width': largeur, 'height': 1000}).new_page()
                    page.set_default_timeout(20000)
                    dialogues = []
                    page.on('dialog', lambda d: (dialogues.append(d.message), d.accept('Motif fictif968') if d.type == 'prompt' else d.accept()))
                    erreurs, serveur = observer(page, app['api_url'])
                    connexion_personnel(page, app, mail, secret)
                    # Menu : plus de numéros ni d'entrées « À venir ».
                    if largeur < 768:
                        page.get_by_role('button', name='Ouvrir la navigation', exact=True).click()
                    nav = page.get_by_role('complementary', name='Navigation principale')
                    for libelle in ['Personnel', 'Traitement de la paie', *SECTIONS]:
                        expect(nav.get_by_role('link', name=libelle, exact=True)).to_be_visible()
                    expect(nav.get_by_text('À venir', exact=True)).to_have_count(0)
                    assert '01 ·' not in nav.inner_text()
                    nav.get_by_role('link', name='Avances & prêts', exact=True).click()
                    page.wait_for_url('**/personnel-paie/avances')
                    # Avance de 1 000 MAD, retenue mensuelle 250.
                    page.get_by_role('button', name='Nouvelle avance ou prêt', exact=True).click()
                    d = page.get_by_role('dialog')
                    d.get_by_label('Salarié', exact=True).select_option(str(eid))
                    d.get_by_label('Montant (MAD)', exact=True).fill('1000.00')
                    d.get_by_label('Retenue mensuelle prévue (MAD)', exact=True).fill('250.00')
                    d.get_by_label('Motif', exact=True).fill('Avance fictive968')
                    d.get_by_role('button', name='Enregistrer', exact=True).click()
                    expect(d).to_have_count(0)
                    ligne = page.get_by_role('table', name='Avances et prêts').locator('tbody tr').filter(has_text=nom).first
                    expect(ligne).to_contain_text('Non comptabilisée')
                    # Bulletin : net estimé recalculé avec la retenue proposée.
                    page.goto(app['web_url'] + '/personnel-paie/bulletins')
                    page.get_by_role('button', name='Établir un bulletin', exact=True).click()
                    d = page.get_by_role('dialog')
                    d.get_by_label('Contrôle IR mensuel (salarié et mois)', exact=True).select_option(str(controle['id']))
                    expect(d.get_by_label('IR à retenir (MAD)', exact=True)).to_have_value('497.02')
                    expect(d.get_by_test_id('net-estime')).to_contain_text('8')
                    d.get_by_label('Motif', exact=True).fill('Bulletin fictif968')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    d.get_by_role('button', name='Valider le bulletin', exact=True).click()
                    expect(d).to_have_count(0)
                    expect(page.locator('[data-notification="succes"]')).to_contain_text('Bulletin établi')
                    expect(page.get_by_test_id('net-bulletin')).to_contain_text('8')
                    page.locator('.bulletin-imprimable').screenshot(path=str(R / f'.codex-tests/paie968_bulletin_{largeur}.png'))
                    b = next(x for x in ok(prep.get(B + '/bulletins', params={'annee': 2026}))['elements'] if x['employe_id'] == eid)
                    assert b['total_avances'] == '250.00' and float(b['net_a_payer']) == round(float(b['brut']) - float(b['cotisations_salariales']) - 497.02 - 250, 2)
                    # Comptabilisation et paiement par l'administrateur (API), puis états à jour sans F5.
                    r = ok(admin.post(B + '/comptabiliser', json={'periode': '2026-11-01', 'date_ecriture': '2026-11-30'}), 201)
                    ok(admin.post(B + '/paiements', json={'bulletin_ids': [b['id']], 'date_paiement': '2026-12-02', 'mode': 'virement'}), 201)
                    page.goto(app['web_url'] + '/personnel-paie/etats')
                    recap = page.get_by_role('table', name='Récapitulatif mensuel de la paie')
                    expect(recap.locator('tr').filter(has_text='2026-11')).to_contain_text('comptabilisés')
                    livre = page.get_by_role('region', name='Livre de paie').locator('tbody tr').filter(has_text=nom)
                    expect(livre.first).to_contain_text('Paiement en brouillon')
                    with page.expect_download() as tele:
                        page.get_by_role('button', name='Exporter le livre de paie (CSV)', exact=True).click()
                    assert tele.value.suggested_filename == 'livre_de_paie_2026.csv'
                    page.goto(app['web_url'] + '/personnel-paie/comptabilisation')
                    expect(page.get_by_role('table', name='Comptabilisation par mois')).to_contain_text('Comptabilisé')
                    assert r['ecriture_id']
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    assert not erreurs and not serveur, (erreurs, serveur)
                except Exception:
                    page.screenshot(path=str(R / f'.codex-tests/paie968_echec_{largeur}.png'))
                    print('Écran 968', page.url, page.locator('body').inner_text()[:1500], erreurs, serveur)
                    raise
                finally:
                    browser.close()
