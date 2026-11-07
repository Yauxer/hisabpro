"""Recette locale isolée des données réelles (Windows/Linux).

Usage : python -X utf8 Test/run_unit_tests.py [fichiers pytest ou options]
Le banc PostgreSQL créant/supprimant un schéma n'est jamais lancé par ce runner.
"""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.environ["PYTHONUTF8"] = "1"
    if not sys.flags.utf8_mode:
        os.execv(sys.executable, [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), *sys.argv[1:]])
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT / "hisabpro-backend"))
    # Les anciens tests de fonctions pures utilisent parfois setdefault avec
    # un faux models : charger les vrais modèles garantit leur isolation.
    import models  # noqa: F401
    import pytest
    arguments = sys.argv[1:] or ["Test"]
    return pytest.main([*arguments, "--ignore=Test/test_patch07b3_postgres_sequences.py", "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
