"""Patch 04B.1 — contrat d’authentification avec rôle."""
from schemas import Token


def test_token_expose_role():
    token = Token(access_token="jwt-test", role="admin")
    assert token.role == "admin"
    assert token.token_type == "bearer"


def test_token_requires_role():
    try:
        Token(access_token="jwt-test")
    except Exception:
        return
    raise AssertionError("Token doit exiger le rôle utilisateur")
