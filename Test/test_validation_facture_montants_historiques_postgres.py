"""Validation définitive des montants historiques : PostgreSQL nonce seulement."""
from contextlib import closing
from datetime import date
from pathlib import Path
import json
import uuid
import pytest
from sqlalchemy import text
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_articles_alertes_stock_historique_postgres import cible
from test_conversion_bon_prix_historique_postgres import photographie as photo_bons


def photographie(application):
    result = photo_bons(application)
    cible(application)
    with application['engine'].connect() as db:
        for table in ('facturation_sequences', 'exercices_comptables', 'periodes_comptables'):
            rows = db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY row_to_json(t)::text')).scalars().all()
            result[table] = rows
    return result


def creer(api, type_facture, proforma, prix=100):
    nom = 'Validation fictive '+uuid.uuid4().hex[:8]
    r = api.post('/api/tiers', json={'nom': nom, 'type': 'fournisseur' if type_facture == 'achat' else 'client'})
    assert r.status_code == 201, r.text
    r = api.post('/api/factures', json={'type': type_facture, 'date': date.today().isoformat(),
        'tiers': nom, 'tiers_id': r.json()['id'], 'est_proforma': proforma,
        'reference': 'FICT-'+uuid.uuid4().hex[:12],
        'lignes': [{'description': 'Service fictif sans mouvement de stock', 'quantite': 1,
                    'prix_unitaire': prix, 'tva': 20}]})
    assert r.status_code == 201, r.text
    return r.json()['id']


def valider(application, api, fid, proforma):
    route = 'convertir-definitive' if proforma else 'valider'
    r = api.post(f'/api/factures/{fid}/{route}', json={})
    if r.status_code == 500:
        path = Path(__file__).resolve().parents[1]/'.codex-tests'/('validation344_api_'+uuid.uuid4().hex[:8]+'.log')
        path.write_text(application['api_log'].read_text(encoding='utf-8', errors='replace'), encoding='utf-8')
        print('Journal API authentique :', path)
    return r


@pytest.mark.parametrize('type_facture', ['achat', 'vente'])
@pytest.mark.parametrize('proforma', [False, True])
@pytest.mark.parametrize('prix', [float('nan'), float('inf'), float('-inf'), 1e308])
def test_validation_prix_historique_invalide_refuse_avant_numero(application, type_facture, proforma, prix):
    with closing(client(application)[0]) as api:
        fid = creer(api, type_facture, proforma)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text('UPDATE lignes_facture SET prix_unitaire=:prix WHERE facture_id=:id'), {'prix': prix, 'id': fid})
        avant = photographie(application)
        r = valider(application, api, fid, proforma)
        apres = photographie(application)
        if r.status_code != 422:
            path = Path(__file__).resolve().parents[1]/'.codex-tests'/('validation344_photos_'+uuid.uuid4().hex[:8]+'.json')
            path.write_text(json.dumps({'status': r.status_code, 'avant': avant, 'apres': apres}), encoding='utf-8')
        assert r.status_code == 422, r.text
        assert r.json()['detail']
        assert apres == avant


@pytest.mark.parametrize('type_facture', ['achat', 'vente'])
@pytest.mark.parametrize('proforma', [False, True])
@pytest.mark.parametrize('prix', [0, 100])
def test_validation_montant_connu_zero_et_identites_preserves(application, type_facture, proforma, prix):
    with closing(client(application)[0]) as api:
        fid = creer(api, type_facture, proforma, prix)
        r = valider(application, api, fid, proforma)
        assert r.status_code == 200, r.text
        cible(application)
        with application['engine'].connect() as db:
            f = db.execute(text('SELECT est_validee,est_proforma,numero,est_comptabilisee FROM factures WHERE id=:id'), {'id': fid}).one()
            ligne = db.execute(text('SELECT prix_unitaire FROM lignes_facture WHERE facture_id=:id'), {'id': fid}).scalar_one()
        assert tuple(f[:2]) == (True, False) and f.numero and f.est_comptabilisee is False
        assert ligne == prix


@pytest.mark.parametrize('type_facture', ['achat', 'vente'])
@pytest.mark.parametrize('proforma', [False, True])
def test_validation_autre_societe404_sans_reservation(application, type_facture, proforma):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        fid = creer(api, type_facture, proforma)
        avant = photographie(application)
        assert valider(application, autre, fid, proforma).status_code == 404
        assert photographie(application) == avant


@pytest.mark.parametrize('proforma', [False, True])
@pytest.mark.parametrize('champ', ['quantite', 'remise', 'rabais', 'frais_transport_ht', 'escompte'])
@pytest.mark.parametrize('valeur', [float('nan'), float('inf'), float('-inf')])
def test_validation_autres_sources_nonfinies_refuse_sans_numero(application, proforma, champ, valeur):
    with closing(client(application)[0]) as api:
        fid = creer(api, 'achat', proforma)
        cible(application)
        table = 'lignes_facture' if champ in ('quantite', 'remise', 'rabais') else 'factures'
        cle = 'facture_id' if table == 'lignes_facture' else 'id'
        with application['engine'].begin() as db:
            db.execute(text(f'UPDATE {table} SET {champ}=:val WHERE {cle}=:id'), {'val': valeur, 'id': fid})
        avant = photographie(application)
        r = valider(application, api, fid, proforma)
        assert r.status_code == 422, r.text
        assert photographie(application) == avant
