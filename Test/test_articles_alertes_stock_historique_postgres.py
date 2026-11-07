"""Draft332 : alertes historiques, API PostgreSQL nonce en lecture seule."""
from contextlib import closing
from pathlib import Path
import uuid
import pytest
from sqlalchemy import text
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client


def cible(application):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])


def photo(application):
    cible(application)
    with application['engine'].connect() as db:
        return {t: db.execute(text(f'SELECT row_to_json(t)::text FROM {t} t ORDER BY id')).scalars().all()
                for t in ('articles', 'familles_articles', 'mouvements_stock', 'ecritures',
                          'lignes_ecriture', 'inventaires_stock', 'inventaires_stock_lignes')}


def article(application, api, stock, *, stockable=True, actif=True):
    cible(application)
    r = api.post('/api/articles', json={'code': 'ALERTE-'+uuid.uuid4().hex[:10],
        'designation': 'Alerte stock fictive', 'stock_actuel': 0, 'is_stockable': stockable,
        'prix_achat_ht': 20, 'prix_vente_ht': 30, 'tva': 20})
    assert r.status_code == 201, r.text
    aid = r.json()['id']
    with application['engine'].begin() as db:
        db.execute(text('UPDATE articles SET stock_actuel=:v,actif=:actif WHERE id=:id'),
                   {'v': stock, 'actif': actif, 'id': aid})
    return aid


def lire(application, api):
    r = api.get('/api/articles/stock/alertes')
    if r.status_code != 200:
        log = application['api_log'].read_text(encoding='utf-8', errors='replace')
        p = Path(__file__).resolve().parents[1]/'.codex-tests'/('alertes_332_api_echec_'+uuid.uuid4().hex[:10]+'.log')
        p.write_text(log, encoding='utf-8')
        print('Vrai journal API nonce conservé :', p)
        print(log[-12000:])
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize('stock', [None, float('nan'), float('inf'), float('-inf')])
def test_alerte_source_inconnue_visible_sans_fausse_classification(application, stock):
    with closing(client(application)[0]) as api:
        aid = article(application, api, stock)
        avant = photo(application)
        sortie = lire(application, api)
        assert sortie['rupture'] == [] and sortie['faible'] == []
        assert [a['id'] for a in sortie['inconnus']] == [aid]
        row = sortie['inconnus'][0]
        assert row['stock_actuel'] is None and row['stock_diagnostic']
        assert 'stock_actuel' in row['nombres_diagnostics']
        assert any(d['article_id'] == aid and d['champ'] == 'stock_actuel' for d in sortie['diagnostics'])
        assert photo(application) == avant


@pytest.mark.parametrize('stock,classe', [(0, 'rupture'), (-1, 'rupture'),
    (0.1, 'faible'), (4.99999, 'faible'), (5, None), (1e308, None)])
def test_classification_connue_signee_et_seuil5_preserves(application, stock, classe):
    with closing(client(application)[0]) as api:
        aid = article(application, api, stock)
        avant = photo(application)
        sortie = lire(application, api)
        assert sortie.get('inconnus', []) == []
        assert sortie.get('diagnostics', []) == []
        for cle in ('rupture', 'faible'):
            assert [a['id'] for a in sortie[cle]] == ([aid] if cle == classe else [])
            if cle == classe:
                assert sortie[cle][0]['stock_actuel'] == stock
        assert photo(application) == avant


def test_services_inactifs_et_autre_societe_exclus_sans_mutation(application):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        aid = article(application, api, 0)
        article(application, api, float('-inf'), stockable=False)
        article(application, api, None, actif=False)
        autre_aid = article(application, autre, float('-inf'))
        avant = photo(application)
        sortie = lire(application, api)
        assert [a['id'] for a in sortie['rupture']] == [aid]
        assert sortie['faible'] == [] and sortie.get('inconnus', []) == []
        inconnus_autre = lire(application, autre)
        assert inconnus_autre['rupture'] == [] and inconnus_autre['faible'] == []
        assert [a['id'] for a in inconnus_autre['inconnus']] == [autre_aid]
        assert photo(application) == avant
