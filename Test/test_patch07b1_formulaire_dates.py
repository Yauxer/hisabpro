"""Tests ciblés Patch 07B.1 — UX dates et référence du justificatif."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT if (ROOT / "src").exists() else ROOT.parent
FORM = PROJECT_ROOT / "src/components/FormulaireEcriture.jsx"


def _form():
    return FORM.read_text(encoding="utf-8")


def test_libelles_metier_sont_clairs():
    code = _form()
    assert "Date comptable *" in code
    assert "Date du justificatif" in code
    assert "Référence du justificatif" in code
    assert "Date d'écriture *" not in code


def test_justificatif_est_synchronise_par_defaut():
    code = _form()
    assert "datePieceInitiale === dateInitiale" in code
    assert "Même date pour le justificatif" in code
    assert "if (datePieceAuto) setDatePiece(v)" in code
    assert "if (memeDate) setDatePiece(date)" in code


def test_date_justificatif_est_desactivee_en_mode_synchro():
    code = _form()
    assert "disabled={datePieceAuto}" in code
    assert "checked={datePieceAuto}" in code
    assert "date_piece: datePiece || date" in code
