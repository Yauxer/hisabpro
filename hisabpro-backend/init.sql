-- ============================================================
-- HisabPro — Initialisation PostgreSQL
-- Exécute ce script UNE SEULE FOIS pour créer la base
-- ============================================================

-- Crée l'utilisateur et la base
CREATE USER hisabpro WITH PASSWORD 'hisabpro123';
CREATE DATABASE hisabpro OWNER hisabpro;
GRANT ALL PRIVILEGES ON DATABASE hisabpro TO hisabpro;

-- Se connecter à la base hisabpro avant de continuer :
-- \c hisabpro

-- Les tables sont créées automatiquement par SQLAlchemy au démarrage
-- (Base.metadata.create_all dans main.py)

-- ── Données de démo (optionnel) ──────────────────────────────────────────────
-- Insère une société et un utilisateur admin de test

-- Note : le mot de passe 'admin123' est haché avec bcrypt
-- Pour générer un nouveau hash : python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('admin123'))"

INSERT INTO societes (raison_sociale, identifiant_fiscal, ice, ville, exercice_debut)
VALUES ('Société Demo SARL', '12345678', '000000000000001', 'Casablanca', 2025)
ON CONFLICT DO NOTHING;

-- L'utilisateur admin sera créé via /api/auth/register
