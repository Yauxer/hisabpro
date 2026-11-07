from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "hisabpro-backend" / "routers" / "fiscalite.py"
PAGE = ROOT / "src" / "pages" / "FiscaliteIS.jsx"
CSS = ROOT / "src" / "pages" / "FiscaliteIS.module.css"
SQL = ROOT / "hisabpro-backend" / "065_reparation_liquidations_is_reference_acomptes.sql"


def test_backend_bloque_liquidation_si_reference_acomptes_indisponible():
    text = ROUTER.read_text(encoding="utf-8")
    assert 'reference_acomptes = (situation.get("acomptes") or {}).get("reference") or {}' in text
    assert 'not reference_acomptes.get("disponible") and not reference_acomptes.get("non_applicable")' in text
    assert "Référence des acomptes" in text


def test_frontend_desactive_confirmation_et_affiche_le_motif():
    text = PAGE.read_text(encoding="utf-8")
    assert "referenceAcomptesBloquante" in text
    assert "disabled={referenceAcomptesBloquante}" in text
    assert "Liquidation bloquée." in text
    css = CSS.read_text(encoding="utf-8")
    assert ".liquidationGuard" in css


def test_premier_exercice_reste_autorise_par_le_garde_fou():
    text = ROUTER.read_text(encoding="utf-8")
    assert 'not reference_acomptes.get("non_applicable")' in text


def test_script_repare_uniquement_les_photographies_sans_reference():
    text = SQL.read_text(encoding="utf-8")
    assert "DISABLE TRIGGER trg_hisabpro_fiscal_liquidation_immutable" in text
    assert "precedent.date_fin < courant.date_debut" in text
    assert "n_1.exercice = l.exercice - 1" in text
    assert "p.acomptes_reference_forcee IS NULL" in text
    assert "ENABLE TRIGGER trg_hisabpro_fiscal_liquidation_immutable" in text
