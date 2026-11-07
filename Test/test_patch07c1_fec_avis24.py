# -*- coding: utf-8 -*-
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
if not BACKEND.exists():
    # Compatibilité avec l'arborescence historique où Test était copié sous backend.
    BACKEND = ROOT
sys.path.insert(0, str(BACKEND))

from services.fec_service import (  # noqa: E402
    ENTETES_FEC_AVIS24,
    controler_fec,
    lignes_fec,
)


def ligne(compte="5141", debit="100.00", credit="0.00", libelle="Banques"):
    return SimpleNamespace(
        compte=compte,
        debit=Decimal(debit),
        credit=Decimal(credit),
        libelle=libelle,
    )


def ecriture(
    eid,
    numero,
    *,
    journal="BQ",
    d=date(2027, 1, 2),
    validee=True,
    reference="REL-001",
    date_piece=date(2027, 1, 1),
    lignes=None,
):
    return SimpleNamespace(
        id=eid,
        numero_ecriture=numero,
        journal=journal,
        exercice=2027,
        date=d,
        date_piece=date_piece,
        reference=reference,
        libelle="Opération bancaire",
        est_validee=validee,
        date_validation=datetime(2027, 1, 3, 10, 0, 0) if validee else None,
        created_at=datetime(2027, 1, 2, 9, 0, eid),
        lignes=lignes or [
            ligne("5141", "100.00", "0.00", "Banques"),
            ligne("1111", "0.00", "100.00", "Capital social"),
        ],
    )


def exercice_obj(statut="ouvert"):
    return SimpleNamespace(
        date_debut=date(2027, 1, 1),
        date_fin=date(2027, 12, 31),
        statut=statut,
    )


def test_entetes_sont_les_18_champs_officiels_avis24():
    assert ENTETES_FEC_AVIS24 == [
        "Code_Journal", "Libelle_Journal", "Num_Ecriture", "Date_Ecriture",
        "Num_Compte", "Libelle_Compte", "Num_Compte_Aux", "Libelle_Compte_Aux",
        "Ref_Piece", "Date_Piece", "Libelle_Ecriture", "Montant_Debit",
        "Montant_Credit", "Lettrage_Ecriture", "Date_Lettrage", "Date_Validation",
        "Montant_Devise", "Id_devise",
    ]
    assert len(ENTETES_FEC_AVIS24) == 18


def test_fec_utilise_numero_interne_date_piece_et_libelle_compte_canonique():
    ec = ecriture(1, "BQ-2027-0001", date_piece=date(2026, 12, 31))
    rows = list(lignes_fec([ec], 2027))
    assert len(rows) == 2
    r = rows[0]
    assert len(r) == 18
    assert r[0] == "BQ"
    assert r[2] == "BQ-2027-0001"
    assert r[3] == "20270102"
    assert r[4] == "5141"
    assert r[5] == "Banques (solde débiteur)"
    assert r[8] == "REL-001"
    assert r[9] == "20261231"
    assert r[15] == "20270103"


def test_brouillon_bloque_export_fec_complet():
    c = controler_fec(
        [ecriture(1, "BQ-2027-0001"), ecriture(2, "BQ-2027-0002", validee=False)],
        2027,
        exercice_obj(),
    )
    assert c["conforme_export"] is False
    assert "ECRITURES_BROUILLON" in {x["code"] for x in c["bloquants"]}


def test_sequence_avec_trou_est_bloquante():
    c = controler_fec(
        [ecriture(1, "BQ-2027-0001"), ecriture(3, "BQ-2027-0003", d=date(2027, 1, 3))],
        2027,
        exercice_obj(),
    )
    assert c["conforme_export"] is False
    anomalie = next(x for x in c["bloquants"] if x["code"] == "SEQUENCE_AVEC_TROUS")
    assert 2 in anomalie["details"]["manquants"]


def test_reference_piece_manquante_est_bloquante():
    c = controler_fec([ecriture(1, "BQ-2027-0001", reference="")], 2027, exercice_obj())
    assert "REFERENCE_PIECE_MANQUANTE" in {x["code"] for x in c["bloquants"]}


def test_ecriture_desequilibree_est_bloquante():
    ec = ecriture(1, "BQ-2027-0001", lignes=[ligne("5141", "100.00", "0.00")])
    c = controler_fec([ec], 2027, exercice_obj())
    codes = {x["code"] for x in c["bloquants"]}
    assert "ECRITURE_DESEQUILIBREE" in codes
    assert "JOURNAL_DESEQUILIBRE" in codes
    assert "BALANCE_GLOBALE_DESEQUILIBREE" in codes


def test_exercice_ouvert_est_avertissement_pas_blocage_si_tout_est_propre():
    c = controler_fec([ecriture(1, "BQ-2027-0001")], 2027, exercice_obj("ouvert"))
    assert c["conforme_export"] is True
    assert "EXERCICE_NON_CLOTURE" in {x["code"] for x in c["avertissements"]}
