from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src" / "pages" / "FiscaliteIS.jsx"


def test_synthese_liquidation_affiche_le_montant_declare_deja_impute():
    text = SOURCE.read_text(encoding="utf-8")
    expected = (
        "Retenues déjà imputées sur acomptes</span>"
        "<strong>{mad(creditsIS.total_deja_impute_acomptes)}</strong>"
    )
    assert expected in text


def test_synthese_ne_reutilise_plus_le_montant_recalcule_des_acomptes():
    text = SOURCE.read_text(encoding="utf-8")
    old = (
        "Retenues déjà imputées sur acomptes</span>"
        "<strong>{mad(liquidation.credits_ras_deja_imputes_sur_acomptes)}</strong>"
    )
    assert old not in text


def test_calcul_du_solde_reste_inchange():
    text = SOURCE.read_text(encoding="utf-8")
    assert "credits_is_disponibles_liquidation" in text
    assert "liquidation.solde_a_payer" in text
