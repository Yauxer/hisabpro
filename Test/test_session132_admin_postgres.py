"""Vrais tests API/PostgreSQL, uniquement dans un cluster éphémère protégé.

L'instance réelle, main.py et son moteur global ne sont jamais utilisés. Les
contraintes ORM/calendriers et les verrous sont testés ici ; les migrations et
triggers comptables font l'objet d'autres recettes PostgreSQL isolées.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import models
from database import Base, get_db
from routers import auth, utilisateurs, multi_societes, exercices, plan_comptable
from postgres_isole import cluster_isole, verifier_cible_isolee


@pytest.fixture(scope="module")
def postgres_admin():
    with cluster_isole() as cluster:
        assert verifier_cible_isolee(cluster["url"], cluster["directory"], cluster["nonce"])
        engine = create_engine(cluster["url"], connect_args={"options": "-c statement_timeout=15000 -c lock_timeout=10000"})
        try:
            Base.metadata.create_all(engine)
            with Session(engine) as db:
                db.add_all([models.CompteCGNCReference(numero=n, libelle=label, classe=int(n[0]), type_compte="SP")
                            for n, label in [("1111", "Capital social"), ("5141", "Banques"),
                                             ("3421", "Clients"), ("4411", "Fournisseurs")]])
                db.commit()
            app = FastAPI()
            for router in (auth.router, utilisateurs.router, multi_societes.router, exercices.router, plan_comptable.router):
                app.include_router(router)

            def db_test():
                with Session(engine, autoflush=False) as db:
                    try:
                        yield db
                    finally:
                        db.rollback()

            app.dependency_overrides[get_db] = db_test
            with TestClient(app) as client:
                yield client, engine
        finally:
            engine.dispose()


@pytest.fixture
def dossier(postgres_admin):
    client, engine = postgres_admin
    suffix = uuid.uuid4().hex[:10]
    data = {"nom": "Admin recette PostgreSQL", "email": f"admin-{suffix}@recette.test",
            "password": "RecettePG132!", "raison_sociale": f"Société fictive PG {suffix}"}
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 200, response.text
    entete = {"Authorization": "Bearer " + response.json()["access_token"]}
    info = client.get("/api/auth/me", headers=entete).json()
    return client, engine, entete, info, data


def test_inscription_reelle_prepare_plan_calendrier_et_connexion(dossier):
    client, engine, entete, info, data = dossier
    with Session(engine) as db:
        user = db.get(models.Utilisateur, info["id"])
        assert user.hashed_password.startswith("$bcrypt-sha256$")
        ex = db.query(models.ExerciceComptable).filter_by(societe_id=info["societe_id"]).one()
        assert ex.annee == date.today().year
        assert len(ex.periodes) == 12
        assert db.query(models.CompteSociete).filter_by(societe_id=info["societe_id"]).count() == 4
    response = client.post("/api/auth/login", json={"email": data["email"], "password": data["password"]})
    assert response.status_code == 200
    assert client.get("/api/exercices", headers=entete).status_code == 200


def test_get_calendrier_fonctionne_dans_transaction_postgres_lecture_seule(dossier):
    _, engine, _, info, _ = dossier
    with Session(engine) as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        resultat = exercices.lister_exercices(current_user={"societe_id": info["societe_id"], "role": "lecture"}, db=db)
        assert len(resultat) == 1
        assert db.execute(text("SHOW transaction_read_only")).scalar() == "on"
        db.rollback()


def test_get_plan_vide_lecture_seule_et_initialisation_admin_reelle(dossier):
    client, engine, entete, info, _ = dossier
    with Session(engine) as db:
        # Suppression exclusivement dans le nouveau dossier synthétique de
        # notre cluster temporaire ; aucune écriture ni société réelle.
        db.query(models.CompteSociete).filter_by(societe_id=info["societe_id"]).delete()
        db.commit()
    with Session(engine) as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        rows = plan_comptable.lister_plan(inclure_inactifs=True,
            current_user={"societe_id": info["societe_id"], "role": "lecture"}, db=db)
        assert rows == []
        assert db.execute(text("SHOW transaction_read_only")).scalar() == "on"
        db.rollback()
    assert client.post("/api/plan-comptable/initialiser", headers=entete).json()["nb_comptes"] == 4
    assert client.post("/api/plan-comptable/initialiser", headers=entete).json()["nb_comptes"] == 4


def test_calendrier_decale_reel_refuse_chevauchement_et_duree(dossier):
    client, engine, entete, info, _ = dossier
    annee = date.today().year + 1
    data = {"annee": annee, "date_debut": f"{annee}-01-01", "date_fin": f"{annee}-06-30"}
    response = client.post("/api/exercices", json=data, headers=entete)
    assert response.status_code == 201, response.text
    assert response.json()["nb_periodes"] == 6
    decale = {"annee": annee + 1, "date_debut": f"{annee}-07-01", "date_fin": f"{annee+1}-06-30"}
    response = client.post("/api/exercices", json=decale, headers=entete)
    assert response.status_code == 201 and response.json()["nb_periodes"] == 12
    trop_long = {"date_debut": f"{annee}-01-01", "date_fin": f"{annee+1}-06-30"}
    assert client.patch(f"/api/exercices/{annee+1}", json=trop_long, headers=entete).status_code == 400
    chevauchement = {"date_debut": f"{annee}-06-30", "date_fin": f"{annee+1}-06-29"}
    assert client.patch(f"/api/exercices/{annee+1}", json=chevauchement, headers=entete).status_code == 409
    with Session(engine) as db:
        ex = db.query(models.ExerciceComptable).filter_by(societe_id=info["societe_id"], annee=annee+1).one()
        assert ex.date_debut == date(annee, 7, 1)


def test_inscription_echouee_annule_societe_user_modules_plan(dossier, monkeypatch):
    client, engine, _, _, _ = dossier
    suffix = uuid.uuid4().hex

    def erreur(*args):
        raise RuntimeError("Sonde isolée : préparation indisponible")

    monkeypatch.setattr(auth, "ensure_exercice", erreur)
    with pytest.raises(RuntimeError, match="Sonde isolée"):
        client.post("/api/auth/register", json={"nom": "Échec isolé", "email": f"echec-{suffix}@recette.test",
                    "password": "RecettePG132!", "raison_sociale": f"Échec isolé {suffix}"})
    with Session(engine) as db:
        assert db.query(models.Societe).filter_by(raison_sociale=f"Échec isolé {suffix}").count() == 0
        assert db.query(models.Utilisateur).filter_by(email=f"echec-{suffix}@recette.test").count() == 0


def creer_admin_invite(client, engine, entete, info):
    suffix = uuid.uuid4().hex[:10]
    response = client.post("/api/auth/register", json={"nom": "Admin invité PG", "email": f"invite-{suffix}@recette.test",
                "password": "RecettePG132!", "raison_sociale": f"Autre société PG {suffix}"})
    assert response.status_code == 200
    principale = {"Authorization": "Bearer " + response.json()["access_token"]}
    invite = client.get("/api/auth/me", headers=principale).json()
    assert client.post(f'/api/societes/{info["societe_id"]}/inviter', headers=entete,
                       params={"email": invite["email"], "role": "admin"}).status_code == 200
    # Employer le vrai parcours de bascule, qui conserve la version du secret.
    bascule = client.post(f'/api/societes/switcher/{info["societe_id"]}', headers=principale)
    assert bascule.status_code == 200, bascule.text
    local = {"Authorization": "Bearer " + bascule.json()['access_token']}
    return invite, local, principale


def test_retrait_invite_revoque_token_et_preserve_compte_postgres(dossier):
    client, engine, entete, info, _ = dossier
    invite, locale, principale = creer_admin_invite(client, engine, entete, info)
    response = client.delete(f'/api/utilisateurs/{invite["id"]}', headers=entete)
    assert response.status_code == 204
    assert client.get("/api/auth/me", headers=locale).status_code == 403
    assert client.get("/api/auth/me", headers=principale).status_code == 200
    with Session(engine) as db:
        assert db.get(models.Utilisateur, invite["id"]).actif is True


def test_deux_retraits_concurrents_preservent_dernier_admin_postgres(dossier):
    client, engine, entete, info, _ = dossier
    invite, locale, _ = creer_admin_invite(client, engine, entete, info)
    barriere = Barrier(2)

    def retirer(role_entete, user_id):
        barriere.wait(timeout=10)
        return client.patch(f"/api/utilisateurs/{user_id}", headers=role_entete, json={"role": "lecture"}).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futurs = [pool.submit(retirer, entete, info["id"]), pool.submit(retirer, locale, invite["id"])]
        statuses = sorted(futur.result(timeout=40) for futur in futurs)
    assert statuses == [200, 400]
    from services.utilisateurs_acces_service import administrateurs_actifs
    with Session(engine) as db:
        assert len(administrateurs_actifs(db, info["societe_id"])) == 1


def test_cloture_calendrier_reelle_jamais_rouverte_par_synchronisation(dossier):
    client, engine, entete, info, _ = dossier
    with Session(engine) as db:
        ex = db.query(models.ExerciceComptable).filter_by(societe_id=info["societe_id"]).one()
        ex.statut = "cloture"
        annee = ex.annee
        db.commit()
    response = client.post("/api/exercices/synchroniser", headers=entete)
    assert response.status_code == 200, response.text
    assert next(row for row in response.json() if row["annee"] == annee)["statut"] == "cloture"
    with Session(engine) as db:
        assert db.query(models.ExerciceComptable).filter_by(societe_id=info["societe_id"], annee=annee).one().statut == "cloture"
