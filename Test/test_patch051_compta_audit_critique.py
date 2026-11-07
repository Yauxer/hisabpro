# -*- coding: utf-8 -*-
from pathlib import Path
from types import SimpleNamespace
import types
import sys

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

sys.modules.setdefault("models", types.SimpleNamespace())

from services.etats_synthese_service import _flux_financement_depuis_lignes
from services.liasse_service import calculer_bilan, calculer_cpc, calculer_tableau_financement


def _solde(debit=0, credit=0):
    return {"debit": debit, "credit": credit}


def _row(ecriture_id, compte, debit=0, credit=0):
    return SimpleNamespace(ecriture_id=ecriture_id, compte=compte, debit=debit, credit=credit)


def test_bilan_reporte_119_sans_masquer_le_resultat_courant():
    soldes = {
        "5141": _solde(debit=100),
        "1191": _solde(credit=100),
    }
    bilan = calculer_bilan(soldes, 0)
    assert bilan["equilibre"] is True
    assert bilan["passif"]["total"] == 100.0
    ligne_119 = next(x for x in bilan["passif"]["capitaux_propres"] if x["code"] == "119_ANT")
    ligne_resultat = next(x for x in bilan["passif"]["capitaux_propres"] if x["code"] == "RESULTAT")
    assert ligne_119["montant"] == 100.0
    assert ligne_resultat["montant"] == 0.0


def test_tableau_financement_ne_double_plus_le_119_dans_financement_permanent():
    soldes = {
        "5141": _solde(debit=100),
        "1191": _solde(credit=100),
    }
    cpc = calculer_cpc(soldes)
    tf = calculer_tableau_financement(soldes, {}, cpc, calculer_cpc({}), {})
    assert tf["masses_n"]["financement_permanent"] == 100.0


def test_tableau_financement_utilise_les_flux_reels_et_se_controle():
    soldes = {
        "2332": _solde(debit=100),
        "1481": _solde(credit=100),
    }
    flux = {
        "acquisitions_immobilisations": 100,
        "augmentations_dettes_financement": 100,
    }
    tf = calculer_tableau_financement(soldes, {}, calculer_cpc(soldes), calculer_cpc({}), flux)
    assert tf["total_ressources"] == 100.0
    assert tf["total_emplois"] == 100.0
    assert tf["controle"] is True
    assert tf["ecart_controle"] == 0.0


def test_6591_n_est_plus_interprete_comme_distribution_de_benefices():
    soldes = {
        "6591": _solde(debit=50),
        "5141": _solde(credit=50),
    }
    tf = calculer_tableau_financement(soldes, {}, calculer_cpc(soldes), calculer_cpc({}), {})
    distribution = next(x for x in tf["ressources"] if "Distributions de bénéfices" in x["libelle"])
    assert distribution["montant"] == 0.0


def test_flux_financement_sont_agreges_par_ecriture_sans_reclassement_interne():
    rows = [
        _row(1, "2332", debit=100), _row(1, "1481", credit=100),
        _row(2, "1481", debit=40), _row(2, "5141", credit=40),
        # Affectation : dividendes mis en paiement au crédit de 4465.
        _row(3, "1191", debit=30), _row(3, "4465", credit=30),
        # Paiement ultérieur : ne doit pas compter une seconde fois.
        _row(4, "4465", debit=20), _row(4, "5141", credit=20),
        # Incorporation de réserves au capital : reclassement interne, pas ressource.
        _row(7, "1140", debit=25), _row(7, "1111", credit=25),
        # Produit de cession.
        _row(5, "5141", debit=50), _row(5, "7510", credit=50),
        # Reclassement d'immobilisation en cours : aucun nouvel emploi stable.
        _row(6, "2321", debit=80), _row(6, "2392", credit=80),
    ]
    flux = _flux_financement_depuis_lignes(rows)
    assert flux["acquisitions_immobilisations"] == 100.0
    assert flux["augmentations_dettes_financement"] == 100.0
    assert flux["remboursements_dettes_financement"] == 40.0
    assert flux["distributions_benefices"] == 30.0
    assert flux["augmentations_capitaux_propres"] == 0.0
    assert flux["cessions_immobilisations"] == 50.0


def test_cloture_exige_explicitement_un_fec_conforme():
    src = (BACK / "routers" / "cloture.py").read_text(encoding="utf-8")
    bloc = src[src.index('@router.post("/cloturer")'):src.index('@router.post("/generer-dotations")')]
    assert "controler_fec_exercice" in bloc
    assert 'if not fec_controle.get("conforme_export")' in bloc
    assert "Clôture bloquée : le FEC" in bloc


def test_liasse_bloque_fec_et_tableau_financement_incoherents():
    src = (BACK / "services" / "liasse_service.py").read_text(encoding="utf-8")
    assert '"FEC_CONFORME"' in src
    assert 'bool(fec.get("conforme_export"))' in src
    assert '"TABLEAU_FINANCEMENT"' in src
    start = src.index('"TABLEAU_FINANCEMENT"')
    end = src.index('bloq=[', start)
    bloc = src[start:end]
    compact = ''.join(bloc.split())
    assert 'TABLEAU_FINANCEMENT' in compact and ',True,' in compact


def test_frontend_bilan_separe_119_et_tableau_financement_recoit_les_flux_backend():
    data = (ROOT / "src" / "data" / "etatsSynthese.js").read_text(encoding="utf-8")
    page = (ROOT / "src" / "pages" / "Bilan.jsx").read_text(encoding="utf-8")
    assert "Résultat antérieur en attente d\\'affectation (119)" in data
    assert "sd(soldes, ['6591'])" not in data
    assert "fluxFinancement" in data
    assert "donneesN.fluxFinancement" in page
    assert "cpc.resultatNet + sc(soldes, ['119'])" not in page


def test_affectation_resultat_est_tracee_par_exercice_source_et_ne_depend_pas_du_solde_global_119():
    src = (BACK / "routers" / "cloture.py").read_text(encoding="utf-8")
    start = src.index("def _etat_affectation_resultat")
    end = src.index("def _dotations_manquantes", start)
    bloc = src[start:end]
    assert '_decision_affectation(db, societe_id, exercice_origine)' in bloc
    # Un ancien résultat non affecté peut coexister au compte 119 : l'état de N
    # doit donc reposer sur sa référence dédiée et non sur le solde global 119.
    assert "soldes_suivants" not in bloc
    assert "if decision or legacy or resultat == 0" in bloc


def test_affectation_resultat_genere_une_od_equilibree_et_est_exposee_dans_la_page_cloture():
    src = (BACK / "routers" / "cloture.py").read_text(encoding="utf-8")
    start = src.index('@router.post("/affecter-resultat")')
    end = src.index('@router.post("/generer-dotations")', start)
    bloc = src[start:end]
    for compte in ("1191", "1140", "1152", "1161", "4465", "1199", "1169"):
        assert f'"{compte}"' in bloc
    assert "AFFECT-RESULTAT-" in bloc
    assert "disponible_source" in bloc
    assert "abs(d - c)" in bloc

    page = (ROOT / "src" / "pages" / "Cloture.jsx").read_text(encoding="utf-8")
    assert "/api/cloture/affecter-resultat?exercice_origine=" in page
    assert "Réserve légale (1140)" in page
    assert "Report à nouveau (1161)" in page
    assert "Dividendes à payer (4465)" in page
    assert "Perte reportée à nouveau (1169)" in page


def test_tableau_financement_distribution_mise_en_paiement_explique_baisse_du_fr():
    courant = {"4465": _solde(credit=30)}
    precedent = {"1191": _solde(credit=30)}
    tf = calculer_tableau_financement(
        courant, precedent, calculer_cpc(courant), calculer_cpc(precedent),
        {"distributions_benefices": 30},
    )
    assert tf["variation_fonds_roulement"] == -30.0
    assert tf["total_emplois"] == 0.0
    assert tf["total_ressources"] == -30.0
    assert tf["controle"] is True


def test_incorporation_reserve_au_capital_n_est_pas_une_ressource_externe():
    rows = [_row(8, "1140", debit=25), _row(8, "1111", credit=25)]
    flux = _flux_financement_depuis_lignes(rows)
    assert flux["augmentations_capitaux_propres"] == 0.0
    assert flux["reductions_capitaux_propres"] == 0.0
