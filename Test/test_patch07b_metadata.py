"""Tests ciblés Patch 07B — métadonnées et numérotation des écritures.

Ces tests sont volontairement sans base PostgreSQL : ils vérifient les garde-fous
structurels du patch. Le trigger d'allocation atomique se teste ensuite par la
migration 014 sur PostgreSQL.
"""
from pathlib import Path
import re

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / "hisabpro-backend"


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_migration_separe_numero_interne_et_piece():
    sql = _read("014_ecriture_metadata.sql")
    assert "numero_ecriture" in sql
    assert "date_piece" in sql
    assert "ecriture_sequences" in sql
    assert "BEFORE INSERT ON ecritures" in sql
    assert "SECURITY DEFINER" in sql
    assert "trg_hisabpro_proteger_numero_ecriture" in sql


def test_numero_interne_est_unique_et_seq_par_journal():
    sql = _read("014_ecriture_metadata.sql")
    assert "ux_ecritures_numero_interne" in sql
    assert "PRIMARY KEY (societe_id, exercice, journal)" in sql
    assert "dernier_numero = ecriture_sequences.dernier_numero + 1" in sql


def test_reference_router_ne_fabrique_plus_fn_pour_banque():
    code = _read("routers/references.py")
    assert 'numero = f"{code}-{annee}-{prochain:04d}"' in code
    assert '"BQ"' in code
    assert 'prefix = "FN"' not in code
    assert "nature" in code and "numero_ecriture_interne" in code


def test_ecriture_create_garde_reference_comme_piece():
    code = _read("routers/ecritures.py")
    assert 'date_piece=getattr(data, "date_piece", None) or data.date' in code
    assert 'reference=(data.reference or "").strip() or None' in code
    assert "numero_ecriture=" not in code.split("@router.post", 1)[1].split("db.add(ecriture)", 1)[0]


def test_frontend_utilise_exercice_selectionne_et_libelle_intelligent():
    form = (PROJECT / "src/components/FormulaireEcriture.jsx").read_text(encoding="utf-8")
    assert "dateDansExercice(exercice, annee)" in form
    assert "exercice=${annee}" in form
    assert "genererLibelleIntelligent" in form
    assert "Référence du justificatif" in form
    assert "N° écriture" in form
    assert "FN°" not in form[form.index("export default function FormulaireEcriture"):]
