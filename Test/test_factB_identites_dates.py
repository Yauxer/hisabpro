from pathlib import Path
import json
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_factB_migration_snapshots_et_categorie_tiers():
    sql = read(BACK / "040_factB_identites_dates.sql")
    assert "categorie_fiscale" in sql
    assert "societe_snapshot_json" in sql
    assert "tiers_telephone_snapshot" in sql
    assert "tiers_email_snapshot" in sql
    assert "notes_snapshot" in sql
    assert "json_build_object" in sql


def test_factB_validation_fige_identites_et_refuse_date_future():
    src = read(BACK / "routers" / "factures.py")
    assert "_figer_identites_facture" in src
    assert "_verifier_date_facture_finale" in src
    assert "facture.date > date_cls.today()" in src
    assert "mentions_identite_manquantes" in src
    assert "avertissements_mentions" in src
    assert "societe_snapshot_json = json.dumps" in src
    assert "facture.notes_snapshot = facture.notes" in src
    assert "facture.notes_snapshot if getattr(facture, \"est_validee\", False)" in src


def test_factB_conversions_utilisent_date_cible_et_exercice_cible():
    commercial = read(BACK / "routers" / "commercial.py")
    schemas = read(BACK / "schemas.py")
    factures = read(BACK / "routers" / "factures.py")
    assert "class ConvertirBCFactureIn" in schemas
    assert "date_facture = data.date or _date.today()" in commercial
    assert "exercice=exercice_facture.annee" in commercial
    assert "exercice=exercice_bl_annee" in commercial
    assert "exercice_bl_annee = _exercice_ref(db, current_user[\"societe_id\"], date_bl)" in commercial
    assert "facture.date = data.date or date_cls.today()" in factures


def test_factB_pdf_utilise_snapshot_societe():
    import sys
    sys.path.insert(0, str(BACK))
    from services.document_pdf_service import societe_pour_document

    live = SimpleNamespace(raison_sociale="NOUVEAU NOM", ice="999")
    piece = SimpleNamespace(societe_snapshot_json=json.dumps({
        "raison_sociale": "ANCIEN NOM", "ice": "111", "adresse": "Ancienne adresse"
    }))
    snap = societe_pour_document(live, piece)
    assert snap.raison_sociale == "ANCIEN NOM"
    assert snap.ice == "111"
    assert snap.adresse == "Ancienne adresse"


def test_factB_guard_ne_revalide_pas_les_factures_historiques_lors_des_backfills():
    guard = read(BACK / "029_factures_validation.sql")
    migration = read(BACK / "040_factB_identites_dates.sql")
    assert "v_devient_validee BOOLEAN" in guard
    assert "IF v_devient_validee THEN" in guard
    assert "COALESCE(OLD.est_validee, FALSE) = FALSE" in guard
    # La migration doit corriger le trigger avant son premier UPDATE sur factures.
    pos_guard = migration.index("CREATE OR REPLACE FUNCTION hisabpro_guard_facture_validee()")
    pos_backfill = migration.index("UPDATE factures f")
    assert pos_guard < pos_backfill
