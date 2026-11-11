# HisabPro

Application marocaine de facturation, de comptabilité, de fiscalité et de paie, pensée pour les TPE/PME et les cabinets comptables. Elle suit le plan comptable marocain (CGNC) et prépare les déclarations (TVA, IS, liasse fiscale, paie).

> HisabPro n'est ni certifié ni homologué par l'administration. Les déclarations se déposent sur les portails officiels (DGI, Damancom).

## Documentation

- **[Mode d'emploi utilisateur](docs/GUIDE_UTILISATEUR.md)** : ce que fait chaque écran, des parcours pas à pas et les questions fréquentes.
- [Guide d'exploitation](docs/EXPLOITATION_HISABPRO.md) : installation, migrations, sauvegardes, déploiement.

## Structure

| Dossier | Contenu |
|---|---|
| `src/` | Interface web (React + Vite). |
| `hisabpro-backend/` | API (FastAPI + SQLAlchemy) et migrations SQL numérotées. |
| `ops/` | Outils d'exploitation : migrations, sauvegarde PostgreSQL, initialisation d'une base de test. |
| `Test/` | Tests automatisés (unitaires, PostgreSQL isolé, navigateur). |
| `docs/` | Documentation. |

## Lancer en local

Prérequis : Node.js, Python 3.11+, PostgreSQL.

```bash
# API
cd hisabpro-backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # sous Windows
cp .env.example .env    # puis renseigner DATABASE_URL et SECRET_KEY
python main.py          # http://localhost:8000

# Interface (dans un autre terminal, à la racine)
npm install
npm run dev             # l'adresse s'affiche dans le terminal (chemin /hisabpro/)
```

Les migrations SQL se passent avec `ops/migrations_hisabpro.py`, comme décrit dans le guide d'exploitation.
