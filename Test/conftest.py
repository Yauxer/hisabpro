"""Configuration pytest commune au dépôt HisabPro.

Les tests historiques importent les modules backend comme lorsqu'ils sont lancés
à l'intérieur de ``hisabpro-backend``. On ajoute ce dossier une seule fois au
PYTHONPATH pour rendre ``pytest Test`` exécutable depuis la racine du projet.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
