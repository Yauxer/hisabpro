"""Familles historiques : TVA inconnue lisible, saisies strictes, PG nonce."""
from contextlib import closing
from datetime import datetime
from pathlib import Path
import uuid
import pytest
from pydantic import ValidationError
from sqlalchemy import text
import schemas
from test_e2e_facturation_isole import application
from test_articles_stock_historique_lecture import dossier
from test_ras_lecture_conservation import client

INVALIDES = [None, float('nan'), float('inf'), float('-inf'), -1, 101]


def photo(application):
    with application['engine'].connect() as db:
        return {t: db.execute(text(f'SELECT row_to_json(t)::text FROM {t} t ORDER BY id')).scalars().all()
                for t in ('familles_articles', 'articles', 'mouvements_stock', 'ecritures', 'lignes_ecriture')}


def famille(api, tva=20):
    r = api.post('/api/familles', json={'code': 'F-'+uuid.uuid4().hex[:10],
        'libelle': 'Famille fictive', 'tva_defaut': tva})
    assert r.status_code == 201, r.text
    return r.json()['id']


def article(api, fid):
    code = 'A-'+uuid.uuid4().hex[:10]
    r = api.post('/api/articles', json={'code': code, 'designation': 'Article famille fictif',
        'famille_id': fid, 'stock_actuel': 0, 'tva': 20, 'prix_vente_ht': 10, 'prix_achat_ht': 8})
    return r, code


@pytest.fixture
def dossier_famille(application):
    with closing(client(application)[0]) as api:
        yield api, api.get('/api/societe/moi').json()['id']


@pytest.mark.parametrize('tva', INVALIDES)
def test_famille_inconnue_lectures_et_reponses_mutation_sures(application, dossier_famille, tva):
    api, sid = dossier_famille
    fid = famille(api)
    r, _ = article(api, fid)
    assert r.status_code == 201, r.text
    aid = r.json()['id']
    with application['engine'].begin() as db:
        db.execute(text('UPDATE familles_articles SET tva_defaut=:v WHERE id=:id AND societe_id=:sid'),
                   {'v': tva, 'id': fid, 'sid': sid})
    avant = photo(application)
    familles = api.get('/api/familles')
    articles = api.get('/api/articles')
    assert photo(application) == avant
    patch = api.patch(f'/api/articles/{aid}', json={'description': 'Note seule explicite'})
    nouveau, nouveau_code = article(api, fid)
    # Observation persistante avant assertions HTTP : une ancienne réponse500
    # pouvait cacher le commit déjà effectué par POST/PATCH.
    with application['engine'].connect() as db:
        assert db.execute(text('SELECT description,tva FROM articles WHERE id=:id'), {'id': aid}).one() == (
            'Note seule explicite', 20)
        assert db.execute(text('SELECT tva FROM articles WHERE code=:code AND societe_id=:sid'),
                          {'code': nouveau_code, 'sid': sid}).scalar_one() == 20
    apres = photo(application)
    assert apres['familles_articles'] == avant['familles_articles']
    assert all(apres[t] == avant[t] for t in ('mouvements_stock', 'ecritures', 'lignes_ecriture'))
    statuts = [familles.status_code, articles.status_code, patch.status_code, nouveau.status_code]
    if statuts != [200, 200, 200, 201]:
        log = application['api_log'].read_text(encoding='utf-8', errors='replace')
        p = Path(__file__).resolve().parents[1]/'.codex-tests'/('familles_324_api_echec_'+uuid.uuid4().hex[:10]+'.log')
        p.write_text(log, encoding='utf-8')
        print('Trace API nonce conservée :', p)
        print(log[-9000:])
    assert statuts == [200, 200, 200, 201], f'HTTPGETfamilles/articles/PATCH/POST={statuts}'
    f = next(x for x in familles.json() if x['id'] == fid)
    a = next(x for x in articles.json() if x['id'] == aid)
    for projection in (f, a['famille'], patch.json()['famille'], nouveau.json()['famille']):
        assert projection['tva_defaut'] is None and 'tva_defaut' in projection['nombres_diagnostics']
    avant_iso = photo(application)
    with closing(client(application)[0]) as autre:
        assert autre.get('/api/familles').json() == []
        assert autre.get('/api/articles').json() == []
        assert autre.patch(f'/api/articles/{aid}', json={'description': 'Interdit'}).status_code == 404
    assert photo(application) == avant_iso


@pytest.mark.parametrize('tva', INVALIDES+[True, False, 'NaN', 'Infinity'])
def test_nouvelle_saisie_famille_invalide_refusee(tva):
    with pytest.raises(ValidationError):
        schemas.FamilleCreate(code='INV', libelle='Fictif', tva_defaut=tva)


@pytest.mark.parametrize('tva', [None, 'NaN', 'Infinity', '-Infinity', -1, 101, True, False])
def test_api_famille_invalide_422_avant_mutation(application, dossier, tva):
    api, _ = dossier
    avant = photo(application)
    r = api.post('/api/familles', json={'code': 'REF-'+uuid.uuid4().hex[:10], 'libelle': 'Refus fictif',
                                      'tva_defaut': tva})
    assert r.status_code == 422, r.text
    assert photo(application) == avant


@pytest.mark.parametrize('tva', INVALIDES+[True, False])
def test_sortie_famille_nullable_ne_relache_pas_saisie(tva):
    out = schemas.FamilleOut(id=1, code='HIST', libelle='Historique fictif', actif=True,
                            created_at=datetime(2026,10,10), tva_defaut=tva)
    assert out.tva_defaut is None and 'tva_defaut' in out.nombres_diagnostics
    assert 'NaN' not in out.model_dump_json() and 'Infinity' not in out.model_dump_json()


@pytest.mark.parametrize('tva', [0, 10, 20])
def test_tva_finie_historique_conservee(tva):
    out = schemas.FamilleOut(id=1, code='HIST', libelle='Historique fictif', actif=True,
                            created_at=datetime(2026,10,10), tva_defaut=tva)
    assert out.tva_defaut == tva and out.nombres_diagnostics == {}


@pytest.mark.parametrize('tva', [0, 20])
def test_api_famille_tva_connue_preservee(application, dossier, tva):
    api, _ = dossier
    fid = famille(api, tva)
    avant = photo(application)
    r = api.get('/api/familles')
    assert r.status_code == 200, r.text
    f = next(x for x in r.json() if x['id'] == fid)
    assert f['tva_defaut'] == tva and f['nombres_diagnostics'] == {}
    assert photo(application) == avant


def test_defaut_saisie_nouvelle_distinct_sortie_historique_absente():
    assert schemas.FamilleCreate(code='NOUV', libelle='Fictif').tva_defaut == 20
    out = schemas.FamilleOut(id=1, code='HIST', libelle='Fictif', actif=True,
                            created_at=datetime(2026,10,10))
    assert out.tva_defaut is None and 'tva_defaut' in out.nombres_diagnostics


def test_api_tva_historique10_preservee_sans_nouvelle_regle(application, dossier):
    api, sid = dossier
    fid = famille(api)
    with application['engine'].begin() as db:
        db.execute(text('UPDATE familles_articles SET tva_defaut=10 WHERE id=:id AND societe_id=:sid'),
                   {'id': fid, 'sid': sid})
    avant = photo(application)
    r = api.get('/api/familles')
    assert r.status_code == 200, r.text
    f = next(x for x in r.json() if x['id'] == fid)
    assert f['tva_defaut'] == 10 and f['nombres_diagnostics'] == {}
    assert photo(application) == avant
