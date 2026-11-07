"""Contrats de saisie articles et vrais refus API sur PostgreSQL nonce."""
from datetime import datetime
import math
import json
import uuid

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import text

import schemas
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application

CHAMPS = ('prix_vente_ht', 'prix_achat_ht', 'stock_actuel', 'stock_min',
          'frais_emballage', 'frais_transport', 'tva')


@pytest.mark.parametrize('classe', [schemas.ArticleCreate, schemas.ArticleUpdate])
@pytest.mark.parametrize('champ', CHAMPS)
@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), float('-inf'), 'NaN', 'Infinity', None, True, False])
def test_saisies_non_finies_null_booleennes_refusees(classe, champ, valeur):
    base = {'code': 'FINITE', 'designation': 'Fictif'} if classe is schemas.ArticleCreate else {}
    with pytest.raises(ValidationError):
        classe(**base, **{champ: valeur})


def test_champs_omis_et_finis_sans_plafond_arbitraire():
    assert schemas.ArticleUpdate().model_dump(exclude_unset=True) == {}
    for classe in (schemas.ArticleCreate, schemas.ArticleUpdate):
        base = {'code': 'FINITE', 'designation': 'Fictif'} if classe is schemas.ArticleCreate else {}
        for valeur in (0, 0.125, 1e308):
            for champ in CHAMPS[:-1]:
                assert getattr(classe(**base, **{champ: valeur}), champ) == valeur
        assert classe(**base, tva=0).tva == 0
        assert classe(**base, tva=20).tva == 20


def test_lecture_historique_stock_et_autres_champs_inchangee():
    base = dict(id=1, code='LEGACY', designation='Historique fictif', actif=True, created_at=datetime(2026, 10, 9))
    for valeur in (None, float('nan'), float('inf'), -1):
        out = schemas.ArticleOut(**base, stock_actuel=valeur)
        assert out.stock_actuel is None and out.stock_diagnostic
    # Le garde de requête ne devient pas une réparation de sortie historique.
    out = schemas.ArticleOut(**base, prix_vente_ht=float('nan'), frais_transport=float('inf'))
    assert out.prix_vente_ht is None and out.frais_transport is None
    assert 'prix_vente_ht' in out.nombres_diagnostics and 'frais_transport' in out.nombres_diagnostics


@pytest.fixture(scope='module')
def dossier(application):
    cible = application['cluster']
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    with httpx.Client(base_url=application['api_url']) as api:
        suffixe = uuid.uuid4().hex[:10]
        r = api.post('/api/auth/register', json={'nom': 'Admin fictif', 'email': suffixe+'@example.com',
            'password': 'ArticleFini2026!', 'raison_sociale': 'Articles finis fictifs '+suffixe})
        assert r.status_code == 200, r.text
        api.headers['Authorization'] = 'Bearer '+r.json()['access_token']
        r = api.post('/api/articles', json={'code': 'FINITE-'+suffixe, 'designation': 'Article fictif',
            'stock_actuel': 0, 'prix_vente_ht': 100, 'frais_emballage': 2.5, 'frais_transport': 3.25, 'tva': 20})
        assert r.status_code == 201, r.text
        yield api, r.json()['id']


def photographie(application):
    with application['engine'].connect() as db:
        return {table: db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).scalars().all()
                for table in ('articles', 'mouvements_stock', 'ecritures')}


@pytest.mark.parametrize('methode,champ,valeur', [('POST', 'prix_vente_ht', 'NaN'), ('PATCH', 'frais_transport', None)])
def test_reproduction_refus_avant_mutation(application, dossier, methode, champ, valeur):
    api, aid = dossier
    avant = photographie(application)
    body = {champ: valeur}
    url = '/api/articles/'+str(aid) if methode == 'PATCH' else '/api/articles'
    if methode == 'POST': body.update(code='INVALID-'+uuid.uuid4().hex[:10], designation='Fictif refusé', stock_actuel=0)
    r = api.request(methode, url, json=body)
    apres = photographie(application)
    modifies = [table for table in avant if avant[table] != apres[table]]
    assert (r.status_code, modifies) == (422, []), f'HTTP {r.status_code}; tables modifiées={modifies}; corps={r.text}'


@pytest.mark.parametrize('methode', ['POST', 'PATCH'])
@pytest.mark.parametrize('champ', CHAMPS)
@pytest.mark.parametrize('valeur', ['NaN', 'Infinity', '-Infinity', None, True, False])
def test_api_saisie_invalide_sans_mutation(application, dossier, methode, champ, valeur):
    api, aid = dossier
    avant = photographie(application)
    body = {champ: valeur}
    url = '/api/articles/'+str(aid) if methode == 'PATCH' else '/api/articles'
    if methode == 'POST': body.update(code='INVALID-'+uuid.uuid4().hex[:10], designation='Fictif refusé')
    r = api.request(methode, url, json=body)
    assert r.status_code == 422, r.text
    assert photographie(application) == avant


def test_api_fractions_grands_prix_patch_partiel_et_stock_protege(application, dossier):
    api, aid = dossier
    r = api.patch('/api/articles/'+str(aid), json={'designation': 'Fictif renommé'})
    assert r.status_code == 200, r.text
    assert r.json()['frais_emballage'] == 2.5 and r.json()['frais_transport'] == 3.25
    for valeur in (0, 0.125, 1e308):
        r = api.post('/api/articles', json={'code': 'VALID-'+uuid.uuid4().hex[:10], 'designation': 'Fictif fini',
            'prix_vente_ht': valeur, 'prix_achat_ht': valeur, 'frais_emballage': valeur, 'frais_transport': valeur,
            'stock_min': valeur, 'stock_actuel': 0, 'tva': 20})
        assert r.status_code == 201, r.text
        assert r.json()['prix_vente_ht'] == valeur and r.json()['frais_transport'] == valeur
        r = api.patch('/api/articles/'+str(r.json()['id']), json={'frais_emballage': valeur, 'prix_achat_ht': valeur})
        assert r.status_code == 200, r.text
    avant = photographie(application)
    r = api.patch('/api/articles/'+str(aid), json={'stock_actuel': 0.125})
    assert r.status_code == 409, r.text
    assert photographie(application) == avant


@pytest.mark.parametrize('methode', ['POST', 'PATCH'])
@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), float('-inf')])
def test_api_litteraux_non_finis_refuses_json_sur(application, dossier, methode, valeur):
    api, aid = dossier
    avant = photographie(application)
    body = {'prix_vente_ht': valeur, 'frais_transport': valeur}
    url = '/api/articles/'+str(aid) if methode == 'PATCH' else '/api/articles'
    if methode == 'POST': body.update(code='RAW-'+uuid.uuid4().hex[:10], designation='Fictif refusé')
    # Littéraux hors JSON standard : FastAPI les parse effectivement avec son
    # décodeur. Vérifier aussi que l'erreur de validation reste JSON sûre.
    r = api.request(methode, url, content=json.dumps(body), headers={'Content-Type': 'application/json'})
    assert r.status_code == 422, r.text
    assert r.json()['detail']
    assert photographie(application) == avant
