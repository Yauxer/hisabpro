"""Saisies administratives API réelles, mémoire isolée, données historiques conservées."""
import pytest
from sqlalchemy.orm import Session
import models
from test_session132_admin_inscription import inscription, donnees
from test_session132_admin_plan_lecture import plan
from test_session132_admin_acces_invites import acces, headers


@pytest.mark.parametrize("champ,valeur", [("nom", ""), ("nom", " \t "), ("nom", "N" * 101),
                                         ("raison_sociale", ""), ("raison_sociale", "   "),
                                         ("raison_sociale", "S" * 201), ("email", "   "), ("email", "e" * 101)])
def test_inscription_invalide_refusee_avant_creation(inscription, champ, valeur):
    client, engine, appels = inscription
    data = donnees()
    data[champ] = valeur
    assert client.post("/api/auth/register", json=data).status_code == 422
    assert not appels
    with Session(engine) as db:
        assert db.query(models.Societe).count() == 0
        assert db.query(models.Utilisateur).count() == 0


def test_inscription_elimine_espaces_peripheriques_des_noms(inscription):
    client, engine, _ = inscription
    data = donnees()
    data.update(nom="  Administrateur recette  ", raison_sociale="  Société recette  ", email="  admin@recette.test  ")
    assert client.post("/api/auth/register", json=data).status_code == 200
    with Session(engine) as db:
        assert db.query(models.Societe).one().raison_sociale == "Société recette"
        user = db.query(models.Utilisateur).one()
        assert user.nom == "Administrateur recette" and user.email == "admin@recette.test"


@pytest.mark.parametrize("nom", ["", " \t ", "N" * 101])
def test_modification_nom_invalide_preserve_utilisateur(acces, nom):
    client, engine = acces
    assert client.patch("/api/utilisateurs/5", json={"nom": nom}, headers=headers()).status_code == 422
    with Session(engine) as db:
        assert db.get(models.Utilisateur, 5).nom == "Ancien administrateur"


@pytest.mark.parametrize("nom", ["", " \t ", "N" * 101])
def test_creation_utilisateur_nom_invalide_ne_cree_pas_compte(acces, nom):
    client, engine = acces
    body = {"nom": nom, "email": "admin.recette@example.com", "mot_de_passe": "Recette132!"}
    assert client.post("/api/utilisateurs", json=body, headers=headers()).status_code == 422
    with Session(engine) as db:
        assert db.query(models.Utilisateur).count() == 5


@pytest.mark.parametrize("libelle", ["  ", " A ", "\t \n"])
def test_libelle_compte_blanc_ou_trop_court_refuse_apres_trim(plan, libelle):
    client, engine = plan
    assert client.post("/api/plan-comptable/initialiser", headers=headers()).status_code == 200
    response = client.post("/api/plan-comptable", json={"numero": "11111", "libelle": libelle}, headers=headers())
    assert response.status_code == 422
    response = client.patch("/api/plan-comptable/1111", json={"libelle": libelle}, headers=headers())
    assert response.status_code == 422
    with Session(engine) as db:
        assert db.query(models.CompteSociete).filter_by(numero="1111").one().libelle == "Capital social"
        assert db.query(models.CompteSociete).count() == 2


def test_noms_et_libelles_valides_normalises_sans_alterer_comptes(plan):
    client, engine = plan
    assert client.post("/api/plan-comptable/initialiser", headers=headers()).status_code == 200
    response = client.post("/api/plan-comptable", json={"numero": "11111", "libelle": "  Capital souscrit  "}, headers=headers())
    assert response.status_code == 201 and response.json()["libelle"] == "Capital souscrit"
    response = client.patch("/api/utilisateurs/5", json={"nom": "  Ancien admin  "}, headers=headers())
    assert response.status_code == 200 and response.json()["nom"] == "Ancien admin"
    # Un PATCH sans nom doit conserver la valeur existante.
    response = client.patch("/api/utilisateurs/5", json={"role": "lecture"}, headers=headers())
    assert response.status_code == 200 and response.json()["nom"] == "Ancien admin"
