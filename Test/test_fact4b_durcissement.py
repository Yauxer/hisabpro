from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"


def txt(path):
    return path.read_text(encoding="utf-8")


def test_patch_sql_numero_commercial_atomique_et_unicites():
    sql = txt(BACK / "030_facturation_durcissement.sql")
    assert "commercial_sequences" in sql
    assert "hisabpro_reserver_numero_commercial" in sql
    assert "FOR UPDATE" in sql
    assert "uq_factures_societe_numero" in sql
    assert "uq_bons_commande_societe_numero" in sql
    assert "uq_bons_livraison_societe_numero" in sql
    assert "uq_avoirs_societe_numero" in sql
    assert "uq_factures_fournisseur_reference_validee" in sql
    assert "LOWER(BTRIM(reference))" in sql


def test_conversions_ne_font_plus_count_ou_max_pour_numero_auto():
    commercial = txt(BACK / "routers" / "commercial.py")
    factures = txt(BACK / "routers" / "factures.py")
    avoirs = txt(BACK / "avoirs.py")
    assert 'reserver_numero_commercial(' in commercial
    assert '"br" if est_achat else "bl"' in commercial
    assert 'reserver_numero_commercial(' in factures
    assert 'reserver_numero_commercial(' in avoirs
    assert 'numero_bc = f"BC-' not in commercial
    assert 'numero_avoir = f"' not in avoirs


def test_changement_date_brouillon_recalcule_echeance_par_defaut():
    route = txt(BACK / "routers" / "factures.py")
    assert "date_facture_modifiee = False" in route
    assert "elif date_facture_modifiee and data.date_echeance is None:" in route
    assert "facture.date_echeance = _calculer_date_echeance(facture.date, facture.delai_paiement)" in route


def test_suivi_distingue_brouillons_et_factures_validees():
    commercial = txt(BACK / "routers" / "commercial.py")
    schemas = txt(BACK / "schemas.py")
    frontend = txt(ROOT / "src" / "pages" / "Commercial.jsx")
    assert "def _facture_validee_active" in commercial
    assert '"facturation_reservee_pct"' in commercial
    assert '"montant_brouillon_ht"' in commercial
    assert "facturation_reservee_pct:" in schemas
    assert "montant_brouillon_ht:" in schemas
    assert "brouillon" in frontend.lower()
    assert "Brouillon de facture #${f.id}" in frontend


def test_violation_unique_concurrente_devient_409_metier():
    route = txt(BACK / "routers" / "factures.py")
    assert "from sqlalchemy.exc import IntegrityError" in route
    assert 'contrainte == "uq_factures_fournisseur_reference_validee"' in route
    assert 'contrainte == "uq_factures_societe_numero"' in route
    assert "db.rollback()" in route
