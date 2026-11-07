"""Dossiers externes isolés : versions, droits, intégrité et aucune écriture."""
from datetime import date
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, update
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models
from auth import get_current_user
from database import get_db
from routers.etats import router


def donnees(montant='100'):
    return {'exercice': 2025, 'fichier_n': 'balance.csv', 'lignes_n': [
        {'compte': '1111', 'credit': montant}, {'compte': '5141', 'debit': montant}]}


@pytest.fixture
def api():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    for model in [models.Societe, models.Utilisateur, models.CompteSociete, models.LiasseBalancePreparation]:
        model.__table__.create(engine)
    # SQLite ne sait pas exécuter les contraintes calendaires PG ; seule la
    # sélection d'exercice du dossier est testée ici, aucun calendrier simulé.
    with engine.begin() as c:
        c.execute(text('CREATE TABLE exercices_comptables(id INTEGER PRIMARY KEY, societe_id INTEGER, annee INTEGER, date_debut DATE, date_fin DATE, statut TEXT, created_at DATETIME, updated_at DATETIME)'))
        c.execute(text("INSERT INTO exercices_comptables VALUES(1,1,2025,'2025-01-01','2025-12-31','ouvert',NULL,NULL)"))
    with Session(engine) as db:
        for id in [1, 2]:
            db.add(models.Societe(id=id, raison_sociale=f'Société fictive {id}'))
            db.add(models.Utilisateur(id=id, societe_id=id, nom='Recette', email=f'user{id}@recette.test', hashed_password='test', role='admin'))
            for compte in ['1111', '5141']:
                db.add(models.CompteSociete(societe_id=id, numero=compte, libelle=compte, classe=int(compte[0])))
        db.commit()
    identity = {'id': 1, 'societe_id': 1, 'role': 'admin'}
    app = FastAPI(); app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: identity
    def database():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        yield client, engine, identity
    engine.dispose()


def test_versions_sources_comparatif_et_relecture_apres_changement_plan(api):
    client, engine, _ = api
    first = client.post('/api/etats/liasse/balance/dossiers', json=donnees())
    assert first.status_code == 201, first.text
    first = first.json()
    assert first['version'] == 1 and len(first['empreinte_sha256']) == 64
    assert first['contenu']['sources']['n1'] is None
    assert first['contenu']['preparation']['pret_a_deposer'] is False
    assert first['contenu']['sources']['n'][0]['credit'] == '100.00'
    second = client.post('/api/etats/liasse/balance/dossiers', json=donnees('200')).json()
    assert second['version'] == 2 and second['id'] != first['id']
    with Session(engine) as db:
        db.query(models.CompteSociete).filter_by(societe_id=1).delete(); db.commit()
    r = client.get(f"/api/etats/liasse/balance/dossiers/{first['id']}")
    assert r.status_code == 200 and r.json() == first
    items = client.get('/api/etats/liasse/balance/dossiers?exercice=2025').json()
    assert [i['version'] for i in items] == [2, 1]


def test_cloisonnement_societe_liste_et_detail(api):
    client, _, identity = api
    first = client.post('/api/etats/liasse/balance/dossiers', json=donnees()).json()
    identity.update(id=2, societe_id=2)
    assert client.get('/api/etats/liasse/balance/dossiers?exercice=2025').json() == []
    assert client.get(f"/api/etats/liasse/balance/dossiers/{first['id']}").status_code == 404


def test_lecture_consulte_mais_ne_cree_pas(api):
    client, _, identity = api
    first = client.post('/api/etats/liasse/balance/dossiers', json=donnees()).json()
    identity['role'] = 'lecture'
    assert client.get(f"/api/etats/liasse/balance/dossiers/{first['id']}").status_code == 200
    assert client.post('/api/etats/liasse/balance/dossiers', json=donnees()).status_code == 403


def test_exercice_absent_ou_balance_invalide_ne_cree_pas_dossier(api):
    client, engine, _ = api
    data = donnees(); data['exercice'] = 2024
    assert client.post('/api/etats/liasse/balance/dossiers', json=data).status_code == 422
    data = donnees(); data['lignes_n'][0]['credit'] = '99'
    assert client.post('/api/etats/liasse/balance/dossiers', json=data).status_code == 422
    with Session(engine) as db:
        assert db.query(models.LiasseBalancePreparation).count() == 0
        assert db.query(models.Societe).count() == 2


def test_nom_fichier_n1_ne_justifie_pas_source_absente(api):
    client, _, _ = api
    data = donnees(); data['fichier_n1'] = 'source_absente.csv'
    assert client.post('/api/etats/liasse/balance/dossiers', json=data).status_code == 422


def test_tamper_snapshot_refuse_a_la_relecture(api):
    client, engine, _ = api
    first = client.post('/api/etats/liasse/balance/dossiers', json=donnees()).json()
    contenu = first['contenu']; contenu['preparation']['pret_a_deposer'] = True
    with engine.begin() as c:
        c.execute(update(models.LiasseBalancePreparation).values(contenu=contenu))
    response = client.get(f"/api/etats/liasse/balance/dossiers/{first['id']}")
    assert response.status_code == 409 and 'Empreinte' in response.text


def test_aucune_route_de_modification_des_versions(api):
    client, _, _ = api
    first = client.post('/api/etats/liasse/balance/dossiers', json=donnees()).json()
    for action in [client.patch, client.delete]:
        assert action(f"/api/etats/liasse/balance/dossiers/{first['id']}").status_code == 405
