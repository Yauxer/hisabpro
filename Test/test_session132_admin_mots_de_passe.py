"""Cryptographie Passlib réelle : compatibilité legacy et secrets non tronqués."""
from fastapi import HTTPException
from passlib.hash import bcrypt
import pytest

from auth import hash_password, verify_password, valider_mot_de_passe


@pytest.mark.parametrize("secret", ["A" * 72 + "suffixe1", "é" * 40 + "suffixe1"])
def test_nouveaux_mots_de_passe_ne_sont_pas_tronques_a_72_octets(secret):
    digest = hash_password(secret)
    assert digest.startswith("$bcrypt-sha256$")
    assert verify_password(secret, digest)
    assert not verify_password(secret[:-1] + "2", digest)
    assert not verify_password(secret[:36], digest)


def test_hash_bcrypt_historique_reste_verifiable_sans_recriture():
    digest = bcrypt.hash("AncienSecret132!")
    assert verify_password("AncienSecret132!", digest)
    assert not verify_password("AutreSecret132!", digest)
    assert digest.startswith("$2")


@pytest.mark.parametrize("secret", ["court", "12345678", " Password ", "azertyui", "motdepasse", " " * 8,
                                  "Secret\x00invalide", "é" * 2049, "A" * 4097])
def test_politique_commune_refuse_secrets_faibles_ou_malformes(secret):
    with pytest.raises(HTTPException) as exc:
        valider_mot_de_passe(secret)
    assert exc.value.status_code == 400


@pytest.mark.parametrize("secret,digest", [("Recette132!", "hash-invalide"), ("Secret\x00invalide", "hash"),
                                        (None, "hash"), ("A" * 4097, "hash"), ("Recette132!", None)])
def test_verification_malformee_retourne_faux_sans_erreur_serveur(secret, digest):
    assert verify_password(secret, digest) is False
