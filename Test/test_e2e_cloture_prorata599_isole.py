"""CCA/PCA : calcul UI → AD → clôture avec CM → AN → CP N+1, PostgreSQL jetable."""
from contextlib import closing
from decimal import Decimal as D
import pytest
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import text

from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_e2e_prorata_inventaire_isole import ouvrir, remplir, ecriture, photo
from test_ajustements_inventaire_isole import exercice
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from test_e2e_annee_connectee_isole import ORACLE as PROFIL, valider_brouillons_ui
from browser_support import chromium_executable


@pytest.mark.parametrize('type_,largeur', [('cca', 1440), ('pca', 390)])
def test_599_cloture_an_contrepassation_et_sources(application, type_, largeur, tmp_path):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        exercice(api)
        s = ok(api.patch('/api/societe/moi', json={'forme_juridique':'SARL', 'regime_fiscal':'is',
            'devise':'MAD', 'exercice_debut':2020, 'capital_social':20000}))
        sid = s['id']
        # Profil déjà livré : hors démarrage, CM sans exonération. Ce laboratoire
        # ne qualifie pas la fiscalité de la société réelle de l'utilisateur.
        ok(api.put('/api/fiscalite/is/2025/parametres', json=PROFIL['profil']['parametres_is']))
        ids = [ecriture(api, '2025-01-02', [('5141','20000',0), ('1111',0,'20000')], 'CAPITAL-FICTIF599')]
        base = [('6125','12000',0), ('5141',0,'12000')] if type_ == 'cca' else [('5141','12000',0), ('7124',0,'12000')]
        ids.append(ecriture(api, '2025-10-01', base, 'BASE-FICTIVE599'))
        sources = photo(application, ids)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width':largeur,'height':1000})
            page.set_default_timeout(20000)
            page.on('dialog', lambda d:d.accept())
            erreurs, serveur = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            resultat = remplir(ouvrir(page, application), type_)
            resultat.get_by_role('button', name='Utiliser le montant et le libellé', exact=True).click()
            page.get_by_role('button', name='Vérifier l’écriture', exact=True).click()
            with page.expect_response(lambda r:r.request.method=='POST' and '/ajustements?exercice=2025' in r.url) as reponse:
                page.get_by_role('button', name='Créer l’écriture', exact=True).click()
            assert reponse.value.status == 200, reponse.value.text()
            a = reponse.value.json()
            valider_brouillons_ui(page, application, 1)
            sources_ad = photo(application, [a['ecriture_id']])
            page.goto(application['web_url']+'/cloture')
            bouton = page.get_by_role('button', name="Clôturer l'exercice 2025", exact=True)
            expect(bouton).to_be_enabled()
            with page.expect_response(lambda r:r.request.method=='POST' and '/cloturer?exercice=2025' in r.url) as reponse:
                bouton.click()
            assert reponse.value.status == 200, reponse.value.text()
            cloture = reponse.value.json()
            attendu = D('-9065.93') if type_ == 'cca' else D('3065.93')
            assert D(str(cloture['resultat_net'])) == attendu
            assert cloture['a_nouveaux_sur'] == 2026
            with application['engine'].connect() as db:
                an = db.execute(text('SELECT ecriture_an_id FROM clotures_exercice WHERE societe_id=:s AND exercice=2025'), {'s':sid}).scalar_one()
                lignes = db.execute(text('SELECT compte,debit-credit AS solde FROM lignes_ecriture WHERE ecriture_id=:i'), {'i':an}).all()
                soldes = {c:v for c,v in lignes}
                assert soldes == ({'5141':D('8000'),'3491':D('5934.07'),'1199':D('9065.93'),'1111':D('-20000'),'4453':D('-3000')} if type_ == 'cca' else
                    {'5141':D('32000'),'1111':D('-20000'),'1191':D('-3065.93'),'4491':D('-5934.07'),'4453':D('-3000')})
                assert sum(soldes.values()) == 0
                assert not db.execute(text('SELECT est_validee FROM ecritures WHERE id=:i'), {'i':a['contrepassation_id']}).scalar_one()
            # La clôture ne réécrit ni la source initiale ni l'ajustement définitif.
            assert photo(application, ids) == sources
            assert photo(application, [a['ecriture_id']]) == sources_ad
            refus = api.delete(f"/api/cloture/ajustements/{a['id']}")
            assert refus.status_code == 423, refus.text
            page.get_by_label('Exercice actif', exact=True).select_option('2026')
            valider_brouillons_ui(page, application, 1)
            cp = photo(application, [a['contrepassation_id']])
            for annee in (2025, 2026):
                fec = ok(api.get(f'/api/fec/apercu?exercice={annee}'))
                assert fec['conforme_export'], fec
                export = api.get(f'/api/fec/export?exercice={annee}')
                assert export.status_code == 200, export.text
                (tmp_path/f'FEC599_{type_}_{annee}.txt').write_bytes(export.content)
            liasse = ok(api.get('/api/etats/liasse/2026'))
            assert D(str(liasse['etats']['cpc']['resultat_net'])) == (D('-5934.07') if type_ == 'cca' else D('5934.07'))
            assert liasse['etats']['bilan']['equilibre']
            with application['engine'].connect() as db:
                compte = '3491' if type_ == 'cca' else '4491'
                assert db.execute(text('SELECT SUM(l.debit-l.credit) FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s AND e.exercice=2026 AND l.compte=:c AND e.est_validee'), {'s':sid,'c':compte}).scalar_one() == 0
            # Relire les états ne modifie aucune des trois pièces définitives.
            assert photo(application, ids) == sources
            assert photo(application, [a['ecriture_id']]) == sources_ad
            assert photo(application, [a['contrepassation_id']]) == cp
            page.screenshot(path=str(tmp_path/f'cloture599_{type_}_{largeur}.png'))
            assert not erreurs and not serveur, (erreurs, serveur)
        finally:
            browser.close()
