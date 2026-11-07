# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
service = (BACKEND / "services" / "livre_inventaire_service.py").read_text(encoding="utf-8")
router = (BACKEND / "routers" / "inventaire.py").read_text(encoding="utf-8")

assert 'and snap["controles"]["bilan_equilibre"]' in service
assert 'and snap["controles"]["stock_rapproche"]' in service
assert 'if not ctrl.get("stock_rapproche")' in router
assert 'Stock non rapproché' in router
print("OK — Patch 05A garde-fous Livre d’inventaire")
