# -*- coding: utf-8 -*-
"""Moteur de résultat fiscal et d'IS marocain — Patch 08.1.

Sources juridiques utilisées pour les règles codées :
- CGI, art. 11 : charges non déductibles (notamment amendes/pénalités) ;
- CGI, art. 12 : déficit reportable ;
- CGI, art. 19 et art. 247-XXXVII-A : taux IS et convergence 2023-2026.

La cotisation minimale, les acomptes et la contribution sociale sont traités
séparément dans les sous-patches suivants : ce module calcule l'IS théorique.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

ZERO = Decimal("0.00")
CENT_MILLIONS = Decimal("100000000.00")
UN_MILLION = Decimal("1000000.00")
TROIS_CENT_MILLE = Decimal("300000.00")

CATEGORIES_IS = {
    "droit_commun": "Régime de droit commun",
    "industrielle": "Société industrielle",
    "cfc_zai": "CFC / Zone d'accélération industrielle",
    "convention_investissement": "Convention d'investissement ≥ 1,5 Md MAD",
    "avantage_20_transition": "Ancien taux plafonné à 20 % (transition 2023–2026)",
    "financier_40": "Établissement de crédit / BAM / CDG / assurance-réassurance",
    "exonere": "Exonération totale d'IS",
}

# Réforme issue de la LF 2023, période transitoire 2023-2026.
TAUX_PETIT_BENEFICE = {2023: Decimal("12.50"), 2024: Decimal("15.00"), 2025: Decimal("17.50"), 2026: Decimal("20.00")}
TAUX_INTERMEDIAIRE = {2023: Decimal("28.25"), 2024: Decimal("25.50"), 2025: Decimal("22.75"), 2026: Decimal("20.00")}
TAUX_SEUIL_100M = {2023: Decimal("32.00"), 2024: Decimal("33.00"), 2025: Decimal("34.00"), 2026: Decimal("35.00")}
TAUX_INDUSTRIEL = {2023: Decimal("24.50"), 2024: Decimal("23.00"), 2025: Decimal("21.50"), 2026: Decimal("20.00")}
TAUX_CFC_ZAI = {2023: Decimal("16.25"), 2024: Decimal("17.50"), 2025: Decimal("18.75"), 2026: Decimal("20.00")}
TAUX_AVANTAGE_20_SEUIL_100M = {2023: Decimal("23.75"), 2024: Decimal("27.50"), 2025: Decimal("31.25"), 2026: Decimal("35.00")}
TAUX_FINANCIER = {2023: Decimal("37.75"), 2024: Decimal("38.50"), 2025: Decimal("39.25"), 2026: Decimal("40.00")}


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def pct(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class TauxIS:
    taux: Decimal
    libelle: str
    source: str
    provisoire: bool = False


def determiner_taux_is(
    exercice: int,
    benefice_fiscal,
    categorie_is: str = "droit_commun",
    maintien_taux_35_transition: bool = False,
    taux_force=None,
) -> TauxIS:
    """Retourne le taux IS applicable au bénéfice fiscal fourni.

    Pour >2026, on applique les taux cibles actuellement prévus par l'art. 19
    (20/35/40). Le résultat est marqué provisoire tant que le CGI de l'exercice
    concerné n'est pas la référence fiscale embarquée par HisabPro.
    """
    benefice = money(benefice_fiscal)
    if categorie_is not in CATEGORIES_IS:
        raise ValueError(f"Catégorie IS inconnue : {categorie_is}")

    if taux_force is not None:
        t = pct(taux_force)
        if t < 0 or t > 100:
            raise ValueError("Le taux IS forcé doit être compris entre 0 et 100%.")
        return TauxIS(t, "Taux dérogatoire paramétré", "Paramétrage fiscal société/exercice", exercice > 2026)

    if categorie_is == "exonere":
        return TauxIS(Decimal("0.000"), "Exonération totale", "CGI — régime d'exonération à justifier", exercice > 2026)

    # Taux cibles après la période transitoire. Ils correspondent au droit
    # actuellement en vigueur ; un exercice futur reste signalé comme provisoire.
    if exercice >= 2027:
        provisoire = True
        if categorie_is == "financier_40":
            return TauxIS(Decimal("40.000"), CATEGORIES_IS[categorie_is], "CGI art. 19-I-C — taux cible", provisoire)
        if categorie_is in ("cfc_zai", "convention_investissement"):
            return TauxIS(Decimal("20.000"), CATEGORIES_IS[categorie_is], "CGI art. 19-I-B — exclusion du taux de 35%", provisoire)
        taux = Decimal("35.000") if benefice >= CENT_MILLIONS else Decimal("20.000")
        return TauxIS(taux, CATEGORIES_IS[categorie_is], "CGI art. 19-I — taux cible", provisoire)

    if exercice < 2023:
        raise ValueError("Le moteur Patch 08.1 couvre les exercices 2023 et suivants.")

    if categorie_is == "financier_40":
        return TauxIS(pct(TAUX_FINANCIER[exercice]), CATEGORIES_IS[categorie_is], "CGI art. 247-XXXVII-A — transition")
    if categorie_is == "cfc_zai":
        return TauxIS(pct(TAUX_CFC_ZAI[exercice]), CATEGORIES_IS[categorie_is], "CGI art. 247-XXXVII-A — transition")
    if categorie_is == "convention_investissement":
        return TauxIS(Decimal("20.000"), CATEGORIES_IS[categorie_is], "CGI art. 19-I-B-3 / art. 247-XXXVII-A")
    if categorie_is == "avantage_20_transition":
        taux = TAUX_AVANTAGE_20_SEUIL_100M[exercice] if (benefice >= CENT_MILLIONS or maintien_taux_35_transition) else Decimal("20.00")
        return TauxIS(pct(taux), CATEGORIES_IS[categorie_is], "CGI art. 247-XXXVII-A — ancien taux plafonné à 20%")

    # Pendant 2023-2026, une société ayant atteint le seuil de 100 MDH ne peut
    # bénéficier ensuite d'un taux inférieur pendant la période transitoire.
    if benefice >= CENT_MILLIONS or maintien_taux_35_transition:
        return TauxIS(pct(TAUX_SEUIL_100M[exercice]), CATEGORIES_IS[categorie_is], "CGI art. 247-XXXVII-A — seuil 100 MDH")

    if categorie_is == "industrielle":
        return TauxIS(pct(TAUX_INDUSTRIEL[exercice]), CATEGORIES_IS[categorie_is], "CGI art. 247-XXXVII-A — activité industrielle")

    if benefice <= TROIS_CENT_MILLE:
        taux = TAUX_PETIT_BENEFICE[exercice]
    elif benefice <= UN_MILLION:
        taux = Decimal("20.00")
    else:
        taux = TAUX_INTERMEDIAIRE[exercice]
    return TauxIS(pct(taux), CATEGORIES_IS[categorie_is], "CGI art. 247-XXXVII-A — droit commun")


def calculer_base_fiscale(*, resultat_comptable_avant_is, reintegrations, deductions,
                         deficit_reportable_disponible=None):
    """Base pure commune ; déficit non fourni = imputation/bénéfice inconnus.

    Aucune vérification d'éligibilité ou de millésime n'est inventée ici :
    les appelants qualifient les déficits avant de transmettre leur disponible.
    """
    if any(v is None for v in (resultat_comptable_avant_is, reintegrations, deductions)):
        raise ValueError("Résultat et retraitements explicitement renseignés requis.")
    valeurs = (resultat_comptable_avant_is, reintegrations, deductions, deficit_reportable_disponible)
    try:
        if any(isinstance(v, bool) or not Decimal(str(v)).is_finite() for v in valeurs if v is not None):
            raise ValueError("Montants fiscaux finis requis.")
        resultat_comptable = money(resultat_comptable_avant_is)
        reintegrations = money(reintegrations)
        deductions = money(deductions)
        deficit_disponible = None if deficit_reportable_disponible is None else money(deficit_reportable_disponible)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Montants fiscaux finis requis.") from exc
    if not all(v.is_finite() for v in (resultat_comptable, reintegrations, deductions)
               + (() if deficit_disponible is None else (deficit_disponible,))):
        raise ValueError("Montants fiscaux finis requis.")
    if reintegrations < 0 or deductions < 0 or (deficit_disponible is not None and deficit_disponible < 0):
        raise ValueError("Réintégrations, déductions et déficit disponible doivent être positifs.")
    resultat_avant_deficit = money(resultat_comptable + reintegrations - deductions)
    deficit_impute = None if deficit_disponible is None else min(deficit_disponible, max(resultat_avant_deficit, ZERO))
    benefice_fiscal = None if deficit_impute is None else money(max(ZERO, resultat_avant_deficit - deficit_impute))
    deficit_genere = money(max(ZERO, -resultat_avant_deficit))
    deficit_restant = None if deficit_impute is None else money(deficit_disponible - deficit_impute)
    return {
        "resultat_comptable_avant_is": resultat_comptable,
        "reintegrations": reintegrations,
        "deductions": deductions,
        "resultat_fiscal_avant_deficit": resultat_avant_deficit,
        "deficit_reportable_disponible": deficit_disponible,
        "deficit_impute": None if deficit_impute is None else money(deficit_impute),
        "deficit_reportable_restant": deficit_restant,
        "deficit_fiscal_genere": deficit_genere,
        "benefice_fiscal_imposable": benefice_fiscal,
    }


def calculer_is(
    *,
    exercice: int,
    resultat_comptable_avant_is,
    reintegrations,
    deductions,
    deficit_reportable_disponible=0,
    categorie_is="droit_commun",
    maintien_taux_35_transition=False,
    taux_force=None,
):
    # Le contrat historique conserve ses valeurs par défaut explicites.
    base = calculer_base_fiscale(
        resultat_comptable_avant_is=money(resultat_comptable_avant_is),
        reintegrations=money(reintegrations), deductions=money(deductions),
        deficit_reportable_disponible=money(deficit_reportable_disponible))
    benefice_fiscal = base["benefice_fiscal_imposable"]

    taux = determiner_taux_is(
        exercice,
        benefice_fiscal,
        categorie_is=categorie_is,
        maintien_taux_35_transition=maintien_taux_35_transition,
        taux_force=taux_force,
    )
    is_theorique = money(benefice_fiscal * taux.taux / Decimal("100"))

    return {
        **base,
        "taux_is": taux.taux,
        "libelle_taux": taux.libelle,
        "source_taux": taux.source,
        "taux_provisoire": taux.provisoire,
        "is_theorique": is_theorique,
    }
