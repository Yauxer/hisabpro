"""Paramètres société sur API réelle isolée, sans base comptable réelle."""
import pytest
from sqlalchemy.orm import Session
import models
from routers import societe
from test_session132_admin_acces_invites import acces, headers


@pytest.fixture
def parametres(acces):
    client, engine = acces
    models.ModuleActif.__table__.create(engine)
    client.app.include_router(societe.router)
    yield client, engine


@pytest.mark.parametrize("capital", ["NaN", "Infinity", "-Infinity", -1, True, False])
def test_capital_invalide_refuse_sans_mutation(parametres, capital):
    client, engine = parametres
    response = client.patch("/api/societe/moi", json={"capital_social": capital}, headers=headers())
    assert response.status_code == 400
    with Session(engine) as db:
        assert db.get(models.Societe, 1).capital_social == 0
        assert db.get(models.Societe, 2).capital_social == 0


@pytest.mark.parametrize("nom", ["", "   ", "S" * 201])
def test_raison_sociale_invalide_preserve_societe(parametres, nom):
    client, engine = parametres
    assert client.patch("/api/societe/moi", json={"raison_sociale": nom}, headers=headers()).status_code == 422
    with Session(engine) as db:
        assert db.get(models.Societe, 1).raison_sociale == "Société recette 1"


@pytest.mark.parametrize("capital", [0, 120000.25])
def test_capital_et_nom_valides_seule_societe_active_modifiee(parametres, capital):
    client, engine = parametres
    response = client.patch("/api/societe/moi", json={"capital_social": capital, "raison_sociale": "  Société recette mise à jour  "}, headers=headers())
    assert response.status_code == 200
    assert response.json()["capital_social"] == capital
    assert response.json()["raison_sociale"] == "Société recette mise à jour"
    with Session(engine) as db:
        assert db.get(models.Societe, 2).raison_sociale == "Société recette 2"
        assert db.get(models.Societe, 2).capital_social == 0


@pytest.mark.parametrize("societe_id", [1, 2])
def test_non_administrateurs_ne_modifient_pas_parametres(parametres, societe_id):
    client, engine = parametres
    response = client.patch("/api/societe/moi", json={"capital_social": 120000}, headers=headers(3, societe_id))
    assert response.status_code == 403
    with Session(engine) as db:
        assert db.get(models.Societe, societe_id).capital_social == 0


def test_parametres_facultatifs_absents_ne_remplacent_pas_historique(parametres):
    client, engine = parametres
    with Session(engine) as db:
        db.get(models.Societe, 1).capital_social = 120000
        db.commit()
    response = client.patch("/api/societe/moi", json={"raison_sociale": None, "capital_social": None}, headers=headers())
    assert response.status_code == 200
    assert response.json()["raison_sociale"] == "Société recette 1"
    assert response.json()["capital_social"] == 120000


@pytest.mark.parametrize("valeur", ["NaN", "Infinity", "-Infinity"])
def test_capital_json_non_standard_erreur_serialisable_et_sans_mutation(parametres, valeur):
    client, engine = parametres
    response = client.patch("/api/societe/moi", content='{"capital_social":' + valeur + '}',
                            headers={**headers(), "Content-Type": "application/json"})
    assert response.status_code == 400
    assert "montant fini" in response.json()["detail"]
    with Session(engine) as db:
        assert db.get(models.Societe, 1).capital_social == 0
