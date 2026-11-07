# -*- coding: utf-8 -*-
"""Préparation de la déclaration des délais de paiement (loi n°69-21).

FACT-F
------
Ce service prépare un état de travail exploitable pour SIMPL-Délais de paiement.
Il ne prétend pas reproduire le schéma EDI officiel : l'export CSV reste un support
à contrôler/viser par le professionnel habilité avant dépôt.

Le reporting concerne les FACTURES FOURNISSEURS (achats), puisque la sanction
vise l'entreprise cliente qui paie son fournisseur hors délai.
"""
from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy.orm import joinedload
from sqlalchemy import and_

import models
from services.etats_synthese_service import source_etats_synthese
from services.tva_service import ventilation_facture, ventilation_avoir, total_ventilation
from services.echeancier_service import echeances_persistantes_ou_defaut

MONEY = Decimal("0.01")
ZERO = Decimal("0.00")
SEUIL_ASSUJETTISSEMENT = Decimal("2000000.00")

# Historique utile à l'application de la loi. Le taux est réputé rester en
# vigueur jusqu'à la date d'effet suivante. FACT-F est conçu pour 2026 ; le
# taux de 2,25 % est resté inchangé lors des conseils de mars et juin 2026.
TAUX_BAM = (
    (date(2023, 3, 23), Decimal("3.00")),
    (date(2024, 6, 27), Decimal("2.75")),
    (date(2024, 12, 19), Decimal("2.50")),
    (date(2025, 3, 20), Decimal("2.25")),
)


def _money(v: Any) -> Decimal:
    return Decimal(str(v or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)


def _enum_value(v):
    return getattr(v, "value", v)


def bornes_trimestre(annee: int, trimestre: int) -> tuple[date, date]:
    if trimestre not in (1, 2, 3, 4):
        raise ValueError("Le trimestre doit être compris entre 1 et 4.")
    mois_debut = (trimestre - 1) * 3 + 1
    mois_fin = mois_debut + 2
    return (
        date(annee, mois_debut, 1),
        date(annee, mois_fin, calendar.monthrange(annee, mois_fin)[1]),
    )


def _add_months(d: date, n: int) -> date:
    total = d.year * 12 + (d.month - 1) + n
    y, m0 = divmod(total, 12)
    m = m0 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def mois_ou_fraction_retard(echeance: date, date_fin_retard: date) -> int:
    """Nombre de mois ou fractions de mois de retard.

    Une journée après l'échéance déclenche le premier mois ; chaque nouvelle
    période mensuelle entamée déclenche un mois supplémentaire.
    """
    if not echeance or not date_fin_retard or date_fin_retard <= echeance:
        return 0
    diff = (date_fin_retard.year - echeance.year) * 12 + (date_fin_retard.month - echeance.month)
    if date_fin_retard.day > echeance.day:
        diff += 1
    return max(1, diff)


def taux_directeur_a(d: date) -> Decimal | None:
    taux = None
    for effet, valeur in TAUX_BAM:
        if effet <= d:
            taux = valeur
        else:
            break
    return taux


def amende_indicative(montant: Any, echeance: date, fin_retard: date) -> dict:
    """Simulation de l'amende sur une tranche de montant.

    1er mois : taux directeur BAM applicable à la fin du premier mois de retard.
    Mois/fraction supplémentaire : +0,85 % par mois.
    """
    montant = _money(montant)
    mois = mois_ou_fraction_retard(echeance, fin_retard)
    if montant <= ZERO or mois <= 0:
        return {"mois": 0, "taux_directeur_pct": None, "taux_total_pct": 0.0, "amende": 0.0}
    fin_premier_mois = _add_months(echeance, 1)
    taux = taux_directeur_a(fin_premier_mois)
    if taux is None:
        return {"mois": mois, "taux_directeur_pct": None, "taux_total_pct": None, "amende": None}
    taux_total = taux + Decimal("0.85") * Decimal(max(0, mois - 1))
    montant_amende = (montant * taux_total / Decimal("100")).quantize(MONEY, rounding=ROUND_HALF_UP)
    return {
        "mois": mois,
        "taux_directeur_pct": float(taux),
        "taux_total_pct": float(taux_total),
        "amende": float(montant_amende),
    }


def _ca_comptable_ht(db, societe_id: int, exercice: int) -> Decimal:
    src = source_etats_synthese(db, societe_id, exercice)
    soldes = src.get("soldes", {})
    ca = ZERO
    for compte, valeurs in soldes.items():
        if str(compte).startswith(("711", "712")):
            ca += _money(valeurs.get("credit")) - _money(valeurs.get("debit"))
    return ca.quantize(MONEY)


def _dernier_exercice_reference(db, societe_id: int, debut_periode: date):
    ex = db.query(models.ExerciceComptable).filter(
        models.ExerciceComptable.societe_id == societe_id,
        models.ExerciceComptable.date_fin < debut_periode,
        models.ExerciceComptable.statut == "cloture",
    ).order_by(models.ExerciceComptable.date_fin.desc()).first()
    if ex:
        return ex, True
    # Fallback explicite si aucun exercice clôturé n'est disponible : le CA est
    # utile pour le diagnostic mais l'assujettissement doit être confirmé.
    ex = db.query(models.ExerciceComptable).filter(
        models.ExerciceComptable.societe_id == societe_id,
        models.ExerciceComptable.date_fin < debut_periode,
    ).order_by(models.ExerciceComptable.date_fin.desc()).first()
    return ex, False


def _date_entree_dispositif(ca_ht: Decimal) -> date | None:
    if ca_ht <= SEUIL_ASSUJETTISSEMENT:
        return None
    if ca_ht > Decimal("50000000"):
        return date(2023, 7, 1)
    if ca_ht > Decimal("10000000"):
        return date(2024, 1, 1)
    return date(2025, 1, 1)


def _total_facture(facture) -> tuple[Decimal, Decimal]:
    apres = total_ventilation(ventilation_facture(facture, appliquer_escompte=True))
    avant = total_ventilation(ventilation_facture(facture, appliquer_escompte=False))
    return _money(apres["ttc"]), _money(avant["base"])


def _montant_avoir(avoir) -> Decimal:
    return _money(total_ventilation(ventilation_avoir(avoir, appliquer_escompte=True))["ttc"])


def _date_livraison_auto(db, facture) -> date | None:
    explicite = getattr(facture, "date_livraison_service", None)
    if explicite:
        return explicite
    ids = [getattr(l, "source_ligne_bl_id", None) for l in (facture.lignes or [])]
    ids = [x for x in ids if x]
    if not ids:
        return None
    rows = db.query(models.BonLivraison.date).join(
        models.LigneBonLivraison,
        models.LigneBonLivraison.bon_livraison_id == models.BonLivraison.id,
    ).filter(models.LigneBonLivraison.id.in_(ids)).all()
    dates = [r[0] for r in rows if r and r[0]]
    return max(dates) if dates else None


def _nature_operation(facture) -> str:
    valeurs = []
    for l in facture.lignes or []:
        txt = " ".join(str(getattr(l, "description", "") or "").split())
        if txt and txt not in valeurs:
            valeurs.append(txt)
    texte = " ; ".join(valeurs)
    return texte[:1000]


def _echeances(facture, total_ttc: Decimal) -> list[dict]:
    rows = echeances_persistantes_ou_defaut(facture, float(total_ttc))
    return [
        {"date": r["date_echeance"], "montant": _money(r["montant"]), "ordre": r.get("ordre") or 1}
        for r in rows
    ]


def _evenements_reglement(db, societe_id: int, facture, total_ht_avant: Decimal, diagnostics=None) -> list[dict]:
    events = []
    regs = db.query(models.Reglement).filter(
        models.Reglement.societe_id == societe_id,
        models.Reglement.facture_id == facture.id,
        models.Reglement.statut.notin_(["rejete", "annule"]),
    ).all()
    for r in regs:
        d = r.date_encaissement or r.date
        if d and _money(r.montant) > ZERO:
            events.append({
                "date": d, "montant": _money(r.montant), "type": "reglement",
                "mode": r.mode, "reference": r.reference,
            })

    avoirs = db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter(
        models.Avoir.societe_id == societe_id,
        models.Avoir.facture_id == facture.id,
        models.Avoir.statut != "annule",
    ).all()
    for a in avoirs:
        montant = _montant_avoir(a)
        if a.date and montant > ZERO:
            events.append({"date": a.date, "montant": montant, "type": "avoir", "mode": "avoir", "reference": a.numero})

    imputations = db.query(models.ImputationAcompte).filter(
        models.ImputationAcompte.societe_id == societe_id,
        models.ImputationAcompte.facture_id == facture.id,
        models.ImputationAcompte.statut == "active",
    ).all()
    for imp in imputations:
        if imp.date_imputation and _money(imp.montant) > ZERO:
            events.append({
                "date": imp.date_imputation, "montant": _money(imp.montant),
                "type": "acompte", "mode": "acompte", "reference": f"Acompte #{imp.acompte_id}",
            })

    utilisations = db.query(models.UtilisationAvoir).filter(
        models.UtilisationAvoir.societe_id == societe_id,
        models.UtilisationAvoir.facture_id == facture.id,
        models.UtilisationAvoir.type_utilisation == "imputation",
        models.UtilisationAvoir.statut == "active",
    ).all()
    for u in utilisations:
        if u.date_utilisation and _money(u.montant) > ZERO:
            events.append({
                "date": u.date_utilisation, "montant": _money(u.montant),
                "type": "avoir_impute", "mode": "avoir",
                "reference": f"Crédit avoir #{u.avoir_id}",
            })

    # Une RAS régulièrement appliquée n'est pas une somme restant due au fournisseur.
    taux_ras = Decimal(str(getattr(facture, "ras_taux", 0) or 0))
    if getattr(facture, 'ras_comptabilisee', False) is True and (not taux_ras.is_finite() or taux_ras < ZERO or taux_ras > Decimal('100')):
        if diagnostics is not None:
            diagnostics.append('RAS historique invalide : montant et date non déterminables.')
    if getattr(facture, 'ras_comptabilisee', False) is True and taux_ras.is_finite() and ZERO < taux_ras <= Decimal('100'):
        montant_ras = (total_ht_avant * taux_ras / Decimal("100")).quantize(MONEY)
        if montant_ras > ZERO:
            from services.ras_paiement_service import date_od_ras_historique
            date_od = date_od_ras_historique(db, societe_id, facture, montant_ras)
            if date_od is not None:
                events.append({'date': date_od, 'montant': montant_ras, 'type': 'ras',
                               'mode': 'retenue_source', 'reference': 'RAS historique — date OD'})
            elif diagnostics is not None:
                diagnostics.append('RAS historiquement comptabilisée : date OD exacte et unique non déterminable ; aucune date d’échéance utilisée comme paiement.')

    from services.ras_reglement_service import captures_facture
    for capture in captures_facture(db, societe_id, facture.id):
        if capture['annulation_id'] is None:
            events.append({'date': capture['date_operation'], 'montant': _money(capture['montant']),
                'type': 'ras', 'mode': 'retenue_source', 'reference': capture['reference']})
    return sorted(events, key=lambda e: (e["date"], e["type"]))


def _allouer(echeances: list[dict], events: list[dict], fin_periode: date) -> tuple[list[dict], list[dict]]:
    tranches = [dict(x, restant=x["montant"], allocations=[]) for x in sorted(echeances, key=lambda x: (x["date"], x["ordre"]))]
    for ev in [e for e in events if e["date"] <= fin_periode]:
        reste_event = ev["montant"]
        for tr in tranches:
            if reste_event <= ZERO:
                break
            if tr["restant"] <= ZERO:
                continue
            montant = min(reste_event, tr["restant"])
            tr["restant"] -= montant
            reste_event -= montant
            tr["allocations"].append({**ev, "montant": montant})
    return tranches, events


def _row_facture(db, societe_id: int, facture, debut: date, fin: date) -> dict | None:
    total_ttc, total_ht_avant = _total_facture(facture)
    if total_ttc <= ZERO:
        return None
    echeances = _echeances(facture, total_ttc)
    diagnostics_ras = []
    events = _evenements_reglement(db, societe_id, facture, total_ht_avant, diagnostics_ras)
    tranches, _ = _allouer(echeances, events, fin)

    paye_hors_delai = ZERO
    non_paye = ZERO
    penalite = ZERO
    penalite_calculable = True
    max_mois = 0
    dates_paiements = []
    modes = []
    refs = []

    for tr in tranches:
        due = tr["date"]
        # Paiements tardifs intervenus pendant la période déclarative.
        for alloc in tr["allocations"]:
            if alloc["date"] > due and debut <= alloc["date"] <= fin:
                paye_hors_delai += alloc["montant"]
                sim = amende_indicative(alloc["montant"], due, alloc["date"])
                max_mois = max(max_mois, sim["mois"])
                if sim["amende"] is None:
                    penalite_calculable = False
                else:
                    penalite += _money(sim["amende"])
                dates_paiements.append(alloc["date"])
                if alloc.get("mode"): modes.append(str(alloc["mode"]))
                if alloc.get("reference"): refs.append(str(alloc["reference"]))

        # Solde encore impayé à la fin de la période.
        if tr["restant"] > ZERO and due < fin:
            non_paye += tr["restant"]
            sim = amende_indicative(tr["restant"], due, fin)
            max_mois = max(max_mois, sim["mois"])
            if sim["amende"] is None:
                penalite_calculable = False
            else:
                penalite += _money(sim["amende"])

    if paye_hors_delai <= ZERO and non_paye <= ZERO:
        return None

    livraison = _date_livraison_auto(db, facture)
    nature = _nature_operation(facture)
    manquants = []
    manquants.extend(diagnostics_ras)
    if not facture.reference: manquants.append("n° facture fournisseur")
    if not facture.tiers_if_snapshot: manquants.append("IF fournisseur")
    if not facture.tiers_ice_snapshot: manquants.append("ICE fournisseur")
    if not facture.tiers_rc_snapshot: manquants.append("RC fournisseur")
    if not facture.tiers_adresse_snapshot: manquants.append("adresse fournisseur")
    if not livraison: manquants.append("date livraison/service")
    if not nature: manquants.append("nature opération")

    return {
        "facture_id": facture.id,
        "numero_interne": facture.numero,
        "reference_facture": facture.reference,
        "date_facture": facture.date.isoformat() if facture.date else None,
        "date_livraison_service": livraison.isoformat() if livraison else None,
        "date_echeance": min((e["date"] for e in echeances), default=None).isoformat() if echeances else None,
        "fournisseur": facture.tiers,
        "fournisseur_adresse": facture.tiers_adresse_snapshot,
        "fournisseur_rc": facture.tiers_rc_snapshot,
        "fournisseur_if": facture.tiers_if_snapshot,
        "fournisseur_ice": facture.tiers_ice_snapshot,
        "nature_operation": nature,
        "montant_ttc": float(total_ttc),
        "montant_non_paye_fin_periode": float(non_paye.quantize(MONEY)),
        "montant_paye_hors_delai_periode": float(paye_hors_delai.quantize(MONEY)),
        "dates_paiements_hors_delai": sorted({d.isoformat() for d in dates_paiements}),
        "modes_paiement": sorted(set(modes)),
        "references_paiement": sorted(set(refs)),
        "mois_retard_max": max_mois,
        "amende_indicative": float(penalite.quantize(MONEY)) if penalite_calculable else None,
        "amende_calculable": penalite_calculable,
        "litige_judiciaire": bool(getattr(facture, "litige_judiciaire", False)),
        "reference_litige": getattr(facture, "reference_litige", None),
        "hors_champ": bool(getattr(facture, "delais_paiement_hors_champ", False)),
        "motif_hors_champ": getattr(facture, "delais_paiement_motif_hors_champ", None),
        "completude": {
            "complete": not manquants,
            "manquants": manquants,
        },
    }


def construire_rapport(db, societe_id: int, annee: int, trimestre: int) -> dict:
    debut, fin = bornes_trimestre(annee, trimestre)
    ex_ref, cloture = _dernier_exercice_reference(db, societe_id, debut)
    ca = _ca_comptable_ht(db, societe_id, ex_ref.annee) if ex_ref else ZERO
    assujetti = ca > SEUIL_ASSUJETTISSEMENT if ex_ref else None
    entree = _date_entree_dispositif(ca) if assujetti else None

    q = db.query(models.Facture).options(
        joinedload(models.Facture.lignes),
        joinedload(models.Facture.echeances),
    ).filter(
        models.Facture.societe_id == societe_id,
        models.Facture.type == "achat",
        models.Facture.est_validee == True,
        models.Facture.est_proforma == False,
        models.Facture.date <= fin,
    )
    if entree:
        q = q.filter(models.Facture.date >= entree)

    rows = []
    for facture in q.order_by(models.Facture.date.asc(), models.Facture.id.asc()).all():
        row = _row_facture(db, societe_id, facture, debut, fin)
        if row and not row["hors_champ"]:
            rows.append(row)

    total_non_paye = _money(sum(Decimal(str(r["montant_non_paye_fin_periode"])) for r in rows))
    total_paye_retard = _money(sum(Decimal(str(r["montant_paye_hors_delai_periode"])) for r in rows))
    amendes_connues = [Decimal(str(r["amende_indicative"])) for r in rows if r["amende_indicative"] is not None]
    total_amende = _money(sum(amendes_connues, ZERO)) if len(amendes_connues) == len(rows) else None
    incompletes = sum(1 for r in rows if not r["completude"]["complete"])

    avertissements = []
    if annee < 2026:
        avertissements.append("FACT-F est optimisé pour le régime trimestriel généralisé à partir de 2026 ; vérifiez les mesures transitoires des exercices antérieurs.")
    if ex_ref is None:
        avertissements.append("Aucun exercice antérieur n'a été trouvé : l'assujettissement au seuil de 2 M MAD HT doit être confirmé manuellement.")
    elif not cloture:
        avertissements.append(f"L'exercice de référence {ex_ref.annee} n'est pas clôturé : le CA HT est indicatif et l'assujettissement doit être confirmé.")
    if incompletes:
        avertissements.append(f"{incompletes} facture(s) à déclarer ont des informations manquantes dans l'état détaillé.")
    if any(r["amende_indicative"] is None for r in rows):
        avertissements.append("Certaines amendes n'ont pas pu être simulées faute de taux directeur historique embarqué pour la date concernée.")

    return {
        "annee": annee,
        "trimestre": trimestre,
        "date_debut": debut.isoformat(),
        "date_fin": fin.isoformat(),
        "cadre": {
            "loi": "69-21",
            "periodicite": "trimestrielle" if annee >= 2026 else "à vérifier selon régime transitoire",
            "seuil_ca_ht": float(SEUIL_ASSUJETTISSEMENT),
            "declaration_requise_meme_sans_retard": bool(assujetti) if assujetti is not None else None,
            "export": "préparatoire — à contrôler et viser avant dépôt DGI",
        },
        "assujettissement": {
            "exercice_reference": ex_ref.annee if ex_ref else None,
            "exercice_reference_cloture": cloture if ex_ref else None,
            "ca_ht_reference": float(ca),
            "assujetti": assujetti,
            "date_entree_dispositif": entree.isoformat() if entree else None,
        },
        "resume": {
            "nb_factures": len(rows),
            "nb_incompletes": incompletes,
            "montant_non_paye_fin_periode": float(total_non_paye),
            "montant_paye_hors_delai_periode": float(total_paye_retard),
            "amende_indicative": float(total_amende) if total_amende is not None else None,
        },
        "factures": rows,
        "avertissements": avertissements,
    }
