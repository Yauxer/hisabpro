from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "hisabpro-backend" / "037_compta2_modeles_ecritures.sql"
PLAN = ROOT / "src" / "data" / "planComptes.js"


def _sql():
    return MIGRATION.read_text(encoding="utf-8")


def _plan_accounts():
    src = PLAN.read_text(encoding="utf-8")
    return set(re.findall(r"compte:\s*'([^']+)'", src))


def test_compta2_migration_declares_55_modeles():
    sql = _sql()
    codes = re.findall(
        r"INSERT INTO modeles_ecritures .*?VALUES \('([^']+)'",
        sql,
        flags=re.S,
    )
    assert len(codes) == 55
    assert len(set(codes)) == 55


def test_compta2_corrige_immo_et_ir():
    sql = _sql()
    assert "'achat_immo'" in sql
    assert "'4481'" in sql
    assert "'paiement_ir'" in sql
    assert "'44525'" in sql


def test_tous_les_comptes_des_lignes_compta2_existent_dans_le_plan():
    sql = _sql()
    plan = _plan_accounts()
    comptes = re.findall(
        r"SELECT id,\s*\d+,\s*'([^']+)'",
        sql,
    )
    assert comptes
    manquants = sorted(set(comptes) - plan)
    assert manquants == []


def test_api_masque_les_modeles_incomplets():
    src = (ROOT / "hisabpro-backend" / "routers" / "modeles.py").read_text(encoding="utf-8")
    assert "COUNT(*) FROM lignes_modele" in src
    assert ">= 2" in src


def test_frontend_ne_recalcule_pas_les_modeles_complexes():
    src = (ROOT / "src" / "components" / "FormulaireEcriture.jsx").read_text(encoding="utf-8")
    assert "function modeleAutoCalculable" in src
    assert "lignes.length <= 3" in src
    assert "modeleAutoCalculable(modeleActif)" in src


def test_categories_retrouvent_les_modeles_historiques():
    src = (ROOT / "src" / "components" / "FormulaireEcriture.jsx").read_text(encoding="utf-8")
    assert "'encaissement_client'" in src
    assert "'paiement_fournisseur'" in src
    assert "'paiement_tva'" in src
    assert "'paiement_is'" in src
