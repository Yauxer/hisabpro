"""Patch 07C.2 — garde-fous statiques de la numérotation à la validation."""
from pathlib import Path


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "hisabpro-backend").is_dir():
            return candidate
        if candidate.name == "hisabpro-backend":
            return candidate.parent
    raise RuntimeError("Racine HisabPro introuvable")


ROOT = _root()
BACKEND = ROOT / "hisabpro-backend"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_018_attribue_le_numero_a_la_validation_et_laisse_les_brouillons_null():
    sql = read(BACKEND / "018_numero_ecriture_a_validation.sql")
    assert "ALTER COLUMN numero_ecriture DROP NOT NULL" in sql
    assert "SET numero_ecriture = NULL" in sql
    assert "BEFORE UPDATE OF est_validee" in sql
    assert "hisabpro_numero_a_la_validation" in sql
    assert "OLD.numero_ecriture IS NULL" in sql
    assert "COALESCE(NEW.est_validee, FALSE)" in sql


def test_018_preserve_historique_et_refuse_renumerotation_silencieuse():
    sql = read(BACKEND / "018_numero_ecriture_a_validation.sql")
    assert "hp_07c2_numeros_a_conserver" in sql
    assert "audit_ecritures" in sql
    assert "séquence définitive avec rupture" in sql
    assert "Aucun historique n''a été renuméroté" in sql


def test_018_protege_continuite_chronologie_et_suppression():
    sql = read(BACKEND / "018_numero_ecriture_a_validation.sql")
    assert "derniere_date" in sql
    assert "Validation non chronologique" in sql
    assert "trg_hisabpro_interdire_suppression_numero" in sql
    assert "Suppression interdite" in sql
    assert "OLD.date IS DISTINCT FROM NEW.date" in sql


def test_backend_brouillon_redevient_modifiable_avant_numero():
    router = read(BACKEND / "routers" / "ecritures.py")
    assert "if not numero:" in router
    assert "ecriture.journal = data.journal" in router
    assert "ecriture.exercice = exercice_nouveau" in router
    assert "_verifier_chronologie_validation" in router
    assert "db.refresh(ecriture)  # récupère le numero_ecriture" in router


def test_backend_interdit_suppression_apres_numero():
    router = read(BACKEND / "routers" / "ecritures.py")
    assert "Suppression interdite : l'écriture possède déjà le numéro définitif" in router
    assert "annulation/contrepassation" in router


def test_frontend_explique_prevision_et_identifie_brouillon():
    form = read(ROOT / "src" / "components" / "FormulaireEcriture.jsx")
    journal = read(ROOT / "src" / "pages" / "Journal.jsx")
    assert "(prévision)" in form
    assert "Attribué à la validation" in form
    assert "numeroVerrouille" in form
    assert "Brouillon #" in journal
    assert "!e.numero_ecriture" in journal

# Le numéro officiel affiché est contrôlé réellement en UI/API dans
# test_e2e_ecritures_reponse_tardive801_isole.py, sans imposer un map local.
