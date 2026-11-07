from pathlib import Path
from types import SimpleNamespace
from datetime import date, datetime
from decimal import Decimal
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.fec_service import controler_fec


def _ec_aux_manquant():
    ligne = SimpleNamespace(
        id=123,
        compte="3421",
        libelle="Client historique",
        debit=Decimal("100.00"),
        credit=Decimal("0.00"),
        tiers_id=None,
        nature_auxiliaire=None,
        compte_auxiliaire_snapshot=None,
        libelle_auxiliaire_snapshot=None,
        auxiliaire_complements=[],
    )
    contrepartie = SimpleNamespace(
        id=124,
        compte="7111",
        libelle="Vente",
        debit=Decimal("0.00"),
        credit=Decimal("100.00"),
        tiers_id=None,
        nature_auxiliaire=None,
        compte_auxiliaire_snapshot=None,
        libelle_auxiliaire_snapshot=None,
        auxiliaire_complements=[],
    )
    return SimpleNamespace(
        id=10,
        societe_id=1,
        exercice=2099,
        journal="VT",
        numero_ecriture="VT-2099-0001",
        date=date(2099, 1, 2),
        date_piece=date(2099, 1, 2),
        date_validation=datetime(2099, 1, 2, 12, 0),
        reference="FAC-1",
        justificatifs=[],
        libelle="Vente",
        source="manuel",
        est_validee=True,
        created_at=datetime(2099, 1, 2, 12, 0),
        lignes=[ligne, contrepartie],
    )


def _exercice():
    return SimpleNamespace(
        annee=2099,
        date_debut=date(2099, 1, 1),
        date_fin=date(2099, 12, 31),
        statut="cloture",
    )


def test_anomalie_auxiliaire_expose_ligne_exacte_a_corriger():
    c = controler_fec([_ec_aux_manquant()], 2099, _exercice())
    aux = next(x for x in c["bloquants"] if x["code"] == "AUXILIAIRE_MANQUANT")
    assert aux["details"]["compte"] == "3421"
    assert aux["details"]["ligne_ecriture_id"] == 123


def test_endpoint_append_only_auxiliaire_historique_existe_et_controle_le_compte():
    src = (BACKEND / "routers" / "ecritures.py").read_text(encoding="utf-8")
    assert '/{ecriture_id}/lignes/{ligne_id}/auxiliaire-complement' in src
    assert 'compte.startswith("3421")' in src
    assert 'compte.startswith("4411")' in src
    assert 'models.LigneAuxiliaireComplement(' in src
    assert 'source_type="manuel_fec"' in src
    assert 'db.query(models.Tiers).filter_by' in src


def test_migration_069_n_ouvre_que_insert_select_et_preserve_append_only():
    sql = (BACKEND / "069_fec_complements_historiques_saisie_manuelle.sql").read_text(encoding="utf-8")
    upper = sql.upper()
    assert "GRANT SELECT, INSERT ON TABLE LIGNE_AUXILIAIRE_COMPLEMENTS" in upper
    assert "GRANT USAGE, SELECT ON SEQUENCE LIGNE_AUXILIAIRE_COMPLEMENTS_ID_SEQ" in upper
    assert "GRANT UPDATE" not in upper
    assert "GRANT DELETE" not in upper
    assert "UPDATE LIGNES_ECRITURE" not in upper
    assert "UPDATE ECRITURES" not in upper


def test_frontend_permet_correction_ciblee_des_deux_anomalies_restantes():
    src = (ROOT / "src" / "pages" / "Journal.jsx").read_text(encoding="utf-8")
    api = (ROOT / "src" / "services" / "api.js").read_text(encoding="utf-8")
    assert "Référence du justificatif existant" in src
    assert "Sélectionner le tiers historique exact" in src
    assert "Ajouter la référence" in src
    assert "Associer ce tiers" in src
    assert "ajouterAuxiliaireComplement" in src
    assert "ajouterAuxiliaireComplement" in api


def test_cloture_legacy_est_un_avertissement_et_non_un_blocage_fec():
    src = (BACKEND / "services" / "fec_service.py").read_text(encoding="utf-8")
    assert '"ECRITURE_CLOTURE_HISTORIQUE_HORS_CL"' in src
    # Le contrôle inverse reste bloquant : CL est réservé aux clôtures HisabPro.
    assert '"JOURNAL_CLOTURE_USAGE_INTERDIT"' in src
