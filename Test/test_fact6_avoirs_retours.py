from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
SRC = ROOT / "src"


def txt(path):
    return path.read_text(encoding="utf-8")


def test_fact6_migration_et_tracabilite_ligne():
    sql = txt(BACK / "031_avoirs_retours.sql")
    models = txt(BACK / "models.py")
    assert "facture_ligne_id" in sql
    assert "retour_stock" in sql
    assert "ux_lignes_avoir_source_par_avoir" in sql
    assert "facture_ligne_id = Column" in models


def test_fact6_backend_fige_tarifs_annule_et_stock():
    route = txt(BACK / "avoirs.py")
    assert "_resoudre_ligne_facture(facture, ligne_in)" in route
    assert "_base_finale_source" in route
    assert "with_for_update()" in route
    assert "_appliquer_retour_stock" in route
    assert '@router.post("/{avoir_id}/annuler")' in route
    assert "annuler_mouvements_source" in route
    assert "Comptabilisez d'abord la facture d'origine" in route


def test_fact6_frontend_envoie_id_et_retour_stock():
    jsx = txt(SRC / "pages" / "Factures.jsx")
    avoirs = txt(SRC / "pages" / "Avoirs.jsx")
    assert "facture_ligne_id: l.facture_ligne_id" in jsx
    assert "retour_stock: natureAvoir === 'retour_annulation' && retourStock" in jsx
    assert "Retour physique de marchandise" in jsx
    assert "/annuler`" in avoirs


def test_fact6_recette_complete():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "Test" / "recette_fact6_avoirs.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
