"""Tests rapides Patch 01. Exécution : python tests/test_patch01_validation.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from schemas import LigneEcritureCreate


def doit_refuser(**kwargs):
    try:
        LigneEcritureCreate(compte="6111", **kwargs)
    except Exception:
        return
    raise AssertionError(f"La ligne aurait dû être refusée : {kwargs}")


LigneEcritureCreate(compte="6111", debit=100.10, credit=0)
LigneEcritureCreate(compte="4411", debit=0, credit=100.10)
doit_refuser(debit=100, credit=20)
doit_refuser(debit=-1, credit=0)
doit_refuser(debit=0, credit=0)

print("Patch 01 — validation des lignes comptables : OK")
