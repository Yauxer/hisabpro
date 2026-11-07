from datetime import date
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND / "services"))

import fiscalite_css_service as css_service
import fiscalite_credits_service as credits_service
import fiscalite_acomptes_service as acomptes_service


def test_css_sous_seuil_un_million_non_due():
    r = css_service.calculer_css(annee=2026, benefice_reference=999999, exercice_reference=2025)
    assert r["disponible"] is True
    assert r["taux"] == Decimal("0.000")
    assert r["montant_du"] == Decimal("0.00")


def test_css_taux_proportionnels_aux_seuils():
    assert css_service.taux_css(1_000_000) == Decimal("1.500")
    assert css_service.taux_css(4_999_999) == Decimal("1.500")
    assert css_service.taux_css(5_000_000) == Decimal("2.500")
    assert css_service.taux_css(10_000_000) == Decimal("3.500")
    assert css_service.taux_css(40_000_000) == Decimal("5.000")
    r = css_service.calculer_css(annee=2026, benefice_reference=8_000_000, exercice_reference=2025)
    assert r["montant_du"] == Decimal("200000.00")


def test_css_reference_forcee_et_echeance_trois_mois():
    r = css_service.calculer_css(
        annee=2026,
        benefice_reference=None,
        exercice_reference=2025,
        date_fin_reference=date(2025, 12, 31),
        reference_forcee=2_000_000,
    )
    assert r["source"] == "manuel"
    assert r["date_echeance"] == date(2026, 3, 31)
    assert r["montant_du"] == Decimal("30000.00")


def test_css_exoneration_permanente_ne_change_pas_la_base_mais_annule_montant():
    r = css_service.calculer_css(
        annee=2026, benefice_reference=3_000_000, exercice_reference=2025, exoneration_permanente=True
    )
    assert r["base"] == Decimal("3000000.00")
    assert r["taux"] == Decimal("1.500")
    assert r["montant_du"] == Decimal("0.00")
    assert r["exoneree_permanente"] is True


def test_css_reference_indisponible_est_explicitement_signalee():
    r = css_service.calculer_css(annee=2026, benefice_reference=None, exercice_reference=2025)
    assert r["disponible"] is False
    assert r["source"] == "indisponible"


def test_credits_is_excluent_la_fraction_deja_imputee_sur_acomptes():
    r = credits_service.construire_credits_is([
        {"id": 1, "type": "pprf", "montant": 10000, "montant_deja_impute_acomptes": 3000},
        {"id": 2, "type": "retenue_tiers", "montant": 5000, "montant_deja_impute_acomptes": 0},
    ])
    assert r["total_montant"] == Decimal("15000.00")
    assert r["total_deja_impute_acomptes"] == Decimal("3000.00")
    assert r["total_disponible_liquidation"] == Decimal("12000.00")
    assert r["par_type"]["pprf"] == Decimal("7000.00")


def test_liquidation_impute_pprf_puis_tiers_puis_acomptes():
    credits = {
        "par_type": {
            "pprf": Decimal("10000"),
            "retenue_tiers": Decimal("7000"),
            "autre": Decimal("0"),
        }
    }
    acomptes = {"total_verse": Decimal("20000"), "credit_n_1_impute": Decimal("5000")}
    r = acomptes_service.calculer_liquidation(
        impot_du_avant_acomptes=30000, situation_acomptes=acomptes, credits_is=credits
    )
    assert r["credits_is_appliques_detail"]["pprf"] == Decimal("10000.00")
    assert r["credits_is_appliques_detail"]["retenue_tiers"] == Decimal("7000.00")
    assert r["acomptes_appliques_liquidation"] == Decimal("13000.00")
    assert r["solde_a_payer"] == Decimal("0.00")
    assert r["excedent_acomptes"] == Decimal("12000.00")


def test_liquidation_separe_excedent_credits_et_acomptes():
    credits = {"par_type": {"pprf": Decimal("15000"), "retenue_tiers": 0, "autre": 0}}
    acomptes = {"total_verse": Decimal("10000"), "credit_n_1_impute": 0}
    r = acomptes_service.calculer_liquidation(
        impot_du_avant_acomptes=10000, situation_acomptes=acomptes, credits_is=credits
    )
    assert r["excedent_credits_is"] == Decimal("5000.00")
    assert r["excedent_acomptes"] == Decimal("10000.00")
    assert r["excedent_total"] == Decimal("15000.00")


def test_ancien_calcul_liquidation_reste_compatible_sans_credits():
    r = acomptes_service.calculer_liquidation(
        impot_du_avant_acomptes=50000,
        situation_acomptes={"total_verse": Decimal("30000"), "credit_n_1_impute": Decimal("5000")},
    )
    assert r["acomptes_et_credit_imputables"] == Decimal("35000.00")
    assert r["solde_a_payer"] == Decimal("15000.00")



def test_retenue_deja_imputee_sur_acompte_couvre_acompte_sans_double_compte():
    reference = {"disponible": True, "montant_annuel": Decimal("40000.00")}
    situation = acomptes_service.construire_acomptes(
        date_debut=date(2026, 1, 1),
        reference=reference,
        paiements=[],
        excedent_precedent=0,
        credits_ras_deja_imputes=6000,
        date_reference=date(2026, 1, 1),
    )
    assert situation["acomptes"][0]["montant_du"] == Decimal("10000.00")
    assert situation["acomptes"][0]["credit_ras_impute"] == Decimal("6000.00")
    assert situation["acomptes"][0]["montant_net_a_verser"] == Decimal("4000.00")
    assert situation["credit_ras_impute"] == Decimal("6000.00")

    credits = credits_service.construire_credits_is([
        {"id": 1, "type": "pprf", "montant": 10000, "montant_deja_impute_acomptes": 6000},
    ])
    liquidation = acomptes_service.calculer_liquidation(
        impot_du_avant_acomptes=12000, situation_acomptes=situation, credits_is=credits
    )
    # 6 000 déjà utilisés sur les acomptes + 4 000 restant à la liquidation.
    assert liquidation["credits_ras_deja_imputes_sur_acomptes"] == Decimal("6000.00")
    assert liquidation["credits_is_disponibles_liquidation"] == Decimal("4000.00")
    assert liquidation["solde_a_payer"] == Decimal("2000.00")


def test_autre_credit_exige_justification_dans_api_et_sql():
    sql = (BACKEND / "025_css_credits_is.sql").read_text(encoding="utf-8")
    router = (BACKEND / "routers" / "fiscalite.py").read_text(encoding="utf-8")
    models = (BACKEND / "models.py").read_text(encoding="utf-8")
    assert "ck_fiscal_credit_is_autre_justifie" in sql
    assert "ck_fiscal_credit_is_autre_justifie" in models
    assert 'self.type == "autre"' in router
    assert "Une justification est obligatoire" in router

def test_sql_router_api_ui_exposent_patch_08_6():
    sql = (BACKEND / "025_css_credits_is.sql").read_text(encoding="utf-8")
    router = (BACKEND / "routers" / "fiscalite.py").read_text(encoding="utf-8")
    api = (ROOT / "src" / "services" / "api.js").read_text(encoding="utf-8")
    page = (ROOT / "src" / "pages" / "FiscaliteIS.jsx").read_text(encoding="utf-8")
    models = (BACKEND / "models.py").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS fiscal_credits_is" in sql
    assert "CREATE TABLE IF NOT EXISTS fiscal_css_paiements" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE fiscal_credits_is TO hisabpro" in sql
    assert "class FiscalCreditIS" in models
    assert "class FiscalCSSPaiement" in models
    assert "contribution_solidarite" in router
    assert "/credits" in router
    assert "enregistrerPaiementCSS" in api
    assert "Contribution sociale de solidarité" in page
    assert "Retenues & crédits imputables sur l'IS" in page
    assert "Retenues imputées" in page
    assert "credits_ras_deja_imputes=credits_is" in router
