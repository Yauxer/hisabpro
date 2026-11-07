"""JWT : refus d'algorithmes inattendus et de clés publiques comme secret HMAC."""
from datetime import timedelta
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException
from jose import jwt
from jose.exceptions import JWSError
import pytest
import auth


def test_cle_publique_openssh_ne_peut_plus_signer_jwt_hmac():
    public = ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(
        serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH)
    with pytest.raises(JWSError, match="asymmetric key"):
        jwt.encode({"sub": "1", "societe_id": 1}, public, algorithm="HS256")


def test_auth_refuse_algorithme_different_du_configure():
    autre = "HS384" if auth.ALGORITHM == "HS256" else "HS256"
    token = jwt.encode({"sub": "1", "societe_id": 1}, auth.SECRET_KEY, algorithm=autre)
    with pytest.raises(HTTPException) as exc:
        auth.decode_token(token)
    assert exc.value.status_code == 401


@pytest.mark.parametrize("token", ["invalide", "eyJhbGciOiJub25lIn0.eyJzdWIiOiIxIn0."])
def test_auth_refuse_jwt_malforme_ou_non_signe(token):
    with pytest.raises(HTTPException) as exc:
        auth.decode_token(token)
    assert exc.value.status_code == 401


def test_auth_refuse_jwt_expire():
    token = auth.create_access_token({"sub": "1", "societe_id": 1}, expires_delta=timedelta(seconds=-2))
    with pytest.raises(HTTPException) as exc:
        auth.decode_token(token)
    assert exc.value.status_code == 401


@pytest.mark.parametrize("token", [None, b"token", "A" * 8193])
def test_auth_refuse_token_surdimensionne_ou_type_incorrect(token):
    with pytest.raises(HTTPException) as exc:
        auth.decode_token(token)
    assert exc.value.status_code == 401


def test_auth_refuse_entete_json_excessivement_imbrique_sans_erreur_serveur():
    import base64
    header = b'{"alg":"HS256","nested":' + b"[" * 1100 + b"0" + b"]" * 1100 + b"}"
    encoded = base64.urlsafe_b64encode(header).rstrip(b"=").decode("ascii")
    token = encoded + ".eyJzdWIiOiIxIn0.c2lnbmF0dXJl"
    assert len(token) < 8192
    with pytest.raises(HTTPException) as exc:
        auth.decode_token(token)
    assert exc.value.status_code == 401
