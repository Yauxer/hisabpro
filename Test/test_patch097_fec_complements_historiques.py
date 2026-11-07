# -*- coding: utf-8 -*-
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

from services.fec_service import auxiliaire_fec, controler_fec, lignes_fec  # noqa: E402


def _complement(tiers_id=7, code="C00000007", nom="ACME SARL", nature="client"):
    return SimpleNamespace(
        id=1,
        tiers_id=tiers_id,
        nature_auxiliaire=nature,
        compte_auxiliaire_snapshot=code,
        libelle_auxiliaire_snapshot=nom,
    )


def _ligne(compte, debit=0, credit=0, *, complement=None, natif=False):
    kw = dict(
        compte=compte,
        debit=Decimal(str(debit)),
        credit=Decimal(str(credit)),
        libelle="Ligne",
        tiers_id=None,
        nature_auxiliaire=None,
        compte_auxiliaire_snapshot=None,
        libelle_auxiliaire_snapshot=None,
        auxiliaire_complements=([complement] if complement else []),
        code_lettrage=None,
        date_lettrage=None,
    )
    if natif:
        kw.update(
            tiers_id=99,
            nature_auxiliaire="client",
            compte_auxiliaire_snapshot="C00000099",
            libelle_auxiliaire_snapshot="Snapshot natif",
        )
    return SimpleNamespace(**kw)


def _ecriture(lignes):
    return SimpleNamespace(
        id=1,
        numero_ecriture="VT-2027-0001",
        journal="VT",
        exercice=2027,
        date=date(2027, 2, 1),
        date_piece=date(2027, 2, 1),
        reference="FAC-001",
        libelle="Facture client",
        source="facture",
        est_validee=True,
        date_validation=datetime(2027, 2, 1, 10, 0, 0),
        created_at=datetime(2027, 2, 1, 9, 0, 0),
        justificatifs=[],
        lignes=lignes,
    )


def _exercice():
    return SimpleNamespace(
        date_debut=date(2027, 1, 1),
        date_fin=date(2027, 12, 31),
        statut="cloture",
    )


def test_auxiliaire_fec_utilise_complement_append_only_si_snapshot_natif_absent():
    ligne = _ligne("3421", 120, 0, complement=_complement())
    tiers_id, nature, code, nom = auxiliaire_fec(ligne)
    assert (tiers_id, nature, code, nom) == (7, "client", "C00000007", "ACME SARL")


def test_snapshot_natif_reste_prioritaire_sur_un_complement_historique():
    ligne = _ligne("3421", 120, 0, complement=_complement(), natif=True)
    assert auxiliaire_fec(ligne)[2:] == ("C00000099", "Snapshot natif")


def test_controle_fec_accepte_un_collectif_documente_par_complement_append_only():
    ec = _ecriture([
        _ligne("3421", 120, 0, complement=_complement()),
        _ligne("7111", 0, 120),
    ])
    controle = controler_fec([ec], 2027, _exercice())
    codes = {x["code"] for x in controle["bloquants"]}
    assert "AUXILIAIRE_MANQUANT" not in codes
    assert "AUXILIAIRES_COLLECTIF_DESEQUILIBRES" not in codes


def test_export_fec_restitue_numero_et_libelle_du_complement():
    ec = _ecriture([
        _ligne("3421", 120, 0, complement=_complement()),
        _ligne("7111", 0, 120),
    ])
    row = next(r for r in lignes_fec([ec], 2027) if r[4] == "3421")
    assert row[6] == "C00000007"
    assert row[7] == "ACME SARL"


def test_migration_068_est_append_only_et_ne_recrit_pas_les_lignes_definitives():
    sql = (BACK / "068_fec_complements_historiques_append_only.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS ligne_auxiliaire_complements" in sql
    assert "trg_ligne_aux_complements_append_only" in sql
    assert "INSERT INTO ligne_auxiliaire_complements" in sql
    assert "INSERT INTO ecriture_justificatifs" in sql
    # La réparation des auxiliaires ne doit plus contourner l'immutabilité des lignes.
    assert "ALTER TABLE lignes_ecriture DISABLE TRIGGER" not in sql
    assert "UPDATE lignes_ecriture" not in sql
    assert "HAVING COUNT(DISTINCT c.tiers_id)=1" in sql


def test_chargeur_fec_precharge_les_complements_auxiliaires():
    src = (BACK / "services" / "fec_exercice_service.py").read_text(encoding="utf-8")
    assert "joinedload(models.Ecriture.lignes).joinedload(models.LigneEcriture.auxiliaire_complements)" in src
