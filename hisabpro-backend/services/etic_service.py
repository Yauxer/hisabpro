# -*- coding: utf-8 -*-
"""Moteur ETIC — Patch 09.2.

L'ETIC (modèle normal CGNC) comporte A1-A3, B1-B14 et C1-C5.
HisabPro sépare les informations :
- calculables depuis la comptabilité / les modules (automatiques) ;
- calculables mais nécessitant un complément extra-comptable (assistées) ;
- impossibles à déduire de la comptabilité seule (manuelles).

Aucune information extra-comptable n'est inventée : les ventilations d'échéance,
sûretés, engagements hors bilan, actionnariat, crédit-bail et événements postérieurs
restent explicitement à compléter lorsqu'HisabPro ne dispose pas de la donnée.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

import models
from services.plan_comptable import libelle_compte
from services.etats_synthese_service import source_etats_synthese
from services.tva_service import ventilation_facture, ventilation_avoir, total_ventilation
from services.echeancier_service import repartition_fifo
from services.fec_source_recovery_service import choisir_facture_source, choisir_candidat_facture_exact, tiers_collectif_compatible_facture
from services.fec_service import nettoyer, piece_fec, auxiliaire_fec

MONEY = Decimal("0.01")
ZERO = Decimal("0.00")


def money(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)


def _num(v):
    return float(money(v))


def _montant_collectif_etic(ecriture, type_facture: str) -> Decimal:
    """Montant porté au compte collectif 3421/4411 par une écriture historique."""
    prefixe = "3421" if type_facture == "vente" else "4411"
    total = ZERO
    for ligne in getattr(ecriture, "lignes", None) or []:
        compte = str(getattr(ligne, "compte", "") or "").strip()
        if not compte.startswith(prefixe):
            continue
        debit = money(getattr(ligne, "debit", 0))
        credit = money(getattr(ligne, "credit", 0))
        total += (debit - credit) if type_facture == "vente" else (credit - debit)
    return money(total)


def _ttc_facture_etic(facture) -> Decimal:
    try:
        return money(total_ventilation(ventilation_facture(facture, appliquer_escompte=True))["ttc"])
    except Exception:
        return ZERO


def _choisir_facture_historique_etic(ecriture, factures: list, type_facture: str):
    """Rapprochement historique ETIC sans exiger ``tiers_id``.

    Certaines factures antérieures à FACT.1 ont une écriture comptable définitive
    mais aucun ``tiers_id`` technique. Pour B6/B7, le tiers n'est pas nécessaire :
    seules la facture et son échéance sont utilisées. On accepte donc uniquement
    une correspondance non ambiguë sur date + montant TTC, puis le sélecteur
    documentaire partagé avec le FEC. Une référence explicite doit correspondre
    exactement au numéro interne ou à la référence fournisseur/client. Sans
    référence, un candidat unique ou un identifiant entier dans le libellé
    peuvent établir la correspondance.
    """
    montant = _montant_collectif_etic(ecriture, type_facture)
    if montant <= ZERO:
        return None

    candidats = [
        f for f in factures
        if getattr(f, "date", None) == getattr(ecriture, "date", None)
        and _ttc_facture_etic(f) == montant
    ]
    facture = choisir_candidat_facture_exact(ecriture, candidats)
    return facture if facture is not None and tiers_collectif_compatible_facture(ecriture, facture, type_facture) else None


CATALOGUE_ETIC = [
    # A — principes et méthodes
    {"code": "A1", "groupe": "A", "titre": "Principales méthodes d'évaluation spécifiques à l'entreprise", "mode": "manuel", "type_saisie": "texte"},
    {"code": "A2", "groupe": "A", "titre": "État des dérogations", "mode": "manuel", "type_saisie": "table",
     "colonnes_saisie": [
         {"cle": "indication", "label": "Indication / dérogation", "type": "text"},
         {"cle": "justification", "label": "Justification", "type": "text"},
         {"cle": "influence", "label": "Influence sur patrimoine / résultat", "type": "text"},
     ]},
    {"code": "A3", "groupe": "A", "titre": "État des changements de méthodes", "mode": "manuel", "type_saisie": "table",
     "colonnes_saisie": [
         {"cle": "nature", "label": "Nature du changement", "type": "text"},
         {"cle": "justification", "label": "Justification", "type": "text"},
         {"cle": "influence", "label": "Influence chiffrée / qualitative", "type": "text"},
     ]},
    # B — compléments Bilan/CPC
    {"code": "B1", "groupe": "B", "titre": "Détail des non-valeurs", "mode": "auto", "type_saisie": "notes"},
    {"code": "B2", "groupe": "B", "titre": "Tableau des immobilisations", "mode": "assiste", "type_saisie": "notes"},
    {"code": "B2bis", "groupe": "B", "titre": "Tableau des amortissements", "mode": "auto", "type_saisie": "notes"},
    {"code": "B3", "groupe": "B", "titre": "Plus ou moins-values sur cessions ou retraits d'immobilisations", "mode": "assiste", "type_saisie": "notes"},
    {"code": "B4", "groupe": "B", "titre": "Tableau des titres de participation", "mode": "assiste", "type_saisie": "notes"},
    {"code": "B5", "groupe": "B", "titre": "Tableau des provisions", "mode": "auto", "type_saisie": "notes"},
    {"code": "B6", "groupe": "B", "titre": "Tableau des créances", "mode": "assiste", "type_saisie": "ventilation"},
    {"code": "B7", "groupe": "B", "titre": "Tableau des dettes", "mode": "assiste", "type_saisie": "ventilation"},
    {"code": "B8", "groupe": "B", "titre": "Sûretés réelles données ou reçues", "mode": "manuel", "type_saisie": "table",
     "colonnes_saisie": [
         {"cle": "nature", "label": "Nature", "type": "text"}, {"cle": "objet", "label": "Objet", "type": "text"},
         {"cle": "tiers", "label": "Tiers", "type": "text"}, {"cle": "montant_couvert", "label": "Montant couvert", "type": "number"},
         {"cle": "valeur_nette", "label": "Valeur nette comptable", "type": "number"}, {"cle": "inscription", "label": "Date / lieu d'inscription", "type": "text"},
     ]},
    {"code": "B9", "groupe": "B", "titre": "Engagements financiers reçus ou donnés hors crédit-bail", "mode": "manuel", "type_saisie": "table",
     "colonnes_saisie": [
         {"cle": "sens", "label": "Reçu / donné", "type": "text"}, {"cle": "nature", "label": "Nature", "type": "text"},
         {"cle": "montant", "label": "Montant exercice", "type": "number"}, {"cle": "montant_n1", "label": "Montant N-1", "type": "number"},
         {"cle": "observation", "label": "Observation", "type": "text"},
     ]},
    {"code": "B10", "groupe": "B", "titre": "Tableau des biens en crédit-bail", "mode": "manuel", "type_saisie": "table",
     "colonnes_saisie": [
         {"cle": "bien", "label": "Bien", "type": "text"}, {"cle": "date_contrat", "label": "Date contrat", "type": "date"},
         {"cle": "duree", "label": "Durée", "type": "text"}, {"cle": "valeur_estimee", "label": "Valeur estimée", "type": "number"},
         {"cle": "redevances_exercice", "label": "Redevances exercice", "type": "number"}, {"cle": "redevances_restantes", "label": "Redevances restantes", "type": "number"},
     ]},
    {"code": "B11", "groupe": "B", "titre": "Détail des postes du CPC", "mode": "auto", "type_saisie": "notes"},
    {"code": "B12", "groupe": "B", "titre": "Passage du résultat net comptable au résultat net fiscal", "mode": "auto", "type_saisie": "notes"},
    {"code": "B13", "groupe": "B", "titre": "Détermination du résultat courant après impôts", "mode": "assiste", "type_saisie": "notes"},
    {"code": "B14", "groupe": "B", "titre": "Détail de la taxe sur la valeur ajoutée", "mode": "assiste", "type_saisie": "notes"},
    # C — autres informations
    {"code": "C1", "groupe": "C", "titre": "État de répartition du capital social", "mode": "manuel", "type_saisie": "table",
     "colonnes_saisie": [
         {"cle": "associe", "label": "Actionnaire / associé", "type": "text"}, {"cle": "identifiant", "label": "Identifiant / adresse", "type": "text"},
         {"cle": "titres", "label": "Nombre de titres / parts", "type": "number"}, {"cle": "nominal", "label": "Valeur nominale", "type": "number"},
         {"cle": "capital", "label": "Montant du capital détenu", "type": "number"}, {"cle": "pourcentage", "label": "% capital", "type": "number"},
     ]},
    {"code": "C2", "groupe": "C", "titre": "Affectation des résultats intervenue au cours de l'exercice", "mode": "manuel", "type_saisie": "table",
     "colonnes_saisie": [
         {"cle": "sens", "label": "Origine / affectation", "type": "text"}, {"cle": "nature", "label": "Nature", "type": "text"},
         {"cle": "montant", "label": "Montant", "type": "number"}, {"cle": "observation", "label": "Observation", "type": "text"},
     ]},
    {"code": "C3", "groupe": "C", "titre": "Résultats et autres éléments caractéristiques des trois derniers exercices", "mode": "auto", "type_saisie": "notes"},
    {"code": "C4", "groupe": "C", "titre": "Opérations en devises comptabilisées pendant l'exercice", "mode": "manuel", "type_saisie": "table",
     "colonnes_saisie": [
         {"cle": "devise", "label": "Devise", "type": "text"}, {"cle": "achats", "label": "Achats", "type": "number"},
         {"cle": "ventes", "label": "Ventes", "type": "number"}, {"cle": "creances", "label": "Créances", "type": "number"},
         {"cle": "dettes", "label": "Dettes", "type": "number"}, {"cle": "observation", "label": "Observation", "type": "text"},
     ]},
    {"code": "C5", "groupe": "C", "titre": "Datation et événements postérieurs", "mode": "manuel", "type_saisie": "texte"},
]

CODES_ETIC = {x["code"] for x in CATALOGUE_ETIC}

VENTILATION_ETIC_CODES = {"B6", "B7"}
VENTILATION_ECHEANCE_KEYS = ("plus_un_an", "moins_un_an", "echues")
VENTILATION_ANALYSE_KEYS = ("devises", "etat_organismes_publics", "entreprises_liees", "effets")


def _date_plus_un_an(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        # 29 février -> 28 février l'année suivante.
        return d.replace(year=d.year + 1, day=28)


def _classer_echeances_ouvertes(echeances: list[dict], date_cloture: date) -> dict[str, Decimal]:
    """Classe les soldes d'échéances selon la grille officielle B6/B7."""
    limite_un_an = _date_plus_un_an(date_cloture)
    result = {"plus_un_an": ZERO, "moins_un_an": ZERO, "echues": ZERO}
    for row in echeances or []:
        reste = money(row.get("reste_du"))
        if reste <= ZERO:
            continue
        d = row.get("date_echeance")
        if not d:
            continue
        if d <= date_cloture:
            result["echues"] += reste
        elif d <= limite_un_an:
            result["moins_un_an"] += reste
        else:
            result["plus_un_an"] += reste
    return {k: money(v) for k, v in result.items()}


def _echeances_documentees_etic(facture, total_ttc: Decimal) -> list[dict]:
    """Utilise seulement les dates enregistrées, sans délai supposé.

    Un échéancier incomplet ou dont le total diverge du TTC ne permet pas de
    qualifier le solde. La date simple n'est utilisée qu'en l'absence de tranches.
    """
    persisted = list(getattr(facture, "echeances", None) or [])
    if persisted:
        rows = [
            {"ordre": e.ordre, "date_echeance": e.date_echeance, "montant": money(e.montant)}
            for e in persisted
        ]
        if (any(not r["date_echeance"] or r["montant"] <= ZERO for r in rows)
                or money(sum((r["montant"] for r in rows), ZERO)) != total_ttc):
            return []
        return rows
    d = getattr(facture, "date_echeance", None)
    return [{"ordre": 1, "date_echeance": d, "montant": total_ttc}] if d else []


def _diagnostic_mouvements_compte(db: Session, societe_id: int, exercice: int, compte: str, sens: str) -> dict:
    """Explique le solde comptable d'un compte B6/B7 sans inventer d'échéance.

    Le diagnostic reprend exactement le périmètre des états de synthèse : écritures
    validées de l'exercice et hors clôture technique. Il sert uniquement à identifier
    la provenance d'un reliquat qui n'est pas couvert par les factures/échéanciers.
    """
    if not hasattr(db, "query"):
        # Facilite les tests unitaires de la logique de préremplissage ; en
        # production ``db`` est toujours une Session SQLAlchemy.
        return {"total": None, "sources": [], "mouvements": []}

    rows = (
        db.query(
            models.Ecriture.id,
            models.Ecriture.numero_ecriture,
            models.Ecriture.date,
            models.Ecriture.journal,
            models.Ecriture.libelle,
            models.Ecriture.reference,
            models.Ecriture.source,
            models.LigneEcriture.debit,
            models.LigneEcriture.credit,
        )
        .join(models.LigneEcriture, models.LigneEcriture.ecriture_id == models.Ecriture.id)
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
            models.LigneEcriture.compte == str(compte),
            ~_condition_cloture_technique(),
        )
        .order_by(models.Ecriture.date, models.Ecriture.id, models.LigneEcriture.id)
        .all()
    )

    par_source = defaultdict(lambda: {"montant": ZERO, "nb_lignes": 0})
    mouvements = []
    total = ZERO
    for row in rows:
        debit = money(row.debit)
        credit = money(row.credit)
        net = money(debit - credit if sens == "debit" else credit - debit)
        if net == ZERO:
            continue
        source = (row.source or "sans_source").strip() or "sans_source"
        par_source[source]["montant"] += net
        par_source[source]["nb_lignes"] += 1
        total += net
        journal = row.journal.value if hasattr(row.journal, "value") else str(row.journal or "")
        mouvements.append({
            "numero": row.numero_ecriture,
            "date": row.date.isoformat() if row.date else None,
            "journal": journal,
            "libelle": row.libelle,
            "reference": row.reference,
            "source": source,
            "debit": _num(debit),
            "credit": _num(credit),
            "impact_solde": _num(net),
        })

    sources = [
        {"source": source, "montant": _num(vals["montant"]), "nb_lignes": int(vals["nb_lignes"])}
        for source, vals in sorted(par_source.items(), key=lambda item: item[0])
    ]
    return {"total": _num(total), "sources": sources, "mouvements": mouvements}


def _factures_eligibles_etic(db: Session, societe_id: int, exercice: int, type_facture: str, fin: date, *, avec_preuves=False):
    """Retourne les factures réellement rattachables à la comptabilité B6/B7.

    Les factures marquées comptabilisées restent la source normale. Pour les
    anciennes données où ce drapeau n'était pas encore fiable, une facture est
    récupérée uniquement si une écriture VT/AC validée correspond *exactement*
    sur journal + date + montant TTC via le même moteur déterministe que le FEC.
    Aucun rapprochement flou n'est accepté.
    """
    enum_type = models.TypeFactureEnum.vente if type_facture == "vente" else models.TypeFactureEnum.achat
    candidates = (
        db.query(models.Facture)
        .options(joinedload(models.Facture.lignes), joinedload(models.Facture.echeances))
        .filter(
            models.Facture.societe_id == societe_id,
            models.Facture.type == enum_type,
            models.Facture.est_proforma.is_(False),
            models.Facture.statut != models.StatutFactureEnum.annulee,
            models.Facture.date <= fin,
        )
        .all()
    )
    if not candidates:
        return ([], set(), {"principales": {}, "ecritures": {}}) if avec_preuves else ([], set())

    # Les factures modernes restent prises directement seulement si elles sont
    # réellement validées + comptabilisées. Les lignes historiques, y compris
    # celles dépourvues de tiers_id technique, ne sont récupérées qu'après
    # rapprochement exact avec une écriture VT/AC validée.
    directes = {
        f.id: f for f in candidates
        if bool(getattr(f, "est_validee", False))
        and bool(getattr(f, "est_comptabilisee", False))
    }
    historiques = [f for f in candidates if f.id not in directes]
    if not historiques and not avec_preuves:
        return list(directes.values()), set()

    journal_attendu = models.JournalEnum.VT if type_facture == "vente" else models.JournalEnum.AC
    ecritures = (
        db.query(models.Ecriture)
        .options(joinedload(models.Ecriture.lignes).joinedload(models.LigneEcriture.auxiliaire_complements),
                 joinedload(models.Ecriture.justificatifs))
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.est_validee.is_(True),
            models.Ecriture.date <= fin,
            ~_condition_cloture_technique(),
        )
        .order_by(models.Ecriture.date, models.Ecriture.id)
        .all()
    )

    matches = []
    usages = defaultdict(int)
    principales = defaultdict(list)
    for ecriture in ecritures:
        journal = getattr(getattr(ecriture, "journal", None), "value", getattr(ecriture, "journal", None))
        if journal != journal_attendu.value:
            continue
        # Moteur FEC en premier pour les factures modernes ; fallback ETIC plus
        # permissif sur la présence de tiers_id, mais toujours exact/non ambigu.
        # Les factures déjà comptabilisées restent des candidats concurrents :
        # les retirer peut transformer un rapprochement ambigu en faux positif.
        facture = choisir_facture_source(ecriture, candidates)
        if facture is None:
            facture = _choisir_facture_historique_etic(ecriture, candidates, type_facture)
        if facture is None:
            continue
        matches.append(facture)
        usages[facture.id] += 1
        principales[facture.id].append(ecriture)

    recuperees = {}
    for facture in matches:
        # Une même facture correspondant à plusieurs écritures reste ambiguë :
        # on ne l'utilise pas pour une ventilation réglementaire.
        if facture.id not in directes and usages.get(facture.id) == 1:
            recuperees[facture.id] = facture

    toutes = dict(directes)
    toutes.update(recuperees)
    result = (list(toutes.values()), set(recuperees))
    if avec_preuves:
        return (*result, {"principales": principales,
                          "ecritures": {e.id: e for e in ecritures}})
    return result


def _montant_compte_source_etic(ecriture, compte: str, type_facture: str) -> Decimal:
    """Compare le compte exact, sans déplacer 4411 vers une subdivision."""
    total = ZERO
    for ligne in getattr(ecriture, "lignes", None) or []:
        if str(getattr(ligne, "compte", "") or "").strip() == compte:
            net = money(getattr(ligne, "debit", 0)) - money(getattr(ligne, "credit", 0))
            total += net if type_facture == "vente" else -net
    return money(total)


def _reduction_source_prouvee_etic(ecriture, montant, compte: str, type_facture: str) -> bool:
    return ecriture is not None and _montant_compte_source_etic(ecriture, compte, type_facture) == -money(montant)


def _reglement_historique_exact_etic(row, facture, ecritures, compte, type_facture):
    """Retrouve REG-<id> sans écrire de lien et sans rapprochement approximatif."""
    if getattr(row, "ecriture_id", None) is not None or getattr(row, "id", None) is None:
        return None
    tiers = getattr(row, "tiers_id", None) or getattr(facture, "tiers_id", None)
    if tiers is None or (getattr(row, "tiers_id", None) is not None
                         and getattr(facture, "tiers_id", None) not in (None, tiers)):
        return None
    ref = f"REG-{row.id}".casefold()
    candidats = [e for e in ecritures.values() if piece_fec(e)[0].casefold() == ref]
    # Une seconde écriture avec cette référence reste une ambiguïté, même si
    # son montant ou sa date est différent : ne pas sélectionner arbitrairement.
    if len(candidats) != 1:
        return None
    e = candidats[0]
    lignes = getattr(e, "lignes", None) or []
    tiers_lignes = [auxiliaire_fec(l)[0] for l in lignes
                    if str(getattr(l, "compte", "") or "").strip() == compte]
    journal = getattr(getattr(e, "journal", None), "value", getattr(e, "journal", None))
    if (getattr(e, "date", None) != row.date or journal not in {"BQ", "CA", "AE"}
            or not tiers_lignes or any(t != tiers for t in tiers_lignes)
            or not _reduction_source_prouvee_etic(e, row.montant, compte, type_facture)
            or sum((money(getattr(l, "debit", 0)) - money(getattr(l, "credit", 0))
                    for l in lignes), ZERO) != ZERO):
        return None
    return e


def _avoir_source_prouve_etic(avoir, ecritures: dict, compte: str, type_facture: str, facture_source=None) -> bool:
    montant = money(total_ventilation(ventilation_avoir(avoir, appliquer_escompte=True))["ttc"])
    ref = nettoyer(getattr(avoir, "numero", None)).casefold()
    matches = [
        e for e in ecritures.values()
        if ref and piece_fec(e)[0].casefold() == ref
        and getattr(e, "date", None) == getattr(avoir, "date", None)
        and getattr(getattr(e, "journal", None), "value", getattr(e, "journal", None)) == "AV"
        and _reduction_source_prouvee_etic(e, montant, compte, type_facture)
        and (facture_source is None or tiers_collectif_compatible_facture(e, facture_source, type_facture))
    ]
    return len(matches) == 1


def _annulations_sources_etic(db, societe_id: int, rows: list) -> dict:
    ids = {getattr(row, "ecriture_annulation_id", None) for row in rows} - {None}
    if not ids:
        return {}
    # La date de la contrepassation peut être postérieure à la clôture : elle
    # sert seulement à reconstituer l'état passé, jamais à réduire ce solde.
    return {e.id: e for e in db.query(models.Ecriture).filter(
        models.Ecriture.societe_id == societe_id,
        models.Ecriture.id.in_(ids), models.Ecriture.est_validee.is_(True),
    ).all()}


def _source_active_a_cloture_etic(row, fin: date, annulations: dict) -> tuple[bool, str | None]:
    statut = getattr(getattr(row, "statut", None), "value", getattr(row, "statut", None))
    if statut == "rejete":
        # Les anciens rejets n'ont pas de date/lien technique dédié. Le statut
        # actuel seul ne prouve pas que le rejet avait déjà eu lieu à la clôture.
        return False, "Rejet sans date historique liée : effet sur le solde à la clôture à vérifier."
    if statut not in {"annule", "annulee"}:
        return True, None
    eid = getattr(row, "ecriture_annulation_id", None)
    if eid is not None:
        ecriture = annulations.get(eid)
        if ecriture is None:
            return False, "Annulation sans contrepassation validée retrouvée."
        original_id = getattr(row, "ecriture_id", None)
        if original_id is not None and getattr(ecriture, "contrepassation_de_id", None) != original_id:
            return False, "La contrepassation ne désigne pas l'écriture d'origine de cette source."
        jour = ecriture.date
    else:
        jour = getattr(row, "date_annulation", None)
        if isinstance(jour, datetime):
            jour = jour.date()
    if jour is None:
        return False, "Annulation sans date enregistrée : état à la clôture indéterminable."
    if jour > fin:
        return True, None
    if eid is None and (getattr(row, "est_comptabilisee", False) or getattr(row, "ecriture_id", None)):
        return False, "Annulation d'une source comptabilisée sans contrepassation liée."
    return False, None


def _ventilation_factures_par_compte(db: Session, societe_id: int, exercice: int, type_facture: str) -> dict[str, dict]:
    """Ventile les soldes factures restant dus à la clôture, sans regarder le futur.

    Les règlements, avoirs et imputations postérieurs à la date de clôture sont
    ignorés. La fonction ne sert qu'à préremplir B6/B7 ; si son total ne recoupe
    pas exactement le solde comptable du compte, aucun préremplissage n'est appliqué.
    """
    _debut, fin = _bornes(db, societe_id, exercice)
    factures, ids_historiques, preuves = _factures_eligibles_etic(
        db, societe_id, exercice, type_facture, fin, avec_preuves=True
    )
    if not factures:
        return {}

    ids = [f.id for f in factures]
    regles = defaultdict(Decimal)
    acomptes = defaultdict(Decimal)
    avoirs = defaultdict(Decimal)
    motifs_evenements = defaultdict(list)
    usages_reductions = defaultdict(list)
    factures_par_id = {f.id: f for f in factures}
    compte_defaut = "3421" if type_facture == "vente" else "4411"

    def compte_facture(fid):
        f = factures_par_id[fid]
        return str(getattr(f, "compte_tiers_snapshot", None) or compte_defaut).strip() or compte_defaut

    def verifier_reduction(row, nom):
        e = preuves["ecritures"].get(getattr(row, "ecriture_id", None))
        f = factures_par_id[row.facture_id]
        refs = {nettoyer(getattr(obj, key, None)).casefold()
                for obj in (row, f, getattr(row, "acompte", None))
                for key in ("numero", "reference")} - {""}
        if nom == "Règlement" and getattr(row, "id", None) is not None:
            refs.add(f"REG-{row.id}".casefold())
            if e is None and getattr(row, "ecriture_id", None) is None:
                e = _reglement_historique_exact_etic(
                    row, f, preuves["ecritures"], compte_facture(row.facture_id), type_facture)
        ref_e = piece_fec(e)[0].casefold() if e is not None else ""
        if e is not None:
            usages_reductions[e.id].append(row.facture_id)
        if (not _reduction_source_prouvee_etic(e, row.montant, compte_facture(row.facture_id), type_facture)
                or getattr(e, "date", None) != getattr(row, "date", getattr(row, "date_imputation", None))
                or (e is not None and not tiers_collectif_compatible_facture(e, f, type_facture))
                or (ref_e and ref_e not in refs)):
            motifs_evenements[row.facture_id].append(
                f"{nom} {getattr(row, 'id', '')} : réduction sans écriture validée recoupant le compte exact à la clôture."
            )

    reglements = db.query(models.Reglement).filter(
        models.Reglement.societe_id == societe_id,
        models.Reglement.facture_id.in_(ids),
        models.Reglement.date <= fin,
    ).all()
    annulations = _annulations_sources_etic(db, societe_id, reglements)
    for r in reglements:
        active, motif = _source_active_a_cloture_etic(r, fin, annulations)
        if motif:
            motifs_evenements[r.facture_id].append(f"Règlement {r.id} : {motif}")
        if not active:
            continue
        regles[r.facture_id] += money(r.montant)
        verifier_reduction(r, "Règlement")

    imputations = db.query(models.ImputationAcompte).options(joinedload(models.ImputationAcompte.acompte)).filter(
        models.ImputationAcompte.societe_id == societe_id,
        models.ImputationAcompte.facture_id.in_(ids),
        models.ImputationAcompte.date_imputation <= fin,
    ).all()
    annulations = _annulations_sources_etic(db, societe_id, imputations)
    for a in imputations:
        active, motif = _source_active_a_cloture_etic(a, fin, annulations)
        if motif:
            motifs_evenements[a.facture_id].append(f"Imputation d'acompte {a.id} : {motif}")
        if not active:
            continue
        acomptes[a.facture_id] += money(a.montant)
        verifier_reduction(a, "Imputation d'acompte")

    utilisations = db.query(models.UtilisationAvoir).filter(
        models.UtilisationAvoir.societe_id == societe_id,
        models.UtilisationAvoir.facture_id.in_(ids),
        models.UtilisationAvoir.date_utilisation <= fin,
        models.UtilisationAvoir.type_utilisation == "imputation",
    ).all()
    avoirs_sources = {
        av.id: av for av in db.query(models.Avoir).options(
            joinedload(models.Avoir.lignes), joinedload(models.Avoir.facture)
        ).filter(
            models.Avoir.societe_id == societe_id,
            models.Avoir.id.in_([u.avoir_id for u in utilisations]),
            models.Avoir.date <= fin,
        ).all()
    } if utilisations else {}
    annulations = _annulations_sources_etic(db, societe_id, [*utilisations, *avoirs_sources.values()])
    for u in utilisations:
        active, motif = _source_active_a_cloture_etic(u, fin, annulations)
        if motif:
            motifs_evenements[u.facture_id].append(f"Imputation d'avoir {u.id} : {motif}")
        if not active:
            continue
        avoirs[u.facture_id] += money(u.montant)
        # Cette imputation déplace un crédit entre deux factures et ne génère
        # normalement pas d'écriture. Sa preuve est l'avoir source comptabilisé,
        # sur le même compte et le même tiers, pas un ecriture_id inventé.
        source = avoirs_sources.get(u.avoir_id)
        cible = factures_par_id[u.facture_id]
        origine = getattr(source, "facture", None) if source else None
        meme_tiers = origine is not None and (
            getattr(origine, "tiers_id", None) is not None
            and origine.tiers_id == getattr(cible, "tiers_id", None)
        )
        compte_origine = str(getattr(origine, "compte_tiers_snapshot", None) or compte_defaut).strip()
        source_active, motif_source = _source_active_a_cloture_etic(source, fin, annulations) if source else (False, None)
        if (not source_active or motif_source or not meme_tiers or compte_origine != compte_facture(u.facture_id)
                or not _avoir_source_prouve_etic(source, preuves["ecritures"], compte_origine, type_facture, origine)):
            motifs_evenements[u.facture_id].append(
                f"Imputation d'avoir {u.id} : crédit source non recoupé sur le même tiers et le même compte."
            )

    pieces_avoirs = db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter(
        models.Avoir.societe_id == societe_id,
        models.Avoir.facture_id.in_(ids),
        models.Avoir.date <= fin,
    ).all()
    annulations = _annulations_sources_etic(db, societe_id, pieces_avoirs)
    for av in pieces_avoirs:
        active, motif = _source_active_a_cloture_etic(av, fin, annulations)
        if motif:
            motifs_evenements[av.facture_id].append(f"Avoir {av.numero} : {motif}")
        if not active:
            continue
        avoirs[av.facture_id] += money(total_ventilation(ventilation_avoir(av, appliquer_escompte=True))["ttc"])
        if not _avoir_source_prouve_etic(av, preuves["ecritures"], compte_facture(av.facture_id), type_facture, factures_par_id[av.facture_id]):
            motifs_evenements[av.facture_id].append(
                f"Avoir {getattr(av, 'numero', av.id)} : écriture AV absente, non unique ou non recoupée à la clôture."
            )

    for fids in usages_reductions.values():
        if len(fids) > 1:
            for fid in set(fids):
                motifs_evenements[fid].append("La même écriture de réduction est liée à plusieurs imputations ; rapprochement non unique.")

    buckets: dict[str, dict] = {}
    for f in factures:
        avant = total_ventilation(ventilation_facture(f, appliquer_escompte=False))
        apres = total_ventilation(ventilation_facture(f, appliquer_escompte=True))
        total_ht = money(avant["base"])
        total_ttc = money(apres["ttc"])
        ras = money(total_ht * Decimal(str(getattr(f, "ras_taux", 0) or 0)) / Decimal("100"))
        total_impute = money(regles[f.id] + acomptes[f.id] + avoirs[f.id] + ras)
        repartition = repartition_fifo(
            _echeances_documentees_etic(f, total_ttc),
            float(total_impute),
            fin,
        )
        compte = str(getattr(f, "compte_tiers_snapshot", None) or compte_defaut).strip() or compte_defaut
        principales = preuves["principales"].get(f.id, [])
        motifs = list(motifs_evenements[f.id])
        if len(principales) != 1:
            motifs.append("Écriture principale absente ou non unique sur date, référence et TTC.")
        elif _montant_compte_source_etic(principales[0], compte, type_facture) != total_ttc:
            motifs.append(f"Le compte source {compte} ne recoupe pas le compte exact de l'écriture principale.")
        if ras > ZERO:
            refs = {nettoyer(getattr(f, key, None)).casefold() for key in ("numero", "reference")}
            ras_sources = [
                e for e in preuves["ecritures"].values()
                if piece_fec(e)[0].casefold() in refs - {""}
                and getattr(getattr(e, "journal", None), "value", getattr(e, "journal", None)) == "OD"
                and _reduction_source_prouvee_etic(e, ras, compte, type_facture)
                and _montant_compte_source_etic(e, "3453" if type_facture == "vente" else "4457", type_facture) == ras
                and tiers_collectif_compatible_facture(e, f, type_facture)
            ]
            if len(ras_sources) != 1:
                motifs.append("Retenue à la source sans écriture OD unique recoupée à la clôture.")
        b = buckets.setdefault(
            compte,
            {
                "plus_un_an": ZERO,
                "moins_un_an": ZERO,
                "echues": ZERO,
                "total_source": ZERO,
                "nb_factures": 0,
                "nb_factures_historiques": 0,
                "anomalies_sources": [],
            },
        )
        if motifs:
            b["anomalies_sources"].append({
                "facture_id": f.id, "numero": getattr(f, "numero", None),
                "reste_du": _num(max(money(total_ttc - total_impute), ZERO)),
                "motifs": motifs,
            })
        c = _classer_echeances_ouvertes(
            [] if motifs else repartition.get("echeances") or [], fin
        )
        for key in VENTILATION_ECHEANCE_KEYS:
            b[key] += c[key]
        # Sans date documentée, le reste existe mais n'appartient à aucune
        # tranche d'échéance. Il reste visible dans le rapprochement du solde.
        b["total_source"] += max(money(total_ttc - total_impute), ZERO)
        b["nb_factures"] += 1
        if f.id in ids_historiques:
            b["nb_factures_historiques"] += 1

    result = {}
    for compte, vals in buckets.items():
        result[compte] = {k: money(vals[k]) for k in VENTILATION_ECHEANCE_KEYS}
        result[compte]["total_source"] = money(vals.get("total_source"))
        result[compte]["nb_factures"] = int(vals.get("nb_factures") or 0)
        result[compte]["nb_factures_historiques"] = int(vals.get("nb_factures_historiques") or 0)
        result[compte]["anomalies_sources"] = vals["anomalies_sources"]
    return result


def _ajouter_echeances_auto(db: Session, societe_id: int, exercice: int, lignes: list[dict], type_facture: str) -> list[dict]:
    sources = _ventilation_factures_par_compte(db, societe_id, exercice, type_facture)
    for ligne in lignes:
        compte = str(ligne.get("compte") or "")
        src = sources.get(compte)
        if not src:
            continue
        total = money(ligne.get("montant"))
        total_source = money(src.get("total_source"))
        total_qualifie = money(sum((src[k] for k in VENTILATION_ECHEANCE_KEYS), ZERO))
        ecart = money(total - total_source)
        ligne["echeance_auto_total"] = _num(total_source)
        ligne["echeance_auto_ecart"] = _num(ecart)
        ligne["echeance_auto_non_qualifie"] = _num(max(total_source - total_qualifie, ZERO))
        ligne["echeance_auto_nb_factures"] = int(src.get("nb_factures") or 0)
        ligne["echeance_auto_nb_factures_historiques"] = int(src.get("nb_factures_historiques") or 0)
        ligne["echeance_auto_anomalies_sources"] = src.get("anomalies_sources") or []
        ligne["echeance_auto_diagnostic"] = {
            k: _num(src[k]) for k in VENTILATION_ECHEANCE_KEYS
        }
        if abs(ecart) <= Decimal("0.02") and total_qualifie == total_source:
            ligne["echeance_auto"] = {k: _num(src[k]) for k in VENTILATION_ECHEANCE_KEYS}
            ligne["echeance_auto_source"] = "factures et échéanciers à la date de clôture"
        else:
            # Patch 111 — même lorsqu'une partie seulement du solde est expliquée
            # par des factures/échéanciers fiables, on conserve cette partie comme
            # préremplissage assisté. Le reliquat reste explicitement à ventiler
            # par l'utilisateur : il n'est jamais affecté arbitrairement à une
            # échéance. Si la source dépasse le solde comptable, aucun préremplissage
            # partiel n'est appliqué car la source elle-même doit d'abord être revue.
            if total_qualifie > ZERO and total_source <= total and total_qualifie < total:
                ligne["echeance_auto_partiel"] = {k: _num(src[k]) for k in VENTILATION_ECHEANCE_KEYS}
                ligne["echeance_auto_reliquat"] = _num(total - total_qualifie)
                ligne["echeance_auto_source"] = "partie certaine issue des factures et échéanciers à la date de clôture"
            ligne["echeance_auto_compta_diagnostic"] = _diagnostic_mouvements_compte(
                db, societe_id, exercice, compte, "debit" if type_facture == "vente" else "credit"
            )
    comptes_affiches = {str(ligne.get("compte") or "") for ligne in lignes}
    hors_solde = [
        {"compte": compte, "total_source": _num(src.get("total_source")),
         "anomalies_sources": src.get("anomalies_sources") or []}
        for compte, src in sources.items()
        if compte not in comptes_affiches
        and (money(src.get("total_source")) > ZERO or src.get("anomalies_sources"))
    ]
    if lignes and hors_solde:
        # Diagnostic seulement : aucune source n'est déplacée vers un autre
        # compte pour faire coïncider les totaux comptables.
        lignes[0]["echeance_auto_sources_hors_solde"] = hors_solde
    return lignes


def _echeance_auto_ligne(ligne: dict, key: str):
    # Le préremplissage complet reste prioritaire. A défaut, Patch 111 expose la
    # partie certaine déjà expliquée par les pièces sources ; la validation garde
    # l'obligation que les trois échéances totalisent le solde comptable.
    bloc = ligne.get("echeance_auto") or ligne.get("echeance_auto_partiel") or {}
    val = bloc.get(key)
    return _decimal_ventilation(val)


def _decimal_ventilation(value):
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        n = money(value)
    except Exception:
        return None
    return n if n.is_finite() and n >= ZERO else None


def _etat_public_auto(code: str, compte: str, montant) -> Decimal | None:
    """Préremplit uniquement les comptes dont la nature Etat est certaine.

    Un client/fournisseur ordinaire peut lui-même être un organisme public : on ne
    déduit donc jamais zéro pour les autres comptes.
    """
    c = str(compte or "")
    if code == "B6" and c.startswith("345"):
        return money(montant)
    if code == "B7" and c.startswith("445"):
        return money(montant)
    return None


def _ventilation_publiee(code: str, automatique: dict, contenu: dict) -> list[dict]:
    if code not in VENTILATION_ETIC_CODES:
        return []
    ventilations = (contenu or {}).get("ventilations") or {}
    autres_neant = bool((contenu or {}).get("autres_analyses_neant"))
    rows = []
    for ligne in (automatique or {}).get("lignes") or []:
        compte = str(ligne.get("compte") or "")
        saved = ventilations.get(compte) or {}
        total = money(ligne.get("montant"))
        row = {
            "compte": compte,
            "intitule": ligne.get("intitule") or "",
            "total": _num(total),
        }
        for key in VENTILATION_ECHEANCE_KEYS:
            val = _decimal_ventilation(saved.get(key))
            if val is None and saved.get(key) in (None, ""):
                val = _echeance_auto_ligne(ligne, key)
            row[key] = _num(val) if val is not None else None
        for key in VENTILATION_ANALYSE_KEYS:
            val = _decimal_ventilation(saved.get(key))
            saisie_invalide = val is None and saved.get(key) not in (None, "")
            if key == "etat_organismes_publics" and val is None and not saisie_invalide:
                val = _etat_public_auto(code, compte, total)
            if val is None and autres_neant and not saisie_invalide:
                val = ZERO
            row[key] = _num(val) if val is not None else None
        rows.append(row)
    return rows


def _erreurs_ventilation_b6_b7(code: str, automatique: dict, contenu: dict) -> list[str]:
    if code not in VENTILATION_ETIC_CODES:
        return []
    ventilations = (contenu or {}).get("ventilations") or {}
    autres_neant = bool((contenu or {}).get("autres_analyses_neant"))
    errors: list[str] = []
    lib_echues = "échues et non recouvrées" if code == "B6" else "échues et non payées"
    for ligne in (automatique or {}).get("lignes") or []:
        compte = str(ligne.get("compte") or "")
        total = money(ligne.get("montant"))
        saved = ventilations.get(compte) or {}
        echeances = []
        for key, label in (("plus_un_an", "+ d'un an"), ("moins_un_an", "- d'un an"), ("echues", lib_echues)):
            val = _decimal_ventilation(saved.get(key))
            if val is None and saved.get(key) not in (None, ""):
                errors.append(f"{compte} : {label} doit être un montant fini et positif ou nul.")
                continue
            if val is None:
                val = _echeance_auto_ligne(ligne, key)
            if val is None:
                errors.append(f"{compte} : renseignez la ventilation {label}.")
            else:
                echeances.append(val)
        if len(echeances) == 3 and money(sum(echeances, ZERO)) != total:
            errors.append(f"{compte} : la ventilation par échéance doit totaliser {total:.2f} MAD.")

        for key, label in (("devises", "montant en devises"), ("etat_organismes_publics", "Etat / organismes publics"), ("entreprises_liees", "entreprises liées"), ("effets", "montant représenté par effets")):
            val = _decimal_ventilation(saved.get(key))
            if val is None and saved.get(key) not in (None, ""):
                errors.append(f"{compte} : {label} doit être un montant fini et positif ou nul.")
                continue
            if key == "etat_organismes_publics" and val is None:
                val = _etat_public_auto(code, compte, total)
            if val is None and autres_neant:
                val = ZERO
            if val is None:
                errors.append(f"{compte} : renseignez {label} ou confirmez que les autres analyses sont néant.")
            elif val > total:
                errors.append(f"{compte} : {label} ne peut pas dépasser le total de la ligne ({total:.2f} MAD).")
    return errors


def valider_contenu_etic(db: Session, societe_id: int, exercice: int, code: str, contenu: dict) -> list[str]:
    """Validation métier des compléments ETIC avant persistance."""
    if code not in VENTILATION_ETIC_CODES:
        return []
    ventilations = (contenu or {}).get("ventilations")
    if ventilations is not None and not isinstance(ventilations, dict):
        return ["Les ventilations doivent être un objet par compte."]
    erreurs = []
    for compte, montants in (ventilations or {}).items():
        if not isinstance(montants, dict):
            erreurs.append(f"{compte} : la ventilation doit être un objet de montants.")
            continue
        for key in (*VENTILATION_ECHEANCE_KEYS, *VENTILATION_ANALYSE_KEYS):
            valeur = montants.get(key)
            if valeur not in (None, "") and _decimal_ventilation(valeur) is None:
                erreurs.append(f"{compte} : {key} doit être un montant fini et positif ou nul.")
    if erreurs:
        return erreurs
    # Un brouillon incomplet reste conservable ; une valeur invalide ne l'est pas.
    if not (contenu or {}).get("confirme"):
        return []
    source = source_etats_synthese(db, societe_id, exercice)
    auto = _automatiques(db, societe_id, exercice, source["soldes"]).get(code) or {}
    return _erreurs_ventilation_b6_b7(code, auto, contenu or {})


def _bornes(db: Session, societe_id: int, exercice: int):
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=exercice).first()
    if ex:
        return ex.date_debut, ex.date_fin
    return date(exercice, 1, 1), date(exercice, 12, 31)


def _sd(soldes, prefixes):
    total = ZERO
    for c, v in soldes.items():
        if any(str(c).startswith(p) for p in prefixes):
            total += money(v.get("debit")) - money(v.get("credit"))
    return money(total)


def _sc(soldes, prefixes):
    total = ZERO
    for c, v in soldes.items():
        if any(str(c).startswith(p) for p in prefixes):
            total += money(v.get("credit")) - money(v.get("debit"))
    return money(total)


def _lignes_soldes(soldes, prefixes, sens="debit", db=None, societe_id=None):
    lignes = []
    for c in sorted(soldes):
        if not any(c.startswith(p) for p in prefixes):
            continue
        v = soldes[c]
        montant = money(v["debit"] - v["credit"] if sens == "debit" else v["credit"] - v["debit"])
        if montant == 0:
            continue
        lignes.append({"compte": c, "intitule": libelle_compte(c, db=db, societe_id=societe_id) or "Compte comptable", "montant": _num(montant)})
    return lignes


def _condition_cloture_technique():
    return or_(
        models.Ecriture.journal == models.JournalEnum.CL,
        func.coalesce(models.Ecriture.reference, "").like("CLOTURE-%"),
    )


def _mouvements_comptes(db: Session, societe_id: int, exercice: int, prefixes: tuple[str, ...]):
    """Mouvements validés par compte/journal, hors clôture technique."""
    rows = (
        db.query(
            models.LigneEcriture.compte,
            models.Ecriture.journal,
            func.coalesce(func.sum(models.LigneEcriture.debit), 0),
            func.coalesce(func.sum(models.LigneEcriture.credit), 0),
        )
        .join(models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id)
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
            ~_condition_cloture_technique(),
        )
        .group_by(models.LigneEcriture.compte, models.Ecriture.journal)
        .all()
    )
    data = defaultdict(lambda: defaultdict(lambda: [ZERO, ZERO]))
    for compte, journal, debit, credit in rows:
        c = str(compte)
        if not any(c.startswith(p) for p in prefixes):
            continue
        j = journal.value if hasattr(journal, "value") else str(journal)
        data[c][j][0] += money(debit)
        data[c][j][1] += money(credit)
    return data


def _section_b2(db, sid, exercice, soldes):
    debut, fin = _bornes(db, sid, exercice)

    # Les immobilisations incorporelles/corporelles (22/23) sont rapprochées
    # avec le registre métier des immobilisations. En revanche, les non-valeurs
    # (21) ne sont pas des fiches d'immobilisation du module HisabPro : elles
    # sont suivies directement par leurs mouvements comptables. Les forcer dans
    # le registre créait un faux écart B2 (cas réel 2117 = 7 000 MAD).
    immos = db.query(models.Immobilisation).filter(models.Immobilisation.societe_id == sid).all()
    agg_registre = defaultdict(lambda: {"ouverture": ZERO, "acquisitions": ZERO, "sorties": ZERO})
    for i in immos:
        compte = str(i.compte_immo or "23")
        if compte.startswith("21"):
            # Même si une ancienne fiche 21 existe, la source officielle de la
            # variation B2 reste ici le grand livre pour éviter un double suivi.
            continue
        valeur = money(i.valeur_brute)
        if i.date_acquisition < debut and (i.date_sortie is None or i.date_sortie >= debut):
            agg_registre[compte]["ouverture"] += valeur
        if debut <= i.date_acquisition <= fin:
            agg_registre[compte]["acquisitions"] += valeur
        if i.date_sortie and debut <= i.date_sortie <= fin:
            agg_registre[compte]["sorties"] += valeur

    agg_non_valeurs = defaultdict(lambda: {"ouverture": ZERO, "acquisitions": ZERO, "sorties": ZERO})
    mouvements_21 = _mouvements_comptes(db, sid, exercice, ("21",))
    for compte, journaux in mouvements_21.items():
        an_d, an_c = journaux.get("AN", [ZERO, ZERO])
        agg_non_valeurs[compte]["ouverture"] = money(an_d - an_c)
        for journal, (debit, credit) in journaux.items():
            if journal == "AN":
                continue
            agg_non_valeurs[compte]["acquisitions"] += money(debit)
            agg_non_valeurs[compte]["sorties"] += money(credit)

    comptes = sorted(
        set(agg_registre)
        | set(agg_non_valeurs)
        | {c for c in soldes if c.startswith(("21", "22", "23")) and not c.startswith(("28", "29"))}
    )
    lignes=[]
    for c in comptes:
        d = agg_non_valeurs[c] if c.startswith("21") else agg_registre[c]
        fin_module=money(d["ouverture"]+d["acquisitions"]-d["sorties"])
        solde=money(soldes.get(c,{}).get("debit",0)-soldes.get(c,{}).get("credit",0))
        if fin_module==0 and solde==0: continue
        lignes.append({"compte":c,"intitule":libelle_compte(c, db=db, societe_id=sid) or "Immobilisation","debut":_num(d["ouverture"]),"augmentations":_num(d["acquisitions"]),"diminutions":_num(d["sorties"]),"fin_module":_num(fin_module),"solde_comptable_fin":_num(solde),"ecart":_num(solde-fin_module)})
    return lignes


def _section_b2bis(db, sid, exercice):
    data=_mouvements_comptes(db,sid,exercice,("281","282","283"))
    lignes=[]
    for c in sorted(data):
        an_d,an_c=data[c].get("AN",[ZERO,ZERO])
        ouverture=money(an_c-an_d)
        dot=ZERO; sorties=ZERO
        for j,(d,cdr) in data[c].items():
            if j=="AN": continue
            dot += cdr
            sorties += d
        fin=money(ouverture+dot-sorties)
        if ouverture==dot==sorties==ZERO: continue
        lignes.append({"compte":c,"intitule":libelle_compte(c, db=db, societe_id=sid) or "Amortissements","cumul_debut":_num(ouverture),"dotations":_num(dot),"amort_sorties":_num(sorties),"cumul_fin":_num(fin)})
    return lignes


def _section_b3(db, sid, exercice):
    debut,fin=_bornes(db,sid,exercice)
    immos=db.query(models.Immobilisation).filter(
        models.Immobilisation.societe_id==sid,
        models.Immobilisation.date_sortie.isnot(None),
        models.Immobilisation.date_sortie>=debut,
        models.Immobilisation.date_sortie<=fin,
    ).order_by(models.Immobilisation.date_sortie).all()
    lignes=[]
    for i in immos:
        vna=ZERO
        if i.ecriture_sortie_id:
            rows=db.query(models.LigneEcriture).filter(models.LigneEcriture.ecriture_id==i.ecriture_sortie_id).all()
            vna=sum((money(r.debit)-money(r.credit) for r in rows if str(r.compte).startswith("651")),ZERO)
        prix=money(i.prix_cession_ht)
        lignes.append({"date":i.date_sortie.isoformat(),"designation":i.designation,"type":i.type_sortie or "sortie","valeur_entree":_num(i.valeur_brute),"vna":_num(vna),"prix_cession":_num(prix),"plus_moins_value":_num(prix-vna)})
    return lignes


def _section_b5(db,sid,exercice):
    data=_mouvements_comptes(db,sid,exercice,("15","29","39","45","59"))
    lignes=[]
    for c in sorted(data):
        an_d,an_c=data[c].get("AN",[ZERO,ZERO])
        ouverture=money(an_c-an_d)
        dot=ZERO; reprises=ZERO
        for j,(d,cr) in data[c].items():
            if j=="AN": continue
            dot+=cr; reprises+=d
        fin=money(ouverture+dot-reprises)
        if ouverture==dot==reprises==ZERO: continue
        lignes.append({"compte":c,"intitule":libelle_compte(c, db=db, societe_id=sid) or "Provision","debut":_num(ouverture),"dotations":_num(dot),"reprises_utilisations":_num(reprises),"fin":_num(fin)})
    return lignes


def _est_liquidation_od_tva(ecriture) -> bool:
    """Reconnaît une centralisation comptable TVA, jamais la preuve d'un dépôt.

    Aucun rapprochement par référence ou libellé : les OD mixtes, corrections
    entre seuls comptes de TVA de travail et paiements restent indéterminés.
    """
    journal = getattr(ecriture.journal, "value", ecriture.journal)
    if journal != "OD":
        return False
    comptes = set()
    debit = credit = ZERO
    for ligne in ecriture.lignes:
        try:
            d = Decimal(str(ligne.debit or 0))
            c = Decimal(str(ligne.credit or 0))
        except (ValueError, ArithmeticError):
            return False
        if not d.is_finite() or not c.is_finite() or d < 0 or c < 0 or (d and c):
            return False
        if not (d or c):
            continue
        compte = str(ligne.compte or "").strip()
        if not re.fullmatch(r"(?:4455|34551|34552|4456|3456)\d*", compte):
            return False
        comptes.add(compte)
        debit += d
        credit += c
    return bool(debit > ZERO and debit == credit
                and any(c.startswith(("4455", "34551", "34552")) for c in comptes)
                and any(c.startswith(("4456", "3456")) for c in comptes))


def _mouvements_tva_b14(db, sid, exercice):
    debut, fin = _bornes(db, sid, exercice)
    prefixes = ("4455", "34551", "34552")
    ecritures = db.query(models.Ecriture).options(joinedload(models.Ecriture.lignes)).filter(
        models.Ecriture.societe_id == sid,
        models.Ecriture.date >= debut, models.Ecriture.date <= fin,
        models.Ecriture.est_validee.is_(True),
        ~_condition_cloture_technique(),
        models.Ecriture.lignes.any(or_(*[
            models.LigneEcriture.compte.startswith(p) for p in prefixes
        ])),
    ).all()
    data = defaultdict(lambda: defaultdict(lambda: [ZERO, ZERO]))
    for ecriture in ecritures:
        journal = getattr(ecriture.journal, "value", ecriture.journal)
        if _est_liquidation_od_tva(ecriture):
            journal = "TV"  # Catégorie du calcul uniquement ; journal source intact.
        for ligne in ecriture.lignes:
            compte = str(ligne.compte or "")
            if compte.startswith(prefixes):
                data[compte][journal][0] += money(ligne.debit)
                data[compte][journal][1] += money(ligne.credit)
    return data


def _section_b14(db,sid,exercice):
    data=_mouvements_tva_b14(db,sid,exercice)
    def calc(prefixes, sens):
        opening=ops=decl=ZERO
        for c,journaux in data.items():
            if not any(c.startswith(p) for p in prefixes): continue
            for j,(d,cr) in journaux.items():
                if sens=="credit":
                    if j=="AN": opening += cr-d
                    elif j=="TV": decl += d-cr
                    else: ops += cr-d
                else:
                    if j=="AN": opening += d-cr
                    elif j=="TV": decl += cr-d
                    else: ops += d-cr
        return money(opening), money(ops), money(decl), money(opening+ops-decl)
    fact=calc(("4455",),"credit")
    chg=calc(("34552",),"debit")
    imm=calc(("34551",),"debit")
    rec=tuple(money(chg[i]+imm[i]) for i in range(4))
    due=tuple(money(fact[i]-rec[i]) for i in range(4))
    def row(nature,t): return {"nature":nature,"solde_debut":_num(t[0]),"operations":_num(t[1]),"declarations":_num(t[2]),"solde_fin":_num(t[3])}
    return [row("A. TVA facturée / collectée",fact),row("B. TVA récupérable",rec),row("• sur charges",chg),row("• sur immobilisations",imm),row("C. TVA due ou crédit de TVA (A - B)",due)]


def _calcul_c3_depuis_soldes(soldes, *, decimal_exact=False):
    """Calcule les indicateurs comptables automatiques de l'état ETIC C3.

    ``source_etats_synthese`` exclut volontairement les écritures techniques de
    clôture. Le résultat de l'exercice n'est donc pas encore porté dans 1191/1199
    dans cette source : il doit être ajouté explicitement à la situation nette.

    C3 définit la situation nette comme : capitaux propres + capitaux propres
    assimilés - immobilisations en non-valeurs nettes. Les comptes 281 sont
    ajoutés pour ramener les non-valeurs de leur brut à leur valeur nette.
    """
    convertir = (lambda v: format(money(v), '.2f')) if decimal_exact else _num
    ca = _sc(soldes, ("711", "712"))
    produits = _sc(soldes, ("71", "73", "75"))
    charges = _sd(soldes, ("61", "63", "65"))
    isr = _sd(soldes, ("67",))
    rai = money(produits - charges)
    net = money(rai - isr)
    situation = money(
        _sc(soldes, ("11", "13"))
        + net
        - _sd(soldes, ("21",))
        + _sc(soldes, ("281",))
    )
    salaires = _sd(soldes, ("6171",))
    return {
        "situation_nette": convertir(situation),
        "chiffre_affaires_ht": convertir(ca),
        "resultat_avant_impots": convertir(rai),
        "impots_resultats": convertir(isr),
        "resultat_net": convertir(net),
        "salaires_bruts": convertir(salaires),
    }


def _section_c3(db,sid,exercice):
    annees=[exercice-2,exercice-1,exercice]
    result=[]
    for y in annees:
        src=source_etats_synthese(db,sid,y)

        # Pour les années comparatives, la simple présence technique d'une ligne
        # dans exercices_comptables ne suffit pas : certaines bases historiques
        # contiennent un exercice fantôme / préparé sans aucune donnée comptable.
        # On reprend exactement la notion de comparatif disponible utilisée par
        # la Liasse : au moins une écriture validée hors clôture technique.
        if y != exercice and not src.get("disponible"):
            result.append({
                "exercice": y,
                "situation_nette": None,
                "chiffre_affaires_ht": None,
                "resultat_avant_impots": None,
                "impots_resultats": None,
                "resultat_net": None,
                "salaires_bruts": None,
                "effectif_indicatif": None,
            })
            continue

        s=src["soldes"]
        ligne = _calcul_c3_depuis_soldes(s)
        effectif=None
        if y==exercice:
            _,fin=_bornes(db,sid,y)
            effectif=db.query(models.Employe).filter(models.Employe.societe_id==sid, or_(models.Employe.date_embauche.is_(None), models.Employe.date_embauche<=fin), models.Employe.actif.is_(True)).count()
        result.append({"exercice":y, **ligne, "effectif_indicatif":effectif})
    return result


def _automatiques(db: Session, sid: int, exercice: int, soldes: dict[str, Any]):
    data={}
    data["B1"]={"colonnes":["compte","intitule","montant"],"lignes":_lignes_soldes(soldes,("21",),"debit",db,sid)}
    data["B2"]={"colonnes":["compte","intitule","debut","augmentations","diminutions","fin_module","solde_comptable_fin","ecart"],"lignes":_section_b2(db,sid,exercice,soldes),"avertissement":"Le rapprochement utilise les mouvements comptables pour les non-valeurs (21) et le registre des immobilisations pour les comptes 22/23 ; tout écart résiduel doit être justifié avant arrêté."}
    data["B2bis"]={"colonnes":["compte","intitule","cumul_debut","dotations","amort_sorties","cumul_fin"],"lignes":_section_b2bis(db,sid,exercice)}
    data["B3"]={"colonnes":["date","designation","type","valeur_entree","vna","prix_cession","plus_moins_value"],"lignes":_section_b3(db,sid,exercice)}
    data["B4"]={"colonnes":["compte","intitule","montant"],"lignes":_lignes_soldes(soldes,("251",),"debit",db,sid),"avertissement":"Les informations sur l'émetteur, le capital, la quote-part détenue et les produits reçus ne sont pas déductibles du seul compte général : complétez-les dans les notes si nécessaire."}
    data["B5"]={"colonnes":["compte","intitule","debut","dotations","reprises_utilisations","fin"],"lignes":_section_b5(db,sid,exercice)}
    creances=_lignes_soldes(soldes,("241","248","34"),"debit",db,sid)
    _ajouter_echeances_auto(db, sid, exercice, creances, "vente")
    data["B6"]={"colonnes":["compte","intitule","montant"],"lignes":creances,"avertissement":"Les échéances des factures clients sont préremplies automatiquement lorsqu'elles recoupent exactement le solde comptable ; les autres ventilations restent extra-comptables."}
    dettes=_lignes_soldes(soldes,("14","44","55"),"credit",db,sid)
    _ajouter_echeances_auto(db, sid, exercice, dettes, "achat")
    data["B7"]={"colonnes":["compte","intitule","montant"],"lignes":dettes,"avertissement":"Les échéances des factures fournisseurs sont préremplies automatiquement lorsqu'elles recoupent exactement le solde comptable ; les autres ventilations restent extra-comptables."}
    # B11 : détail des comptes de charges et produits réellement mouvementés.
    cpc=[]
    for c in sorted(soldes):
        if c.startswith("6"):
            m=money(soldes[c]["debit"]-soldes[c]["credit"])
            if m: cpc.append({"compte":c,"intitule":libelle_compte(c, db=db, societe_id=sid) or "Charge","nature":"Charge","montant":_num(m)})
        elif c.startswith("7"):
            m=money(soldes[c]["credit"]-soldes[c]["debit"])
            if m: cpc.append({"compte":c,"intitule":libelle_compte(c, db=db, societe_id=sid) or "Produit","nature":"Produit","montant":_num(m)})
    data["B11"]={"colonnes":["compte","intitule","nature","montant"],"lignes":cpc}

    # B12 : réutilise le moteur fiscal Patch 08, sans dupliquer ses règles.
    try:
        from routers.fiscalite import situation_is
        fis=situation_is(exercice,current_user={"societe_id":sid,"id":0,"role":"comptable"},db=db)
        calc=fis["calcul"]; source=fis["source_comptable"]
        is_comp=money(source.get("is_deja_comptabilise"))
        resultat_net=money(calc["resultat_comptable_avant_is"]-is_comp)
        reint=money(calc["reintegrations"])+is_comp
        ded=money(calc["deductions"])
        data["B12"]={"colonnes":["rubrique","montant"],"lignes":[
            {"rubrique":"Résultat net comptable","montant":_num(resultat_net)},
            {"rubrique":"Réintégrations fiscales (dont IS comptabilisé)","montant":_num(reint)},
            {"rubrique":"Déductions fiscales","montant":_num(ded)},
            {"rubrique":"Résultat fiscal avant déficits","montant":_num(calc["resultat_fiscal_avant_deficit"])},
            {"rubrique":"Déficits imputés","montant":_num(calc["deficit_impute"])},
            {"rubrique":"Bénéfice fiscal imposable","montant":_num(calc["benefice_fiscal_imposable"])},
        ],"source":"Moteur fiscal Patch 08"}
    except Exception as exc:
        data["B12"]={"colonnes":["rubrique","montant"],"lignes":[],"avertissement":f"Moteur fiscal indisponible : {exc}"}

    courant=money(_sc(soldes,("71","73"))-_sd(soldes,("61","63")))
    impots=_sd(soldes,("67",))
    data["B13"]={"colonnes":["rubrique","montant"],"lignes":[
        {"rubrique":"Résultat courant avant impôts","montant":_num(courant)},
        {"rubrique":"Impôts sur les résultats comptabilisés","montant":_num(impots)},
        {"rubrique":"Résultat courant après impôts — indicatif","montant":_num(courant-impots)},
    ],"avertissement":"L'affectation de l'impôt entre résultat courant et non courant peut nécessiter un ajustement extra-comptable ; vérifiez ce tableau avant arrêté."}
    data["B14"]={"colonnes":["nature","solde_debut","operations","declarations","solde_fin"],"lignes":_section_b14(db,sid,exercice),"avertissement":"La colonne « déclarations » est reconstituée à partir du journal TVA (TV) et des liquidations OD équilibrées exclusivement en comptes TVA avec contrepartie 4456 ou 3456. Ces mouvements comptables ne prouvent pas un dépôt fiscal : vérifiez-les avec les déclarations effectivement déposées. Le solde A - B porte sur 4455/34551/34552, distinct de la dette déjà liquidée en 4456 ou du crédit reporté en 3456."}
    data["C3"]={"colonnes":["exercice","situation_nette","chiffre_affaires_ht","resultat_avant_impots","impots_resultats","resultat_net","salaires_bruts","effectif_indicatif"],"lignes":_section_c3(db,sid,exercice),"avertissement":"Les bénéfices distribués et le résultat par titre dépendent de l'affectation/actionnariat saisis dans C1/C2 et ne sont pas inventés automatiquement."}
    return data


def construire_etic(db: Session, societe_id: int, exercice: int):
    societe=db.query(models.Societe).filter_by(id=societe_id).first()
    if not societe:
        raise ValueError("Société introuvable")
    source=source_etats_synthese(db,societe_id,exercice)
    auto=_automatiques(db,societe_id,exercice,source["soldes"])
    saisies={x.code:x for x in db.query(models.ETICSectionExercice).filter_by(societe_id=societe_id,exercice=exercice).all()}
    sections=[]
    nb_completes=0
    for meta in CATALOGUE_ETIC:
        rec=saisies.get(meta["code"])
        contenu=(rec.contenu or {}) if rec else {}
        automatique=auto.get(meta["code"],{"colonnes":[],"lignes":[]})
        # Une section auto est complète si la source est disponible; une section manuelle
        # l'est dès qu'elle contient un texte ou au moins une ligne.
        erreurs_ventilation = _erreurs_ventilation_b6_b7(meta["code"], automatique, contenu) if meta["code"] in VENTILATION_ETIC_CODES else []
        ventilation = _ventilation_publiee(meta["code"], automatique, contenu) if meta["code"] in VENTILATION_ETIC_CODES else []
        if meta["mode"]=="auto":
            complete=True
        elif meta["mode"]=="assiste":
            complete=bool(contenu.get("confirme")) and not erreurs_ventilation
        else:
            complete=bool((contenu.get("texte") or "").strip() or contenu.get("lignes") or contenu.get("neant"))
        if complete: nb_completes+=1
        sections.append({**meta,"automatique":automatique,"contenu":contenu,"complete":complete,"ventilation":ventilation,"erreurs_ventilation":erreurs_ventilation,"updated_at":rec.updated_at.isoformat() if rec and rec.updated_at else None})
    total=len(sections)
    return {
        "exercice":exercice,
        "societe":{"raison_sociale":societe.raison_sociale,"identifiant_fiscal":societe.identifiant_fiscal,"ice":societe.ice,"capital_social":_num(societe.capital_social)},
        "source":source["source"],
        "controle_source":source["controle"],
        "sections":sections,
        "progression":{"completes":nb_completes,"total":total,"pourcentage":round(nb_completes*100/total) if total else 100},
        "referentiel":{"modele":"ETIC — modèle normal CGNC","sections":"A1-A3, B1-B14, C1-C5","note":"Les états automatiques proviennent des écritures validées. Les informations extra-comptables restent à confirmer ou à saisir."},
    }
