"""07B.2 — périmètre du numéro interne, adapté au modèle 07C.2.

07B.2 reste vrai : un numéro attribué verrouille son périmètre. 07C.2 décale
simplement l'attribution de la création vers la validation, ce qui rend les vrais
brouillons à nouveau modifiables avant numérotation.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT if (ROOT / "src").exists() else ROOT.parent
BACKEND = PROJECT_ROOT / "hisabpro-backend"
FORM = PROJECT_ROOT / "src/components/FormulaireEcriture.jsx"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_api_verrouille_le_perimetre_si_un_numero_existe():
    code = _read(BACKEND / "routers/ecritures.py")
    assert "def _verifier_perimetre_numero" in code
    assert "if not numero:" in code
    assert "Journal verrouillé par le numéro définitif" in code
    assert "Exercice verrouillé par le numéro définitif" in code
    assert "Date comptable verrouillée par le numéro définitif" in code


def test_api_autorise_journal_et_exercice_sur_vrai_brouillon():
    code = _read(BACKEND / "routers/ecritures.py")
    patch_block = code.split("@router.patch", 1)[1].split("def _liberer_document_source", 1)[0]
    assert "ecriture.journal = data.journal" in patch_block
    assert "ecriture.exercice = exercice_nouveau" in patch_block
    assert "_verifier_perimetre_numero" in patch_block


def test_migration_015_conserve_les_garde_fous_historiques():
    sql = _read(BACKEND / "015_ecriture_numero_scope.sql")
    assert "OLD.societe_id IS DISTINCT FROM NEW.societe_id" in sql
    assert "OLD.exercice IS DISTINCT FROM NEW.exercice" in sql
    assert "OLD.journal IS DISTINCT FROM NEW.journal" in sql
    assert "ux_ecritures_societe_numero_interne" in sql


def test_migration_018_etend_le_verrou_a_la_date_apres_validation():
    sql = _read(BACKEND / "018_numero_ecriture_a_validation.sql")
    assert "OLD.numero_ecriture IS NULL" in sql
    assert "OLD.date IS DISTINCT FROM NEW.date" in sql
    assert "BEFORE UPDATE OF numero_ecriture, societe_id, exercice, journal, date" in sql


def test_frontend_verrouille_seulement_si_numero_definitif():
    code = _read(FORM)
    assert "const numeroVerrouille" in code
    assert "if (numeroVerrouille) return" in code
    assert "disabled={numeroVerrouille}" in code
    assert "Brouillon non numéroté" in code
