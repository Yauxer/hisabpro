"""API RBAC / administration des invités sur données synthétiques en mémoire.

Les verrous PostgreSQL ne sont pas simulés : leur concurrence doit être testée
séparément sur PostgreSQL isolé. Aucun accès à la base réelle.
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models
from auth import create_access_token
from database import get_db
from routers import utilisateurs, multi_societes, auth


@pytest.fixture
def acces():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in (models.Societe.__table__, models.Utilisateur.__table__, models.UtilisateurSociete.__table__):
        table.create(engine)
    with Session(engine) as db:
        db.add_all([models.Societe(id=i, raison_sociale=f"Société recette {i}") for i in (1, 2, 3)])
        db.flush()
        db.add_all([
            models.Utilisateur(id=1, societe_id=1, nom="Admin principale", email="admin1@recette.test", hashed_password="hash", role="admin", actif=True),
            models.Utilisateur(id=2, societe_id=2, nom="Admin invitée", email="admin2@recette.test", hashed_password="hash", role="admin", actif=True),
            models.Utilisateur(id=3, societe_id=2, nom="Lecteur invité", email="lecteur@recette.test", hashed_password="hash", role="comptable", actif=True),
            models.Utilisateur(id=4, societe_id=3, nom="Autre société", email="autre@recette.test", hashed_password="hash", role="admin", actif=True),
            models.Utilisateur(id=5, societe_id=1, nom="Ancien administrateur", email="ancien@recette.test", hashed_password="hash", role="admin", actif=False),
        ])
        db.flush()
        db.add_all([
            models.UtilisateurSociete(utilisateur_id=2, societe_id=1, role="admin", actif=True),
            models.UtilisateurSociete(utilisateur_id=3, societe_id=1, role="lecture", actif=True),
        ])
        db.commit()
    app = FastAPI()
    for router in (utilisateurs.router, multi_societes.router, auth.router):
        app.include_router(router)

    def db_test():
        with Session(engine) as db:
            try:
                yield db
            finally:
                db.rollback()

    app.dependency_overrides[get_db] = db_test
    with TestClient(app) as client:
        yield client, engine
    engine.dispose()


def headers(user_id=1, societe_id=1, role="admin"):
    # Hash synthétique des comptes de cette fixture ; le JWT courant doit porter
    # sa version. Les anciens JWT sont testés explicitement dans les cas dédiés.
    return {"Authorization": "Bearer " + create_access_token({"sub": str(user_id), "societe_id": societe_id, "role": role}, password_hash="hash")}


def test_annuaire_inclut_invites_sans_divulguer_autres_societes(acces):
    client, _ = acces
    response = client.get("/api/utilisateurs", headers=headers())
    assert response.status_code == 200
    rows = {row["id"]: row for row in response.json()}
    assert set(rows) == {1, 2, 3, 5}
    assert rows[3]["role"] == "lecture"
    assert rows[3]["societe_id"] == 1
    assert rows[3]["acces_invite"] is True
    assert rows[1]["acces_invite"] is False
    assert all("hashed_password" not in row for row in rows.values())


@pytest.mark.parametrize("method,path,body", [
    ("patch", "/api/utilisateurs/2", {"role": "admin"}),
    ("delete", "/api/utilisateurs/2", None),
    ("post", "/api/utilisateurs", {"nom": "Interdit", "email": "non@recette.test", "mot_de_passe": "Recette132!"}),
])
def test_lecture_seule_refuse_mutations_meme_si_jwt_affirme_admin(acces, method, path, body):
    client, _ = acces
    kwargs = {"headers": headers(3, role="admin")}
    if body is not None:
        kwargs["json"] = body
    assert client.request(method, path, **kwargs).status_code == 403


def test_changement_role_invite_limite_a_societe_active_et_jwt_revalide(acces):
    client, engine = acces
    response = client.patch("/api/utilisateurs/3", json={"role": "comptable"}, headers=headers(2))
    assert response.status_code == 200
    assert response.json()["role"] == "comptable"
    with Session(engine) as db:
        assert db.get(models.Utilisateur, 3).role == "comptable"
        assert db.query(models.UtilisateurSociete).filter_by(utilisateur_id=3, societe_id=1).one().role == "comptable"
    assert client.get("/api/auth/me", headers=headers(3, role="lecture")).json()["role"] == "comptable"
    assert client.get("/api/auth/me", headers=headers(3, 2, role="lecture")).json()["role"] == "comptable"


def test_desactivation_invite_revoque_token_local_et_preserve_compte(acces):
    client, engine = acces
    assert client.patch("/api/utilisateurs/3", json={"actif": False}, headers=headers()).status_code == 200
    assert client.get("/api/auth/me", headers=headers(3)).status_code == 403
    assert client.get("/api/auth/me", headers=headers(3, 2)).status_code == 200
    with Session(engine) as db:
        assert db.get(models.Utilisateur, 3).actif is True


def test_reactivation_invite_retourne_droits_locaux(acces):
    client, _ = acces
    assert client.patch("/api/utilisateurs/3", json={"actif": False}, headers=headers()).status_code == 200
    response = client.patch("/api/utilisateurs/3", json={"actif": True}, headers=headers())
    assert response.status_code == 200 and response.json()["actif"] is True
    assert client.get("/api/auth/me", headers=headers(3)).status_code == 200


@pytest.mark.parametrize("body", [{"nom": "Identité imposée"}, {"mot_de_passe": "AutreSecret132!"},
                                  {"role": "admin", "mot_de_passe": "AutreSecret132!"}])
def test_admin_invite_ne_modifie_pas_compte_global(acces, body):
    client, engine = acces
    assert client.patch("/api/utilisateurs/3", json=body, headers=headers()).status_code == 403
    with Session(engine) as db:
        user = db.get(models.Utilisateur, 3)
        assert user.nom == "Lecteur invité" and user.hashed_password == "hash"
        assert db.query(models.UtilisateurSociete).filter_by(utilisateur_id=3, societe_id=1).one().role == "lecture"


def test_retirer_invite_ne_supprime_pas_son_compte(acces):
    client, engine = acces
    assert client.delete("/api/utilisateurs/3", headers=headers()).status_code == 204
    assert client.get("/api/auth/me", headers=headers(3)).status_code == 403
    assert client.get("/api/auth/me", headers=headers(3, 2)).status_code == 200
    with Session(engine) as db:
        assert db.get(models.Utilisateur, 3) is not None
        assert db.query(models.UtilisateurSociete).filter_by(utilisateur_id=3, societe_id=1).count() == 0


@pytest.mark.parametrize("method,body", [("patch", {"role": "lecture"}), ("delete", None)])
def test_utilisateur_autre_societe_inaccessible(acces, method, body):
    client, _ = acces
    kwargs = {"headers": headers()}
    if body:
        kwargs["json"] = body
    assert client.request(method, "/api/utilisateurs/4", **kwargs).status_code == 404


def test_admin_invite_compte_pour_conserver_administration(acces):
    client, _ = acces
    response = client.patch("/api/utilisateurs/1", json={"role": "lecture"}, headers=headers())
    assert response.status_code == 200
    assert client.get("/api/auth/me", headers=headers()).json()["role"] == "lecture"
    # L'admin invité devenu seul admin ne peut ensuite retirer son rôle.
    response = client.patch("/api/utilisateurs/2", json={"role": "lecture"}, headers=headers(2))
    assert response.status_code == 400


def test_admin_inactif_peut_etre_supprime_sans_reduire_admins_actifs(acces):
    client, engine = acces
    assert client.delete("/api/utilisateurs/2", headers=headers()).status_code == 204
    assert client.delete("/api/utilisateurs/5", headers=headers()).status_code == 204
    with Session(engine) as db:
        assert db.get(models.Utilisateur, 5) is None
        assert db.get(models.Utilisateur, 1).role == "admin"


def test_compte_principal_partage_ne_peut_pas_etre_supprime_par_autre_societe(acces):
    client, engine = acces
    response = client.delete("/api/utilisateurs/3", headers=headers(2, 2))
    assert response.status_code == 409
    with Session(engine) as db:
        assert db.get(models.Utilisateur, 3) is not None


def test_invitation_sur_societe_principale_ne_cree_pas_faux_role(acces):
    client, engine = acces
    response = client.post("/api/societes/1/inviter", params={"email": "admin1@recette.test", "role": "lecture"}, headers=headers(2))
    assert response.status_code == 409
    with Session(engine) as db:
        assert db.query(models.UtilisateurSociete).filter_by(utilisateur_id=1, societe_id=1).count() == 0


def test_invitation_ne_contourne_pas_protection_dernier_admin(acces):
    client, _ = acces
    assert client.patch("/api/utilisateurs/1", json={"role": "lecture"}, headers=headers()).status_code == 200
    response = client.post("/api/societes/1/inviter", params={"email": "admin2@recette.test", "role": "lecture"}, headers=headers(2))
    assert response.status_code == 400


def test_desactivation_propre_acces_interdite(acces):
    client, _ = acces
    response = client.patch("/api/utilisateurs/2", json={"actif": False}, headers=headers(2))
    assert response.status_code == 400


def test_desactivation_globale_preserve_dernier_admin_societe_secondaire(acces):
    client, engine = acces
    with Session(engine) as db:
        db.add(models.Utilisateur(id=6, societe_id=2, nom="Autre admin principale", email="admin6@recette.test",
                                  hashed_password="hash", role="admin", actif=True))
        db.commit()
    assert client.patch("/api/utilisateurs/1", json={"role": "lecture"}, headers=headers()).status_code == 200
    # Le compte 2 n'est pas le dernier admin principal de 2, mais demeure
    # le seul admin invité de 1 : sa désactivation globale est interdite.
    response = client.patch("/api/utilisateurs/2", json={"actif": False}, headers=headers(6, 2))
    assert response.status_code == 400
    assert "société 1" in response.json()["detail"]
    with Session(engine) as db:
        assert db.get(models.Utilisateur, 2).actif is True


def test_desactivation_globale_autorisee_si_toutes_societes_conservent_admin(acces):
    client, engine = acces
    with Session(engine) as db:
        db.add(models.Utilisateur(id=6, societe_id=2, nom="Autre admin principale", email="admin6@recette.test",
                                  hashed_password="hash", role="admin", actif=True))
        db.commit()
    assert client.patch("/api/utilisateurs/2", json={"actif": False}, headers=headers(6, 2)).status_code == 200
    assert client.get("/api/auth/me", headers=headers(2)).status_code == 401
    assert client.get("/api/auth/me", headers=headers(2, 2)).status_code == 401


def test_invitation_compte_desactive_ne_cree_pas_acces_ineffectif(acces):
    client, engine = acces
    response = client.post("/api/societes/2/inviter", params={"email": "ancien@recette.test", "role": "lecture"}, headers=headers(2, 2))
    assert response.status_code == 409
    with Session(engine) as db:
        assert db.query(models.UtilisateurSociete).filter_by(utilisateur_id=5, societe_id=2).count() == 0
