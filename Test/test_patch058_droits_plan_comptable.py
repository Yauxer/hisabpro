"""Tests de non-régression du correctif des permissions du plan comptable."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"


def test_referentiel_cgnc_reste_lecture_seule_pour_application():
    source = (BACK / "services" / "plan_comptable.py").read_text(encoding="utf-8")
    ast.parse(source)
    bloc = source.split("def assurer_plan_societe(", 1)[1].split("\ndef libelle_compte(", 1)[0]
    assert "db.query(models.CompteCGNCReference).all()" in bloc
    assert "db.add_all(refs_manquantes)" not in bloc
    assert "models.CompteCGNCReference(" not in bloc
    assert "db.add_all(ajouts)" in bloc
    assert "Référentiel CGNC vide" in bloc


def test_migration_permissions_cible_uniquement_les_objets_requis():
    sql = (BACK / "058_droits_plan_comptable.sql").read_text(encoding="utf-8")
    assert "GRANT SELECT ON TABLE public.plan_comptable_cgnc_reference" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.comptes_societe" in sql
    assert "pg_get_serial_sequence('public.comptes_societe', 'id')" in sql
    assert "GRANT USAGE, SELECT ON SEQUENCE" in sql
    assert "to_regclass('public.plan_comptable_cgnc_reference')" in sql
    assert "GRANT ALL PRIVILEGES ON ALL TABLES" not in sql
    assert "COMMIT;" in sql
