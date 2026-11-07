"""Normalisation prudente des identifiants administratifs marocains.

On ne tente pas de vérifier l'existence réelle d'un identifiant auprès d'un
service externe. Les contrôles portent uniquement sur la forme afin d'éviter
les fautes de saisie et de conserver les zéros initiaux.
"""
from __future__ import annotations

import re

_SEPARATEURS = re.compile(r"[\s.\-/]+")
_TP_AUTORISEE = re.compile(r"^[A-Z0-9][A-Z0-9 .\-/]*$")


def _vide(value):
    return value is None or str(value).strip() == ""


def normaliser_ice(value):
    """ICE : 15 chiffres. Espaces, points, tirets et slash sont tolérés à la saisie."""
    if _vide(value):
        return None
    raw = str(value).strip()
    nettoye = _SEPARATEURS.sub("", raw)
    if not nettoye.isdigit() or len(nettoye) != 15:
        raise ValueError("L’ICE doit contenir exactement 15 chiffres")
    return nettoye


def normaliser_if(value):
    """IF : identifiant numérique ; on évite de figer une longueur trop stricte."""
    if _vide(value):
        return None
    raw = str(value).strip()
    nettoye = _SEPARATEURS.sub("", raw)
    if not nettoye.isdigit():
        raise ValueError("L’identifiant fiscal (IF) doit être numérique")
    if len(nettoye) > 20:
        raise ValueError("L’identifiant fiscal (IF) est trop long")
    return nettoye


def normaliser_tp(value):
    """N° de taxe professionnelle / patente : normalisation légère et non destructive."""
    if _vide(value):
        return None
    nettoye = " ".join(str(value).strip().upper().split())
    if len(nettoye) > 50 or not _TP_AUTORISEE.fullmatch(nettoye):
        raise ValueError("Le numéro de taxe professionnelle contient des caractères invalides")
    return nettoye


def ice_valide(value) -> bool:
    try:
        return normaliser_ice(value) is not None
    except ValueError:
        return False
