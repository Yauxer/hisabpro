"""976 — paie du mois en un clic depuis une société vide. Montants vérifiés à la main. PG nonce, données fictives."""
from decimal import Decimal
import pytest
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import text
from browser_support import chromium_executable
from test_paie974_validation_unique_isole import application, application131, V
from test_paie968_bulletins_isole import (
    application124, application123, application122, application121, application120, application119, application118, application117,
    application116, application115, application114, application113, application112, application111, application110, application109, application108,
    application107, application875, application873, application093, application092, application091, application090, application089, application087,
    migration, cles_coffre885, B)
from test_paie919_rattachement_isole import ok, grant, activer, CAPS
from test_ras_lecture_conservation import client
from test_paie909_bases_isole import S, dec
from test_personnel_workflow877_isole import W, creation, soumettre, approuver, proposition
from test_e2e_administration_isole import connexion, observer


def salarie(eq, m, nom, **fiche):
    e = ok(eq['a'].post(W, json=creation(m, nom=nom, date_embauche='2025-12-15', **fiche)), 201); eid = e['employe_id']
    soumettre(eq['a'], e['demande']['id'], 0); approuver(eq, e['demande']['id'], 0)
    c = proposition(eq, eid, 1, 'CONTRAT', {'type_contrat': 'CDI', 'date_effet': '2026-01-01', 'date_debut': '2026-01-01', 'reference_justificatif': 'CONTRAT-' + m})
    soumettre(eq['a'], c['id'], 1); approuver(eq, c['id'], 1); cid = ok(eq['a'].get(f'{W}/{eid}?au=2026-11-01'))['contrat']['id']
    r = proposition(eq, eid, 2, 'REMUNERATION', {'contrat_version_id': cid, 'montant': '9000.10', 'date_effet': '2026-01-01', 'periodicite': 'mensuelle', 'reference_justificatif': 'REM-' + m})
    soumettre(eq['a'], r['id'], 2); approuver(eq, r['id'], 2)
    return eid


@pytest.mark.parametrize('largeur', [1440])
def test_976_paie_du_mois_en_un_clic(application, largeur):
    app = application
    api, email, password = client(app)
    try:
        me = ok(api.get('/api/auth/me'))
        activer(api)
        for cap in [*CAPS, 'personnel.valider_regles_paie']:
            grant(api, me['id'], cap)
        ok(api.post(V, json={'active': True, 'motif': 'Petite entreprise FICTIVE976'}))
        eq = {'a': api, 'b': api, 'sid': me['societe_id']}
        complet = salarie(eq, 'P976A', 'Salarié complet FICTIF976', personnes_charge_ir=2)
        incomplet = salarie(eq, 'P976B', 'Salarié incomplet FICTIF976')
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(30000)
                dialogues = []
                page.on('dialog', lambda d: (dialogues.append(d.message), d.accept()))
                erreurs, serveur = observer(page, app['api_url'])
                connexion(page, app['web_url'], email, password)
                page.goto(app['web_url'] + '/personnel-paie/charges-sociales')
                page.get_by_role('button', name='Charger le modèle CNSS (à vérifier)', exact=True).click()
                expect(page.locator('[data-notification="succes"]')).to_contain_text('5 cotisation(s) proposée(s)')
                with app['engine'].connect() as db:
                    ids = db.scalars(text("SELECT id FROM paie_branche_sociale_versions WHERE societe_id=:s AND statut='PROPOSEE'"), {'s': me['societe_id']}).all()
                assert len(ids) == 5
                for i in ids:
                    ok(api.post(f'{S}/versions/{i}/approuver', json=dec(verification_reglementaire_confirmee=True)))
                page.goto(app['web_url'] + '/personnel-paie/paie-du-mois')
                page.get_by_label('Mois de paie', exact=True).fill('2026-11')
                page.get_by_role('button', name='Calculer la paie du mois', exact=True).click()
                resultat = page.get_by_role('region', name='Résultat du calcul du mois')
                expect(resultat).to_contain_text('Bulletins établis : 1', timeout=60000)
                ligne = resultat.locator('tbody tr').filter(has_text='Salarié complet FICTIF976')
                expect(ligne).to_contain_text('Bulletin établi')
                expect(ligne).to_contain_text('8.205,66 MAD')
                expect(resultat.locator('tbody tr').filter(has_text='Salarié incomplet FICTIF976')).to_contain_text('Personnes à charge non renseignées')
                assert any('2 916,66 DH' in d for d in dialogues)
                page.screenshot(path=str(__import__('pathlib').Path(__file__).resolve().parents[1] / '.codex-tests/paie976_resultat.png'), full_page=True)
                # Relancer ne refait pas le bulletin déjà établi.
                page.get_by_role('button', name='Calculer la paie du mois', exact=True).click()
                expect(resultat.locator('tbody tr').filter(has_text='Salarié complet FICTIF976')).to_contain_text('Déjà établi')
                assert not erreurs and not serveur, (erreurs, serveur)
            finally:
                browser.close()
        b = next(x for x in ok(api.get(B + '/bulletins', params={'annee': 2026}))['elements'] if x['employe_id'] == complet and x['statut'] == 'VALIDE')
        c = ok(api.get(f'{B}/bulletins/{b["id"]}'))['contenu']
        # 472,20 = 31,20 + 237,60 + 203,40 ; frais 25 % = 2 250,03 ; RNI 6 277,87 ; IR (5 066,888 / 12) − 100 = 322,24
        assert (c['brut'], c['cotisations_salariales'], c['rni'], c['ir_retenu'], c['net_a_payer']) == ('9000.10', '472.20', '6277.87', '322.24', '8205.66'), c
        assert c['cotisations_patronales'] == '1484.71' and Decimal(c['cout_employeur']) == Decimal('10484.81')
        with app['engine'].connect() as db:
            assert db.scalar(text("SELECT count(*) FROM paie_bulletins WHERE societe_id=:s AND employe_id=:e"), {'s': me['societe_id'], 'e': incomplet}) == 0
    finally:
        api.close()
