# -*- coding: utf-8 -*-
"""COMPTA.1 — résolution centralisée des comptes issus des formulaires métier.

Priorité des comptes :
- tiers : snapshot facture/acompte -> fiche tiers -> compte CGNC par défaut ;
- vente/achat : snapshot ligne -> surcharge article -> famille -> compte par défaut ;
- trésorerie : caisse -> 5161 ; banque sélectionnée -> compte bancaire paramétré -> 5141.

Les fonctions de regroupement garantissent un total au centime égal au montant
comptable cible afin de ne jamais déséquilibrer une écriture à cause des arrondis.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from sqlalchemy.orm import joinedload

from services.tva_service import D, HUNDRED, ZERO, money

DEFAULT_CLIENT = "3421"
DEFAULT_FOURNISSEUR = "4411"
DEFAULT_VENTE = "7111"
DEFAULT_ACHAT = "6111"
DEFAULT_BANQUE = "5141"
DEFAULT_CAISSE = "5161"


def _clean(value, default=None):
    value = str(value or "").strip()
    return value or default


def _type_value(value):
    return getattr(value, "value", value)


def _tiers_compatible(tiers, est_vente: bool) -> bool:
    if not tiers:
        return False
    attendu = "client" if est_vente else "fournisseur"
    return getattr(tiers, "type", None) in {attendu, "les_deux"}


def trouver_tiers(db, societe_id: int, *, tiers_id=None, nom=None, est_vente=True):
    """Résolution non ambiguë d'un tiers dans la société courante."""
    import models
    if tiers_id:
        tiers = db.query(models.Tiers).filter_by(
            id=tiers_id, societe_id=societe_id, actif=True
        ).first()
        return tiers if _tiers_compatible(tiers, est_vente) else None
    if not nom:
        return None
    candidats = db.query(models.Tiers).filter(
        models.Tiers.societe_id == societe_id,
        models.Tiers.actif == True,
        models.Tiers.nom.ilike(str(nom).strip()),
    ).all()
    compatibles = [t for t in candidats if _tiers_compatible(t, est_vente)]
    return compatibles[0] if len(compatibles) == 1 else None


def compte_tiers(db, societe_id: int, *, est_vente: bool, tiers_id=None, nom=None, snapshot=None):
    if _clean(snapshot):
        return _clean(snapshot)
    tiers = trouver_tiers(
        db, societe_id, tiers_id=tiers_id, nom=nom, est_vente=est_vente
    )
    if tiers:
        champ = "compte_client" if est_vente else "compte_fournisseur"
        return _clean(getattr(tiers, champ, None), DEFAULT_CLIENT if est_vente else DEFAULT_FOURNISSEUR)
    return DEFAULT_CLIENT if est_vente else DEFAULT_FOURNISSEUR


def compte_tiers_facture(db, societe_id: int, facture):
    est_vente = _type_value(getattr(facture, "type", None)) == "vente"
    return compte_tiers(
        db,
        societe_id,
        est_vente=est_vente,
        tiers_id=getattr(facture, "tiers_id", None),
        nom=getattr(facture, "tiers", None),
        snapshot=getattr(facture, "compte_tiers_snapshot", None),
    )


def _article_avec_famille(db, societe_id: int, article_id):
    import models
    if not article_id:
        return None
    return db.query(models.Article).options(joinedload(models.Article.famille)).filter_by(
        id=article_id, societe_id=societe_id
    ).first()


def compte_article(db, societe_id: int, article_id, *, est_vente: bool):
    article = _article_avec_famille(db, societe_id, article_id)
    if not article:
        return DEFAULT_VENTE if est_vente else DEFAULT_ACHAT
    champ = "compte_vente" if est_vente else "compte_achat"
    override = _clean(getattr(article, champ, None))
    if override:
        return override
    famille = getattr(article, "famille", None)
    compte_famille = _clean(getattr(famille, champ, None)) if famille else None
    return compte_famille or (DEFAULT_VENTE if est_vente else DEFAULT_ACHAT)


def figer_comptes_facture(db, societe_id: int, facture):
    """Fige les comptes applicables au moment de la validation."""
    est_vente = _type_value(getattr(facture, "type", None)) == "vente"
    facture.compte_tiers_snapshot = compte_tiers(
        db,
        societe_id,
        est_vente=est_vente,
        tiers_id=getattr(facture, "tiers_id", None),
        nom=getattr(facture, "tiers", None),
        snapshot=getattr(facture, "compte_tiers_snapshot", None),
    )
    for ligne in getattr(facture, "lignes", []) or []:
        if not _clean(getattr(ligne, "compte_vente_snapshot", None)):
            ligne.compte_vente_snapshot = compte_article(
                db, societe_id, getattr(ligne, "article_id", None), est_vente=True
            )
        if not _clean(getattr(ligne, "compte_achat_snapshot", None)):
            ligne.compte_achat_snapshot = compte_article(
                db, societe_id, getattr(ligne, "article_id", None), est_vente=False
            )


def compte_ligne_facture(db, societe_id: int, ligne, *, est_vente: bool):
    champ_snapshot = "compte_vente_snapshot" if est_vente else "compte_achat_snapshot"
    snapshot = _clean(getattr(ligne, champ_snapshot, None))
    if snapshot:
        return snapshot
    return compte_article(db, societe_id, getattr(ligne, "article_id", None), est_vente=est_vente)


def compte_tresorerie(db, societe_id: int, *, mode=None, banque=None):
    import models
    mode = str(mode or "").lower()
    if mode == "especes":
        return DEFAULT_CAISSE

    banque = str(banque or "").strip()
    q = db.query(models.CompteBancaire).filter_by(societe_id=societe_id, actif=True)
    if banque:
        comptes = q.filter(models.CompteBancaire.banque.ilike(banque)).all()
        if len(comptes) == 1:
            return _clean(comptes[0].compte_comptable, DEFAULT_BANQUE)
    else:
        comptes = q.all()
        if len(comptes) == 1:
            return _clean(comptes[0].compte_comptable, DEFAULT_BANQUE)
    return DEFAULT_BANQUE


def _net_ligne(ligne) -> Decimal:
    qte = D(getattr(ligne, "quantite", 0))
    pu = D(getattr(ligne, "prix_unitaire", 0))
    remise1 = D(getattr(ligne, "remise", 0)) / HUNDRED
    remise2 = D(getattr(ligne, "remise2", 0)) / HUNDRED
    rabais = D(getattr(ligne, "rabais", 0))
    net = qte * pu * (D(1) - remise1) * (D(1) - remise2) - rabais * qte
    return max(net, ZERO)


def _ajuster_groupes(groupes_raw: dict, cible) -> dict[str, Decimal]:
    """Arrondit les groupes et affecte l'écart final au groupe principal."""
    cible = money(cible)
    if not groupes_raw:
        return {}
    groupes = {compte: money(montant) for compte, montant in groupes_raw.items() if D(montant) != ZERO}
    if not groupes:
        return {}
    ecart = money(cible - sum(groupes.values(), ZERO))
    if ecart:
        principal = max(groupes, key=lambda c: abs(groupes[c]))
        groupes[principal] = money(groupes[principal] + ecart)
    return {c: m for c, m in groupes.items() if m != ZERO}


def groupes_facture_par_compte(db, societe_id: int, facture, *, est_vente: bool, cible) -> dict[str, Decimal]:
    coef = (D(1) - D(getattr(facture, "remise_globale", 0)) / HUNDRED) * (
        D(1) - D(getattr(facture, "ristourne", 0)) / HUNDRED
    )
    groupes = defaultdict(lambda: ZERO)
    for ligne in getattr(facture, "lignes", []) or []:
        compte = compte_ligne_facture(db, societe_id, ligne, est_vente=est_vente)
        groupes[compte] += _net_ligne(ligne) * coef
    return _ajuster_groupes(groupes, cible)


def groupes_avoir_par_compte(db, societe_id: int, avoir, facture, *, est_vente: bool, cible) -> dict[str, Decimal]:
    coef = (D(1) - D(getattr(avoir, "remise_globale_snapshot", 0)) / HUNDRED) * (
        D(1) - D(getattr(avoir, "ristourne_snapshot", 0)) / HUNDRED
    )
    sources = {l.id: l for l in getattr(facture, "lignes", []) or []}
    groupes = defaultdict(lambda: ZERO)
    for ligne in getattr(avoir, "lignes", []) or []:
        source = sources.get(getattr(ligne, "facture_ligne_id", None))
        if source is not None:
            compte = compte_ligne_facture(db, societe_id, source, est_vente=est_vente)
        else:
            compte = compte_article(db, societe_id, getattr(ligne, "article_id", None), est_vente=est_vente)
        groupes[compte] += _net_ligne(ligne) * coef
    return _ajuster_groupes(groupes, cible)


def repartir_par_poids(montant, poids: dict[str, Decimal]) -> dict[str, Decimal]:
    """Répartit un montant au centime selon les poids, avec total exact."""
    montant = money(montant)
    poids = {c: max(D(v), ZERO) for c, v in poids.items() if D(v) > ZERO}
    total = sum(poids.values(), ZERO)
    if montant == ZERO or total == ZERO:
        return {}
    bruts = {c: montant * v / total for c, v in poids.items()}
    return _ajuster_groupes(bruts, montant)
