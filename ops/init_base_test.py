"""Initialise une base PostgreSQL VIERGE de test pour HisabPro.

Étapes : rôle « hisabpro » (requis par les GRANT des migrations), tables ORM
(create_all), puis migrations SQL 001→132 via ops/migrations_hisabpro.py.
À n'utiliser QUE sur une base vide de test (Neon, local…), jamais en production.

Usage (depuis la racine du projet) :
    DATABASE_URL=postgresql://... python ops/init_base_test.py
"""
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

RACINE = Path(__file__).resolve().parents[1]
BACK = RACINE / 'hisabpro-backend'

url = os.environ.get('DATABASE_URL')
if not url:
    sys.exit('DATABASE_URL manquante.')
nom_base = make_url(url).database

engine = create_engine(url)
with engine.begin() as db:
    if db.scalar(text("SELECT to_regclass('public.ecritures') IS NOT NULL")):
        print("Base déjà initialisée : rien à faire.")
        sys.exit(0)
    if not db.scalar(text("SELECT 1 FROM pg_roles WHERE rolname = 'hisabpro'")):
        db.execute(text('CREATE ROLE hisabpro NOLOGIN'))
        print('Rôle hisabpro créé.')

sys.path.insert(0, str(BACK))
os.environ.setdefault('PYTHON_DOTENV_DISABLED', '1')
import models  # noqa: E402,F401  (enregistre les modèles)
from database import Base  # noqa: E402

Base.metadata.create_all(engine)
print(f'{len(Base.metadata.tables)} tables ORM créées.')

# Toutes les migrations dans l'ordre, sauf les réparations historiques et le registre.
sys.path.insert(0, str(RACINE / 'ops'))
from migrations_hisabpro import fichiers, numero, REPARATIONS, REGISTRE  # noqa: E402
liste = [p.name for p in fichiers(BACK) if numero(p.name) not in REPARATIONS and p.name != REGISTRE]
subprocess.run([sys.executable, str(RACINE / 'ops' / 'migrations_hisabpro.py'), 'appliquer',
                '--base-attendue', nom_base, '--fichier', *liste], check=True)
print('Base prête.')
