"""Règlements historiques : lecture qualifiée, sources conservées, actions refusées."""
from pathlib import Path
import sys
from contextlib import closing
from datetime import date
import math
import os
import pytest
from sqlalchemy import text
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Test'))
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_validation_facture_montants_historiques_postgres import creer, photographie
from test_articles_alertes_stock_historique_postgres import cible
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer


def preparer(application, api, valeur, sens, mode='virement'):
    fid = creer(api, sens, False, 100)
    r = api.post(f'/api/factures/{fid}/valider', json={})
    assert r.status_code == 200, r.text
    ids = []
    for montant in (20, 10):
        r = api.post('/api/reglements', json={'facture_id': fid, 'date': date.today().isoformat(),
            'tiers': 'Tiers repris de la facture', 'montant': montant, 'mode': mode, 'comptabiliser': False,
            'date_echeance': date.today().isoformat() if mode == 'effet' else None})
        assert r.status_code == 201, r.text
        ids.append(r.json()['id'])
    # Uniquement un règlement non comptabilisé fictif, jamais une écriture validée.
    cible(application)
    with application['engine'].begin() as db:
        db.execute(text('UPDATE reglements SET montant=:v WHERE id=:id AND est_comptabilisee=false'),
                   {'v': valeur, 'id': ids[1]})
    return fid, ids


def photo(application):
    result = photographie(application)
    with application['engine'].connect() as db:
        result['reglements'] = db.execute(text('SELECT row_to_json(t)::text FROM reglements t ORDER BY id')).scalars().all()
    return result


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), float('-inf'), 0, -10], ids=['nan', 'inf', '-inf', 'zero', 'negatif'])
def test_lecture200_conserve_sources_et_bloque_actions(application, valeur, sens):
    with closing(client(application)[0]) as api:
        fid, ids = preparer(application, api, valeur, sens)
        # Deuxième société créée avant la photographie de conservation.
        autre = client(application)[0]
        try:
            avant = photo(application)
            for params in ({'exercice': date.today().year}, {'exercice': date.today().year, 'facture_id': fid}):
                r = api.get('/api/reglements', params=params)
                assert r.status_code == 200, r.text
                rows = {x['id']: x for x in r.json()}
                assert set(rows) == set(ids)
                assert rows[ids[0]]['montant'] == 20 and rows[ids[0]]['montant_valide'] is True
                assert rows[ids[1]]['montant'] == (valeur if math.isfinite(valeur) else None)
                assert rows[ids[1]]['montant_valide'] is False
                assert rows[ids[1]]['montant_anomalie']
                assert [x['id'] for x in r.json()] == list(reversed(ids))
            assert api.get('/api/reglements', params={'exercice': date.today().year + 1}).json() == []
            assert autre.get('/api/reglements', params={'exercice': date.today().year}).json() == []
            situation = api.get(f'/api/factures/{fid}/reglements')
            assert situation.status_code == 422, situation.text
            factures = api.get('/api/factures', params={'exercice': date.today().year})
            assert factures.status_code == 200, factures.text
            ligne_facture = next(f for f in factures.json() if f['id'] == fid)
            assert ligne_facture['montants_valides'] is False
            for methode, suffixe, contenu in (
                ('POST', '/comptabiliser', {}), ('POST', '/transition', {'action': 'rejeter'}),
                ('POST', '/annuler', {}), ('PATCH', '', {'notes': 'Tentative sur source inconnue'}),
                ('DELETE', '', None),
            ):
                r = api.request(methode, f'/api/reglements/{ids[1]}{suffixe}', json=contenu)
                assert r.status_code == 422, (methode, suffixe, r.text)
                assert 'historique' in r.json()['detail']
                assert photo(application) == avant
            assert photo(application) == avant
        finally:
            autre.close()


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('largeur', [1365, 390])
@pytest.mark.parametrize('valeur', [float('nan'), 0], ids=['nan', 'zero'])
def test_reglements_historiques_ui_visible_non_financiere(application, sens, largeur, valeur):
    api, email, password = client(application)
    try:
        fid, ids = preparer(application, api, valeur, sens)
        avant = photo(application)
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                erreurs, serveurs = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/commercial')
                page.get_by_role('button', name='Vente' if sens == 'vente' else 'Achat', exact=True).click()
                page.get_by_role('button', name='Règlements', exact=True).click()
                pw.expect(page.locator('tbody tr')).to_have_count(2)
                pw.expect(page.get_by_role('alert').filter(has_text='Total à vérifier')).to_be_visible()
                historique = page.locator('tbody tr').filter(has_text='Montant historique du règlement à vérifier')
                pw.expect(historique).to_have_count(1)
                pw.expect(historique).to_contain_text('Situation à vérifier')
                for titre in ('Modifier', 'Supprimer', 'Consulter ou déclarer la RAS'):
                    pw.expect(historique.get_by_title(titre, exact=True)).to_be_disabled()
                sain = page.locator('tbody tr').filter(has_not_text='Montant historique du règlement à vérifier')
                pw.expect(sain).to_contain_text('20,00')
                pw.expect(sain.get_by_title('Modifier', exact=True)).to_be_enabled()
                # Le montant nul reste explicite et signalé ; le NaN reste inconnu.
                pw.expect(historique).to_contain_text('0,00' if valeur == 0 else 'À vérifier')
                if os.environ.get('HISABPRO_CAPTURE_368') and sens == 'vente' and math.isnan(valeur):
                    page.evaluate('() => Promise.all(document.getAnimations().filter(a => Number.isFinite(a.effect.getTiming().iterations)).map(a => a.finished))')
                    page.screenshot(path=str(Path(__file__).resolve().parents[1]/'.codex-tests'/f'reglements368_{largeur}.png'), full_page=True)
                assert not erreurs and not serveurs, (erreurs, serveurs)
                assert photo(application) == avant
            finally:
                browser.close()
    finally:
        api.close()


@pytest.mark.parametrize('sens,mode', [('vente','cheque'), ('vente','effet'), ('achat','effet')])
@pytest.mark.parametrize('largeur', [1365,390])
def test_effets_consommateur_nullable_sans_zero_fictif(application, sens, mode, largeur):
    api, email, password = client(application)
    try:
        fid, ids = preparer(application, api, float('nan'), sens, mode)
        avant = photo(application)
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width':largeur,'height':1000})
                page.set_default_timeout(15000)
                erreurs, serveurs = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/effets')
                pw.expect(page.locator('tbody tr')).to_have_count(2)
                pw.expect(page.get_by_role('alert').filter(has_text='Montants historiques à vérifier')).to_be_visible()
                historique = page.locator('tbody tr').filter(has_text='Montant historique du règlement à vérifier')
                pw.expect(historique).to_have_count(1)
                pw.expect(historique).to_contain_text('À vérifier')
                boutons = historique.get_by_role('button')
                assert boutons.count() > 0
                for bouton in boutons.all(): pw.expect(bouton).to_be_disabled()
                if sens == 'vente':
                    pw.expect(page.get_by_text('Portefeuille :', exact=False)).to_contain_text('À vérifier')
                if os.environ.get('HISABPRO_CAPTURE_368') and sens == 'vente' and mode == 'effet':
                    page.evaluate('() => Promise.all(document.getAnimations().filter(a => Number.isFinite(a.effect.getTiming().iterations)).map(a => a.finished))')
                    page.screenshot(path=str(Path(__file__).resolve().parents[1]/'.codex-tests'/f'effets368_{largeur}.png'), full_page=True)
                assert not erreurs and not serveurs, (erreurs,serveurs)
                assert photo(application) == avant
            finally:
                browser.close()
    finally:
        api.close()
