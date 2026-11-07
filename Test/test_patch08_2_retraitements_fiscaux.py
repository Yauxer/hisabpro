from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND / "services"))

import fiscalite_retraitements_service as service


def _by_category(items, category):
    return next((x for x in items if x["categorie"] == category), None)


def test_amendes_et_liberalites_sont_reintegrees_automatiquement():
    r = service.analyser_retraitements(
        charges_par_compte={
            "65831": Decimal("125.50"),
            "65862": Decimal("500.00"),
        },
        produits_par_compte={},
    )
    penalites = _by_category(r["automatiques"], "amendes_penalites")
    liberalites = _by_category(r["automatiques"], "liberalites")
    assert penalites["montant"] == Decimal("125.50")
    assert liberalites["montant"] == Decimal("500.00")
    assert r["total_automatique_reintegrations"] == Decimal("625.50")
    assert r["total_automatique_deductions"] == Decimal("0.00")
    assert all(x["impacte_calcul"] for x in r["automatiques"])


def test_cadeaux_et_dons_sont_detectes_sans_impact_automatique():
    r = service.analyser_retraitements(
        charges_par_compte={
            "61447": Decimal("800.00"),
            "61462": Decimal("1200.00"),
        },
        produits_par_compte={},
    )
    cadeaux = _by_category(r["a_confirmer"], "cadeaux_publicitaires")
    dons = _by_category(r["a_confirmer"], "dons")
    assert cadeaux["montant_detecte"] == Decimal("800.00")
    assert dons["montant_detecte"] == Decimal("1200.00")
    assert cadeaux["impacte_calcul"] is False
    assert dons["impacte_calcul"] is False
    assert any("100 MAD" in q for q in cadeaux["questions"])


def test_provisions_et_interets_associes_sont_a_confirmer():
    r = service.analyser_retraitements(
        charges_par_compte={
            "6195": Decimal("3000.00"),
            "63114": Decimal("900.00"),
        },
        produits_par_compte={},
    )
    provisions = _by_category(r["a_confirmer"], "provisions_non_deductibles")
    interets = _by_category(r["a_confirmer"], "interets_comptes_courants_associes")
    assert provisions["montant_detecte"] == Decimal("3000.00")
    assert interets["montant_detecte"] == Decimal("900.00")
    assert "capital" in " ".join(interets["questions"]).lower()


def test_dividendes_et_reprises_peuvent_produire_des_deductions_a_confirmer():
    r = service.analyser_retraitements(
        charges_par_compte={},
        produits_par_compte={
            "7321": Decimal("10000.00"),
            "7195": Decimal("2500.00"),
        },
    )
    participation = _by_category(r["a_confirmer"], "produits_participation_abattement")
    reprises = _by_category(r["a_confirmer"], "reprises_provisions_taxees")
    assert participation["type_suggere"] == "deduction"
    assert participation["montant_detecte"] == Decimal("10000.00")
    assert reprises["type_suggere"] == "deduction"
    assert reprises["montant_detecte"] == Decimal("2500.00")


def test_absence_reference_est_un_signal_et_non_une_reintegration_aveugle():
    r = service.analyser_retraitements(
        charges_par_compte={"6111": Decimal("4000.00")},
        produits_par_compte={},
        charges_sans_reference=Decimal("4000.00"),
    )
    pieces = _by_category(r["a_confirmer"], "charges_non_justifiees")
    assert pieces is not None
    assert pieces["montant_detecte"] == Decimal("4000.00")
    assert pieces["impacte_calcul"] is False
    assert r["total_automatique_reintegrations"] == Decimal("0.00")


def test_vehicule_tourisme_superieur_plafond_est_signale_sans_inventer_montant():
    r = service.analyser_retraitements(
        charges_par_compte={},
        produits_par_compte={},
        vehicules_tourisme_superieurs_plafond=[
            {"id": 1, "designation": "Véhicule test", "valeur_brute": Decimal("450000.00")}
        ],
    )
    vehicule = _by_category(r["a_confirmer"], "amortissement_vehicule")
    assert vehicule is not None
    assert vehicule["montant_detecte"] is None
    assert "400 000" in vehicule["libelle"]


def test_checklist_conserve_les_controles_non_automatisables():
    r = service.analyser_retraitements(charges_par_compte={}, produits_par_compte={})
    codes = {x["code"] for x in r["checklist"]}
    assert {"paiements_especes", "pieces_justificatives", "vehicules", "charges_produits_exoneres"} <= codes


def test_router_expose_les_trois_niveaux_et_valide_les_categories():
    src = (BACKEND / "routers" / "fiscalite.py").read_text(encoding="utf-8")
    assert '"retraitements_a_confirmer"' in src
    assert '"checklist_fiscale"' in src
    assert '"synthese_retraitements"' in src
    assert "Catégorie de retraitement fiscal inconnue" in src
    assert "total_automatique_reintegrations" in src


def test_frontend_distingue_automatique_a_confirmer_et_manuel():
    page = (ROOT / "src" / "pages" / "FiscaliteIS.jsx").read_text(encoding="utf-8")
    css = (ROOT / "src" / "pages" / "FiscaliteIS.module.css").read_text(encoding="utf-8")
    assert "Retraitements automatiques — inclus dans le calcul" in page
    assert "Éléments à confirmer — aucun impact fiscal tant qu'ils ne sont pas validés" in page
    assert "Retraitements manuels confirmés" in page
    assert "Préremplir" in page
    assert ".confirmBlock" in css
    assert ".checklistGrid" in css


def test_detection_ne_prend_que_le_solde_net_positif_du_compte():
    # Le routeur agrège désormais les mouvements signés par compte ; le service
    # ne doit retenir que la charge nette positive qui lui est transmise.
    r = service.analyser_retraitements(
        charges_par_compte={"6583": Decimal("25.00"), "65862": Decimal("-100.00")},
        produits_par_compte={"7321": Decimal("-50.00")},
    )
    penalites = _by_category(r["automatiques"], "amendes_penalites")
    assert penalites["montant"] == Decimal("25.00")
    assert _by_category(r["automatiques"], "liberalites") is None
    assert _by_category(r["a_confirmer"], "produits_participation_abattement") is None
