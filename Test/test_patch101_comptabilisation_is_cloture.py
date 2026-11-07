from decimal import Decimal
from pathlib import Path

from services.cloture_service import construire_cascade_resultat

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
FISCAL = (BACK / "routers" / "fiscalite.py").read_text(encoding="utf-8")
CLOTURE = (BACK / "routers" / "cloture.py").read_text(encoding="utf-8")
PAGE = (ROOT / "src" / "pages" / "Cloture.jsx").read_text(encoding="utf-8")
SQL = (BACK / "070_reparation_is_cloture_historique_2026.sql").read_text(encoding="utf-8")


def test_cascade_cloture_integre_impot_courant_dans_resultat_net():
    # Convention du service : débit - crédit. Le bénéfice avant IS vaut
    # 143 940,00 - 19 075,12 = 124 864,88 MAD.
    # Pour éviter de coupler le test au détail des comptes de recette, on
    # remplace les charges par un seul compte 61 conservant le total observé.
    soldes = {
        "7111": Decimal("-143940.00"),
        "6111": Decimal("19075.12"),
        "6701": Decimal("24972.98"),
    }
    lignes, resultat, compte_resultat = construire_cascade_resultat(soldes)
    assert resultat == Decimal("99891.90")
    assert compte_resultat == "1191"
    assert any(l["compte"] == "6701" and l["credit"] == Decimal("24972.98") for l in lignes)
    assert any(l["compte"] == "1191" and l["credit"] == Decimal("99891.90") for l in lignes)


def test_cloture_comptabilise_is_ou_cm_avant_la_cascade():
    assert "def _comptabiliser_is_cloture" in CLOTURE
    assert 'compte_charge = etat_is.get("compte_charge_attendu") or "6701"' in CLOTURE
    assert 'models.LigneEcriture(compte=compte_charge' in CLOTURE
    assert 'models.LigneEcriture(compte="4453"' in CLOTURE
    assert "_comptabiliser_is_cloture(db, societe_id, exercice_obj, fiscalite_is, current_user)" in CLOTURE
    assert CLOTURE.index("_comptabiliser_is_cloture(db, societe_id, exercice_obj, fiscalite_is, current_user)") < CLOTURE.index("construire_cascade_resultat(soldes)")


def test_liquidation_refuse_un_impot_courant_non_comptabilise():
    assert '"comptabilisation_is": comptabilisation_is' in FISCAL
    assert "Liquidation bloquée : l'impôt courant attendu" in FISCAL
    assert "La clôture comptable doit d'abord constater l'impôt sur les résultats." in FISCAL
    assert 'compte_attendu = "6705" if nature == "CM" else "6701"' in FISCAL
    assert 'compte.startswith(("6701", "6705"))' in FISCAL


def test_apres_cloture_les_references_de_liquidation_restent_completables():
    # Ne pas reproduire le blocage trop large qui aurait empêché, après clôture,
    # de documenter la référence annuelle d'acomptes avant liquidation.
    assert "def _verifier_parametres_is_modifiables" in FISCAL
    assert "_PARAMETRES_IMPACTANT_IMPOT_COURANT" in FISCAL
    assert '"acomptes_reference_forcee"' not in FISCAL.split("_PARAMETRES_IMPACTANT_IMPOT_COURANT = (", 1)[1].split(")", 1)[0]
    assert '"css_benefice_reference_forcee"' not in FISCAL.split("_PARAMETRES_IMPACTANT_IMPOT_COURANT = (", 1)[1].split(")", 1)[0]
    assert "_verifier_parametres_is_modifiables(db, societe_id, exercice, data)" in FISCAL


def test_reparation_2026_est_append_only_et_propage_les_an_2027():
    assert "REGUL-IS-2026" in SQL
    assert "CLOTURE-2026-CORR-IS" in SQL
    assert "AN-CORR-IS-2027" in SQL
    assert "'6705' ELSE '6701'" in SQL
    assert "'4453'" in SQL
    assert "'8800'" in SQL
    assert "'1191'" in SQL and "'1199'" in SQL
    assert "ALTER TABLE ecritures DISABLE TRIGGER trg_hisabpro_verifier_periode_ecriture" in SQL
    assert "ALTER TABLE ecritures ENABLE TRIGGER trg_hisabpro_verifier_periode_ecriture" in SQL
    # Le patch crée des écritures correctives : il ne réécrit ni la liquidation
    # fiscale figée, ni la trace historique de clôture, ni des lignes existantes.
    upper = SQL.upper()
    assert "UPDATE FISCAL_LIQUIDATIONS_IS" not in upper
    assert "UPDATE CLOTURES_EXERCICE" not in upper
    assert "DELETE FROM ECRITURES" not in upper
    assert "DELETE FROM LIGNES_ECRITURE" not in upper
    assert "UPDATE LIGNES_ECRITURE" not in upper


def test_ecran_cloture_annonce_le_resultat_net_apres_impot():
    assert "resultat_net_apres_is" in PAGE
    assert "Résultat comptable avant IS" in PAGE
    assert "Résultat net après impôt" in PAGE
    assert "sera comptabilisé automatiquement avant le soldage" in PAGE
