from pathlib import Path
from types import SimpleNamespace
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
SRC = ROOT / "src"

import sys
sys.path.insert(0, str(BACK))

from services.compta_mapping_service import groupes_facture_par_compte, groupes_avoir_par_compte, repartir_par_poids


def txt(path):
    return path.read_text(encoding="utf-8")


def test_compta1_migration_persiste_et_fige_les_comptes():
    sql = txt(BACK / "032_compta_mapping.sql")
    assert "ADD COLUMN IF NOT EXISTS compte_vente" in sql
    assert "ADD COLUMN IF NOT EXISTS compte_achat" in sql
    assert "compte_tiers_snapshot" in sql
    assert "compte_vente_snapshot" in sql
    assert "compte_achat_snapshot" in sql
    assert "ALTER TABLE acomptes ADD COLUMN IF NOT EXISTS tiers_id" in sql


def test_compta1_article_api_accepte_les_surcharges_comptables():
    schemas = txt(BACK / "schemas.py")
    models = txt(BACK / "models.py")
    route = txt(BACK / "routers" / "articles.py")
    assert "compte_vente:    Optional[str]" in schemas
    assert "compte_achat:    Optional[str]" in schemas
    assert "compte_vente    = Column(String(10), nullable=True)" in models
    assert "compte_achat    = Column(String(10), nullable=True)" in models
    assert "model_dump(exclude_unset=True)" in route


def test_compta1_facture_utilise_comptes_parametres_et_snapshots():
    route = txt(BACK / "routers" / "factures.py")
    assert "figer_comptes_facture(db, societe_id, facture)" in route
    assert "compte_tiers_facture(db, societe_id, facture)" in route
    assert "groupes_facture_par_compte" in route
    bloc = route[route.index("def comptabiliser_facture"):route.index("@router.get(\"/{facture_id}/pdf\")")]
    assert 'compte="71243"' not in bloc
    assert 'compte="3421"' not in bloc
    assert 'compte="4411"' not in bloc


def test_compta1_reglements_utilisent_compte_bancaire_et_tiers():
    route = txt(BACK / "routers" / "commercial.py")
    bloc = route[route.index("def _ecriture_reception_reglement"):route.index("@router_regl.patch")]
    assert "compte_tresorerie(" in bloc
    assert "compte_tiers_facture(" in bloc
    assert "compte=tiers_compte" in bloc


def test_compta1_avoirs_inversent_les_memes_comptes_que_la_facture():
    route = txt(BACK / "avoirs.py")
    bloc = route[route.index("def comptabiliser_avoir"):route.index('@router.post("/{avoir_id}/annuler")')]
    assert "groupes_avoir_par_compte" in bloc
    assert "compte_tiers_facture" in bloc
    assert 'compte="71243"' not in bloc
    assert 'compte="3421"' not in bloc
    assert 'compte="4411"' not in bloc


def test_compta1_groupement_facture_est_exact_au_centime():
    facture = SimpleNamespace(
        remise_globale=7.5,
        ristourne=2.0,
        lignes=[
            SimpleNamespace(quantite=3, prix_unitaire=101.17, remise=5, remise2=2, rabais=1.25,
                            article_id=1, compte_vente_snapshot="7111", compte_achat_snapshot="6111"),
            SimpleNamespace(quantite=2, prix_unitaire=77.33, remise=0, remise2=0, rabais=0,
                            article_id=2, compte_vente_snapshot="71243", compte_achat_snapshot="6131"),
        ],
    )
    cible = Decimal("392.57")
    groupes = groupes_facture_par_compte(None, 1, facture, est_vente=True, cible=cible)
    assert set(groupes) == {"7111", "71243"}
    assert sum(groupes.values(), Decimal("0")) == cible


def test_compta1_groupement_avoir_reutilise_snapshot_ligne_source():
    src1 = SimpleNamespace(id=10, article_id=1, compte_vente_snapshot="7111", compte_achat_snapshot="6111")
    src2 = SimpleNamespace(id=20, article_id=2, compte_vente_snapshot="71243", compte_achat_snapshot="6131")
    facture = SimpleNamespace(lignes=[src1, src2])
    avoir = SimpleNamespace(
        remise_globale_snapshot=5,
        ristourne_snapshot=0,
        lignes=[
            SimpleNamespace(facture_ligne_id=10, article_id=1, quantite=1, prix_unitaire=100, remise=0, remise2=0, rabais=0),
            SimpleNamespace(facture_ligne_id=20, article_id=2, quantite=1, prix_unitaire=50, remise=0, remise2=0, rabais=0),
        ],
    )
    cible = Decimal("142.50")
    groupes = groupes_avoir_par_compte(None, 1, avoir, facture, est_vente=False, cible=cible)
    assert groupes == {"6111": Decimal("95.00"), "6131": Decimal("47.50")}


def test_compta1_repartition_tva_non_deductible_equilibree():
    out = repartir_par_poids(Decimal("12.37"), {"6111": Decimal("100"), "6131": Decimal("50")})
    assert sum(out.values(), Decimal("0")) == Decimal("12.37")
    assert all(v >= 0 for v in out.values())


def test_compta1_recette_complete():
    import subprocess, sys
    proc = subprocess.run([sys.executable, str(ROOT / "Test" / "recette_compta1_mapping.py")], cwd=ROOT, text=True, capture_output=True)
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
