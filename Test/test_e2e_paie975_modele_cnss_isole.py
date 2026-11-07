"""975 — modèle CNSS chargé depuis l'écran, approuvé, puis cotisations calculées et vérifiées à la main. PG nonce, données fictives."""
from uuid import uuid4
import pytest
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import text
from browser_support import chromium_executable
from test_paie974_validation_unique_isole import application, application131, V
from test_paie968_bulletins_isole import (
    application124, application123, application122, application121, application120, application119, application118, application117,
    application116, application115, application114, application113, application112, application111, application110, application109, application108,
    application107, application875, application873, application093, application092, application091, application090, application089, application087,
    migration, cles_coffre885)
from test_paie919_rattachement_isole import ok, grant, activer, CAPS
from test_ras_lecture_conservation import client
from test_paie909_bases_isole import S, dec
from test_paie893_campagnes_isole import salarie, simuler as brut
from test_e2e_administration_isole import connexion, observer

C = '/api/employes/personnel/social/simulations'


@pytest.mark.parametrize('largeur', [1440])
def test_975_modele_cnss_charge_approuve_et_calcul_exact(application, largeur):
    app = application
    api, email, password = client(app)
    try:
        me = ok(api.get('/api/auth/me'))
        activer(api)
        for cap in [*CAPS, 'personnel.valider_regles_paie']:
            grant(api, me['id'], cap)
        ok(api.post(V, json={'active': True, 'motif': 'Petite entreprise FICTIVE975'}))
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(20000)
                dialogues = []
                page.on('dialog', lambda d: (dialogues.append(d.message), d.accept()))
                erreurs, serveur = observer(page, app['api_url'])
                connexion(page, app['web_url'], email, password)
                page.goto(app['web_url'] + '/personnel-paie/charges-sociales')
                page.get_by_role('button', name='Charger le modèle CNSS (à vérifier)', exact=True).click()
                expect(page.locator('[data-notification="succes"]')).to_contain_text('5 cotisation(s) proposée(s)')
                assert dialogues and '2.26 % salarié' in dialogues[0] and 'cnss.ma' in dialogues[0]
                for code in ['CNSS_PS_COURT_TERME', 'CNSS_PS_LONG_TERME', 'CNSS_ALLOCATIONS_FAMILIALES', 'CNSS_AMO', 'CNSS_AMO_SOLIDARITE']:
                    expect(page.get_by_role('region', name=f'Branche CNSS {code}', exact=True)).to_be_visible()
                assert not erreurs and not serveur, (erreurs, serveur)
            finally:
                browser.close()
        # Approbation par le même administrateur (validation unique), contenus tels que chargés.
        with app['engine'].connect() as db:
            versions = db.execute(text("SELECT v.id, b.code, v.contenu FROM paie_branche_sociale_versions v JOIN paie_branches_sociales b ON b.id=v.branche_id "
                                       "WHERE v.societe_id=:s AND v.statut='PROPOSEE' ORDER BY b.code"), {'s': me['societe_id']}).mappings().all()
        assert len(versions) == 5 and all(v['contenu']['statut_reglementaire'] == 'A_VERIFIER' and 'cnss.ma' in v['contenu']['url_source']
                                         and v['contenu']['deductibilite_ir']['article'].startswith('article 59') for v in versions)
        for v in versions:
            ok(api.post(f'{S}/versions/{v["id"]}/approuver', json=dec(verification_reglementaire_confirmee=True)))
        # Salarié à 9 000,10 MAD, brut de novembre 2026, cotisations calculées.
        eq = {'a': api, 'b': api, 'sid': me['societe_id']}
        eid, _ = salarie(eq, m='P975')
        q = brut(eq, [eid])
        r = ok(api.post(C, json={'brut_id': q['id'], 'regime': 'CNSS', 'declarations': [{'employe_id': eid, 'base_cnss': '9000.10', 'base_amo': '9000.10',
               'conditions_confirmees': True, 'reference_controle': 'CTRL-FICTIF975'}], 'mode_pedagogique_confirme': True,
               'cle_idempotence': str(uuid4()), 'motif': 'Calcul FICTIF975'}), 201)['contenu']
        assert r['complet_pour_social'], r['employes'][0]['anomalies']
        # 31,20 + 237,60 + 203,40 ; 63,00 + 475,80 + 576,01 + 203,40 + 166,50
        assert r['totaux']['cotisations_salariales'] == '472.20' and r['totaux']['cotisations_patronales'] == '1484.71', r['totaux']
    finally:
        api.close()
