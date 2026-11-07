# -*- coding: utf-8 -*-
"""Comptabilité auxiliaire native des tiers.

Patch 053 : l'identité auxiliaire utilisée dans le FEC et les états est figée
sur chaque ligne comptable avant validation définitive. Le tiers vivant peut
ensuite être renommé/désactivé sans réécrire l'historique comptable.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException

import models


# Comptes de l'application qui représentent directement une créance/dette
# envers un client/fournisseur. La règle reste volontairement explicite : on ne
# déduit jamais la nature du tiers à partir d'un libellé libre.
COMPTES_AUX_CLIENT = ("3421", "3425", "4421")
COMPTES_AUX_FOURNISSEUR = ("4411", "4415", "3411", "4481")


def nature_auxiliaire_pour_compte(compte: Optional[str]) -> Optional[str]:
    numero = str(compte or "").strip()
    if any(numero.startswith(p) for p in COMPTES_AUX_CLIENT):
        return "client"
    if any(numero.startswith(p) for p in COMPTES_AUX_FOURNISSEUR):
        return "fournisseur"
    return None


def compte_collectif_requiert_auxiliaire(compte: Optional[str]) -> bool:
    """Les comptes collectifs principaux ne peuvent être validés sans tiers."""
    numero = str(compte or "").strip()
    return numero.startswith("3421") or numero.startswith("4411")


def generer_code_auxiliaire(tiers_id: int, nature: str) -> str:
    prefixe = "C" if nature == "client" else "F"
    return f"{prefixe}{int(tiers_id):08d}"


def code_auxiliaire_tiers(tiers, nature: str) -> str:
    champ = "code_aux_client" if nature == "client" else "code_aux_fournisseur"
    code = str(getattr(tiers, champ, None) or "").strip()
    return code or generer_code_auxiliaire(tiers.id, nature)


def _type_tiers_compatible(tiers, nature: str) -> bool:
    type_tiers = str(getattr(tiers, "type", "") or "")
    if nature == "client":
        return type_tiers in {"client", "les_deux"}
    return type_tiers in {"fournisseur", "les_deux"}


def charger_tiers_auxiliaire(db, societe_id: int, tiers_id: int, nature: str):
    tiers = db.query(models.Tiers).filter_by(id=int(tiers_id), societe_id=societe_id).first()
    if not tiers:
        raise HTTPException(422, "Tiers auxiliaire introuvable pour cette société.")
    if not _type_tiers_compatible(tiers, nature):
        lib = "client" if nature == "client" else "fournisseur"
        raise HTTPException(422, f"Le tiers sélectionné n'est pas utilisable comme {lib}.")
    return tiers


def rattacher_ligne_auxiliaire(
    db,
    societe_id: int,
    ligne,
    *,
    tiers_id: Optional[int] = None,
    tiers=None,
    nature: Optional[str] = None,
):
    """Fige l'auxiliaire sur une ligne encore modifiable.

    Si le compte n'est pas un compte auxiliaire connu, toute métadonnée auxiliaire
    est retirée afin d'éviter d'exporter un tiers sur un compte qui ne le concerne pas.
    """
    nature_compte = nature_auxiliaire_pour_compte(getattr(ligne, "compte", None))
    nature_effective = nature or nature_compte
    if nature_compte is None:
        ligne.tiers_id = None
        ligne.nature_auxiliaire = None
        ligne.compte_auxiliaire_snapshot = None
        ligne.libelle_auxiliaire_snapshot = None
        return ligne

    # La nature portée par l'appel ne peut pas contredire le compte.
    if nature_effective != nature_compte:
        raise HTTPException(422, "Le tiers sélectionné est incompatible avec le compte comptable de la ligne.")

    if tiers is None and tiers_id is not None:
        tiers = charger_tiers_auxiliaire(db, societe_id, int(tiers_id), nature_effective)
    elif tiers is not None:
        if int(getattr(tiers, "societe_id", -1)) != int(societe_id):
            raise HTTPException(422, "Le tiers auxiliaire appartient à une autre société.")
        if not _type_tiers_compatible(tiers, nature_effective):
            raise HTTPException(422, "Le type du tiers est incompatible avec le compte comptable.")

    if tiers is None:
        # Un brouillon manuel peut rester temporairement sans auxiliaire. La
        # validation définitive le refusera sur 3421/4411.
        ligne.tiers_id = None
        ligne.nature_auxiliaire = nature_effective
        ligne.compte_auxiliaire_snapshot = None
        ligne.libelle_auxiliaire_snapshot = None
        return ligne

    ligne.tiers_id = tiers.id
    ligne.nature_auxiliaire = nature_effective
    ligne.compte_auxiliaire_snapshot = code_auxiliaire_tiers(tiers, nature_effective)
    ligne.libelle_auxiliaire_snapshot = str(getattr(tiers, "nom", "") or "").strip()
    return ligne


def rattacher_tiers_aux_lignes(db, societe_id: int, lignes, *, tiers_id: Optional[int], nature: str):
    if not tiers_id:
        return lignes
    tiers = charger_tiers_auxiliaire(db, societe_id, int(tiers_id), nature)
    for ligne in lignes:
        nature_compte = nature_auxiliaire_pour_compte(getattr(ligne, "compte", None))
        if nature_compte == nature:
            rattacher_ligne_auxiliaire(db, societe_id, ligne, tiers=tiers, nature=nature)
    return lignes


def verifier_auxiliaires_avant_validation(lignes):
    """Refuse une écriture définitive dont le collectif 3421/4411 est anonyme."""
    manquantes = []
    for ligne in lignes or []:
        if not compte_collectif_requiert_auxiliaire(getattr(ligne, "compte", None)):
            continue
        if not (
            getattr(ligne, "tiers_id", None)
            and str(getattr(ligne, "compte_auxiliaire_snapshot", None) or "").strip()
            and str(getattr(ligne, "libelle_auxiliaire_snapshot", None) or "").strip()
        ):
            manquantes.append(str(getattr(ligne, "compte", "") or ""))
    if manquantes:
        comptes = ", ".join(sorted(set(manquantes)))
        raise HTTPException(
            422,
            f"Auxiliaire obligatoire sur le(s) compte(s) collectif(s) {comptes}. "
            "Sélectionnez explicitement le client/fournisseur avant validation : ouvrez le brouillon dans le Journal, "
            "choisissez le tiers sur chaque ligne de ce compte, enregistrez puis validez.",
        )
