# -*- coding: utf-8 -*-
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

# Les services de calcul testés ici n'ont pas besoin du vrai mapping ORM.
sys.modules.setdefault("models", types.SimpleNamespace())

from services.affectation_resultat_service import (
    calculer_contraintes_affectation,
    regle_reserve_legale,
)
from services.etats_synthese_service import _flux_financement_depuis_lignes
from services.liasse_service import calculer_cpc, calculer_tableau_financement


def _solde(debit=0, credit=0):
    return {"debit": debit, "credit": credit}


def _row(ecriture_id, compte, debit=0, credit=0):
    return SimpleNamespace(ecriture_id=ecriture_id, compte=compte, debit=debit, credit=credit)


def test_reserve_legale_sa_5_pourcent_apres_pertes_et_plafond_10_pourcent():
    c = calculer_contraintes_affectation(
        resultat_beneficiaire=100_000,
        forme_juridique="SA",
        capital_social=500_000,
        reserve_legale_avant=45_000,
        report_deficitaire=20_000,
    )
    assert c["forme_supportee"] is True
    assert c["pertes_a_apurer"] == Decimal("20000.00")
    assert c["base_apres_pertes"] == Decimal("80000.00")
    assert c["reserve_legale_minimale"] == Decimal("4000.00")
    assert c["plafond_reserve_legale"] == Decimal("50000.00")


def test_reserve_legale_sa_ne_depasse_pas_le_manque_au_plafond():
    c = calculer_contraintes_affectation(
        resultat_beneficiaire=50_000,
        forme_juridique="Société anonyme",
        capital_social=500_000,
        reserve_legale_avant=49_000,
        report_deficitaire=0,
    )
    assert c["reserve_legale_minimale"] == Decimal("1000.00")


def test_reserve_legale_sarl_sarrete_au_cinquieme_du_capital():
    c = calculer_contraintes_affectation(
        resultat_beneficiaire=50_000,
        forme_juridique="SARL",
        capital_social=100_000,
        reserve_legale_avant=19_000,
        report_deficitaire=0,
    )
    assert c["regle"]["plafond_ratio"] == Decimal("0.20")
    assert c["reserve_legale_minimale"] == Decimal("1000.00")


def test_forme_juridique_non_documentee_n_est_pas_assimilee_a_une_sa_ou_sarl():
    assert regle_reserve_legale("SAS") is None
    c = calculer_contraintes_affectation(
        resultat_beneficiaire=1000,
        forme_juridique="SAS",
        capital_social=10000,
        reserve_legale_avant=0,
        report_deficitaire=0,
    )
    assert c["forme_supportee"] is False


def test_cloture_reclasse_un_119_non_affecte_en_118_avant_les_an_suivants():
    src = (BACK / "routers" / "cloture.py").read_text(encoding="utf-8")
    assert "def _reclasser_resultat_non_affecte" in src
    assert 'f"INSTANCE-AFFECT-{origine}"' in src
    assert 'source, cible = "1191", "1181"' in src
    assert 'source, cible = "1199", "1189"' in src
    bloc = src[src.index('@router.post("/cloturer")'):src.index('@router.post("/affecter-resultat")')]
    assert "_reclasser_resultat_non_affecte" in bloc
    assert "soldes = _soldes_comptes" in bloc


def test_decision_affectation_est_tracee_et_immutable_en_base():
    models_src = (BACK / "models.py").read_text(encoding="utf-8")
    sql = (BACK / "052_conformite_normative.sql").read_text(encoding="utf-8")
    router = (BACK / "routers" / "cloture.py").read_text(encoding="utf-8")
    assert 'class DecisionAffectationResultat' in models_src
    for champ in ("date_decision", "reference_decision", "organe_decision", "forme_juridique_snapshot", "capital_social_snapshot"):
        assert champ in models_src
    assert "BEFORE UPDATE OR DELETE" in sql
    assert "hisabpro_guard_decision_affectation_immutable" in sql
    assert "models.EcritureJustificatif" in router
    assert 'source_type="decision_affectation"' in router
    assert "prioritaire=True" in router


def test_affectation_benefice_impose_pertes_anterieures_et_reserve_minimale():
    src = (BACK / "routers" / "cloture.py").read_text(encoding="utf-8")
    bloc = src[src.index('@router.post("/affecter-resultat")'):src.index('@router.post("/generer-dotations")')]
    assert 'reserve_legale_minimale' in bloc
    assert 'perte_1169' in bloc and 'perte_1189' in bloc
    assert 'Réserve légale insuffisante' in bloc
    assert 'Dividendes trop élevés' in bloc
    assert 'date_decision' in bloc and 'reference_decision' in bloc and 'organe_decision' in bloc


def test_flux_tableau_financement_sont_ventiles_par_nature_cgnc():
    rows = [
        _row(1, "2220", debit=10), _row(1, "5141", credit=10),
        _row(2, "2332", debit=20), _row(2, "5141", credit=20),
        _row(3, "2510", debit=30), _row(3, "5141", credit=30),
        _row(4, "2410", debit=40), _row(4, "5141", credit=40),
        _row(5, "5141", debit=12), _row(5, "7512", credit=12),
        _row(6, "5141", debit=23), _row(6, "7513", credit=23),
        _row(7, "5141", debit=34), _row(7, "7514", credit=34),
    ]
    f = _flux_financement_depuis_lignes(rows)
    assert f["acquisitions_immobilisations_incorporelles"] == 10.0
    assert f["acquisitions_immobilisations_corporelles"] == 20.0
    assert f["acquisitions_immobilisations_financieres"] == 30.0
    assert f["augmentations_creances_immobilisees"] == 40.0
    assert f["cessions_immobilisations_incorporelles"] == 12.0
    assert f["cessions_immobilisations_corporelles"] == 23.0
    assert f["cessions_immobilisations_financieres"] == 34.0


def test_tableau_financement_presente_a_h_et_deduit_distributions_de_la_caf():
    courant = {"4465": _solde(credit=30)}
    precedent = {"1191": _solde(credit=30)}
    tf = calculer_tableau_financement(
        courant,
        precedent,
        calculer_cpc(courant),
        calculer_cpc(precedent),
        {"distributions_benefices": 30},
    )
    codes = {x["code"] for x in tf["ressources"] + tf["emplois"]}
    assert {"A", "B", "C", "D", "E", "F", "G", "H"}.issubset(codes)
    autof = next(x for x in tf["ressources"] if x["code"] == "A")
    distrib = next(x for x in tf["ressources"] if x["code"] == "A2")
    assert autof["montant"] == -30.0
    assert distrib["montant"] == 30.0
    assert tf["total_emplois"] == 0.0
    assert tf["total_ressources"] == -30.0
    assert tf["controle"] is True


def test_tableau_financement_acquisition_financee_par_dette_est_equilibre():
    soldes = {"2332": _solde(debit=100), "1481": _solde(credit=100)}
    flux = {
        "acquisitions_immobilisations_corporelles": 100,
        "augmentations_dettes_financement": 100,
    }
    tf = calculer_tableau_financement(soldes, {}, calculer_cpc(soldes), calculer_cpc({}), flux)
    assert tf["total_ressources"] == 100.0
    assert tf["total_emplois"] == 100.0
    assert tf["controle"] is True


def test_frontend_cloture_capture_la_decision_et_affiche_les_controles_normatifs():
    page = (ROOT / "src" / "pages" / "Cloture.jsx").read_text(encoding="utf-8")
    for token in (
        "date_decision", "reference_decision", "organe_decision",
        "reserve_legale_minimale", "pertes_a_apurer", "montant_a_ventiler",
        "forme_juridique_supportee", "resultat_anterieur_a_reclasser",
    ):
        assert token in page
    assert "HisabPro ne calcule pas automatiquement la réserve légale" not in page


def test_frontend_tableau_financement_affiche_les_rubriques_cgnc_et_n_n1():
    data = (ROOT / "src" / "data" / "etatsSynthese.js").read_text(encoding="utf-8")
    page = (ROOT / "src" / "pages" / "Bilan.jsx").read_text(encoding="utf-8")
    for token in ("AUTOFINANCEMENT (A)", "CESSIONS ET RÉDUCTIONS D’IMMOBILISATIONS (B)", "REMBOURSEMENT DES DETTES DE FINANCEMENT (G)"):
        assert token in data
    assert "donneesN1.fluxFinancement" in page
    assert "total général" in page
