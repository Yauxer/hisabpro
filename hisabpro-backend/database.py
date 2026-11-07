from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DBAPIError
from fastapi import HTTPException
from dotenv import load_dotenv
import os

load_dotenv()

_env_database_url = os.getenv("DATABASE_URL")
if not _env_database_url and os.getenv("APP_ENV", "dev").strip().casefold() in ("prod", "production"):
    raise RuntimeError("DATABASE_URL manquante en production : aucun identifiant de base par défaut n'est autorisé.")
DATABASE_URL = _env_database_url or "postgresql://hisabpro:hisabpro123@localhost:5432/hisabpro"

# pool_pre_ping évite de réutiliser une connexion PostgreSQL morte après une
# coupure réseau / veille de poste ; utile aussi derrière un proxy de connexion.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Les droits sont définis par les migrations et l'administrateur PostgreSQL.
# Un démarrage ne doit jamais réaccorder INSERT/UPDATE/DELETE sur les archives
# et pistes d'audit dont les migrations ont volontairement révoqué ces droits.

# Dépendance FastAPI pour obtenir une session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    except DBAPIError as exc:
        code = getattr(exc.orig, 'pgcode', None)
        contrainte = getattr(getattr(exc.orig, 'diag', None), 'constraint_name', None)
        if (code, contrainte) in {
            ('40001', 'ck_tva_cloture_concurrence'),
            ('23514', 'ck_tva_parametres_exercice_ouvert'),
            ('23514', 'ck_journal_exercice_ouvert'),
        }:
            db.rollback()
            message = ('Une opération TVA/clôture est en cours. Réessayez.'
                       if code == '40001' else 'Exercice clôturé : les paramètres TVA sont verrouillés.')
            if contrainte == 'ck_journal_exercice_ouvert':
                message = 'Exercice clôturé : le Journal est verrouillé.'
            raise HTTPException(status_code=409, detail=message) from exc
        raise
    finally:
        db.close()
