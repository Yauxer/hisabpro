# -*- coding: utf-8 -*-
"""Règles normatives d'affectation du résultat.

Patch 052 — conformité normative
---------------------------------
Ce module isole les règles de calcul qui doivent rester indépendantes de l'UI :
- SA : réserve légale de 5 % du bénéfice après pertes antérieures, dans la
  limite de 10 % du capital (loi 17-95, art. 329) ;
- SARL / SARL AU : prélèvement de 5 % jusqu'au cinquième du capital, selon
  les règles du DOC applicables à la SARL ;
- les pertes antérieures sont apurées avant toute réserve/dividende ;
- une forme juridique non couverte n'est jamais assimilée silencieusement à
  une SA/SARL pour autoriser une distribution.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import re
import unicodedata

MONEY = Decimal("0.01")
TAUX_DOTATION = Decimal("0.05")


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)


def _canon(value: str | None) -> str:
    txt = unicodedata.normalize("NFKD", (value or "").upper())
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    return re.sub(r"[^A-Z0-9]", "", txt)


def regle_reserve_legale(forme_juridique: str | None):
    """Retourne la règle automatique fiable pour les formes supportées.

    Le ``plafond_ratio`` correspond au niveau de réserve à partir duquel le
    prélèvement obligatoire cesse. Les autres formes restent volontairement
    non automatisées : HisabPro ne doit pas inventer une règle juridique.
    """
    f = _canon(forme_juridique)
    if f in {"SA", "SOCIETEANONYME"}:
        return {
            "code": "SA",
            "taux": TAUX_DOTATION,
            "plafond_ratio": Decimal("0.10"),
            "referentiel": "Loi 17-95, article 329",
        }
    if f in {"SARL", "SARLAU", "SOCIETERESPONSABILITELIMITEE", "SOCIETERESPONSABILITELIMITEEASSOCIEUNIQUE"}:
        return {
            "code": "SARL",
            "taux": TAUX_DOTATION,
            "plafond_ratio": Decimal("0.20"),
            "referentiel": "DOC, articles 1038-1039 (SARL)",
        }
    return None


def calculer_contraintes_affectation(
    *,
    resultat_beneficiaire,
    forme_juridique,
    capital_social,
    reserve_legale_avant,
    report_deficitaire,
    resultat_instance_deficitaire=0,
    report_beneficiaire=0,
):
    """Calcule les minima/limites nécessaires à une affectation bénéficiaire.

    Les montants sont positifs dans cette fonction. Le résultat courant sert
    d'abord à apurer les pertes antérieures ; la réserve légale porte seulement
    sur le reliquat positif. Le bénéfice distribuable indiqué ici correspond au
    maximum théorique contrôlable automatiquement à partir des données
    comptables connues par HisabPro. Les réserves statutaires restent à la
    charge de la décision sociale et sont signalées séparément dans l'UI.
    """
    resultat = max(money(resultat_beneficiaire), Decimal("0.00"))
    capital = max(money(capital_social), Decimal("0.00"))
    reserve_avant = max(money(reserve_legale_avant), Decimal("0.00"))
    pertes = max(money(report_deficitaire), Decimal("0.00")) + max(
        money(resultat_instance_deficitaire), Decimal("0.00")
    )
    report_crediteur = max(money(report_beneficiaire), Decimal("0.00"))
    pertes_a_apurer = min(resultat, pertes)
    base_apres_pertes = money(resultat - pertes_a_apurer)

    regle = regle_reserve_legale(forme_juridique)
    reserve_min = Decimal("0.00")
    plafond = None
    manque_plafond = None
    if regle and capital > 0:
        plafond = money(capital * regle["plafond_ratio"])
        manque_plafond = max(money(plafond - reserve_avant), Decimal("0.00"))
        reserve_theorique = money(base_apres_pertes * regle["taux"])
        reserve_min = min(reserve_theorique, manque_plafond)

    affectable_apres_pertes = base_apres_pertes
    dividendes_max_resultat = max(money(base_apres_pertes - reserve_min), Decimal("0.00"))
    benefice_distribuable_indicatif = money(dividendes_max_resultat + report_crediteur)

    return {
        "regle": regle,
        "resultat": resultat,
        "pertes_anterieures": money(pertes),
        "pertes_a_apurer": money(pertes_a_apurer),
        "base_apres_pertes": base_apres_pertes,
        "reserve_legale_avant": reserve_avant,
        "reserve_legale_minimale": money(reserve_min),
        "plafond_reserve_legale": money(plafond) if plafond is not None else None,
        "manque_au_plafond": money(manque_plafond) if manque_plafond is not None else None,
        "affectable_apres_pertes": affectable_apres_pertes,
        "dividendes_max_sur_resultat": dividendes_max_resultat,
        "report_beneficiaire_anterieur": report_crediteur,
        "benefice_distribuable_indicatif": benefice_distribuable_indicatif,
        "forme_supportee": regle is not None,
        "capital_renseigne": capital > 0,
    }
