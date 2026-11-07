"""Démarrage auth synthétique, sans fichier .env ni connexion de base."""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def charger_auth(monkeypatch, environnement, secret):
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda: None)
    monkeypatch.setenv("APP_ENV", environnement)
    if secret is None:
        monkeypatch.delenv("SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("SECRET_KEY", secret)
    namespace = {"__name__": "auth_configuration_synthetique"}
    path = ROOT / "hisabpro-backend" / "auth.py"
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
    return namespace


@pytest.mark.parametrize("environnement", ["prod", "production", " Production ", " PROD\t"])
@pytest.mark.parametrize("secret", [None, "", "   ", "dev-secret-change-in-production"])
def test_production_refuse_absence_blanc_ou_secret_public(monkeypatch, environnement, secret):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        charger_auth(monkeypatch, environnement, secret)


@pytest.mark.parametrize("environnement", ["production", " Production "])
def test_production_conserve_exactement_secret_prive(monkeypatch, environnement):
    # Secret fictif, avec espaces significatifs : ne pas altérer la signature.
    secret = "  secret-prive-uniquement-pour-recette-132  "
    configuration = charger_auth(monkeypatch, environnement, secret)
    assert configuration["SECRET_KEY"] == secret
    token = configuration["create_access_token"]({"sub": "1", "societe_id": 1})
    assert configuration["decode_token"](token)["societe_id"] == 1


def test_developpement_reste_utilisable_sans_secret(monkeypatch):
    configuration = charger_auth(monkeypatch, "dev", None)
    assert configuration["SECRET_KEY"] == "dev-secret-change-in-production"


@pytest.mark.parametrize("environnement", ["prod", "production", " Production ", " PROD\t"])
def test_production_refuse_database_url_absente_sans_connexion(monkeypatch, environnement):
    import dotenv
    import sqlalchemy
    monkeypatch.setattr(dotenv, "load_dotenv", lambda: None)
    monkeypatch.setenv("APP_ENV", environnement)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    creations = []
    monkeypatch.setattr(sqlalchemy, "create_engine", lambda *args, **kwargs: creations.append(args))
    path = ROOT / "hisabpro-backend" / "database.py"
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), {"__name__": "database_synthetique"})
    assert not creations
