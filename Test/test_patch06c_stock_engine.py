# -*- coding: utf-8 -*-
"""Tests de garde-fou du Patch 06C.

Ils sont volontairement indépendants d'une base PostgreSQL : le test final E2E
sera exécuté dans HisabPro avec une société/exercice propres.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"


def _load_stock_engine():
    # Le module importe ``models`` uniquement pour ses opérations DB. Les helpers
    # de calcul testés ici n'en ont pas besoin.
    old = sys.modules.get("models")
    sys.modules["models"] = types.ModuleType("models")
    try:
        spec = importlib.util.spec_from_file_location(
            "stock_movement_service_test", BACKEND / "services" / "stock_movement_service.py"
        )
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        if old is None:
            sys.modules.pop("models", None)
        else:
            sys.modules["models"] = old


def test_cout_net_ligne_remises_en_cascade():
    svc = _load_stock_engine()
    ligne = types.SimpleNamespace(prix_unitaire=100, remise=10, remise2=5, rabais=2)
    # 100 * 90% * 95% - 2 = 83.50
    assert svc.cout_net_ligne(ligne) == 83.5


def test_reconstitution_cmup_legacy_entree():
    svc = _load_stock_engine()
    # Stock avant 10 à CMUP 10, entrée 5 à 20 => CMUP après 13.3333.
    mvt = types.SimpleNamespace(
        type="entree", stock_avant=10, stock_apres=15, quantite=5,
        cout_unitaire=20, cmup_apres=13.3333, cmup_avant=None,
    )
    assert abs(float(svc._cmup_avant_legacy(mvt)) - 9.99995) < 0.001


def test_aucun_writer_stock_hors_moteur_unique():
    cibles = [
        BACKEND / "routers" / "articles.py",
        BACKEND / "routers" / "commercial.py",
        BACKEND / "routers" / "factures.py",
        BACKEND / "services" / "stock_service.py",
    ]
    for path in cibles:
        text = path.read_text(encoding="utf-8")
        assert "models.MouvementStock(" not in text, f"Constructeur direct dans {path.name}"
        assert not re.search(r"\.stock_actuel\s*=", text), f"Mutation directe dans {path.name}"


def test_migration_idempotence_et_tracabilite():
    sql = (BACKEND / "012_stock_movement_engine.sql").read_text(encoding="utf-8")
    for token in [
        "date_mouvement",
        "cmup_avant",
        "source_type",
        "source_ligne_id",
        "cle_idempotence",
        "annule_mouvement_id",
        "uq_mouvements_stock_idempotence_06c",
        "uq_mouvements_stock_annulation_06c",
        "CHECK (quantite > 0) NOT VALID",
    ]:
        assert token in sql


if __name__ == "__main__":
    tests = [
        test_cout_net_ligne_remises_en_cascade,
        test_reconstitution_cmup_legacy_entree,
        test_aucun_writer_stock_hors_moteur_unique,
        test_migration_idempotence_et_tracabilite,
    ]
    for test in tests:
        test()
    print("OK — 4 tests Patch 06C moteur unique des mouvements de stock")
