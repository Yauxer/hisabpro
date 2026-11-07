"""Draft333 : sortie brute des mouvements, PG nonce et projections pures."""
from contextlib import closing
from datetime import datetime, date
from pathlib import Path
from types import SimpleNamespace
import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models
import schemas
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client

CHAMPS = ('quantite', 'stock_avant', 'stock_apres')


def cible(application):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])


def photo(application):
    cible(application)
    with application['engine'].connect() as db:
        return {t: db.execute(text(f'SELECT row_to_json(t)::text FROM {t} t ORDER BY id')).scalars().all()
                for t in ('articles', 'mouvements_stock', 'ecritures', 'lignes_ecriture')}


def source(**champs):
    return SimpleNamespace(id=1, type='sortie', quantite=1, stock_avant=2, stock_apres=1,
        reference='HISTORIQUE', note='Trace fictive', created_at=datetime(2026,10,10), **champs)


@pytest.mark.parametrize('champ', CHAMPS)
@pytest.mark.parametrize('valeur', [None, float('nan'), float('inf'), float('-inf'), True, False])
def test_projection_inconnue_sans_mutation(champ, valeur):
    origine = source()
    setattr(origine, champ, valeur)
    sortie = schemas.MouvementStockOut.model_validate(origine)
    assert getattr(sortie, champ) is None and champ in sortie.nombres_diagnostics
    assert getattr(origine, champ) is valeur
    assert 'NaN' not in sortie.model_dump_json() and 'Infinity' not in sortie.model_dump_json()


@pytest.mark.parametrize('valeur', [-1, 0, 0.1, 1e308])
def test_quantites_connues_signees_preservees(valeur):
    origine = source()
    for champ in CHAMPS:
        setattr(origine, champ, valeur)
    sortie = schemas.MouvementStockOut.model_validate(origine)
    assert all(getattr(sortie, c) == valeur for c in CHAMPS)
    assert sortie.nombres_diagnostics == {}
    assert all(getattr(origine, c) == valeur for c in CHAMPS)


def creer(application, api, valeurs):
    cible(application)
    r = api.post('/api/articles', json={'code': 'HIST-'+uuid.uuid4().hex[:10],
        'designation': 'Mouvements fictifs', 'stock_actuel': 0, 'tva': 20})
    assert r.status_code == 201, r.text
    aid = r.json()['id']
    sid = api.get('/api/societe/moi').json()['id']
    with Session(application['engine']) as db:
        donnees = dict(quantite=1, stock_avant=2, stock_apres=1)
        donnees.update(valeurs)
        m = models.MouvementStock(societe_id=sid, article_id=aid, type='sortie',
            reference='SOURCE-FICTIVE', note='Historique conservé',
            date_mouvement=date(2026,6,30), cout_unitaire=20, cmup_apres=20, **donnees)
        db.add(m)
        db.flush()
        mid = m.id
        db.commit()
    return aid, mid


def lire(application, api, aid):
    r = api.get(f'/api/articles/{aid}/mouvements')
    if r.status_code != 200:
        log = application['api_log'].read_text(encoding='utf-8', errors='replace')
        p = Path(__file__).resolve().parents[1]/'.codex-tests'/('mouvements_333_api_echec_'+uuid.uuid4().hex[:10]+'.log')
        p.write_text(log, encoding='utf-8')
        print('Vrai journal API nonce conservé :', p)
        print(log[-9000:])
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize('champ,valeur', [(c,v) for c in CHAMPS
    for v in [float('nan'), float('inf'), float('-inf')]
    if not (c == 'quantite' and v == float('-inf'))])
def test_api_nonfinis_lisibles_et_autre_societe404(application, champ, valeur):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        aid, mid = creer(application, api, {champ: valeur})
        avant = photo(application)
        lignes = lire(application, api, aid)
        assert len(lignes) == 1 and lignes[0]['id'] == mid
        assert lignes[0][champ] is None and champ in lignes[0]['nombres_diagnostics']
        assert lignes[0]['reference'] == 'SOURCE-FICTIVE' and lignes[0]['note'] == 'Historique conservé'
        assert 'cout_unitaire' not in lignes[0] and 'cmup_apres' not in lignes[0]
        assert autre.get(f'/api/articles/{aid}/mouvements').status_code == 404
        assert photo(application) == avant


def test_api_signed_zero_metadata_preservees(application):
    with closing(client(application)[0]) as api:
        aid, mid = creer(application, api, {'quantite': 1, 'stock_avant': 0, 'stock_apres': -1})
        avant = photo(application)
        row = lire(application, api, aid)[0]
        assert row['id'] == mid and (row['quantite'], row['stock_avant'], row['stock_apres']) == (1,0,-1)
        assert row['nombres_diagnostics'] == {}
        assert photo(application) == avant


@pytest.mark.parametrize('quantite', [0, float('-inf')])
def test_postgres_conserve_contrainte_quantite_positive(application, quantite):
    cible(application)
    with closing(client(application)[0]) as api:
        aid, mid = creer(application, api, {})
        avant = photo(application)
        with application['engine'].begin() as db:
            with pytest.raises(IntegrityError, match='ck_mouvements_stock_quantite_positive_06c'):
                db.execute(text('UPDATE mouvements_stock SET quantite=:q WHERE id=:id'),
                           {'q': quantite, 'id': mid})
            db.rollback()
        assert photo(application) == avant
