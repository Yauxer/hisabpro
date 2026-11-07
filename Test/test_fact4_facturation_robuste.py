from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
SRC = ROOT / "src"


def txt(path):
    return path.read_text(encoding="utf-8")


def test_migration_numero_validation_et_echeance():
    sql = txt(BACK / "029_factures_validation.sql")
    assert "ADD COLUMN IF NOT EXISTS est_validee" in sql
    assert "ADD COLUMN IF NOT EXISTS date_echeance" in sql
    assert "facturation_sequences" in sql
    assert "hisabpro_reserver_numero_facture" in sql
    assert "trg_hisabpro_guard_facture_validee" in sql
    assert "trg_hisabpro_guard_ligne_facture_validee" in sql


def test_modele_facture_supporte_brouillon_et_validation():
    models = txt(BACK / "models.py")
    schemas = txt(BACK / "schemas.py")
    assert "numero        = Column(String(50), nullable=True)" in models
    assert "est_validee      = Column(Boolean" in models
    assert "date_validation" in models
    assert "date_echeance" in models
    assert "numero:         Optional[str] = None" in schemas
    assert "est_validee:" in schemas


def test_creation_brouillon_ne_consomme_pas_numero():
    route = txt(BACK / "routers" / "factures.py")
    assert "numero = None" in route
    assert "Aucun mouvement de stock, aucune consommation de plafond" in route
    assert '@router.post("/{facture_id}/valider")' in route


def test_validation_reserve_numero_atomiquement_et_fige():
    route = txt(BACK / "routers" / "factures.py")
    assert "reserver_numero(db, societe_id, facture.exercice" in route
    assert "facture.est_validee = True" in route
    assert "facture.date_validation" in route
    assert "_mouvements_stock_validation_facture" in route
    assert "Facture validée : les données de facturation sont figées" in route


def test_doublon_fournisseur_et_reference_obligatoire():
    route = txt(BACK / "routers" / "factures.py")
    sql = txt(BACK / "029_factures_validation.sql")
    assert "_verifier_doublon_facture_fournisseur" in route
    assert "Le N° de facture fournisseur est obligatoire" in route
    assert "Facture fournisseur en doublon" in sql
    assert "ix_factures_fournisseur_reference" in sql


def test_actions_aval_refusent_un_brouillon():
    factures = txt(BACK / "routers" / "factures.py")
    commercial = txt(BACK / "routers" / "commercial.py")
    avoirs = txt(BACK / "avoirs.py")
    assert "validez-la avant de la comptabiliser" in factures
    assert "validez-la avant d'enregistrer un règlement" in commercial
    assert "validez-la avant de créer un avoir" in avoirs
    assert "validez-la avant de créer un bon de livraison" in factures


def test_conversions_bc_bl_creent_brouillon_sans_numero():
    commercial = txt(BACK / "routers" / "commercial.py")
    assert commercial.count("numero_f = None") >= 2
    # Chaque conversion crée un brouillon avec l'échéance du tiers lié,
    # et conserve 60 jours comme repli lorsque le tiers n'a pas de délai.
    assert commercial.count('date_echeance=date_facture + timedelta(days=_delai_paiement_tiers(tiers_obj))') == 2
    assert 'return 60 if delai is None else delai' in commercial


def test_frontend_direct_brouillon_validation_et_echeance():
    jsx = txt(SRC / "pages" / "Factures.jsx")
    ctx = txt(SRC / "data" / "FacturesContext.jsx")
    assert "N° facture interne" in jsx
    assert "(prévision)" in jsx
    assert "N° facture fournisseur" in jsx
    assert '>Échéance</label>' in jsx
    assert 'Échéance contractuelle' not in jsx
    assert "Valider & comptabiliser immédiatement" in jsx
    assert "Enregistrer en brouillon" in jsx
    assert "BROUILLON" in jsx
    assert "async function validerFacture" in ctx
