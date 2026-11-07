"""Tests statiques du Patch 07A — aucune base n'est modifiée."""
from pathlib import Path
import ast

PATCH_ROOT = Path(__file__).resolve().parents[1]
BACKEND = PATCH_ROOT / "hisabpro-backend"


def test_router_python_syntax_and_routes():
    src = (BACKEND / "routers" / "ecritures.py").read_text(encoding="utf-8")
    ast.parse(src)
    assert '@router.get("/{ecriture_id}/audit")' in src
    assert '@router.get("/audit/journal")' in src
    assert 'class ContrepasserIn(BaseModel)' in src
    assert '@router.post("/{ecriture_id}/contrepasser")' in src


def test_transaction_local_actor_context():
    src = (BACKEND / "routers" / "ecritures.py").read_text(encoding="utf-8")
    assert "set_config('hisabpro.audit_actor_id', :v, true)" in src
    assert "set_config('hisabpro.audit_societe_id', :v, true)" in src
    assert "set_config('hisabpro.audit_action', :v, true)" in src
    assert "set_config('hisabpro.audit_motif', :v, true)" in src


def test_migration_has_append_only_guards_and_baseline():
    sql = (BACKEND / "013_audit_ecritures.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS audit_ecritures" in sql
    assert "baseline_initiale" in sql and "baseline_ligne" in sql
    assert "trg_hisabpro_audit_ecritures" in sql
    assert "trg_hisabpro_audit_lignes_ecriture" in sql
    assert "trg_hisabpro_audit_append_only" in sql
    assert "REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON audit_ecritures FROM hisabpro" in sql
    lowered = sql.lower()
    assert "update ecritures set" not in lowered
    assert "update lignes_ecriture set" not in lowered


def test_frontend_exposes_history_and_reason():
    journal = (PATCH_ROOT / "src" / "pages" / "Journal.jsx").read_text(encoding="utf-8")
    api = (PATCH_ROOT / "src" / "services" / "api.js").read_text(encoding="utf-8")
    ctx = (PATCH_ROOT / "src" / "data" / "EcrituresContext.jsx").read_text(encoding="utf-8")
    assert "Piste d'audit" in journal
    assert "contrepassation traçable" in journal
    assert "ecrituresAPI.audit(e.id)" in journal
    assert "contrepasser(id, payload = {})" in api
    assert "contrepasserEcriture(id, payload = {})" in ctx


if __name__ == "__main__":
    tests = [
        test_router_python_syntax_and_routes,
        test_transaction_local_actor_context,
        test_migration_has_append_only_guards_and_baseline,
        test_frontend_exposes_history_and_reason,
    ]
    for test in tests:
        test()
    print("OK — 4 tests Patch 07A piste d'audit comptable")
