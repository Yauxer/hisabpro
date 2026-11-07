# -*- coding: utf-8 -*-
"""Acomptes provisionnels et liquidation IS — Patch 08.5.

Référentiel principal : CGI 2026, article 170, et article 247-XXXVII-B pour
la transition 2023-2026.

Le service reste pur (pas d'accès DB) : le routeur lui fournit la liquidation
confirmée N-1, les paiements enregistrés et les paramètres fiscaux de N.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

try:
    from services.fiscalite_is_service import determiner_taux_is
except ModuleNotFoundError:  # exécution directe des tests depuis le dossier services
    from fiscalite_is_service import determiner_taux_is

ZERO = Decimal("0.00")
QUART = Decimal("0.25")


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _add_months(d: date, months: int) -> date:
    idx = (d.month - 1) + months
    year = d.year + idx // 12
    month = idx % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def echeances_acomptes(date_debut: date) -> list[date]:
    """Echéances des 3e, 6e, 9e et 12e mois suivant l'ouverture.

    Pour un exercice ouvert le 01/01, cela donne 31/03, 30/06, 30/09, 31/12.
    """
    return [_add_months(date_debut, n) - timedelta(days=1) for n in (3, 6, 9, 12)]


def determiner_reference_acomptes(
    *,
    exercice: int,
    liquidation_precedente: dict | None,
    categorie_is: str,
    maintien_taux_35_transition: bool = False,
    taux_force=None,
    reference_forcee=None,
    exercice_reference_existe: bool = True,
) -> dict:
    """Détermine l'impôt annuel servant de base aux quatre acomptes.

    - Référence manuelle justifiée : elle prime, utile lors d'une reprise de dossier.
    - 2023-2026 : bénéfice fiscal N-1 × taux IS applicable à N (règle transitoire).
    - Après 2026 : impôt dû confirmé au titre de N-1 (règle générale de l'art. 170).
    """
    if reference_forcee is not None:
        forcee = money(reference_forcee)
        if forcee < ZERO:
            raise ValueError("L'impôt de référence forcé ne peut pas être négatif.")
        return {
            "disponible": True,
            "non_applicable": False,
            "montant_annuel": forcee,
            "source": "manuel",
            "libelle_source": "Référence annuelle saisie manuellement et justifiée",
            "exercice_reference": exercice - 1,
            "benefice_reference": None,
            "taux_reference": None,
            "provisoire": exercice > 2026,
        }

    if not liquidation_precedente:
        if not exercice_reference_existe:
            return {
                "disponible": False,
                "non_applicable": True,
                "montant_annuel": ZERO,
                "source": "premier_exercice",
                "libelle_source": "Premier exercice — aucun exercice de référence antérieur",
                "exercice_reference": exercice - 1,
                "benefice_reference": None,
                "taux_reference": None,
                "provisoire": False,
            }
        return {
            "disponible": False,
            "non_applicable": False,
            "montant_annuel": ZERO,
            "source": "indisponible",
            "libelle_source": f"Liquidation fiscale {exercice - 1} non confirmée",
            "exercice_reference": exercice - 1,
            "benefice_reference": None,
            "taux_reference": None,
            "provisoire": exercice > 2026,
        }

    benefice_ref = money(liquidation_precedente.get("benefice_fiscal_imposable"))
    impot_ref = money(liquidation_precedente.get("impot_du"))

    if 2023 <= exercice <= 2026:
        taux = determiner_taux_is(
            exercice,
            benefice_ref,
            categorie_is=categorie_is,
            maintien_taux_35_transition=maintien_taux_35_transition,
            taux_force=taux_force,
        )
        annuel = money(benefice_ref * taux.taux / Decimal("100"))
        return {
            "disponible": True,
            "non_applicable": False,
            "montant_annuel": annuel,
            "source": "transition_2023_2026",
            "libelle_source": f"Bénéfice fiscal {exercice - 1} × taux IS applicable à {exercice}",
            "exercice_reference": exercice - 1,
            "benefice_reference": benefice_ref,
            "taux_reference": taux.taux,
            "provisoire": bool(taux.provisoire),
        }

    return {
        "disponible": True,
        "non_applicable": False,
        "montant_annuel": impot_ref,
        "source": "liquidation_n_1",
        "libelle_source": f"Impôt dû confirmé au titre de {exercice - 1}",
        "exercice_reference": exercice - 1,
        "benefice_reference": benefice_ref,
        "taux_reference": None,
        "provisoire": exercice > 2026,
    }


def construire_acomptes(
    *,
    date_debut: date,
    reference: dict,
    paiements: list[dict] | None = None,
    excedent_precedent=0,
    credits_ras_deja_imputes=0,
    date_reference: date | None = None,
) -> dict:
    paiements = paiements or []
    par_numero = {int(p.get("numero")): p for p in paiements}
    aujourd_hui = date_reference or date.today()
    annuel = money(reference.get("montant_annuel")) if reference.get("disponible") else ZERO
    du_unitaire = money(annuel * QUART)
    credit_restant = money(max(ZERO, money(excedent_precedent)))
    credit_initial = credit_restant
    credit_ras_restant = money(max(ZERO, money(credits_ras_deja_imputes)))
    credit_ras_initial = credit_ras_restant
    lignes = []
    total_verse = ZERO
    total_credit = ZERO
    total_credit_ras = ZERO
    total_du = ZERO

    for numero, echeance in enumerate(echeances_acomptes(date_debut), start=1):
        p = par_numero.get(numero, {})
        du = du_unitaire
        credit = money(min(credit_restant, du))
        credit_restant = money(credit_restant - credit)
        reste_apres_n1 = money(max(ZERO, du - credit))
        credit_ras = money(min(credit_ras_restant, reste_apres_n1))
        credit_ras_restant = money(credit_ras_restant - credit_ras)
        net_a_verser = money(max(ZERO, du - credit - credit_ras))
        verse = money(p.get("montant_verse"))
        dispense = bool(p.get("dispense", False))
        couverture = money(credit + credit_ras + verse)

        if dispense:
            statut = "dispense"
        elif du == ZERO and reference.get("non_applicable"):
            statut = "non_applicable"
        elif du == ZERO and not reference.get("disponible"):
            statut = "reference_manquante"
        elif couverture >= du and du > ZERO:
            statut = "solde"
        elif aujourd_hui > echeance:
            statut = "partiel_en_retard" if couverture > ZERO else "en_retard"
        else:
            statut = "a_venir" if couverture == ZERO else "partiel"

        lignes.append({
            "numero": numero,
            "date_echeance": echeance,
            "montant_du": du,
            "credit_n_1_impute": credit,
            "credit_ras_impute": credit_ras,
            "montant_net_a_verser": net_a_verser,
            "montant_verse": verse,
            "date_versement": p.get("date_versement"),
            "reference_paiement": p.get("reference_paiement"),
            "dispense": dispense,
            "reference_dispense": p.get("reference_dispense"),
            "commentaire": p.get("commentaire"),
            "statut": statut,
            "reste_a_couvrir": money(max(ZERO, du - couverture)),
        })
        total_du += du
        total_verse += verse
        total_credit += credit
        total_credit_ras += credit_ras

    return {
        "reference": reference,
        "acomptes": lignes,
        "total_du": money(total_du),
        "total_verse": money(total_verse),
        "credit_n_1_initial": credit_initial,
        "credit_n_1_impute": money(total_credit),
        "credit_n_1_restant_apres_acomptes": credit_restant,
        "credit_ras_initial": credit_ras_initial,
        "credit_ras_impute": money(total_credit_ras),
        "credit_ras_restant_apres_acomptes": credit_ras_restant,
        "total_imputable": money(total_verse + total_credit + total_credit_ras),
    }


def calculer_liquidation(*, impot_du_avant_acomptes, situation_acomptes: dict, credits_is: dict | None = None) -> dict:
    """Liquidation annuelle en respectant l'ordre d'imputation documenté.

    Les retenues PPRF puis celles sur rémunérations à des tiers sont imputées
    avant les acomptes. Les crédits déjà utilisés sur des acomptes sont exclus
    du solde disponible pour éviter toute double imputation.
    """
    impot = money(impot_du_avant_acomptes)
    verse = money(situation_acomptes.get("total_verse"))
    credit_n_1 = money(situation_acomptes.get("credit_n_1_impute"))
    credit_ras_acomptes = money(situation_acomptes.get("credit_ras_impute"))
    acomptes_disponibles = money(verse + credit_n_1 + credit_ras_acomptes)

    credits_is = credits_is or {}
    par_type = credits_is.get("par_type") or {}
    disponibles = {
        "pprf": money(par_type.get("pprf")),
        "retenue_tiers": money(par_type.get("retenue_tiers")),
        "autre": money(par_type.get("autre")),
    }

    restant = impot
    credits_appliques = {}
    credits_excedentaires = {}
    for typ in ("pprf", "retenue_tiers", "autre"):
        disponible = disponibles[typ]
        applique = money(min(restant, disponible))
        restant = money(restant - applique)
        credits_appliques[typ] = applique
        credits_excedentaires[typ] = money(disponible - applique)

    acomptes_appliques = money(min(restant, acomptes_disponibles))
    restant = money(restant - acomptes_appliques)
    excedent_acomptes = money(acomptes_disponibles - acomptes_appliques)
    credits_disponibles = money(sum(disponibles.values(), ZERO))
    credits_appliques_total = money(sum(credits_appliques.values(), ZERO))
    excedent_credits = money(sum(credits_excedentaires.values(), ZERO))
    excedent_total = money(excedent_credits + excedent_acomptes)

    return {
        "impot_du_avant_acomptes": impot,
        "credits_is_disponibles_liquidation": credits_disponibles,
        "credits_is_appliques": credits_appliques_total,
        "credits_is_appliques_detail": credits_appliques,
        "excedent_credits_is": excedent_credits,
        "acomptes_verses": verse,
        "credit_n_1_impute_sur_acomptes": credit_n_1,
        "credits_ras_deja_imputes_sur_acomptes": credit_ras_acomptes,
        "acomptes_et_credit_imputables": acomptes_disponibles,
        "acomptes_appliques_liquidation": acomptes_appliques,
        "solde_a_payer": restant,
        "excedent_acomptes": excedent_acomptes,
        "excedent_total": excedent_total,
        "nature_solde": "a_payer" if restant > ZERO else ("excedent" if excedent_total > ZERO else "solde"),
    }


def _snapshot_json(value):
    """Convertit récursivement les valeurs fiscales en JSON stable et exact."""
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _snapshot_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_snapshot_json(v) for v in value]
    return value


def construire_snapshot_liquidation(situation: dict) -> dict:
    """Construit le détail immuable à conserver avec la liquidation confirmée."""
    acomptes = situation.get("acomptes") or {}
    credits = situation.get("credits_is") or {}
    liquidation = situation.get("liquidation") or {}
    calcul = situation.get("calcul") or {}
    parametres = situation.get("parametres") or {}
    detail = {
        "version": 1,
        "exercice": situation.get("exercice"),
        "calcul": {
            "benefice_fiscal_imposable": calcul.get("benefice_fiscal_imposable"),
            "is_theorique": liquidation.get("is_theorique"),
            "cm_exigible": liquidation.get("cm_exigible"),
            "impot_du_avant_acomptes": liquidation.get("impot_du_avant_acomptes"),
            "nature_impot_du": liquidation.get("nature_impot_du"),
        },
        "parametres_fiscaux": {
            "categorie_is": parametres.get("categorie_is"),
            "taux_is_force": parametres.get("taux_is_force"),
            "acomptes_reference_forcee": parametres.get("acomptes_reference_forcee"),
            "acomptes_justification_reference_forcee": parametres.get("acomptes_justification_reference_forcee"),
        },
        "reference_acomptes": acomptes.get("reference"),
        "acomptes": list(acomptes.get("acomptes") or []),
        "totaux_acomptes": {
            "total_du": acomptes.get("total_du"),
            "total_verse": acomptes.get("total_verse"),
            "credit_n_1_initial": acomptes.get("credit_n_1_initial"),
            "credit_n_1_impute": acomptes.get("credit_n_1_impute"),
            "credit_ras_initial": acomptes.get("credit_ras_initial"),
            "credit_ras_impute": acomptes.get("credit_ras_impute"),
            "total_imputable": acomptes.get("total_imputable"),
        },
        "credits_is": {
            "lignes": list(credits.get("lignes") or []),
            "par_type": credits.get("par_type") or {},
            "total_montant": credits.get("total_montant"),
            "total_deja_impute_acomptes": credits.get("total_deja_impute_acomptes"),
            "total_disponible_liquidation": credits.get("total_disponible_liquidation"),
        },
        "liquidation": {
            "impot_du_avant_acomptes": liquidation.get("impot_du_avant_acomptes"),
            "credits_is_disponibles_liquidation": liquidation.get("credits_is_disponibles_liquidation"),
            "credits_is_appliques": liquidation.get("credits_is_appliques"),
            "credits_is_appliques_detail": liquidation.get("credits_is_appliques_detail") or {},
            "acomptes_verses": liquidation.get("acomptes_verses"),
            "credit_n_1_impute_sur_acomptes": liquidation.get("credit_n_1_impute_sur_acomptes"),
            "credits_ras_deja_imputes_sur_acomptes": liquidation.get("credits_ras_deja_imputes_sur_acomptes"),
            "acomptes_et_credit_imputables": liquidation.get("acomptes_et_credit_imputables"),
            "solde_a_payer": liquidation.get("solde_a_payer"),
            "excedent_acomptes": liquidation.get("excedent_acomptes"),
            "excedent_credits_is": liquidation.get("excedent_credits_is"),
            "excedent_total": liquidation.get("excedent_total"),
            "nature_solde": liquidation.get("nature_solde"),
        },
    }
    return _snapshot_json(detail)
