# -*- coding: utf-8 -*-
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import sys
import types

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

# Ces helpers purs n'ont pas besoin du mapping ORM ni d'une connexion PostgreSQL.
sys.modules.setdefault("models", types.SimpleNamespace())

from services.auxiliaire_service import (  # noqa: E402
    generer_code_auxiliaire,
    nature_auxiliaire_pour_compte,
    verifier_auxiliaires_avant_validation,
)
from services.fec_service import controler_fec, lignes_fec  # noqa: E402


def _ligne(compte, debit=0, credit=0, **kwargs):
    base = dict(
        compte=compte,
        debit=Decimal(str(debit)),
        credit=Decimal(str(credit)),
        libelle=kwargs.pop("libelle", "Ligne"),
        tiers_id=None,
        nature_auxiliaire=None,
        compte_auxiliaire_snapshot=None,
        libelle_auxiliaire_snapshot=None,
        code_lettrage=None,
        date_lettrage=None,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


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
        statut="ouvert",
    )


def test_codes_auxiliaires_stables_et_roles_de_comptes():
    assert generer_code_auxiliaire(12, "client") == "C00000012"
    assert generer_code_auxiliaire(12, "fournisseur") == "F00000012"
    assert nature_auxiliaire_pour_compte("3421") == "client"
    assert nature_auxiliaire_pour_compte("3425001") == "client"
    assert nature_auxiliaire_pour_compte("4411") == "fournisseur"
    assert nature_auxiliaire_pour_compte("4415001") == "fournisseur"
    assert nature_auxiliaire_pour_compte("5141") is None


def test_validation_collectif_refuse_un_tiers_anonyme():
    with pytest.raises(HTTPException) as exc:
        verifier_auxiliaires_avant_validation([
            _ligne("3421", debit=100, libelle="Client libre"),
            _ligne("7111", credit=100),
        ])
    assert exc.value.status_code == 422
    assert "Auxiliaire obligatoire" in str(exc.value.detail)


def test_validation_collectif_accepte_snapshot_auxiliaire_complet():
    verifier_auxiliaires_avant_validation([
        _ligne(
            "3421", debit=100,
            tiers_id=7,
            nature_auxiliaire="client",
            compte_auxiliaire_snapshot="C00000007",
            libelle_auxiliaire_snapshot="ACME SARL",
        ),
        _ligne("7111", credit=100),
    ])


def test_fec_alimente_num_et_libelle_compte_auxiliaire():
    ec = _ecriture([
        _ligne(
            "3421", debit=120,
            tiers_id=7,
            nature_auxiliaire="client",
            compte_auxiliaire_snapshot="C00000007",
            libelle_auxiliaire_snapshot="ACME SARL",
        ),
        _ligne("7111", credit=120),
    ])
    rows = list(lignes_fec([ec], 2027))
    ligne_client = next(r for r in rows if r[4] == "3421")
    assert ligne_client[6] == "C00000007"
    assert ligne_client[7] == "ACME SARL"
    assert len(ligne_client) == 18


def test_fec_bloque_un_collectif_sans_auxiliaire_natif():
    ec = _ecriture([
        _ligne("3421", debit=120, libelle="ACME SARL"),
        _ligne("7111", credit=120),
    ])
    controle = controler_fec([ec], 2027, _exercice())
    assert controle["conforme_export"] is False
    assert "AUXILIAIRE_MANQUANT" in {x["code"] for x in controle["bloquants"]}


def test_lettrage_priorise_identifiant_natif_et_non_libelle():
    src = (BACK / "lettrage.py").read_text(encoding="utf-8")
    bloc = src[src.index("def _cle_tiers_ligne"):src.index("def _verifier_compte_demande")]
    assert 'tiers_id = getattr(ligne, "tiers_id", None)' in bloc
    assert 'return f"tiers_id:{int(tiers_id)}"' in bloc
    assert 'compte_auxiliaire_snapshot' in bloc
    # Le libellé ne subsiste qu'en repli legacy, après les identifiants natifs.
    assert bloc.index('tiers_id = getattr') < bloc.index('tiers = _normaliser_tiers(ligne.libelle)')


def test_migration_cree_backfill_et_gardes_postgresql():
    sql = (BACK / "053_comptabilite_auxiliaire_avis24.sql").read_text(encoding="utf-8")
    for token in (
        "code_aux_client", "code_aux_fournisseur",
        "compte_auxiliaire_snapshot", "libelle_auxiliaire_snapshot",
        "UPDATE reglements r", "UPDATE lignes_ecriture l",
        "hisabpro_guard_auxiliaire_validation",
        "hisabpro_guard_ligne_auxiliaire_definitive",
        "trg_hisabpro_auxiliaire_validation",
        "trg_hisabpro_ligne_auxiliaire_definitive",
    ):
        assert token in sql
    assert "LOWER(BTRIM(t.nom))=LOWER(BTRIM(COALESCE(l.libelle,'')))" in sql
    assert "HAVING COUNT(*)=1" in sql


def test_ecritures_automatiques_propaguent_le_tiers_auxiliaire():
    fichiers = {
        "factures": (BACK / "routers" / "factures.py").read_text(encoding="utf-8"),
        "reglements": (BACK / "routers" / "commercial.py").read_text(encoding="utf-8"),
        "avoirs": (BACK / "avoirs.py").read_text(encoding="utf-8"),
        "acomptes": (BACK / "acomptes.py").read_text(encoding="utf-8"),
        "immobilisations": (BACK / "routers" / "immobilisations.py").read_text(encoding="utf-8"),
    }
    for nom, src in fichiers.items():
        assert "rattacher_" in src, f"{nom} ne rattache pas l'auxiliaire natif"
    assert 'payload["tiers_id"]' in fichiers["reglements"]
    assert "tiers_id=getattr(l, \"tiers_id\", None)" in fichiers["reglements"]


def test_formulaire_journal_envoie_tiers_id_et_refuse_validation_collectif_anonyme():
    src = (ROOT / "src" / "components" / "FormulaireEcriture.jsx").read_text(encoding="utf-8")
    for token in (
        "function natureAuxiliaireCompte",
        "onSelect?.(null)",
        "tiers_id: l.tiers_id || null",
        "auxiliairesComplets",
        "onSelect={tiers => majLigne(i, 'tiers_id'",
    ):
        assert token in src


def test_fiche_tiers_expose_codes_auxiliaires_sans_les_rendre_saisissables():
    api = (BACK / "routers" / "tiers.py").read_text(encoding="utf-8")
    page = (ROOT / "src" / "pages" / "Tiers.jsx").read_text(encoding="utf-8")
    assert "code_aux_client" in api and "code_aux_fournisseur" in api
    assert 'f"C{tiers.id:08d}"' in api and 'f"F{tiers.id:08d}"' in api
    assert "Auxiliaire client" in page and "Auxiliaire fournisseur" in page
