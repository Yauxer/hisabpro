"""La route GET exercices reste une lecture, synchronisation réservée admin."""
from datetime import date
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from auth import get_current_user
from database import get_db
from routers import exercices
from services import exercices_service
import models


class QueryLecture:
    def __init__(self, rows):
        self.rows = rows

    def filter_by(self, **kwargs):
        assert kwargs == {"societe_id": 13}
        return self

    def order_by(self, *args):
        return self

    def all(self):
        return self.rows


class SessionLecture:
    def __init__(self, rows):
        self.rows = rows

    def query(self, *args):
        return QueryLecture(self.rows)

    def commit(self):
        raise AssertionError("Une consultation ne doit pas écrire")


def creer_client(monkeypatch, role, synchronisations):
    row = SimpleNamespace(id=7, annee=2026, date_debut=date(2026, 1, 1), date_fin=date(2026, 12, 31),
                          statut="cloture", periodes=[])
    db = SessionLecture([row])

    def synchroniser(session, societe_id):
        synchronisations.append(societe_id)
        return session.rows

    monkeypatch.setattr(exercices, "synchroniser_exercices", synchroniser)
    app = FastAPI()
    app.include_router(exercices.router)
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "societe_id": 13, "role": role}
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


@pytest.mark.parametrize("role", ["admin", "comptable", "lecture"])
def test_get_exercices_ne_synchronise_et_ne_modifie_jamais(monkeypatch, role):
    appels = []
    with creer_client(monkeypatch, role, appels) as client:
        response = client.get("/api/exercices")
    assert response.status_code == 200
    assert response.json()[0]["statut"] == "cloture"
    assert appels == []


@pytest.mark.parametrize("role", ["comptable", "lecture"])
def test_synchronisation_interdite_aux_profils_non_admin(monkeypatch, role):
    appels = []
    with creer_client(monkeypatch, role, appels) as client:
        assert client.post("/api/exercices/synchroniser").status_code == 403
    assert appels == []


def test_synchronisation_explicitement_accessible_admin(monkeypatch):
    appels = []
    with creer_client(monkeypatch, "admin", appels) as client:
        response = client.post("/api/exercices/synchroniser")
    assert response.status_code == 200
    assert appels == [13]


def test_synchronisation_ne_reouvre_pas_cloture_meme_sans_snapshot(monkeypatch):
    annee = date.today().year - 1
    exercice = SimpleNamespace(id=9, annee=annee, date_debut=date(annee, 1, 1),
                               date_fin=date(annee, 12, 31), statut="cloture")

    class Query:
        def __init__(self, rows):
            self.rows = rows

        def filter_by(self, **kwargs):
            return self

        def filter(self, *args):
            return self

        def order_by(self, *args):
            return self

        def distinct(self):
            return self

        def all(self):
            return self.rows

    class DB:
        commits = 0

        def query(self, entity):
            # Aucun snapshot de clôture ; le statut définitif existant reste
            # une interdiction de réouverture par le calendrier.
            return Query([exercice] if entity is models.ExerciceComptable else [])

        def commit(self):
            self.commits += 1

    suivants = []

    def preparer(db, societe_id, precedent):
        assert precedent.statut == "cloture"
        suivants.append(precedent.annee + 1)

    monkeypatch.setattr(exercices_service, "preparer_exercice_suivant", preparer)
    db = DB()
    assert exercices_service.synchroniser_exercices(db, 13) == [exercice]
    assert exercice.statut == "cloture"
    assert suivants == [annee + 1]
    assert db.commits == 1
