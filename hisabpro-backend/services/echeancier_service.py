from __future__ import annotations

from datetime import date, timedelta
from math import isfinite
from typing import Iterable, Optional

TOLERANCE = 0.02


def montant_echeance_fini(valeur) -> float:
    if isinstance(valeur, bool):
        raise ValueError("Le montant d'une échéance ne peut pas être un booléen.")
    try:
        montant = float(valeur)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Montant d'échéance invalide.") from exc
    if not isfinite(montant) or montant <= 0:
        raise ValueError("Chaque échéance doit avoir un montant fini strictement positif.")
    return montant


def tranche_age(jours: int) -> str:
    if jours <= 0:
        return "non_echu"
    if jours <= 30:
        return "1_30"
    if jours <= 60:
        return "31_60"
    if jours <= 90:
        return "61_90"
    return "plus_90"


def date_echeance_defaut(facture) -> date:
    if getattr(facture, "date_echeance", None):
        return facture.date_echeance
    delai = getattr(facture, "delai_paiement", None)
    delai = 60 if delai is None else int(delai)
    return facture.date + timedelta(days=max(delai, 0))


def normaliser_echeances(lignes: Iterable, total_ttc: float, date_facture: date) -> list[dict]:
    """Valide et normalise un échéancier contractuel.

    Les montants de l'échéancier représentent le TTC contractuel d'origine. Les
    règlements, avoirs, acomptes et la RAS sont ensuite imputés FIFO sur ces
    tranches, ce qui permet de conserver la structure contractuelle même après
    une réduction du solde.
    """
    rows = list(lignes or [])
    if not rows:
        raise ValueError("L'échéancier doit contenir au moins une échéance.")
    if len(rows) > 24:
        raise ValueError("Un échéancier ne peut pas contenir plus de 24 échéances.")

    normalisees = []
    total = 0.0
    for idx, row in enumerate(rows, start=1):
        d = row.get("date_echeance") if isinstance(row, dict) else getattr(row, "date_echeance", None)
        montant = row.get("montant") if isinstance(row, dict) else getattr(row, "montant", None)
        libelle = row.get("libelle") if isinstance(row, dict) else getattr(row, "libelle", None)
        if isinstance(d, str):
            try:
                d = date.fromisoformat(d[:10])
            except ValueError as exc:
                raise ValueError(f"Date d'échéance invalide à la ligne {idx}.") from exc
        if not d:
            raise ValueError(f"La date est obligatoire pour l'échéance {idx}.")
        if d < date_facture:
            raise ValueError("Une échéance ne peut pas être antérieure à la date de facture.")
        try:
            montant = round(montant_echeance_fini(montant), 2)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Montant invalide à l'échéance {idx}.") from exc
        if montant <= 0:
            raise ValueError("Chaque échéance doit avoir un montant strictement positif.")
        total += montant
        normalisees.append({
            "ordre": idx,
            "date_echeance": d,
            "montant": montant,
            "libelle": (str(libelle).strip()[:120] if libelle else None),
        })

    try:
        attendu = float(total_ttc or 0)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Le TTC contractuel doit être un montant fini.") from exc
    if isinstance(total_ttc, bool) or not isfinite(attendu):
        raise ValueError("Le TTC contractuel doit être un montant fini.")
    attendu = round(attendu, 2)
    if abs(round(total, 2) - attendu) > TOLERANCE:
        raise ValueError(
            f"Le total de l'échéancier ({total:.2f} MAD) doit être égal au TTC de la facture ({attendu:.2f} MAD)."
        )
    normalisees.sort(key=lambda x: (x["date_echeance"], x["ordre"]))
    for idx, row in enumerate(normalisees, start=1):
        row["ordre"] = idx
    return normalisees


def repartition_fifo(echeances: Iterable[dict], montant_impute: float, date_reference: Optional[date] = None) -> dict:
    """Affecte automatiquement le montant imputé aux échéances les plus anciennes."""
    date_reference = date_reference or date.today()
    restant_a_affecter = max(float(montant_impute or 0), 0.0)
    rows = []
    for raw in sorted(list(echeances or []), key=lambda x: (x["date_echeance"], x.get("ordre", 0))):
        montant = round(float(raw.get("montant") or 0), 2)
        impute = min(montant, restant_a_affecter)
        restant_a_affecter = max(restant_a_affecter - impute, 0.0)
        reste = max(montant - impute, 0.0)
        d = raw["date_echeance"]
        jours = (date_reference - d).days if reste > TOLERANCE and d < date_reference else 0
        if reste <= TOLERANCE:
            statut = "reglee"
        elif d < date_reference:
            statut = "en_retard_partiel" if impute > TOLERANCE else "en_retard"
        elif d == date_reference:
            statut = "echue_aujourdhui_partielle" if impute > TOLERANCE else "echue_aujourdhui"
        else:
            statut = "a_echoir_partielle" if impute > TOLERANCE else "a_echoir"
        rows.append({
            **raw,
            "montant": round(montant, 2),
            "impute": round(impute, 2),
            "reste_du": round(reste, 2),
            "jours_retard": max(jours, 0),
            "tranche_age": tranche_age(max(jours, 0)),
            "statut": statut,
        })

    ouvertes = [r for r in rows if r["reste_du"] > TOLERANCE]
    retard = [r for r in ouvertes if r["jours_retard"] > 0]
    prochaine = min(ouvertes, key=lambda x: (x["date_echeance"], x.get("ordre", 0)), default=None)
    return {
        "echeances": rows,
        "total_echeancier": round(sum(r["montant"] for r in rows), 2),
        "total_impute": round(min(float(montant_impute or 0), sum(r["montant"] for r in rows)), 2),
        "reste_du": round(sum(r["reste_du"] for r in rows), 2),
        "montant_en_retard": round(sum(r["reste_du"] for r in retard), 2),
        "nb_echeances": len(rows),
        "nb_ouvertes": len(ouvertes),
        "nb_retard": len(retard),
        "retard_max": max((r["jours_retard"] for r in retard), default=0),
        "prochaine_echeance": prochaine,
    }


def echeances_persistantes_ou_defaut(facture, total_ttc: float) -> list[dict]:
    persisted = list(getattr(facture, "echeances", None) or [])
    if persisted:
        return [
            {
                "id": e.id,
                "ordre": e.ordre,
                "date_echeance": e.date_echeance,
                "montant": float(e.montant or 0),
                "libelle": e.libelle,
            }
            for e in persisted
        ]
    return [{
        "id": None,
        "ordre": 1,
        "date_echeance": date_echeance_defaut(facture),
        "montant": round(float(total_ttc or 0), 2),
        "libelle": "Échéance unique",
    }]


def remplacer_echeancier_db(db, societe_id: int, facture, lignes: Iterable, total_ttc: float) -> list:
    """Remplace atomiquement les tranches persistées d'une facture."""
    import models
    normalisees = normaliser_echeances(lignes, total_ttc, facture.date)
    db.query(models.EcheanceFacture).filter_by(
        societe_id=societe_id, facture_id=facture.id
    ).delete(synchronize_session=False)
    objets = []
    for row in normalisees:
        obj = models.EcheanceFacture(
            societe_id=societe_id,
            facture_id=facture.id,
            ordre=row["ordre"],
            date_echeance=row["date_echeance"],
            montant=row["montant"],
            libelle=row["libelle"],
        )
        db.add(obj)
        objets.append(obj)
    # Compatibilité avec les écrans/PDF historiques : la date simple devient la
    # première échéance contractuelle. Le détail reste dans echeances_facture.
    if not bool(getattr(facture, "est_validee", False)):
        facture.date_echeance = normalisees[0]["date_echeance"]
    db.flush()
    return objets


def supprimer_echeancier_db(db, societe_id: int, facture) -> None:
    import models
    db.query(models.EcheanceFacture).filter_by(
        societe_id=societe_id, facture_id=facture.id
    ).delete(synchronize_session=False)
    db.flush()
