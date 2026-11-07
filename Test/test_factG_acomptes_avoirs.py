from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
SRC = ROOT / "src"


def txt(path):
    return path.read_text(encoding="utf-8")


def test_factg_migration_couvre_cycles_acomptes_avoirs():
    sql = txt(BACK / "045_factG_acomptes_avoirs.sql")
    for token in [
        "statut_paiement", "compte_bancaire_id", "date_echeance",
        "statut VARCHAR(20) NOT NULL DEFAULT 'active'",
        "montant_ht_force", "rrr_pourcentage", "correction_prix",
        "CREATE TABLE IF NOT EXISTS utilisations_avoirs",
    ]:
        assert token in sql


def test_factg_acompte_annulation_imputation_et_inter_exercices():
    route = txt(BACK / "acomptes.py")
    assert '@router.get("/{acompte_id}/factures-imputables")' in route
    assert '@router.post("/{acompte_id}/imputations/{imputation_id}/annuler")' in route
    assert '@router.post("/{acompte_id}/statut-paiement")' in route
    assert 'ImputationAcompte.statut == "active"' in route or 'getattr(x, "statut", "active") == "active"' in route
    assert 'statut_paiement="en_attente"' in route or 'statut_paiement = "en_attente"' in route


def test_factg_avoirs_rrr_prix_credit_reel():
    route = txt(BACK / "avoirs.py")
    assert 'mode_recu == "rrr_pourcentage"' in route
    assert 'mode_recu == "rrr_montant"' in route
    assert '_base_finale_correction_prix' in route
    assert '@router.post("/{avoir_id}/utiliser"' in route
    assert '@router.post("/{avoir_id}/utilisations/{utilisation_id}/annuler"' in route
    assert '_credit_excedentaire_avoir' in route


def test_factg_situation_facture_prend_credit_et_imputations_actives():
    route = txt(BACK / "routers" / "factures.py")
    assert 'filter_by(facture_id=facture.id, societe_id=societe_id, statut="active")' in route
    assert 'type_utilisation="imputation", statut="active"' in route


def test_factg_frontend_acomptes_expose_historique_et_cycle_effets():
    jsx = txt(SRC / "pages" / "Acomptes.jsx")
    assert 'Historique des imputations' in jsx
    assert '/statut-paiement`' in jsx
    assert '/imputations/${row.id}/annuler`' in jsx
    assert '/factures-imputables`' in jsx
    assert "a.statut_paiement === 'encaisse'" in jsx


def test_factg_frontend_avoir_ne_preselectionne_plus_tout_et_expose_vrais_calculs():
    jsx = txt(SRC / "pages" / "Factures.jsx")
    assert "const quantiteInitiale = quantitesRetour ? Math.min(dispoRetour, quantiteRetour) : 0" in jsx
    assert 'mode_calcul:' in jsx
    assert 'taux_rrr:' in jsx
    assert 'nouveau_prix_unitaire:' in jsx
    assert "natureAvoir === 'retour_annulation' && retourStock" in jsx
    assert 'RRR %' in jsx


def test_factg_frontend_avoirs_expose_credit_imputation_remboursement():
    jsx = txt(SRC / "pages" / "Avoirs.jsx")
    assert 'Crédit libre' in jsx
    assert 'Imputer sur une facture' in jsx
    assert 'Rembourser' in jsx
    assert '/utiliser`' in jsx
    assert '/utilisations/${utilisation.id}/annuler`' in jsx
    assert 'Historique du crédit' in jsx


def test_factg_python_compile():
    for name in ["acomptes.py", "avoirs.py", "models.py", "schemas.py"]:
        py_compile.compile(str(BACK / name), doraise=True)
