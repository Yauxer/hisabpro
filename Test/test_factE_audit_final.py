from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACK))

from services.identifiants_maroc_service import normaliser_ice, normaliser_if, normaliser_tp


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_identifiants_maroc_normalisation_prudente():
    assert normaliser_ice("001 234 567-890/123") == "001234567890123"
    assert normaliser_if("12 345-678") == "12345678"
    assert normaliser_tp("  tp-12 / 34  ") == "TP-12 / 34"
    assert normaliser_ice(None) is None
    with pytest.raises(ValueError):
        normaliser_ice("123")
    with pytest.raises(ValueError):
        normaliser_ice("00123456789012A")
    with pytest.raises(ValueError):
        normaliser_if("IF-ABC")


def test_tiers_societe_et_creation_multi_societes_normalisent_cote_serveur():
    tiers = read("hisabpro-backend/routers/tiers.py")
    soc = read("hisabpro-backend/routers/societe.py")
    auth = read("hisabpro-backend/routers/auth.py")
    multi = read("hisabpro-backend/routers/multi_societes.py")
    assert "normaliser_ice" in tiers and "normaliser_if" in tiers
    assert "normaliser_ice" in soc and "normaliser_tp" in soc
    assert "normaliser_ice" in auth and "normaliser_if" in auth
    assert "normaliser_ice" in multi and "normaliser_if" in multi


def test_facture_fige_des_identifiants_normalises():
    src = read("hisabpro-backend/routers/factures.py")
    assert 'societe_snapshot["ice"] = societe_ice' in src
    assert "tiers_ice = normaliser_ice" in src
    assert "Identité société invalide" in src
    assert "Identité du tiers invalide" in src


def test_bc_bl_refuse_depassement_reliquat_sans_troncature_silencieuse():
    src = read("hisabpro-backend/routers/commercial.py")
    bloc = src.split("def convertir_bc_en_bl", 1)[1].split("# ═══════════════════════════════════════════════════════════════════════════════\n# BON DE LIVRAISON", 1)[0]
    assert "quantité demandée" in bloc and "supérieure au reliquat" in bloc
    assert "qte = min(qte, reste)" not in bloc
    assert "n'appartient pas à ce bon de commande" in bloc


def test_audit_production_couvre_les_trous_facturation_identifies():
    src = read("hisabpro-backend/services/production_audit_service.py")
    for code in (
        "FACTURE_VALIDEE_NON_COMPTABILISEE",
        "AVOIR_NON_COMPTABILISE",
        "REGLEMENT_NON_COMPTABILISE",
        "ACOMPTE_NON_COMPTABILISE",
        "IMPUTATION_ACOMPTE_NON_COMPTABILISEE",
        "LIGNE_FACTURE_INVALIDE",
        "LIEN_BC_AUTRE_SOCIETE",
        "LIEN_BL_AUTRE_SOCIETE",
        "LIEN_LIGNE_SOURCE_AUTRE_SOCIETE",
        "SNAPSHOT_VENDEUR_INCOMPLET",
        "SNAPSHOT_CLIENT_B2B_INCOMPLET",
        "IDENTIFIANTS_SOCIETE_INVALIDES",
    ):
        assert code in src


def test_migration_facte_pose_gardes_db_sans_bloquer_legacy():
    sql = read("hisabpro-backend/043_factE_audit_identifiants.sql")
    assert "ck_societes_ice_format_facte" in sql
    assert "ck_tiers_ice_format_facte" in sql
    assert "ck_lignes_facture_valeurs_facte" in sql
    assert "ck_lignes_bc_valeurs_facte" in sql
    assert "ck_lignes_bl_valeurs_facte" in sql
    assert sql.count("NOT VALID") >= 6
    assert "COMMIT;" in sql


def test_frontend_normalise_ice_if_tp_avant_envoi():
    utils = read("src/utils/formUtils.js")
    tiers = read("src/pages/Tiers.jsx")
    params = read("src/pages/Parametres.jsx")
    assert "normaliserIceSaisie" in utils
    assert "normaliserIfSaisie" in utils
    assert "normaliserTpSaisie" in utils
    assert "normaliserIfSaisie(form.identifiant_fiscal)" in tiers
    assert "normaliserTpSaisie(form.patente)" in params
