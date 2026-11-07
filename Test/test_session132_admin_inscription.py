"""Inscription API isolée : initialisation transactionnelle, sans PostgreSQL réel.

Le service du calendrier PostgreSQL est remplacé par une sonde ; ses contraintes
propres restent couvertes par la recette PostgreSQL distincte.
"""
from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models
from database import get_db
from routers import auth as route


@pytest.fixture
def inscription(monkeypatch):
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in (models.Societe.__table__, models.Utilisateur.__table__, models.ModuleActif.__table__,
                  models.CompteCGNCReference.__table__, models.CompteSociete.__table__):
        table.create(engine)
    with Session(engine) as db:
        db.add(models.CompteCGNCReference(numero="1111", libelle="Capital social", classe="1", type_compte="SP"))
        db.commit()
    appels = []

    def preparer(db, societe_id, annee):
        # La préparation doit voir toutes les autres créations non encore
        # validées, y compris le plan réellement initialisé par son service.
        assert db.query(models.Utilisateur).filter_by(societe_id=societe_id).one().role == "admin"
        assert db.query(models.ModuleActif).filter_by(societe_id=societe_id).count() == 3
        assert db.query(models.CompteSociete).filter_by(societe_id=societe_id, numero="1111").one()
        appels.append((societe_id, annee))

    monkeypatch.setattr(route, "ensure_exercice", preparer)
    monkeypatch.setattr(route, "hash_password", lambda password: "hash-isole")
    app = FastAPI()
    app.include_router(route.router)

    def db_test():
        with Session(engine) as db:
            try:
                yield db
            finally:
                db.rollback()

    app.dependency_overrides[get_db] = db_test
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, engine, appels
    engine.dispose()


def donnees():
    return {"nom": "Administrateur recette", "email": "admin@recette.test", "password": "Recette132!",
            "raison_sociale": "Société fictive de recette"}


def test_inscription_prepare_plan_et_exercice_avant_validation(inscription):
    client, engine, appels = inscription
    response = client.post("/api/auth/register", json=donnees())
    assert response.status_code == 200, response.text
    assert response.json()["role"] == "admin"
    with Session(engine) as db:
        societe = db.query(models.Societe).one()
        assert societe.exercice_debut == date.today().year
        assert appels == [(societe.id, date.today().year)]
        assert db.query(models.CompteSociete).filter_by(societe_id=societe.id).count() == 1


def test_echec_preparation_ne_laisse_aucun_compte_orphelin(inscription, monkeypatch):
    client, engine, _ = inscription

    def erreur(*args):
        raise RuntimeError("Sonde : calendrier indisponible")

    monkeypatch.setattr(route, "ensure_exercice", erreur)
    assert client.post("/api/auth/register", json=donnees()).status_code == 500
    with Session(engine) as db:
        for model in (models.Societe, models.Utilisateur, models.ModuleActif, models.CompteSociete):
            assert db.query(model).count() == 0
        assert db.query(models.CompteCGNCReference).count() == 1


def test_inscription_dupliquee_ne_recree_pas_societe(inscription):
    client, engine, appels = inscription
    assert client.post("/api/auth/register", json=donnees()).status_code == 200
    assert client.post("/api/auth/register", json=donnees()).status_code == 400
    assert len(appels) == 1
    with Session(engine) as db:
        assert db.query(models.Societe).count() == 1


def test_mot_de_passe_faible_refuse_avant_creation(inscription):
    client, engine, appels = inscription
    data = donnees()
    data["password"] = "12345678"
    assert client.post("/api/auth/register", json=data).status_code == 400
    assert appels == []
    with Session(engine) as db:
        assert db.query(models.Societe).count() == 0
