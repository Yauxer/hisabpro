from __future__ import annotations

from collections import defaultdict
import math
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional

from sqlalchemy.orm import Session, joinedload

from services.tva_service import ventilation_facture, ventilation_avoir, total_ventilation
from services.echeancier_service import echeances_persistantes_ou_defaut, repartition_fifo
from services.ras_paiement_service import lecture_ras_paiement

TOLERANCE = 0.01


def _enum_value(value):
    return getattr(value, "value", value)


def _totaux_facture(facture) -> tuple[float, float, float]:
    avant = total_ventilation(ventilation_facture(facture, appliquer_escompte=False))
    apres = total_ventilation(ventilation_facture(facture, appliquer_escompte=True))
    return float(avant["base"]), float(apres["tva"]), float(apres["ttc"])


def _echeance_facture(facture) -> Optional[date]:
    if getattr(facture, "date_echeance", None):
        return facture.date_echeance
    if getattr(facture, "date", None):
        delai = getattr(facture, "delai_paiement", None)
        delai = 60 if delai is None else int(delai)
        return facture.date + timedelta(days=delai)
    return None


def _tranche_age(jours_retard: int) -> str:
    if jours_retard <= 0:
        return "non_echu"
    if jours_retard <= 30:
        return "1_30"
    if jours_retard <= 60:
        return "31_60"
    if jours_retard <= 90:
        return "61_90"
    return "plus_90"


def _statuts(reste: float, total_effectif: float, echeance: Optional[date], date_reference: date) -> tuple[str, str, str, int]:
    if reste <= TOLERANCE:
        return "reglee", "reglee", "reglee", 0

    statut_paiement = "partiellement_reglee" if total_effectif > TOLERANCE else "non_reglee"
    if echeance is None:
        return statut_paiement, "sans_echeance", statut_paiement, 0

    delta = (date_reference - echeance).days
    if delta < 0:
        statut_echeance = "a_echoir"
        statut_global = "partiellement_reglee" if statut_paiement == "partiellement_reglee" else "a_echoir"
        jours_retard = 0
    elif delta == 0:
        statut_echeance = "echue"
        statut_global = "echue"
        jours_retard = 0
    else:
        statut_echeance = "en_retard"
        statut_global = "en_retard"
        jours_retard = delta
    return statut_paiement, statut_echeance, statut_global, jours_retard


def calculer_etat_facture(
    *,
    total_ttc: float,
    total_ht: float,
    total_regle: float = 0.0,
    total_avoirs: float = 0.0,
    total_acomptes: float = 0.0,
    taux_ras: float = 0.0,
    ras_comptabilisee: bool = False,
    montant_ras_capture: float = 0.0,
    echeance: Optional[date] = None,
    date_reference: Optional[date] = None,
) -> dict:
    """Calcul pur de la dette/créance restante d'une facture."""
    date_reference = date_reference or date.today()
    taux = float(taux_ras or 0)
    estime = float(total_ht or 0) * (taux / 100.0) if math.isfinite(taux) and 0 <= taux <= 100 else None
    ras = lecture_ras_paiement(estime, ras_comptabilisee, montant_ras_capture)
    montant_ras = ras['montant_ras_impute']
    if montant_ras is None:
        return {**ras, 'total_impute': None, 'reste_du': None, 'credit_tiers': None,
                'statut_paiement': 'indetermine', 'statut_echeance': 'indetermine',
                'statut': 'indetermine', 'jours_retard': 0, 'tranche_age': 'indetermine',
                'ras_anomalie': 'RAS historique invalide : calcul du solde indéterminable.'}
    total_effectif = float(total_regle or 0) + float(total_avoirs or 0) + float(total_acomptes or 0) + montant_ras
    brut = float(total_ttc or 0) - total_effectif
    reste = max(0.0, brut)
    credit_tiers = max(0.0, -brut)
    statut_paiement, statut_echeance, statut_global, jours_retard = _statuts(
        reste, total_effectif, echeance, date_reference
    )
    return {
        "montant_ras": round(montant_ras, 2),
        **ras,
        "total_impute": round(total_effectif, 2),
        "reste_du": round(reste, 2),
        "credit_tiers": round(credit_tiers, 2),
        "statut_paiement": statut_paiement,
        "statut_echeance": statut_echeance,
        "statut": statut_global,
        "jours_retard": jours_retard,
        "tranche_age": _tranche_age(jours_retard if statut_echeance == "en_retard" else 0),
    }


def construire_situation(
    db: Session,
    societe_id: int,
    exercice: int,
    date_reference: Optional[date] = None,
) -> dict:
    """Calcule une situation clients/fournisseurs exacte côté serveur.

    Le calcul est volontairement dérivé des pièces sources : règlements non rejetés,
    avoirs actifs, acomptes imputés et RAS. Aucun statut historique de facture n'est
    utilisé comme source de vérité pour le solde.
    """
    import models
    from services.ras_reglement_service import montant_actif

    date_reference = date_reference or date.today()

    factures = (
        db.query(models.Facture)
        .options(joinedload(models.Facture.lignes), joinedload(models.Facture.echeances))
        .filter(
            models.Facture.societe_id == societe_id,
            models.Facture.exercice == exercice,
            models.Facture.est_validee.is_(True),
            models.Facture.est_proforma.is_(False),
            models.Facture.statut != models.StatutFactureEnum.annulee,
        )
        .order_by(models.Facture.date.desc(), models.Facture.id.desc())
        .all()
    )

    ids = [f.id for f in factures]
    regle = defaultdict(float)
    acomptes = defaultdict(float)
    avoirs = defaultdict(float)
    relances = {}

    if ids:
        for r in db.query(models.Reglement).filter(
            models.Reglement.societe_id == societe_id,
            models.Reglement.facture_id.in_(ids),
            models.Reglement.statut.notin_(["rejete", "annule"]),
        ).all():
            regle[r.facture_id] += float(r.montant or 0)

        for a in db.query(models.ImputationAcompte).filter(
            models.ImputationAcompte.societe_id == societe_id,
            models.ImputationAcompte.facture_id.in_(ids),
            models.ImputationAcompte.statut == "active",
        ).all():
            acomptes[a.facture_id] += float(a.montant or 0)

        # FACT-G/H : un crédit d'avoir provenant d'une autre facture peut être
        # imputé sur la facture cible. Il réduit exactement son reste à payer.
        for u in db.query(models.UtilisationAvoir).filter(
            models.UtilisationAvoir.societe_id == societe_id,
            models.UtilisationAvoir.facture_id.in_(ids),
            models.UtilisationAvoir.type_utilisation == "imputation",
            models.UtilisationAvoir.statut == "active",
        ).all():
            avoirs[u.facture_id] += float(u.montant or 0)

        for av in db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter(
            models.Avoir.societe_id == societe_id,
            models.Avoir.facture_id.in_(ids),
            models.Avoir.statut != models.StatutAvoirEnum.annule,
        ).all():
            avoirs[av.facture_id] += float(
                total_ventilation(ventilation_avoir(av, appliquer_escompte=True))["ttc"]
            )

        # Dernière relance réellement effectuée, sans N+1.
        rows = db.query(models.RelanceRecouvrement).filter(
            models.RelanceRecouvrement.societe_id == societe_id,
            models.RelanceRecouvrement.facture_id.in_(ids),
            models.RelanceRecouvrement.statut != "annulee",
        ).order_by(
            models.RelanceRecouvrement.facture_id,
            models.RelanceRecouvrement.date_relance.desc(),
            models.RelanceRecouvrement.id.desc(),
        ).all()
        for row in rows:
            relances.setdefault(row.facture_id, row)

    tranches_vides = {"non_echu": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "plus_90": 0.0}
    blocs = {
        "vente": {
            "facture": 0.0, "regle": 0.0, "reste": 0.0, "en_retard": 0.0,
            "nb_ouvertes": 0, "nb_retard": 0, "tranches": dict(tranches_vides), "tiers": {},
        },
        "achat": {
            "facture": 0.0, "regle": 0.0, "reste": 0.0, "en_retard": 0.0,
            "nb_ouvertes": 0, "nb_retard": 0, "tranches": dict(tranches_vides), "tiers": {},
        },
    }

    lignes = []
    for f in factures:
        total_ht, total_tva, total_ttc = _totaux_facture(f)
        total_regle = regle[f.id]
        total_avoirs = avoirs[f.id]
        total_acomptes = acomptes[f.id]
        taux_ras = float(getattr(f, "ras_taux", 0) or 0)
        echeance = _echeance_facture(f)
        etat = calculer_etat_facture(
            total_ttc=total_ttc, total_ht=total_ht, total_regle=total_regle,
            total_avoirs=total_avoirs, total_acomptes=total_acomptes, taux_ras=taux_ras,
            ras_comptabilisee=getattr(f, 'ras_comptabilisee', False),
            montant_ras_capture=montant_actif(db, societe_id, f.id),
            echeance=echeance, date_reference=date_reference,
        )
        montant_ras = etat["montant_ras"]
        total_effectif = etat["total_impute"]
        reste = etat["reste_du"]
        credit_tiers = etat["credit_tiers"]
        statut_paiement = etat["statut_paiement"]
        if total_effectif is None:
            bloc = blocs[_enum_value(f.type)]
            bloc['calcul_incomplet'] = True
            lignes.append({**etat, 'id': f.id, 'numero': f.numero, 'type': _enum_value(f.type),
                'date': f.date, 'date_echeance': echeance, 'tiers': f.tiers, 'tiers_id': f.tiers_id,
                'total_ttc': total_ttc, 'total_regle': total_regle, 'total_avoirs': total_avoirs,
                'total_acomptes': total_acomptes, 'montant_en_retard': None, 'echeances': [],
                'prochaine_echeance': None, 'derniere_relance': None})
            continue

        # FACT.8 : les paiements/avoirs/acomptes/RAS sont affectés FIFO aux
        # échéances contractuelles. La balance âgée porte donc sur chaque tranche
        # restante et non plus sur une date unique de facture.
        ech_calc = repartition_fifo(
            echeances_persistantes_ou_defaut(f, total_ttc), total_effectif, date_reference
        )
        prochaine = ech_calc["prochaine_echeance"]
        jours_retard = ech_calc["retard_max"]
        if reste <= TOLERANCE:
            statut_echeance = "reglee"
            statut_global = "reglee"
        elif ech_calc["nb_retard"] > 0:
            statut_echeance = "en_retard"
            statut_global = "en_retard"
        elif prochaine and prochaine["date_echeance"] == date_reference:
            statut_echeance = "echue"
            statut_global = "echue"
        else:
            statut_echeance = "a_echoir"
            statut_global = "partiellement_reglee" if statut_paiement == "partiellement_reglee" else "a_echoir"
        tranche = next((e["tranche_age"] for e in ech_calc["echeances"] if e["reste_du"] > TOLERANCE and e["jours_retard"] > 0), "non_echu")
        echeance = prochaine["date_echeance"] if prochaine else _echeance_facture(f)
        type_value = _enum_value(f.type)
        bloc = blocs[type_value]
        bloc["facture"] += total_ttc
        bloc["regle"] += min(total_effectif, total_ttc)

        dernier = relances.get(f.id)
        ligne = {
            "id": f.id,
            "numero": f.numero,
            "type": type_value,
            "date": f.date,
            "date_echeance": echeance,
            "tiers": f.tiers,
            "tiers_id": f.tiers_id,
            "total_ttc": round(total_ttc, 2),
            "total_regle": round(total_regle, 2),
            "total_avoirs": round(total_avoirs, 2),
            "total_acomptes": round(total_acomptes, 2),
            "montant_ras": round(montant_ras, 2),
            "montant_ras_estime": etat['montant_ras_estime'],
            "montant_ras_impute": etat['montant_ras_impute'],
            "ras_origine": etat['ras_origine'],
            "total_impute": round(total_effectif, 2),
            "reste_du": round(reste, 2),
            "credit_tiers": round(credit_tiers, 2),
            "statut_paiement": statut_paiement,
            "statut_echeance": statut_echeance,
            "statut": statut_global,
            "jours_retard": jours_retard,
            "tranche_age": tranche,
            "montant_en_retard": ech_calc["montant_en_retard"],
            "echeances": ech_calc["echeances"],
            "prochaine_echeance": prochaine,
            "derniere_relance": None if not dernier else {
                "id": dernier.id,
                "niveau": dernier.niveau,
                "date_relance": dernier.date_relance,
                "canal": dernier.canal,
                "prochaine_relance": dernier.prochaine_relance,
                "date_promesse_reglement": dernier.date_promesse_reglement,
                "montant_promis": float(dernier.montant_promis or 0) if dernier.montant_promis is not None else None,
            },
        }
        if reste > TOLERANCE:
            lignes.append(ligne)
            bloc["reste"] += reste
            bloc["nb_ouvertes"] += 1
            for ech in ech_calc["echeances"]:
                if ech["reste_du"] > TOLERANCE:
                    bloc["tranches"][ech["tranche_age"]] += ech["reste_du"]
            if ech_calc["montant_en_retard"] > TOLERANCE:
                bloc["en_retard"] += ech_calc["montant_en_retard"]
                bloc["nb_retard"] += 1

            cle_tiers = f.tiers_id or f"nom:{f.tiers}"
            if cle_tiers not in bloc["tiers"]:
                bloc["tiers"][cle_tiers] = {
                    "tiers_id": f.tiers_id,
                    "tiers": f.tiers,
                    "montant": 0.0,
                    "nb_factures": 0,
                    "retard_max": 0,
                    "tranches": dict(tranches_vides),
                }
            t = bloc["tiers"][cle_tiers]
            t["montant"] += reste
            t["nb_factures"] += 1
            t["retard_max"] = max(t["retard_max"], jours_retard)
            for ech in ech_calc["echeances"]:
                if ech["reste_du"] > TOLERANCE:
                    t["tranches"][ech["tranche_age"]] += ech["reste_du"]

    for bloc in blocs.values():
        bloc["taux_reglement"] = round((bloc["regle"] / bloc["facture"] * 100), 2) if bloc["facture"] > TOLERANCE else 0.0
        bloc["tiers"] = sorted(bloc["tiers"].values(), key=lambda x: x["montant"], reverse=True)
        for t in bloc["tiers"]:
            t["montant"] = round(t["montant"], 2)
            t["tranches"] = {k: round(v, 2) for k, v in t["tranches"].items()}
        for key in ("facture", "regle", "reste", "en_retard"):
            bloc[key] = round(bloc[key], 2)
        bloc["tranches"] = {k: round(v, 2) for k, v in bloc["tranches"].items()}
        if bloc.get('calcul_incomplet'):
            for key in ('facture', 'regle', 'reste', 'en_retard', 'taux_reglement', 'nb_ouvertes', 'nb_retard'):
                bloc[key] = None
            bloc['tranches'] = {k: None for k in bloc['tranches']}
            bloc['tiers'] = []

    # Effets/chèques encore en circulation — période réelle de l'exercice si elle existe.
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=exercice).first()
    debut_ex = ex.date_debut if ex else date(exercice, 1, 1)
    fin_ex = ex.date_fin if ex else date(exercice, 12, 31)
    effets_rows = db.query(models.Reglement).filter(
        models.Reglement.societe_id == societe_id,
        models.Reglement.date >= debut_ex,
        models.Reglement.date <= fin_ex,
        models.Reglement.statut.in_(["portefeuille", "encaissement", "a_payer"]),
    ).all()
    effets = {
        "portefeuille": round(sum(float(r.montant or 0) for r in effets_rows if r.statut == "portefeuille"), 2),
        "encaissement": round(sum(float(r.montant or 0) for r in effets_rows if r.statut == "encaissement"), 2),
        "a_payer": round(sum(float(r.montant or 0) for r in effets_rows if r.statut == "a_payer"), 2),
        "echus": sum(1 for r in effets_rows if r.date_echeance and r.date_echeance <= date_reference),
    }

    lignes.sort(key=lambda x: (
        0 if x["statut_echeance"] == "en_retard" else 1,
        -x["jours_retard"],
        x["date_echeance"] or date.max,
        x["id"],
    ))

    return {
        "exercice": exercice,
        "date_reference": date_reference,
        "resume": {
            "vente": blocs["vente"],
            "achat": blocs["achat"],
            "position_nette": None if any(b.get('calcul_incomplet') for b in blocs.values()) else round(blocs["vente"]["reste"] - blocs["achat"]["reste"], 2),
        },
        "factures": lignes,
        "effets": effets,
    }
