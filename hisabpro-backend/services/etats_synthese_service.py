# -*- coding: utf-8 -*-
"""Source comptable des états de synthèse CGNC.

Patch 09.1
-----------
Les états de synthèse ne doivent jamais dépendre de la pagination de l'écran
Journal ni inclure des brouillons. Ce service agrège donc directement dans
PostgreSQL toutes les lignes des écritures VALIDÉES d'un exercice.

Les écritures techniques de détermination du résultat (journal CL, ainsi que
les anciennes références CLOTURE-N produites avant l'introduction du journal
CL) sont exclues de la source de consultation. Cela permet de conserver le CPC
et l'ESG historiques après clôture : l'écriture de clôture solde les classes
6/7 uniquement pour la mécanique comptable, elle ne doit pas effacer la lecture
économique de l'exercice.

Les à-nouveaux (AN) restent inclus : ils constituent le bilan d'ouverture de
l'exercice suivant.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models

MONEY = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)


def _est_cloture_technique():
    """Condition SQL identifiant les écritures de soldage des classes 6/7.

    - depuis 07C.3 : journal CL ;
    - historique : référence CLOTURE-YYYY, parfois encore au journal OD.
    """
    return or_(
        models.Ecriture.journal == models.JournalEnum.CL,
        func.coalesce(models.Ecriture.reference, "").like("CLOTURE-%"),
    )



def _flux_financement_depuis_lignes(rows):
    """Ventile les flux réels selon le tableau de financement CGNC.

    Patch 052 : la restitution ne se contente plus d'agrégats génériques. Les
    familles correspondent aux rubriques du modèle normal (cessions par nature,
    acquisitions par nature, créances immobilisées, non-valeurs, capitaux et
    dettes de financement). Les reclassements internes sont neutralisés par
    agrégation au niveau de chaque écriture.
    """
    par_ecriture = {}
    for row in rows:
        eid = getattr(row, "ecriture_id", None)
        compte = str(getattr(row, "compte", "") or "")
        debit = _money(getattr(row, "debit", 0))
        credit = _money(getattr(row, "credit", 0))
        x = par_ecriture.setdefault(eid, {
            "non_valeurs": Decimal("0.00"),
            "incorporelles": Decimal("0.00"),
            "corporelles": Decimal("0.00"),
            "creances_immobilisees": Decimal("0.00"),
            "titres_immobilises": Decimal("0.00"),
            "capitaux_core": Decimal("0.00"),
            "capitaux_11": Decimal("0.00"),
            "subventions_investissement": Decimal("0.00"),
            "dettes_financement": Decimal("0.00"),
            "dividendes_mis_en_paiement": Decimal("0.00"),
            "cession_incorporelle": Decimal("0.00"),
            "cession_corporelle": Decimal("0.00"),
            "cession_financiere": Decimal("0.00"),
            "cession_non_ventilee": Decimal("0.00"),
        })
        mouvement = debit - credit
        if compte.startswith("21"):
            x["non_valeurs"] += mouvement
        elif compte.startswith("22"):
            x["incorporelles"] += mouvement
        elif compte.startswith("23"):
            x["corporelles"] += mouvement
        elif compte.startswith("24"):
            x["creances_immobilisees"] += mouvement
        elif compte.startswith("25"):
            x["titres_immobilises"] += mouvement

        if compte.startswith(("111", "112", "113")):
            x["capitaux_core"] += credit - debit
        if compte.startswith("11"):
            x["capitaux_11"] += credit - debit
        if compte.startswith("131"):
            x["subventions_investissement"] += credit - debit
        if compte.startswith("14"):
            x["dettes_financement"] += credit - debit
        if compte.startswith("4465"):
            x["dividendes_mis_en_paiement"] += credit - debit

        if compte.startswith("7512"):
            x["cession_incorporelle"] += credit - debit
        elif compte.startswith("7513"):
            x["cession_corporelle"] += credit - debit
        elif compte.startswith("7514"):
            x["cession_financiere"] += credit - debit
        elif compte.startswith("7518") or compte == "7510":
            # 7518 ne permet pas de connaître la nature de l'immobilisation
            # cédée. On conserve le flux mais on le signale comme non ventilé.
            x["cession_non_ventilee"] += credit - debit

    total = {
        "emplois_non_valeurs": Decimal("0.00"),
        "acquisitions_immobilisations_incorporelles": Decimal("0.00"),
        "acquisitions_immobilisations_corporelles": Decimal("0.00"),
        "acquisitions_immobilisations_financieres": Decimal("0.00"),
        "augmentations_creances_immobilisees": Decimal("0.00"),
        "cessions_immobilisations_incorporelles": Decimal("0.00"),
        "cessions_immobilisations_corporelles": Decimal("0.00"),
        "cessions_immobilisations_financieres": Decimal("0.00"),
        "cessions_immobilisations_non_ventilees": Decimal("0.00"),
        "recuperations_creances_immobilisees": Decimal("0.00"),
        "augmentations_capitaux_propres": Decimal("0.00"),
        "reductions_capitaux_propres": Decimal("0.00"),
        "subventions_investissement_recues": Decimal("0.00"),
        "augmentations_dettes_financement": Decimal("0.00"),
        "remboursements_dettes_financement": Decimal("0.00"),
        "distributions_benefices": Decimal("0.00"),
    }
    for x in par_ecriture.values():
        total["emplois_non_valeurs"] += max(x["non_valeurs"], Decimal("0.00"))
        total["acquisitions_immobilisations_incorporelles"] += max(x["incorporelles"], Decimal("0.00"))
        total["acquisitions_immobilisations_corporelles"] += max(x["corporelles"], Decimal("0.00"))
        total["acquisitions_immobilisations_financieres"] += max(x["titres_immobilises"], Decimal("0.00"))
        total["augmentations_creances_immobilisees"] += max(x["creances_immobilisees"], Decimal("0.00"))
        total["recuperations_creances_immobilisees"] += max(-x["creances_immobilisees"], Decimal("0.00"))
        total["cessions_immobilisations_incorporelles"] += max(x["cession_incorporelle"], Decimal("0.00"))
        total["cessions_immobilisations_corporelles"] += max(x["cession_corporelle"], Decimal("0.00"))
        total["cessions_immobilisations_financieres"] += max(x["cession_financiere"], Decimal("0.00"))
        total["cessions_immobilisations_non_ventilees"] += max(x["cession_non_ventilee"], Decimal("0.00"))

        core = x["capitaux_core"]
        total_11 = x["capitaux_11"]
        if core > 0 and total_11 > 0:
            total["augmentations_capitaux_propres"] += min(core, total_11)
        elif core < 0 and total_11 < 0:
            total["reductions_capitaux_propres"] += min(-core, -total_11)

        total["subventions_investissement_recues"] += max(x["subventions_investissement"], Decimal("0.00"))
        total["augmentations_dettes_financement"] += max(x["dettes_financement"], Decimal("0.00"))
        total["remboursements_dettes_financement"] += max(-x["dettes_financement"], Decimal("0.00"))
        total["distributions_benefices"] += max(x["dividendes_mis_en_paiement"], Decimal("0.00"))

    # Clés agrégées conservées pour compatibilité API avec les versions 051.
    total["acquisitions_immobilisations"] = (
        total["acquisitions_immobilisations_incorporelles"]
        + total["acquisitions_immobilisations_corporelles"]
        + total["acquisitions_immobilisations_financieres"]
        + total["augmentations_creances_immobilisees"]
    )
    total["cessions_immobilisations"] = (
        total["cessions_immobilisations_incorporelles"]
        + total["cessions_immobilisations_corporelles"]
        + total["cessions_immobilisations_financieres"]
        + total["cessions_immobilisations_non_ventilees"]
    )
    return {k: float(_money(v)) for k, v in total.items()}


def source_etats_synthese(db: Session, societe_id: int, exercice: int) -> Dict[str, Any]:
    """Retourne les soldes débit/crédit complets et les contrôles de source.

    La structure retournée est volontairement stable et simple afin d'être
    consommée par le moteur CGNC frontend actuel, puis par l'ETIC (Patch 09.2).
    """
    cloture_technique = _est_cloture_technique()

    # Agrégation SQL : aucune limite/pagination, uniquement écritures validées,
    # et aucune écriture de clôture technique.
    rows = (
        db.query(
            models.LigneEcriture.compte.label("compte"),
            func.coalesce(func.sum(models.LigneEcriture.debit), 0).label("debit"),
            func.coalesce(func.sum(models.LigneEcriture.credit), 0).label("credit"),
        )
        .join(models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id)
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
            ~cloture_technique,
        )
        .group_by(models.LigneEcriture.compte)
        .order_by(models.LigneEcriture.compte)
        .all()
    )

    soldes = {
        str(r.compte): {
            "debit": float(_money(r.debit)),
            "credit": float(_money(r.credit)),
        }
        for r in rows
    }

    # Statistiques de traçabilité / contrôles.
    inclus = (
        db.query(models.Ecriture.id)
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
            ~cloture_technique,
        )
        .count()
    )
    brouillons = (
        db.query(models.Ecriture.id)
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(False),
        )
        .count()
    )
    clotures_exclues = (
        db.query(models.Ecriture.id)
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
            cloture_technique,
        )
        .count()
    )

    bornes = (
        db.query(func.min(models.Ecriture.date), func.max(models.Ecriture.date))
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
            ~cloture_technique,
        )
        .first()
    )

    total_debit = sum((_money(v["debit"]) for v in soldes.values()), Decimal("0.00"))
    total_credit = sum((_money(v["credit"]) for v in soldes.values()), Decimal("0.00"))
    ecart = _money(total_debit - total_credit)

    cloture_obj = db.query(models.ClotureExercice).filter_by(
        societe_id=societe_id, exercice=exercice
    ).first()

    avertissements = []
    if brouillons:
        avertissements.append(
            f"{brouillons} écriture(s) brouillon sont exclues des états de synthèse."
        )
    if ecart != Decimal("0.00"):
        avertissements.append(
            f"Balance générale déséquilibrée de {ecart:+.2f} MAD : états à contrôler avant arrêté."
        )

    # CA indicatif pour signaler l'éligibilité au modèle simplifié (art. 21
    # loi 9-88 modifiée par 44-03). L'utilisateur peut néanmoins conserver le
    # modèle normal : le seuil donne une faculté, pas une obligation.
    ca = Decimal("0.00")
    for compte, valeurs in soldes.items():
        if compte.startswith(("711", "712")):
            ca += _money(valeurs["credit"]) - _money(valeurs["debit"])
    ca = _money(ca)

    # Tableau de financement : les emplois/ressources sont des FLUX de la
    # période, pas de simples écarts de soldes. On extrait donc les mouvements
    # réels hors AN et hors clôture technique, puis on les agrège par écriture.
    flux_rows = (
        db.query(
            models.Ecriture.id.label("ecriture_id"),
            models.LigneEcriture.compte.label("compte"),
            models.LigneEcriture.debit.label("debit"),
            models.LigneEcriture.credit.label("credit"),
        )
        .join(models.LigneEcriture, models.LigneEcriture.ecriture_id == models.Ecriture.id)
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
            models.Ecriture.journal != models.JournalEnum.AN,
            models.Ecriture.journal != models.JournalEnum.CL,
            ~func.coalesce(models.Ecriture.reference, "").like("CLOTURE-%"),
        )
        .all()
    )
    flux_financement = _flux_financement_depuis_lignes(flux_rows)

    return {
        "exercice": int(exercice),
        "soldes": soldes,
        "disponible": inclus > 0,
        "source": {
            "ecritures_validees_incluses": inclus,
            "brouillons_exclus": brouillons,
            "clotures_techniques_exclues": clotures_exclues,
            "comptes_mouvementes": len(soldes),
            "date_min": bornes[0].isoformat() if bornes and bornes[0] else None,
            "date_max": bornes[1].isoformat() if bornes and bornes[1] else None,
            "exercice_clos": bool(cloture_obj),
        },
        "controle": {
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "ecart_balance": float(ecart),
            "balance_equilibree": ecart == Decimal("0.00"),
            "avertissements": avertissements,
        },
        "flux_financement": flux_financement,
        "modele": {
            "chiffre_affaires_indicatif": float(ca),
            "eligible_modele_simplifie": abs(ca) <= Decimal("10000000.00"),
            "modele_utilise": "normal",
        },
    }
