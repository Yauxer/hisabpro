"""Captures guidées, IS/états et vrai lettrage, sans imputation fiscale présumée."""
from contextlib import closing
from datetime import date
from decimal import Decimal
import pytest
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import text
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    preparer, paiement, capturer,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import champ
from test_e2e_ras_situation_isole import photo
from browser_support import chromium_executable


def valider(api):
    lignes = ok(api.get('/api/ecritures', params={'exercice':date.today().year}))
    for e in lignes:
        if not e['est_validee']:
            ok(api.post(f"/api/ecritures/{e['id']}/valider"))


def situation(api):
    annee = date.today().year
    fiscal = ok(api.get(f'/api/fiscalite/is/{annee}'))
    liasse = ok(api.get(f'/api/etats/liasse/{annee}'))
    bilan = liasse['etats']['bilan']
    assert bilan['equilibre'] and Decimal(str(bilan['ecart'])) == 0
    return {k:fiscal[k] for k in ('calcul','acomptes','credits_is','liquidation')}, {
        'resultat':liasse['etats']['cpc']['resultat_net'],
        'actif':bilan['actif']['total'], 'passif':bilan['passif']['total']}


@pytest.mark.parametrize('nature,largeur', [('vente',1440), ('achat',390)])
def test_587_guides_lettrage_etats_et_is_sans_credit_implicite(application, nature, largeur, tmp_path):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        ok(api.post('/api/ecritures', json={'date':date.today().isoformat(),'journal':'BQ',
            'reference':'CAPITAL-FICTIF587','libelle':'Capital fictif de recette587',
            'lignes':[{'compte':'5141','debit':10000},{'compte':'1111','credit':10000}]}),201)
        f, r1 = preparer(api, nature=nature)
        sid = ok(api.get('/api/societe/moi'))['id']
        valider(api)
        initial = situation(api)
        assert Decimal(str(initial[1]['resultat'])) == (Decimal('1000') if nature=='vente' else Decimal('-1000'))
        assert Decimal(str(initial[1]['actif']['net'])) == (Decimal('11200') if nature=='vente' else Decimal('9675'))
        c1, _ = capturer(api, r1, nature=nature);valider(api)
        apres_un = situation(api)
        assert apres_un == initial
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant'] == 600
        r2 = paiement(api, f, '525.00');valider(api)
        avant_capture2 = situation(api)
        assert avant_capture2[0] == initial[0] and avant_capture2[1]['resultat'] == initial[1]['resultat']
        assert Decimal(str(avant_capture2[1]['actif']['net'])) == (Decimal('11200') if nature=='vente' else Decimal('9150'))
        c2, _ = capturer(api, r2, nature=nature);valider(api)
        assert situation(api) == avant_capture2
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['est_solde']
        with application['engine'].connect() as db:
            # Oracle :10000 capital +1200 facture +525 +75 +525 +75 =12400.
            sommes = db.execute(text('SELECT sum(l.debit),sum(l.credit),count(*) FROM lignes_ecriture l '
                'JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s'), {'s':sid}).one()
            assert sommes == (Decimal('12400.00'),Decimal('12400.00'),13)
            ids = db.execute(text('SELECT id FROM ecritures WHERE societe_id=:s ORDER BY id'), {'s':sid}).scalars().all()
            assert len(ids) == 6
        original = photo(application, ids)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            confirmations = []
            def confirmer(dialogue):
                confirmations.append(dialogue.message)
                dialogue.accept()
            page.on('dialog', confirmer)
            erreurs, serveur = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url']+'/lettrage')
            champ(page,'Compte','select').select_option('3421' if nature=='vente' else '4411')
            champ(page,'Tiers','select').select_option(label=f['tiers'])
            expect(page.locator('tbody input[type="checkbox"]')).to_have_count(5)
            for box in page.locator('tbody input[type="checkbox"]').all():box.check()
            with page.expect_response(lambda r:'/api/lettrage' in r.url and r.request.method=='POST') as resultat:
                page.get_by_role('button',name='Lettrer 5 lignes',exact=True).click()
            assert resultat.value.status == 200 and resultat.value.json()['code'] == 'AAA'
            expect(page.get_by_text('5 lettrée(s)',exact=True)).to_be_visible()
            page.screenshot(path=str(tmp_path/f'lettrage587_{nature}_{largeur}.png'))
            assert photo(application,ids) == original
            assert situation(api) == avant_capture2
            corps = {'motif':'Annulation fictive après délettrage587','date_annulation':date.today().isoformat()}
            if nature == 'achat':
                with page.expect_response(lambda r:'/api/lettrage/comptable/delettrer/' in r.url and r.request.method=='POST') as resultat:
                    page.get_by_title('Délettrer le code AAA',exact=True).first.click()
                assert resultat.value.status == 200
                assert len(confirmations) == 1 and 'AAA' in confirmations[0]
                assert photo(application,ids) == original
            else:
                corps['motif']='Contrepassation fictive sans reecriture du groupe lettre587'
            ok(api.post(f"/api/reglements/{r2['id']}/annuler",json=corps));valider(api)
            assert situation(api) == initial
            assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant'] == 600
            registre = ok(api.get(f'/api/tva/ras/registre/{date.today().year}'))
            assert registre['totaux'][nature]['actives_validees']['montant'] == '75.00'
            assert registre['totaux'][nature]['annulees']['montant'] == '75.00'
            with application['engine'].connect() as db:
                sommes = db.execute(text('SELECT sum(l.debit),sum(l.credit),count(*) FROM lignes_ecriture l '
                    'JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s'), {'s':sid}).one()
                assert sommes == (Decimal('13000.00'),Decimal('13000.00'),17)
            assert photo(application,ids) == original
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:
            browser.close()
