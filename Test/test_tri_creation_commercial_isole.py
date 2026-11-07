"""Ordre de création : vraies API/UI, PostgreSQL éphémère exclusivement."""
from datetime import date, datetime
import uuid

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import application, connexion, observer

CASES = [
    (models.Devis, '/api/devis', {}, 'Devis', 'vente'),
    (models.BonCommande, '/api/bons-commande', {'type': 'vente'}, 'Bons de commande', 'vente'),
    (models.BonLivraison, '/api/bons-livraison', {'type': 'vente'}, 'Bons de livraison', 'vente'),
    (models.BonLivraison, '/api/bons-reception', {'type': 'achat'}, 'Bons de réception', 'achat'),
    (models.Facture, '/api/factures', {'type': 'vente'}, 'Factures', 'vente'),
    (models.Reglement, '/api/reglements', {}, 'Règlements', 'vente'),
]


def ok(response):
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize('model,endpoint,extra,onglet,mode', CASES, ids=['devis', 'bc', 'bl', 'br', 'factures', 'reglements'])
def test_creation_meme_instant_antidate_historique_filtres_et_ui(application, model, endpoint, extra, onglet, mode):
    suffix = uuid.uuid4().hex[:8]
    email, password = f'tri-{suffix}@example.com', 'TriCreation132!'
    year = date.today().year
    with httpx.Client(base_url=application['api_url'], timeout=30) as api:
        admin = ok(api.post('/api/auth/register', json={'nom': 'Admin tri fictif', 'email': email,
            'password': password, 'raison_sociale': 'Tri fictif ' + suffix}))
        api.headers['Authorization'] = 'Bearer ' + admin['access_token']
        sid = ok(api.get('/api/societe/moi'))['id']
        autre = ok(api.post('/api/auth/register', json={'nom': 'Autre admin fictif',
            'email': f'autre-tri-{suffix}@example.com', 'password': password, 'raison_sociale': 'Autre tri fictif ' + suffix}))
        autre_sid = ok(api.get('/api/societe/moi', headers={'Authorization': 'Bearer ' + autre['access_token']}))['id']
        with Session(application['engine']) as db:
            facture_source = None
            facture_source_id = None
            if model is models.Reglement:
                facture_source = models.Facture(societe_id=sid, numero='SOURCE-TRI', type='vente',
                    date=date(year, 1, 1), exercice=year, tiers='Client fictif source')
                db.add(facture_source); db.flush()
                facture_source_id = facture_source.id

            def piece(i, company=sid, annee=year, sens=None):
                business = date(annee, 1, 1) if i == 2 else date(annee, 12, 1) if i >= 3 else date(annee, 6, 1)
                attrs = dict(societe_id=company, numero=f'TRI-{suffix}-{annee}-{sens or mode}-{i}', tiers=f'FICTIF-TRI-{i}', date=business,
                             created_at=datetime(year, 10, 7, [9, 10, 10, 8, 7, 7, 12][i]))
                if model is models.Reglement:
                    attrs.update(montant=1, facture_id=facture_source_id if company == sid else None)
                else:
                    attrs['exercice'] = annee
                if model in (models.BonCommande, models.BonLivraison, models.Facture):
                    attrs['type'] = sens or extra['type']
                row = model(**attrs); db.add(row); db.flush()
                return row

            rows = [piece(i) for i in range(6)]
            # Simule deux timestamps historiques manquants dans ce laboratoire.
            for row in rows[4:]:
                db.execute(text(f'UPDATE {model.__tablename__} SET created_at=NULL WHERE id=:id'), {'id': row.id})
                db.refresh(row)
            piece(6, company=autre_sid)
            piece(6, annee=year - 1)
            if model in (models.BonCommande, models.BonLivraison, models.Facture):
                inverse = piece(6, sens='achat' if extra['type'] == 'vente' else 'vente')
                inverse.created_at = datetime(year, 1, 1)
            db.commit()
            expected = [rows[i].id for i in [2, 1, 0, 3, 5, 4]]
            before = [(row.id, row.date, row.created_at) for row in rows]
        params = {'exercice': year, **extra}
        # BR filtre son type lui-même ; il n'a pas de paramètre type.
        if endpoint == '/api/bons-reception':
            params.pop('type')
        response = api.get(endpoint, params=params)
        if response.status_code >= 500:
            print(application['api_log'].read_text(encoding='utf-8', errors='replace')[-7000:])
        result = ok(response)
        assert [r['id'] for r in result] == expected
        assert result[0]['date'] == f'{year}-01-01'
        assert result[-1]['created_at'] is None and result[-2]['created_at'] is None
        assert [r['id'] for r in ok(api.get(endpoint, params=params))] == expected
        if model is not models.Reglement:
            assert [r['id'] for r in ok(api.get(endpoint, params={**params, 'statut': result[0]['statut']}))] == expected
        if model is models.Facture:
            assert [r['id'] for r in ok(api.get(endpoint, params={**params, 'skip': 1, 'limit': 2}))] == expected[1:3]
        if model in (models.Devis, models.BonCommande, models.Facture):
            assert [r['id'] for r in ok(api.get(endpoint, params={**params, 'recherche': 'FICTIF-TRI-2'}))] == expected[:1]
        if model is models.Reglement:
            assert [r['id'] for r in ok(api.get(endpoint, params={**params, 'facture_id': facture_source_id}))] == expected
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium/Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(); page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/commercial')
                if mode == 'achat':
                    page.get_by_role('button', name='Achat', exact=True).click()
                page.get_by_role('button', name=onglet, exact=True).click()
                first = page.locator('tbody tr').first
                playwright.expect(first).to_contain_text('FICTIF-TRI-2')
                assert not errors, errors
                assert not server_errors, server_errors
            finally:
                browser.close()
        with Session(application['engine']) as db:
            after = [(db.get(model, rowid).id, db.get(model, rowid).date, db.get(model, rowid).created_at) for rowid, _, _ in before]
            assert after == before
