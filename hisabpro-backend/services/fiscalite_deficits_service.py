# -*- coding: utf-8 -*-
"""Gestion des déficits fiscaux reportables — Patch 08.3.

Référentiel : CGI 2026, article 12.
- la fraction ordinaire d'un déficit est reportable sur les quatre exercices
  qui suivent l'exercice déficitaire ;
- la fraction correspondant à des amortissements régulièrement comptabilisés
  et fiscalement déductibles n'est pas soumise à cette limitation.

Le service est volontairement indépendant de SQLAlchemy afin d'être testable
sans base de données.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0.00")

# Comptes de dotations aux amortissements (hors provisions).
# 6191/2/3 = amortissements d’exploitation ; 6391 = primes de remboursement.
# Les dotations exceptionnelles / exercices antérieurs ne sont pas présumées
# fiscalement déductibles automatiquement : elles restent à qualifier.
AMORTISSEMENT_PREFIXES = ("6191", "6192", "6193", "6391")


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _get(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def montant_amortissements_comptabilises(charges_par_compte: dict[str, Decimal]) -> Decimal:
    """Retourne les dotations aux amortissements nettes comptabilisées.

    Les mouvements transmis sont déjà nets des contre-écritures. Les provisions
    (6194+ etc.) sont volontairement exclues.
    """
    total = ZERO
    for compte, montant in (charges_par_compte or {}).items():
        if any(str(compte).startswith(prefixe) for prefixe in AMORTISSEMENT_PREFIXES):
            total += money(montant)
    return money(max(ZERO, total))


def ventiler_deficit_genere(deficit_fiscal, amortissements_deductibles) -> dict:
    """Ventile un déficit entre fraction ordinaire et fraction amortissements."""
    deficit = money(max(ZERO, money(deficit_fiscal)))
    amort = money(max(ZERO, money(amortissements_deductibles)))
    part_amort = money(min(deficit, amort))
    return {
        "montant_total": deficit,
        "part_ordinaire": money(deficit - part_amort),
        "part_amortissements": part_amort,
    }


def _somme_imputations(imputations, deficit_id, *, avant_exercice=None, exercice_exact=None, champ="montant_ordinaire"):
    total = ZERO
    for imp in imputations or []:
        if _get(imp, "deficit_id") != deficit_id:
            continue
        cible = int(_get(imp, "exercice_cible"))
        if avant_exercice is not None and cible >= avant_exercice:
            continue
        if exercice_exact is not None and cible != exercice_exact:
            continue
        total += money(_get(imp, champ, ZERO))
    return money(total)


def construire_situation_deficits(*, deficits, imputations, exercice_cible: int, base_avant_deficit) -> dict:
    """Calcule soldes, expiration et proposition d'imputation d'un exercice.

    La proposition HisabPro utilise d'abord les fractions ordinaires les plus
    proches de leur expiration, puis les fractions d'amortissements, qui ne sont
    pas limitées dans le temps. Cela évite de perdre inutilement un déficit
    ordinaire ; la proposition reste explicitement identifiable dans l'UI.
    """
    cible = int(exercice_cible)
    base = money(max(ZERO, money(base_avant_deficit)))
    lots = []

    for d in deficits or []:
        did = int(_get(d, "id"))
        origine = int(_get(d, "exercice_origine"))
        ord_initial = money(_get(d, "montant_ordinaire", ZERO))
        amort_initial = money(_get(d, "montant_amortissements", ZERO))

        ord_consomme_avant = _somme_imputations(imputations, did, avant_exercice=cible, champ="montant_ordinaire")
        amort_consomme_avant = _somme_imputations(imputations, did, avant_exercice=cible, champ="montant_amortissements")
        ord_restant = money(max(ZERO, ord_initial - ord_consomme_avant))
        amort_restant = money(max(ZERO, amort_initial - amort_consomme_avant))

        # Déficit de N : utilisable à partir de N+1. Fraction ordinaire jusqu'à N+4 inclus.
        ord_eligible = money(ord_restant if (cible > origine and cible <= origine + 4) else ZERO)
        ord_expire = money(ord_restant if cible > origine + 4 else ZERO)
        amort_eligible = money(amort_restant if cible > origine else ZERO)

        ord_confirme = _somme_imputations(imputations, did, exercice_exact=cible, champ="montant_ordinaire")
        amort_confirme = _somme_imputations(imputations, did, exercice_exact=cible, champ="montant_amortissements")

        lots.append({
            "id": did,
            "exercice_origine": origine,
            "montant_ordinaire_initial": ord_initial,
            "montant_amortissements_initial": amort_initial,
            "ordinaire_restant_avant_exercice": ord_restant,
            "amortissements_restants_avant_exercice": amort_restant,
            "ordinaire_eligible": ord_eligible,
            "amortissements_eligibles": amort_eligible,
            "ordinaire_expire": ord_expire,
            "exercice_expiration_ordinaire": origine + 4,
            "montant_confirme_exercice": money(ord_confirme + amort_confirme),
            "ordinaire_confirme_exercice": ord_confirme,
            "amortissements_confirmes_exercice": amort_confirme,
            "source": _get(d, "source", "manuel"),
            "commentaire": _get(d, "commentaire"),
        })

    disponible_ordinaire = money(sum((l["ordinaire_eligible"] for l in lots), ZERO))
    disponible_amort = money(sum((l["amortissements_eligibles"] for l in lots), ZERO))
    expire_ordinaire = money(sum((l["ordinaire_expire"] for l in lots), ZERO))

    restant_a_imputer = base
    proposition = []

    # 1) Déficits ordinaires : plus proche expiration en premier.
    for lot in sorted(lots, key=lambda l: (l["exercice_expiration_ordinaire"], l["exercice_origine"], l["id"])):
        if restant_a_imputer <= 0:
            break
        montant = money(min(restant_a_imputer, lot["ordinaire_eligible"]))
        if montant > 0:
            proposition.append({
                "deficit_id": lot["id"],
                "exercice_origine": lot["exercice_origine"],
                "nature": "ordinaire",
                "montant": montant,
                "expiration": lot["exercice_expiration_ordinaire"],
            })
            restant_a_imputer = money(restant_a_imputer - montant)

    # 2) Fraction amortissements : pas de délai de quatre exercices.
    for lot in sorted(lots, key=lambda l: (l["exercice_origine"], l["id"])):
        if restant_a_imputer <= 0:
            break
        montant = money(min(restant_a_imputer, lot["amortissements_eligibles"]))
        if montant > 0:
            proposition.append({
                "deficit_id": lot["id"],
                "exercice_origine": lot["exercice_origine"],
                "nature": "amortissements",
                "montant": montant,
                "expiration": None,
            })
            restant_a_imputer = money(restant_a_imputer - montant)

    total_propose = money(sum((p["montant"] for p in proposition), ZERO))
    total_confirme = money(sum((l["montant_confirme_exercice"] for l in lots), ZERO))

    confirme_par_cle = {}
    for l in lots:
        if l["ordinaire_confirme_exercice"] > 0:
            confirme_par_cle[(l["id"], "ordinaire")] = l["ordinaire_confirme_exercice"]
        if l["amortissements_confirmes_exercice"] > 0:
            confirme_par_cle[(l["id"], "amortissements")] = l["amortissements_confirmes_exercice"]
    propose_par_cle = {(p["deficit_id"], p["nature"]): p["montant"] for p in proposition}
    confirmation_a_jour = bool(confirme_par_cle) and confirme_par_cle == propose_par_cle

    return {
        "lots": lots,
        "disponible_ordinaire": disponible_ordinaire,
        "disponible_amortissements": disponible_amort,
        "disponible_total": money(disponible_ordinaire + disponible_amort),
        "ordinaire_expire": expire_ordinaire,
        "base_avant_deficit": base,
        "proposition": proposition,
        "total_propose": total_propose,
        "total_confirme": total_confirme,
        "confirmation_a_jour": confirmation_a_jour,
    }
