# -*- coding: utf-8 -*-
"""COMPTA.4 — justificatifs non bloquants et résolution FEC."""
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACK))

from services.fec_service import controler_fec, lignes_fec, piece_fec  # noqa: E402


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _ligne(compte, debit, credit):
    return SimpleNamespace(compte=compte, libelle="", debit=Decimal(debit), credit=Decimal(credit))


def _ecriture(reference="", justificatifs=None):
    return SimpleNamespace(
        id=1,
        numero_ecriture="OD-2027-0001",
        journal="OD",
        exercice=2027,
        date=date(2027, 2, 3),
        date_piece=date(2027, 2, 3),
        reference=reference,
        libelle="Écriture test",
        source="manuel",
        est_validee=True,
        date_validation=datetime(2027, 2, 4, 10, 0, 0),
        created_at=datetime(2027, 2, 3, 9, 0, 0),
        justificatifs=justificatifs or [],
        lignes=[
            _ligne("5141", "100.00", "0.00"),
            _ligne("1111", "0.00", "100.00"),
        ],
    )


def test_migration_039_cree_justificatifs_et_date_piece_auto():
    sql = read(BACK / "039_compta4_justificatifs_fec.sql")
    assert "CREATE TABLE IF NOT EXISTS ecriture_justificatifs" in sql
    assert "PAS réécrites" in sql
    assert "UPDATE ecritures\n   SET date_piece = date" not in sql
    assert "hisabpro_completer_date_piece" in sql
    assert "trg_ecritures_completer_date_piece" in sql
    assert "hisabpro_verrouiller_justificatif_ecriture" in sql
    assert "append-only" in sql


def test_fec_utilise_complement_si_reference_origine_absente():
    j = SimpleNamespace(
        reference="PJ-2027-0042",
        date_piece=date(2027, 2, 1),
        prioritaire=False,
    )
    ec = _ecriture(reference="", justificatifs=[j])
    ref, d = piece_fec(ec)
    assert ref == "PJ-2027-0042"
    assert d == date(2027, 2, 1)
    controle = controler_fec([ec], 2027)
    assert "REFERENCE_PIECE_MANQUANTE" not in {x["code"] for x in controle["bloquants"]}
    assert list(lignes_fec([ec], 2027))[0][8] == "PJ-2027-0042"


def test_complement_prioritaire_peut_corriger_reference_sans_modifier_original():
    ancien = SimpleNamespace(reference="REF-COMPLETEE", date_piece=date(2027, 2, 2), prioritaire=True)
    ec = _ecriture(reference="REF-ORIGINE", justificatifs=[ancien])
    assert piece_fec(ec) == ("REF-COMPLETEE", date(2027, 2, 2))


def test_backend_expose_recherche_piece_et_ajout_append_only():
    src = read(BACK / "routers" / "ecritures.py")
    ast.parse(src)
    assert '@router.get("/par-piece"' in src
    assert '@router.get("/{ecriture_id}/justificatifs")' in src
    assert '@router.post("/{ecriture_id}/justificatifs"' in src
    assert "models.EcritureJustificatif" in src
    assert "prioritaire=True" in src
    assert "joinedload(models.Ecriture.justificatifs)" in src


def test_pieces_jointes_acceptent_ecriture_sans_recrire_ecriture():
    src = read(BACK / "attachments.py")
    ast.parse(src)
    assert '"ecriture": (models.Ecriture, None)' in src
    assert "models.EcritureJustificatif" in src
    assert 'source_type="fichier"' in src
    assert "Une pièce jointe à une écriture définitive est conservée dans l'archive" in src


def test_front_journal_permet_piece_apres_validation():
    journal = read(ROOT / "src" / "pages" / "Journal.jsx")
    api = read(ROOT / "src" / "services" / "api.js")
    assert "PiecesJointes" in journal
    assert 'docType="ecriture"' in journal
    assert "ajouterReferenceJustificative" in journal
    assert "reference_fec || e.reference" in journal
    assert "ajouterJustificatif" in api
    assert "rechercherParPiece" in api


def test_modele_complete_date_piece_sans_saisie_utilisateur():
    models = read(BACK / "models.py")
    assert '@event.listens_for(Ecriture, "before_insert")' in models
    assert "if target.date_piece is None" in models
    assert "target.date_piece = target.date" in models


if __name__ == "__main__":
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj):
            obj()
    print("OK — COMPTA.4 justificatifs / FEC")
