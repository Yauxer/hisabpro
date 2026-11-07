# -*- coding: utf-8 -*-
"""Non-régression : fonctions TVA SQL pour les champs Float des documents."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"


def test_060_signature_sql_de_la_fonction_initiale_et_surcharge():
    initial = (BACK / "033_conformite_tva_frais.sql").read_text(encoding="utf-8")
    migration = (BACK / "060_compatibilite_tva_double_precision.sql").read_text(encoding="utf-8")
    assert "hisabpro_tva_combinaison_valide(p_date DATE, p_taux NUMERIC, p_qualification VARCHAR)" in initial
    assert re.search(r"p_taux\s+DOUBLE PRECISION", migration)
    assert "p_taux::NUMERIC" in migration
    assert "public.hisabpro_tva_combinaison_valide(" in migration


def test_060_toutes_les_colonnes_flottantes_sont_couvertes():
    models = (BACK / "models.py").read_text(encoding="utf-8")
    trigger = (BACK / "033_conformite_tva_frais.sql").read_text(encoding="utf-8")
    for col in ("frais_transport_tva", "frais_emballage_tva"):
        assert re.search(rf"\b{col}\s*= Column\(Float", models)
        assert f"NEW.{col}" in trigger
    assert re.search(r"\btva\s*= Column\(Float", models)
    assert "NEW.tva, NEW.qualification_tva" in trigger


def test_060_garde_les_controles_et_est_rejouable():
    migration = (BACK / "060_compatibilite_tva_double_precision.sql").read_text(encoding="utf-8")
    assert "CREATE OR REPLACE FUNCTION public.hisabpro_tva_combinaison_valide" in migration
    assert "033_conformite_tva_frais.sql" in migration
    assert "GRANT EXECUTE" in migration
    assert "20.0::DOUBLE PRECISION" in migration
    assert "0.0::DOUBLE PRECISION" in migration
    assert "DROP TRIGGER" not in migration
    assert "DROP FUNCTION" not in migration
    assert "UPDATE factures" not in migration
    assert migration.count("BEGIN;") == 1
    assert migration.strip().endswith("COMMIT;")
