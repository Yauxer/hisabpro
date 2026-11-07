# -*- coding: utf-8 -*-
"""Contrôles et sérialisation FEC selon l'annexe 3 de l'Avis n°24 du CNC.

Ce module ne dépend pas de FastAPI afin que les règles de contrôle puissent être
unit-testées indépendamment de la couche HTTP.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re

from services.plan_comptable import libelle_compte


ENTETES_FEC_AVIS24 = [
    "Code_Journal",
    "Libelle_Journal",
    "Num_Ecriture",
    "Date_Ecriture",
    "Num_Compte",
    "Libelle_Compte",
    "Num_Compte_Aux",
    "Libelle_Compte_Aux",
    "Ref_Piece",
    "Date_Piece",
    "Libelle_Ecriture",
    "Montant_Debit",
    "Montant_Credit",
    "Lettrage_Ecriture",
    "Date_Lettrage",
    "Date_Validation",
    "Montant_Devise",
    "Id_devise",
]

JOURNAUX_LIB = {
    "AC": "Journal des achats",
    "VT": "Journal des ventes",
    "BQ": "Journal de banque",
    "CA": "Journal de caisse",
    "OD": "Opérations diverses",
    "AN": "À nouveaux",
    "EN": "Journal des encours",
    "AE": "Effets à encaisser",
    "AV": "Journal des avoirs",
    "AM": "Journal des amortissements",
    "TV": "Journal de TVA",
    "PR": "Journal des provisions",
    "SA": "Journal des salaires",
    # Réservé au futur journal de clôture 07C.3.
    "CL": "Journal de clôture",
}


def journal_code(value) -> str:
    return str(getattr(value, "value", value) or "").strip()


def nettoyer(value) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def fmt_date(value) -> str:
    """Représentation texte compacte d'une date dans le fichier FEC.

    L'Avis 24 prescrit le type Date mais ne fixe pas, dans son annexe 3, un
    séparateur textuel. HisabPro conserve le format AAAAMMJJ déjà utilisé par
    les exports comptables afin d'éviter toute ambiguïté jour/mois.
    """
    if not value:
        return ""
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    raw = str(value).strip()
    return raw.replace("-", "")[:8]


def money(value) -> Decimal:
    try:
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")


def fmt_montant(value) -> str:
    return f"{money(value):.2f}".replace(".", ",")


def numero_sequence(numero: str, journal: str, exercice: int) -> int | None:
    m = re.fullmatch(rf"{re.escape(journal)}-{int(exercice)}-(\d+)", nettoyer(numero))
    return int(m.group(1)) if m else None


def auxiliaire_fec(ligne):
    """Résout l'auxiliaire FEC sans réécrire une ligne définitive.

    Priorité : snapshot natif de la ligne, puis dernier complément append-only
    complet. Les historiques antérieurs au patch COMPTA-AUX peuvent ainsi être
    documentés sans désactiver l'immutabilité des écritures validées.
    """
    tiers_id = getattr(ligne, "tiers_id", None)
    nature = nettoyer(getattr(ligne, "nature_auxiliaire", None))
    num_aux = nettoyer(getattr(ligne, "compte_auxiliaire_snapshot", None))
    lib_aux = nettoyer(getattr(ligne, "libelle_auxiliaire_snapshot", None))
    if tiers_id and num_aux and lib_aux:
        return tiers_id, nature, num_aux, lib_aux

    complements = list(getattr(ligne, "auxiliaire_complements", None) or [])
    complets = [
        c for c in complements
        if getattr(c, "tiers_id", None)
        and nettoyer(getattr(c, "compte_auxiliaire_snapshot", None))
        and nettoyer(getattr(c, "libelle_auxiliaire_snapshot", None))
    ]
    if complets:
        c = complets[-1]
        return (
            getattr(c, "tiers_id", None),
            nettoyer(getattr(c, "nature_auxiliaire", None)),
            nettoyer(getattr(c, "compte_auxiliaire_snapshot", None)),
            nettoyer(getattr(c, "libelle_auxiliaire_snapshot", None)),
        )
    return tiers_id, nature, num_aux, lib_aux


def piece_fec(ecriture):
    """Résout la référence/date documentaire sans réécrire l'écriture.

    Ordre de priorité COMPTA.4 :
    1. dernier complément marqué prioritaire ;
    2. référence portée par l'écriture à sa création ;
    3. dernier complément documentaire (ex. fichier joint) ;
    4. pour la date uniquement, date comptable en dernier recours (§2.3.e).
    """
    justificatifs = list(getattr(ecriture, "justificatifs", None) or [])
    prioritaires = [j for j in justificatifs if bool(getattr(j, "prioritaire", False))
                    and nettoyer(getattr(j, "reference", None))]
    if prioritaires:
        j = prioritaires[-1]
        return nettoyer(j.reference), getattr(j, "date_piece", None) or getattr(ecriture, "date_piece", None) or getattr(ecriture, "date", None)

    ref_origine = nettoyer(getattr(ecriture, "reference", None))
    if ref_origine:
        return ref_origine, getattr(ecriture, "date_piece", None) or getattr(ecriture, "date", None)

    autres = [j for j in justificatifs if nettoyer(getattr(j, "reference", None))]
    if autres:
        j = autres[-1]
        return nettoyer(j.reference), getattr(j, "date_piece", None) or getattr(ecriture, "date_piece", None) or getattr(ecriture, "date", None)

    return "", getattr(ecriture, "date_piece", None) or getattr(ecriture, "date", None)


def _anomalie(code, message, *, ecriture_id=None, journal=None, numero=None, details=None):
    item = {"code": code, "message": message}
    if ecriture_id is not None:
        item["ecriture_id"] = ecriture_id
    if journal:
        item["journal"] = journal
    if numero:
        item["numero_ecriture"] = numero
    if details is not None:
        item["details"] = details
    return item


def controler_fec(ecritures, exercice: int, exercice_obj=None, cloture=None, db=None, societe_id: int | None = None) -> dict:
    """Contrôle les prérequis d'un FEC exploitable selon l'Avis n°24.

    Les anomalies qui rendraient le fichier incomplet, non séquentiel ou non
    équilibré sont bloquantes. Les éléments de qualité qui n'empêchent pas la
    sérialisation sont remontés comme avertissements.
    """
    exercice = int(exercice)
    bloquants = []
    avertissements = []
    valides = [e for e in ecritures if bool(getattr(e, "est_validee", False))]
    brouillons = [e for e in ecritures if not bool(getattr(e, "est_validee", False))]

    if brouillons:
        bloquants.append(_anomalie(
            "ECRITURES_BROUILLON",
            f"{len(brouillons)} écriture(s) de l'exercice sont encore en brouillon. "
            "Le FEC doit représenter l'ensemble des écritures comptables définitives de l'exercice.",
            details={"ids": [getattr(e, "id", None) for e in brouillons[:50]]},
        ))

    if not valides:
        bloquants.append(_anomalie(
            "AUCUNE_ECRITURE_VALIDEE",
            "Aucune écriture validée n'est disponible pour cet exercice.",
        ))

    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    total_lignes = 0
    par_journal = defaultdict(lambda: {"ecritures": [], "debit": Decimal("0.00"), "credit": Decimal("0.00")})
    numeros_vus = set()
    # Avis n°24 § comptabilités auxiliaires : les totaux des comptes individuels
    # clients/fournisseurs doivent recouper les mouvements des comptes collectifs.
    # Le contrôle est rendu explicite même si, avec l'auxiliaire natif du patch 053,
    # les deux sources proviennent désormais de la même ligne comptable.
    collectifs_aux = defaultdict(lambda: {"debit": Decimal("0.00"), "credit": Decimal("0.00")})
    individuels_aux = defaultdict(lambda: {"debit": Decimal("0.00"), "credit": Decimal("0.00")})

    date_debut = getattr(exercice_obj, "date_debut", None)
    date_fin = getattr(exercice_obj, "date_fin", None)

    for ec in valides:
        eid = getattr(ec, "id", None)
        journal = journal_code(getattr(ec, "journal", None))
        numero = nettoyer(getattr(ec, "numero_ecriture", None))
        date_ec = getattr(ec, "date", None)
        ref_piece, date_piece = piece_fec(ec)
        source = nettoyer(getattr(ec, "source", None)).lower()
        date_validation = getattr(ec, "date_validation", None)
        lignes = list(getattr(ec, "lignes", None) or [])

        # HisabPro réserve le journal CL aux clôtures depuis le patch 07C.3.
        # Cette règle interne reste bloquante pour toute NOUVELLE écriture
        # ordinaire placée dans CL. En revanche, une clôture historique créée
        # avant l'introduction de CL (par ex. en OD) reste sérialisable dans le
        # FEC : on la signale sans réécrire l'écriture définitive.
        if journal == "CL" and source != "cloture":
            bloquants.append(_anomalie(
                "JOURNAL_CLOTURE_USAGE_INTERDIT",
                "Le journal CL est réservé exclusivement aux écritures de clôture générées par HisabPro.",
                ecriture_id=eid, journal=journal, numero=numero,
            ))
        if source == "cloture" and ref_piece.startswith("CLOTURE-") and journal != "CL":
            avertissements.append(_anomalie(
                "ECRITURE_CLOTURE_HISTORIQUE_HORS_CL",
                f"Clôture historique {ref_piece} conservée dans {journal or 'un journal vide'} ; "
                "les nouvelles clôtures HisabPro utilisent le journal CL.",
                ecriture_id=eid, journal=journal, numero=numero,
            ))

        if not numero:
            bloquants.append(_anomalie(
                "NUMERO_MANQUANT", "Écriture validée sans Num_Ecriture.",
                ecriture_id=eid, journal=journal,
            ))
            seq = None
        else:
            if numero in numeros_vus:
                bloquants.append(_anomalie(
                    "NUMERO_DOUBLON", f"Numéro d'écriture dupliqué : {numero}.",
                    ecriture_id=eid, journal=journal, numero=numero,
                ))
            numeros_vus.add(numero)
            seq = numero_sequence(numero, journal, exercice)
            if seq is None:
                bloquants.append(_anomalie(
                    "NUMERO_PERIMETRE_INVALIDE",
                    f"Le numéro {numero} ne correspond pas au journal {journal} et à l'exercice {exercice}.",
                    ecriture_id=eid, journal=journal, numero=numero,
                ))

        if int(getattr(ec, "exercice", exercice)) != exercice:
            bloquants.append(_anomalie(
                "EXERCICE_INCOHERENT", "L'écriture ne porte pas l'exercice demandé.",
                ecriture_id=eid, journal=journal, numero=numero,
            ))

        if ((date_debut and date_ec and date_ec < date_debut)
                or (date_fin and date_ec and date_ec > date_fin)):
            bloquants.append(_anomalie(
                "DATE_HORS_EXERCICE",
                f"Date comptable {date_ec} hors des bornes de l'exercice.",
                ecriture_id=eid, journal=journal, numero=numero,
            ))

        if not ref_piece:
            bloquants.append(_anomalie(
                "REFERENCE_PIECE_MANQUANTE",
                "Référence de pièce justificative manquante. Ajoutez-la depuis le Journal ; la validation de l'écriture reste inchangée.",
                ecriture_id=eid, journal=journal, numero=numero,
            ))

        if not date_piece:
            bloquants.append(_anomalie(
                "DATE_PIECE_MANQUANTE",
                "Date de pièce justificative (ou date de saisie) manquante.",
                ecriture_id=eid, journal=journal, numero=numero,
            ))

        if not date_validation:
            bloquants.append(_anomalie(
                "DATE_VALIDATION_MANQUANTE",
                "Écriture validée sans date de validation définitive.",
                ecriture_id=eid, journal=journal, numero=numero,
            ))

        if not lignes:
            bloquants.append(_anomalie(
                "ECRITURE_SANS_LIGNE", "Écriture comptable sans ligne.",
                ecriture_id=eid, journal=journal, numero=numero,
            ))
            continue

        debit_ec = Decimal("0.00")
        credit_ec = Decimal("0.00")
        for ligne in lignes:
            compte = nettoyer(getattr(ligne, "compte", None))
            debit = money(getattr(ligne, "debit", 0))
            credit = money(getattr(ligne, "credit", 0))
            total_lignes += 1
            debit_ec += debit
            credit_ec += credit

            if len(compte) < 3 or not compte[:3].isdigit():
                bloquants.append(_anomalie(
                    "COMPTE_INVALIDE",
                    f"Compte '{compte}' invalide : les trois premiers caractères doivent être numériques.",
                    ecriture_id=eid, journal=journal, numero=numero,
                ))
            if debit < 0 or credit < 0 or (debit > 0 and credit > 0) or (debit == 0 and credit == 0):
                bloquants.append(_anomalie(
                    "MONTANT_LIGNE_INVALIDE",
                    f"Ligne du compte {compte} avec débit/crédit invalide.",
                    ecriture_id=eid, journal=journal, numero=numero,
                ))

            # Avis n°24 / COMPTA-AUX : sur les comptes collectifs clients et
            # fournisseurs, l'identité auxiliaire doit être une donnée native
            # figée à la validation, jamais reconstruite depuis un libellé libre.
            if compte.startswith(("3421", "4411")):
                racine_aux = "3421" if compte.startswith("3421") else "4411"
                tiers_id, _nature_aux, num_aux, lib_aux = auxiliaire_fec(ligne)
                collectifs_aux[racine_aux]["debit"] += debit
                collectifs_aux[racine_aux]["credit"] += credit
                if not (tiers_id and num_aux and lib_aux):
                    bloquants.append(_anomalie(
                        "AUXILIAIRE_MANQUANT",
                        f"Compte collectif {compte} sans compte auxiliaire client/fournisseur explicite.",
                        ecriture_id=eid, journal=journal, numero=numero,
                        details={"compte": compte, "ligne_ecriture_id": getattr(ligne, "id", None)},
                    ))
                else:
                    individuels_aux[racine_aux]["debit"] += debit
                    individuels_aux[racine_aux]["credit"] += credit
            if not libelle_compte(compte, db=db, societe_id=societe_id):
                avertissements.append(_anomalie(
                    "COMPTE_HORS_NOMENCLATURE_EMBARQUEE",
                    f"Compte {compte} absent de la nomenclature embarquée ; le libellé de ligne sera utilisé dans le FEC.",
                    ecriture_id=eid, journal=journal, numero=numero,
                ))

        if debit_ec != credit_ec:
            bloquants.append(_anomalie(
                "ECRITURE_DESEQUILIBREE",
                f"Écriture déséquilibrée : débit {debit_ec:.2f} / crédit {credit_ec:.2f}.",
                ecriture_id=eid, journal=journal, numero=numero,
            ))

        total_debit += debit_ec
        total_credit += credit_ec
        par_journal[journal]["debit"] += debit_ec
        par_journal[journal]["credit"] += credit_ec
        par_journal[journal]["ecritures"].append({
            "id": eid,
            "numero": numero,
            "sequence": seq,
            "date": date_ec,
            "created_at": getattr(ec, "created_at", None),
        })

    # Avis 24 : séquence chronologique, croissante et sans rupture au sein d'un journal.
    for journal, info in sorted(par_journal.items()):
        entries = [x for x in info["ecritures"] if x["sequence"] is not None]
        seqs = sorted(x["sequence"] for x in entries)
        if seqs:
            attendu = list(range(1, max(seqs) + 1))
            if seqs != attendu:
                manquants = sorted(set(attendu) - set(seqs))
                bloquants.append(_anomalie(
                    "SEQUENCE_AVEC_TROUS",
                    f"Journal {journal} : séquence non continue ; numéro(s) manquant(s) {manquants[:20]}.",
                    journal=journal,
                    details={"manquants": manquants[:200], "max_sequence": max(seqs)},
                ))

            # Le numéro est attribué à la validation (018) : en suivant la séquence,
            # la date comptable ne doit jamais reculer. Un même jour peut être validé
            # dans un autre ordre que celui de création des brouillons (963).
            dates_par_numero = [x["date"] or date.min for x in sorted(entries, key=lambda x: x["sequence"])]
            if any(apres < avant for avant, apres in zip(dates_par_numero, dates_par_numero[1:])):
                bloquants.append(_anomalie(
                    "SEQUENCE_NON_CHRONOLOGIQUE",
                    f"Journal {journal} : la numérotation n'est pas croissante selon la date comptable.",
                    journal=journal,
                ))

        if info["debit"] != info["credit"]:
            bloquants.append(_anomalie(
                "JOURNAL_DESEQUILIBRE",
                f"Journal {journal} déséquilibré : débit {info['debit']:.2f} / crédit {info['credit']:.2f}.",
                journal=journal,
            ))

    for racine_aux in ("3421", "4411"):
        coll = collectifs_aux[racine_aux]
        indiv = individuels_aux[racine_aux]
        if coll["debit"] != indiv["debit"] or coll["credit"] != indiv["credit"]:
            bloquants.append(_anomalie(
                "AUXILIAIRES_COLLECTIF_DESEQUILIBRES",
                f"Compte collectif {racine_aux} : les mouvements auxiliaires ne recoupent pas le compte collectif.",
                details={
                    "collectif_debit": float(coll["debit"]),
                    "collectif_credit": float(coll["credit"]),
                    "auxiliaires_debit": float(indiv["debit"]),
                    "auxiliaires_credit": float(indiv["credit"]),
                },
            ))

    if total_debit != total_credit:
        bloquants.append(_anomalie(
            "BALANCE_GLOBALE_DESEQUILIBREE",
            f"Exercice déséquilibré : débit {total_debit:.2f} / crédit {total_credit:.2f}.",
        ))

    if exercice_obj is not None and getattr(exercice_obj, "statut", None) != "cloture":
        avertissements.append(_anomalie(
            "EXERCICE_NON_CLOTURE",
            "L'exercice n'est pas clôturé : l'export est un état courant et non l'archive définitive de clôture.",
        ))

    return {
        "exercice": exercice,
        "conforme_export": len(bloquants) == 0,
        "nb_ecritures": len(ecritures),
        "nb_ecritures_validees": len(valides),
        "nb_ecritures_brouillon": len(brouillons),
        "nb_lignes": total_lignes,
        "total_debit": float(total_debit),
        "total_credit": float(total_credit),
        "equilibre": total_debit == total_credit,
        "ecart": float(total_debit - total_credit),
        "nb_bloquants": len(bloquants),
        "nb_avertissements": len(avertissements),
        "bloquants": bloquants,
        "avertissements": avertissements,
        "controle_auxiliaires": {
            racine: {
                "collectif_debit": float(collectifs_aux[racine]["debit"]),
                "collectif_credit": float(collectifs_aux[racine]["credit"]),
                "auxiliaires_debit": float(individuels_aux[racine]["debit"]),
                "auxiliaires_credit": float(individuels_aux[racine]["credit"]),
                "conforme": (collectifs_aux[racine]["debit"] == individuels_aux[racine]["debit"]
                              and collectifs_aux[racine]["credit"] == individuels_aux[racine]["credit"]),
            } for racine in ("3421", "4411")
        },
        "exercice_cloture": bool(cloture) or (getattr(exercice_obj, "statut", None) == "cloture"),
    }


def lignes_fec(ecritures, exercice: int, cloture=None, db=None, societe_id: int | None = None):
    """Transforme des écritures validées en lignes 18 colonnes Avis 24."""
    date_cloture = getattr(cloture, "date_cloture", None) if cloture else None

    for ec in sorted(
        (e for e in ecritures if bool(getattr(e, "est_validee", False))),
        key=lambda e: (getattr(e, "date", date.min), getattr(e, "id", 0)),
    ):
        journal = journal_code(getattr(ec, "journal", None))
        numero = nettoyer(getattr(ec, "numero_ecriture", None))
        date_ec = getattr(ec, "date", None)
        ref_piece, date_piece = piece_fec(ec)
        # Date_Validation est celle de l'écriture définitive. La date de clôture
        # n'est qu'un fallback pour les historiques anciens dépourvus de métadonnée ;
        # elle ne doit jamais écraser une date de validation réellement connue.
        validation = getattr(ec, "date_validation", None) or date_cloture
        libelle_ec = nettoyer(getattr(ec, "libelle", None))

        # Un JOIN ou une restauration peut changer l'ordre physique de lecture.
        # Trier une copie conserve la collection ORM et les écritures définitives.
        for ligne in sorted(getattr(ec, "lignes", None) or [],
                            key=lambda ligne: getattr(ligne, "id", None) or 0):
            compte = nettoyer(getattr(ligne, "compte", None))
            compte_lib = libelle_compte(compte, db=db, societe_id=societe_id) or nettoyer(getattr(ligne, "libelle", None)) or libelle_ec
            yield [
                journal,
                JOURNAUX_LIB.get(journal, journal),
                numero,
                fmt_date(date_ec),
                compte,
                nettoyer(compte_lib),
                auxiliaire_fec(ligne)[2],
                auxiliaire_fec(ligne)[3],
                ref_piece,
                fmt_date(date_piece),
                libelle_ec,
                fmt_montant(getattr(ligne, "debit", 0)),
                fmt_montant(getattr(ligne, "credit", 0)),
                nettoyer(getattr(ligne, "code_lettrage", None)),
                fmt_date(getattr(ligne, "date_lettrage", None)),
                fmt_date(validation),
                "",  # Montant_Devise : non utilisé actuellement
                "",  # Id_devise
            ]
