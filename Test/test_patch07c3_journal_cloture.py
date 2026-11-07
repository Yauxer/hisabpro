from pathlib import Path
from types import SimpleNamespace
from datetime import date, datetime
from decimal import Decimal
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.fec_service import controler_fec, JOURNAUX_LIB


def _ligne(compte="6111", debit="100.00", credit="0.00"):
    return SimpleNamespace(
        compte=compte,
        libelle="Ligne",
        debit=Decimal(debit),
        credit=Decimal(credit),
    )


def _ec(journal="CL", source="cloture", reference="CLOTURE-2099", numero="CL-2099-0001"):
    return SimpleNamespace(
        id=1,
        societe_id=1,
        exercice=2099,
        journal=journal,
        numero_ecriture=numero,
        date=date(2099, 12, 31),
        date_piece=date(2099, 12, 31),
        date_validation=datetime(2100, 1, 2, 10, 0),
        reference=reference,
        libelle="Détermination du résultat 2099",
        source=source,
        est_validee=True,
        created_at=datetime(2100, 1, 2, 10, 0),
        lignes=[
            _ligne("6111", "100.00", "0.00"),
            _ligne("1199", "0.00", "100.00"),
        ],
    )


def _exercice():
    return SimpleNamespace(
        annee=2099,
        date_debut=date(2099, 1, 1),
        date_fin=date(2099, 12, 31),
        statut="cloture",
    )


def test_cl_est_libelle_journal_cloture():
    assert JOURNAUX_LIB["CL"] == "Journal de clôture"


def test_cloture_dans_cl_n_est_pas_signalee_hors_journal():
    c = controler_fec([_ec()], 2099, _exercice(), cloture=SimpleNamespace(date_cloture=datetime.now()))
    codes = {x["code"] for x in c["bloquants"]}
    assert "ECRITURE_CLOTURE_HORS_JOURNAL_DEDIE" not in codes
    assert "JOURNAL_CLOTURE_USAGE_INTERDIT" not in codes


def test_cloture_legacy_od_est_signalee_sans_bloquer_export():
    c = controler_fec([_ec(journal="OD", numero="OD-2099-0001")], 2099, _exercice())
    bloquants = {x["code"] for x in c["bloquants"]}
    avertissements = {x["code"] for x in c["avertissements"]}
    assert "ECRITURE_CLOTURE_HORS_JOURNAL_DEDIE" not in bloquants
    assert "ECRITURE_CLOTURE_HISTORIQUE_HORS_CL" in avertissements


def test_ecriture_ordinaire_dans_cl_est_detectee():
    c = controler_fec([_ec(source="manuel", reference="PIECE-1")], 2099, _exercice())
    codes = {x["code"] for x in c["bloquants"]}
    assert "JOURNAL_CLOTURE_USAGE_INTERDIT" in codes


def test_frontend_affiche_cl_mais_ne_le_propose_pas_comme_standard_ou_special():
    data = (ROOT / "src" / "data" / "donnees.js").read_text(encoding="utf-8")
    form = (ROOT / "src" / "components" / "FormulaireEcriture.jsx").read_text(encoding="utf-8")
    assert "code: 'CL'" in data
    assert "groupe: 'system'" in data
    assert "filter(j => j.groupe === 'standard')" in form
    assert "filter(j => j.groupe === 'special')" in form


def test_migration_reserve_cl_sans_recrire_historique():
    sql = (BACKEND / "019_journal_cloture_dedie.sql").read_text(encoding="utf-8")
    assert "ADD VALUE" in sql and "'CL'" in sql
    assert "hisabpro_controler_journal_cloture" in sql
    assert "UPDATE ecritures" not in sql.upper()
