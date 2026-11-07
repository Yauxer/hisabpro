# -*- coding: utf-8 -*-
"""COMPTA.5 — garde-fous de recette comptable et FEC."""
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

from services.fec_service import controler_fec, lignes_fec  # noqa: E402


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _ligne(compte, debit="0", credit="0", libelle=""):
    # Depuis COMPTA-AUX, les comptes collectifs portent une identité auxiliaire
    # native. La recette E2E doit donc représenter des écritures conformes au
    # même contrat que la production.
    est_client = str(compte).startswith("3421")
    est_fournisseur = str(compte).startswith("4411")
    return SimpleNamespace(
        compte=compte, libelle=libelle,
        debit=Decimal(debit), credit=Decimal(credit),
        tiers_id=(101 if est_client else 202 if est_fournisseur else None),
        nature_auxiliaire=("client" if est_client else "fournisseur" if est_fournisseur else None),
        compte_auxiliaire_snapshot=("C00000101" if est_client else "F00000202" if est_fournisseur else None),
        libelle_auxiliaire_snapshot=("Client recette" if est_client else "Fournisseur recette" if est_fournisseur else None),
    )


def _ec(eid, journal, numero, d, ref, lignes, *, source="facture", validation=None):
    return SimpleNamespace(
        id=eid, journal=journal, numero_ecriture=numero, exercice=d.year,
        date=d, date_piece=d, reference=ref, libelle=f"Ecriture {ref}",
        source=source, est_validee=True,
        date_validation=validation or datetime(d.year, d.month, d.day, 12, 0, 0),
        created_at=datetime(d.year, d.month, d.day, 10, 0, 0),
        justificatifs=[], lignes=lignes,
    )


def test_facture_achat_utilise_reference_fournisseur_et_source_metier():
    src = read(BACK / "routers" / "factures.py")
    ast.parse(src)
    assert "reference_piece = (facture.numero if est_vente else (facture.reference or facture.numero))" in src
    assert 'source="facture"' in src
    assert "date_piece=facture.date" in src


def test_reglements_et_documents_auto_portent_source_et_date_piece():
    commercial = read(BACK / "routers" / "commercial.py")
    acomptes = read(BACK / "acomptes.py")
    avoirs = read(BACK / "avoirs.py")
    ast.parse(commercial); ast.parse(acomptes); ast.parse(avoirs)
    assert 'source="reglement"' in commercial
    assert "date_piece=reglement.date" in commercial
    assert 'source="acompte"' in acomptes
    assert 'source="avoir"' in avoirs


def test_fec_ne_remplace_pas_date_validation_par_date_cloture():
    validation = datetime(2026, 9, 10, 14, 30, 0)
    ec = _ec(
        1, "VT", "VT-2026-0001", date(2026, 9, 10), "FA-2026-0001",
        [_ligne("3421", "120"), _ligne("7111", credit="100"), _ligne("4455", credit="20")],
        validation=validation,
    )
    cloture = SimpleNamespace(date_cloture=datetime(2027, 1, 15, 9, 0, 0))
    row = list(lignes_fec([ec], 2026, cloture))[0]
    assert row[15] == "20260910"


def test_chaine_vente_achat_reglements_cloture_est_fec_equilibree():
    d1 = date(2026, 9, 10)
    d2 = date(2026, 9, 11)
    d3 = date(2026, 12, 31)
    ecritures = [
        _ec(1, "VT", "VT-2026-0001", d1, "FA-2026-0001", [
            _ligne("3421", "120"), _ligne("7111", credit="100"), _ligne("4455", credit="20"),
        ]),
        _ec(2, "BQ", "BQ-2026-0001", d1, "VIR-CLIENT-001", [
            _ligne("5141", "120"), _ligne("3421", credit="120"),
        ], source="reglement"),
        _ec(3, "AC", "AC-2026-0001", d2, "FF-ATLAS-001", [
            _ligne("6126", "50"), _ligne("34552", "10"), _ligne("4411", credit="60"),
        ]),
        _ec(4, "BQ", "BQ-2026-0002", d2, "VIR-FOURN-001", [
            _ligne("4411", "60"), _ligne("5141", credit="60"),
        ], source="reglement"),
        _ec(5, "CL", "CL-2026-0001", d3, "CLOTURE-2026", [
            _ligne("7111", "100"), _ligne("6126", credit="50"), _ligne("1191", credit="50"),
        ], source="cloture"),
    ]
    ex = SimpleNamespace(date_debut=date(2026, 1, 1), date_fin=date(2026, 12, 31), statut="cloture")
    cloture = SimpleNamespace(date_cloture=datetime(2027, 1, 5, 10, 0, 0))
    ctl = controler_fec(ecritures, 2026, ex, cloture)
    assert ctl["conforme_export"], ctl["bloquants"]
    rows = list(lignes_fec(ecritures, 2026, cloture))
    assert rows and all(len(r) == 18 for r in rows)
    assert any(r[8] == "FF-ATLAS-001" for r in rows)
    assert any(r[8] == "VIR-CLIENT-001" for r in rows)


def test_recette_postgresql_est_transactionnelle_et_protegee():
    src = read(ROOT / "Test" / "recette_compta5_postgres.py")
    ast.parse(src)
    assert "HISABPRO_ALLOW_REMOTE_PG_TESTS" in src
    assert "db.commit = db.flush" in src
    assert "real_rollback()" in src
    assert "cloturer_exercice" in src
    assert "apercu_fec" in src
    assert "Ref_Piece = numéro facture fournisseur" in src


def test_message_exercice_cloture_ne_propose_plus_reouverture():
    src = read(BACK / "routers" / "ecritures.py")
    assert "Rouvrez l'exercice si une correction est indispensable" not in src
    assert "contrepassation traçable" in src
