# -*- coding: utf-8 -*-
"""FACT.9 - préparation des données des documents commerciaux PDF.

Le module ne dessine rien. Il normalise uniquement l'identité du tiers et les
récapitulatifs TVA afin que Devis / BC / BL-BR / Factures / Avoirs utilisent les
mêmes règles de présentation.
"""
from __future__ import annotations

from decimal import Decimal
import json
from types import SimpleNamespace

from services.tva_service import D, ZERO, QUALIF_CLE_INTERNE, CLE_CONSIGNE

QUALIFICATION_LABELS = {
    "taxable": "Taxable",
    "exonere_droit_deduction": "Exonérée avec droit à déduction",
    "exonere_sans_deduction": "Exonérée sans droit à déduction",
    "hors_champ": "Hors champ TVA",
    "suspension": "Suspension de TVA",
}

QUALIFICATION_LABELS_COURTS = {
    "taxable": "",
    "exonere_droit_deduction": "Exon. avec DD",
    "exonere_sans_deduction": "Exon. sans DD",
    "hors_champ": "Hors champ",
    "suspension": "Suspension",
}

_CLE_QUALIF = {v: k for k, v in QUALIF_CLE_INTERNE.items()}


def _attr(obj, name, default=None):
    return getattr(obj, name, default) if obj is not None else default


def tiers_infos(db, models, societe_id: int, piece, *, facture_source=None) -> dict:
    """Retourne une identité de tiers prête à imprimer.

    Les snapshots d'une facture ont priorité pour préserver l'identité légale
    historique. Les coordonnées non figées (téléphone/e-mail) sont complétées
    depuis la fiche tiers lorsqu'elle existe encore.
    """
    tiers_id = _attr(piece, "tiers_id") or _attr(facture_source, "tiers_id")
    tiers = None
    if tiers_id:
        tiers = db.query(models.Tiers).filter_by(id=tiers_id, societe_id=societe_id).first()

    snap = {}
    raw_snap = _attr(piece, "tiers_snapshot_json")
    if raw_snap:
        try:
            snap = json.loads(raw_snap) if isinstance(raw_snap, str) else dict(raw_snap)
        except (TypeError, ValueError, json.JSONDecodeError):
            snap = {}

    nom = snap.get("nom") or _attr(piece, "tiers") or _attr(facture_source, "tiers") or _attr(tiers, "nom") or ""
    infos = {
        "nom": nom,
        "ice": snap.get("ice") or _attr(piece, "tiers_ice_snapshot") or _attr(facture_source, "tiers_ice_snapshot") or _attr(tiers, "ice"),
        "if": snap.get("if") or _attr(piece, "tiers_if_snapshot") or _attr(facture_source, "tiers_if_snapshot") or _attr(tiers, "identifiant_fiscal"),
        "rc": snap.get("rc") or _attr(piece, "tiers_rc_snapshot") or _attr(facture_source, "tiers_rc_snapshot") or _attr(tiers, "rc"),
        "adresse": snap.get("adresse") or _attr(piece, "tiers_adresse_snapshot") or _attr(facture_source, "tiers_adresse_snapshot") or _attr(tiers, "adresse"),
        "ville": snap.get("ville") or _attr(piece, "tiers_ville_snapshot") or _attr(facture_source, "tiers_ville_snapshot") or _attr(tiers, "ville"),
        "telephone": snap.get("telephone") or _attr(piece, "tiers_telephone_snapshot") or _attr(facture_source, "tiers_telephone_snapshot") or _attr(tiers, "telephone"),
        "email": snap.get("email") or _attr(piece, "tiers_email_snapshot") or _attr(facture_source, "tiers_email_snapshot") or _attr(tiers, "email"),
        "categorie_fiscale": snap.get("categorie_fiscale") or _attr(piece, "tiers_categorie_snapshot") or _attr(facture_source, "tiers_categorie_snapshot") or _attr(tiers, "categorie_fiscale"),
    }
    return infos


def societe_pour_document(societe, piece=None):
    """Retourne l'identité société figée sur une facture définitive.

    Les documents non définitifs et les anciens documents sans snapshot gardent
    un fallback sur la fiche société courante pour compatibilité.
    """
    raw = _attr(piece, "societe_snapshot_json")
    if raw:
        try:
            data = json.loads(raw) if isinstance(raw, str) else dict(raw)
            return SimpleNamespace(**data)
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    return societe


def resume_tva_depuis_lignes(lignes_pdf) -> list[dict]:
    """Récapitulatif TVA d'un document commercial sans frais de pied.

    ``total_ht`` doit déjà représenter le net commercial de la ligne.
    """
    groupes: dict[tuple[str, Decimal], dict] = {}
    for ligne in lignes_pdf or []:
        qualification = (ligne.get("qualification_tva") or "taxable").strip().lower()
        taux = D(ligne.get("tva") or 0) if qualification == "taxable" else ZERO
        cle = (qualification, taux)
        base = D(ligne.get("total_ht") or 0)
        tva = base * taux / D(100)
        g = groupes.setdefault(cle, {"base": ZERO, "tva": ZERO})
        g["base"] += base
        g["tva"] += tva

    out = []
    for (qualification, taux), vals in sorted(groupes.items(), key=lambda x: (x[0][0] != "taxable", x[0][1])):
        label = f"TVA {float(taux):g} %" if qualification == "taxable" else QUALIFICATION_LABELS.get(qualification, qualification)
        out.append({
            "label": label,
            "base": float(vals["base"]),
            "tva": float(vals["tva"]),
        })
    return out


def resume_tva_depuis_ventilation(ventilation: dict) -> list[dict]:
    """Transforme une ventilation TVA HisabPro en lignes lisibles de PDF."""
    out = []
    for cle, vals in sorted(ventilation.items(), key=lambda item: float(item[0])):
        cle_d = D(cle)
        if cle_d == CLE_CONSIGNE:
            label = "Emballage consigné - hors base TVA"
        elif cle_d < ZERO:
            q = _CLE_QUALIF.get(cle_d, "hors_champ")
            label = QUALIFICATION_LABELS.get(q, q)
        else:
            label = f"TVA {float(cle_d):g} %"
        out.append({
            "label": label,
            "base": float(D(vals.get("base"))),
            "tva": float(D(vals.get("tva"))),
        })
    return out


def mentions_tva_depuis_lignes(lignes_pdf) -> list[str]:
    """Mentions informatives pour les traitements TVA non taxables présents."""
    qualifications = []
    for l in lignes_pdf or []:
        q = (l.get("qualification_tva") or "taxable").strip().lower()
        if q != "taxable" and q not in qualifications:
            qualifications.append(q)
    return [QUALIFICATION_LABELS[q] for q in qualifications if q in QUALIFICATION_LABELS]


def conditions_paiement(delai_paiement, date_echeance=None, mode_reglement=None, reference_reglement=None) -> str:
    if delai_paiement is None:
        txt = "Selon conditions convenues"
    else:
        try:
            jours = int(delai_paiement)
        except (TypeError, ValueError):
            jours = 0
        if jours <= 0:
            txt = "Paiement comptant"
        else:
            txt = f"Paiement à {jours} jour{'s' if jours > 1 else ''}"
    if date_echeance:
        txt += f" - échéance au {date_echeance.day:02d}/{date_echeance.month:02d}/{date_echeance.year}"
    labels = {
        "virement": "virement", "cheque": "chèque", "especes": "espèces",
        "effet": "effet de commerce", "carte": "carte",
        "prelevement": "prélèvement", "autre": "autre moyen",
    }
    if mode_reglement:
        txt += f" - règlement prévu par {labels.get(str(mode_reglement), str(mode_reglement))}"
    if reference_reglement:
        txt += f" (réf. {reference_reglement})"
    return txt
