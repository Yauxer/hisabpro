# -*- coding: utf-8 -*-
"""CONFORM.1 — règles de cohérence TVA utilisées par les formulaires métier.

Le service ne tente pas de déduire le régime fiscal d'une opération à partir de son
libellé : cette qualification reste une donnée métier explicite. Il centralise en
revanche les contrôles structurels et les taux usuels/transitoires de la réforme TVA.

Références de conception : CGI marocain et mesures transitoires de la LF 2024.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

QUALIFICATIONS_TVA = {
    "taxable",
    "exonere_droit_deduction",
    "exonere_sans_deduction",
    "hors_champ",
    "suspension",
}
QUALIFICATIONS_SANS_TVA = QUALIFICATIONS_TVA - {"taxable"}

# Catalogue de saisie générique. Il contient les taux usuels et les taux de transition
# connus de la réforme. Une qualification sectorielle précise reste à la charge du
# comptable : HisabPro empêche surtout un taux impossible pour l'année du document.
TAUX_PAR_ANNEE = {
    2024: (0, 8, 10, 11, 12, 13, 14, 16, 20),
    2025: (0, 9, 10, 12, 15, 18, 20),
}
TAUX_HISTORIQUES = (0, 7, 10, 14, 20)
TAUX_2026_PLUS = (0, 10, 20)


def _annee(value) -> int:
    if isinstance(value, date):
        return value.year
    if isinstance(value, str):
        return date.fromisoformat(value).year
    return int(value)


def taux_autorises(value) -> tuple[int, ...]:
    annee = _annee(value)
    if annee <= 2023:
        return TAUX_HISTORIQUES
    if annee in TAUX_PAR_ANNEE:
        return TAUX_PAR_ANNEE[annee]
    return TAUX_2026_PLUS


def qualification_valide(value: str | None) -> str:
    qualif = (value or "taxable").strip().lower()
    if qualif not in QUALIFICATIONS_TVA:
        raise ValueError("Qualification TVA invalide.")
    return qualif


def valider_tva(value_date, taux, qualification: str | None = "taxable") -> float:
    """Valide une combinaison date/taux/qualification.

    - une opération taxable doit porter un taux strictement positif du catalogue ;
    - une opération exonérée/hors champ/suspendue doit porter un taux 0 ;
    - en 2026+, la saisie générique est limitée aux taux 10/20 et au 0 qualifié.
    """
    qualif = qualification_valide(qualification)
    taux_d = Decimal(str(taux if taux is not None else 0))
    if taux_d < 0 or taux_d > 100:
        raise ValueError("Le taux de TVA doit être compris entre 0 et 100 %.")
    if qualif in QUALIFICATIONS_SANS_TVA:
        if taux_d != 0:
            raise ValueError("Une opération exonérée, hors champ ou en suspension doit avoir un taux de TVA de 0 %.")
        return 0.0
    if taux_d == 0:
        raise ValueError("Un taux de 0 % doit être qualifié (exonération, hors champ ou suspension).")
    autorises = {Decimal(str(t)) for t in taux_autorises(value_date) if t != 0}
    if taux_d not in autorises:
        liste = ", ".join(f"{t:g} %" for t in taux_autorises(value_date) if t)
        raise ValueError(f"Taux TVA {taux_d:g} % non proposé pour cette date. Taux de saisie disponibles : {liste}.")
    return float(taux_d)


def taux_effectif(taux, qualification: str | None) -> Decimal:
    return Decimal("0") if qualification_valide(qualification) in QUALIFICATIONS_SANS_TVA else Decimal(str(taux or 0))


def est_sans_tva(qualification: str | None) -> bool:
    return qualification_valide(qualification) in QUALIFICATIONS_SANS_TVA
