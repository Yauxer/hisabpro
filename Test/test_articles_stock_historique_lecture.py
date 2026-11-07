"""Lecture API d'un stock historique inconnu, sans réparation : PG nonce."""
import uuid

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

import models
import schemas
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application


@pytest.fixture(scope='module')
def dossier(application):
    cluster = application['cluster']
    verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
    with httpx.Client(base_url=application['api_url']) as api:
        suffixe = uuid.uuid4().hex[:12]
        r = api.post('/api/auth/register', json={
            'nom': 'Lecture stock fictive', 'email': suffixe + '@example.com',
            'password': 'StockHistorique2026!', 'raison_sociale': 'Stock fictif ' + suffixe})
        assert r.status_code == 200, 'Inscription fictive refusée'
        api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        sid = api.get('/api/societe/moi').json()['id']
        yield api, sid


def photographie(application):
    with application['engine'].connect() as db:
        return {
            table: db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).scalars().all()
            for table in ('articles', 'mouvements_stock', 'ecritures')
        }


@pytest.mark.parametrize('stock', [None, float('nan'), float('inf'), float('-inf'), -1])
def test_stock_inconnu_lisible_non_repare(application, dossier, stock):
    api, sid = dossier
    with Session(application['engine']) as db:
        article = models.Article(societe_id=sid, code='LEG-' + uuid.uuid4().hex[:10],
            designation='Article historique fictif', is_stockable=True)
        db.add(article)
        db.flush()
        article.stock_actuel = stock
        aid = article.id
        db.commit()
    avant = photographie(application)
    r = api.get('/api/articles')
    assert r.status_code == 200, r.text
    ligne = next(a for a in r.json() if a['id'] == aid)
    assert ligne['stock_actuel'] is None
    assert ligne['stock_diagnostic']
    assert not any(t in r.text for t in ('NaN', 'Infinity'))
    diagnostic = api.post('/api/devis/diagnostic-stock', json={
        'lignes': [{'article_id': aid, 'quantite': 2}]})
    assert diagnostic.status_code == 200, diagnostic.text
    assert diagnostic.json()['articles'][0]['statut'] == 'inconnu'
    assert photographie(application) == avant


@pytest.mark.parametrize('stock', [0, 5, 0.1])
def test_stock_fini_conserve(application, dossier, stock):
    api, sid = dossier
    r = api.post('/api/articles', json={'code': 'FIN-' + uuid.uuid4().hex[:10],
        'designation': 'Article fini fictif', 'stock_actuel': stock, 'tva': 20})
    assert r.status_code == 201, r.text
    assert r.json()['stock_actuel'] == stock
    assert r.json()['stock_diagnostic'] is None
    avant = photographie(application)
    lecture = api.get('/api/articles')
    assert lecture.status_code == 200, lecture.text
    ligne = next(a for a in lecture.json() if a['id'] == r.json()['id'])
    assert ligne['stock_actuel'] == stock and ligne['stock_diagnostic'] is None
    assert photographie(application) == avant


def test_sortie_nullable_ne_rend_pas_creation_nullable():
    with pytest.raises(ValidationError):
        schemas.ArticleCreate(code='REFUS', designation='Fictif', stock_actuel=None)
