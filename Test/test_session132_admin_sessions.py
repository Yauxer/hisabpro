"""Version des nouveaux JWT et invalidation après modification du mot de passe."""
from sqlalchemy.orm import Session
import pytest
import models
from auth import create_access_token, decode_token
from datetime import datetime, timedelta
from types import SimpleNamespace
from jose import jwt
import auth as auth_module
from test_session132_admin_acces_invites import acces, headers


def version_headers(user_id=3, societe_id=1, password_hash="hash"):
    return {"Authorization": "Bearer " + create_access_token({"sub": str(user_id), "societe_id": societe_id, "role": "lecture"}, password_hash=password_hash)}


def test_jwt_versionne_ne_contient_pas_hash_de_connexion_ni_secret():
    secret_hash = "$bcrypt-sha256$valeur-confidentielle-de-recette"
    payload = decode_token(create_access_token({"sub": "1", "societe_id": 1}, password_hash=secret_hash))
    assert len(payload["pwd_version"]) == 64
    assert secret_hash not in str(payload)
    assert "password_hash" not in payload


def test_changement_mot_de_passe_invalide_toutes_nouvelles_sessions_societes(acces):
    client, engine = acces
    local = version_headers(3, 1)
    principal = version_headers(3, 2)
    assert client.get("/api/auth/me", headers=local).status_code == 200
    assert client.get("/api/auth/me", headers=principal).status_code == 200
    # Seul l'administrateur de la société principale peut changer le secret.
    response = client.patch("/api/utilisateurs/3", json={"mot_de_passe": "NouveauSecret132!"}, headers=headers(2, 2))
    assert response.status_code == 200
    assert client.get("/api/auth/me", headers=local).status_code == 401
    assert client.get("/api/auth/me", headers=principal).status_code == 401
    with Session(engine) as db:
        digest = db.get(models.Utilisateur, 3).hashed_password
    assert client.get("/api/auth/me", headers=version_headers(3, 1, digest)).status_code == 200
    response = client.post("/api/auth/login", json={"email": "lecteur@recette.test", "password": "NouveauSecret132!"})
    assert response.status_code == 200
    assert "pwd_version" in decode_token(response.json()["access_token"])


def test_switch_societe_preserve_version_du_mot_de_passe(acces):
    client, _ = acces
    response = client.post("/api/societes/switcher/1", headers=version_headers(3, 2))
    assert response.status_code == 200
    assert "pwd_version" in decode_token(response.json()["access_token"])


@pytest.mark.parametrize("version", [None, 123, "", "incorrect"])
def test_claim_version_malformee_ou_incorrecte_refusee_sans_erreur_serveur(acces, version):
    client, _ = acces
    token = create_access_token({"sub": "3", "societe_id": 1, "pwd_version": version})
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_jwt_historique_sans_version_exige_reconnexion(acces):
    client, _ = acces
    token = create_access_token({"sub": "3", "societe_id": 1})
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer " + token})
    assert r.status_code == 401 and r.json()['detail'] == 'Session ancienne : reconnectez-vous'
    assert client.get("/api/auth/me", headers=version_headers()).status_code == 200


def test_expiration_explicitement_nulle_ne_devient_pas_huit_heures(monkeypatch):
    maintenant = datetime(2026, 10, 6, 20, 0, 0)
    monkeypatch.setattr(auth_module, "datetime", SimpleNamespace(utcnow=lambda: maintenant))
    token = create_access_token({"sub": "1", "societe_id": 1}, expires_delta=timedelta(0))
    payload = jwt.decode(token, auth_module.SECRET_KEY, algorithms=[auth_module.ALGORITHM], options={"verify_exp": False})
    from calendar import timegm
    assert payload["exp"] == timegm(maintenant.utctimetuple())
