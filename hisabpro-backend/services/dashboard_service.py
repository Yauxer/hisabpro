from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Dict

from sqlalchemy.orm import Session, joinedload

from services.tva_service import ventilation_facture, ventilation_avoir, total_ventilation
from services.recouvrement_service import construire_situation


def _enum_value(value):
    return getattr(value, "value", value)


def _f(value) -> float:
    return float(value or 0)


def _net_ligne(ligne) -> float:
    q = _f(getattr(ligne, "quantite", 0))
    pu = _f(getattr(ligne, "prix_unitaire", 0))
    r1 = _f(getattr(ligne, "remise", 0)) / 100.0
    r2 = _f(getattr(ligne, "remise2", 0)) / 100.0
    rabais = _f(getattr(ligne, "rabais", 0))
    return max(q * pu * (1 - r1) * (1 - r2) - rabais * q, 0.0)


def _coef_pied(facture) -> float:
    return (
        (1 - _f(getattr(facture, "remise_globale", 0)) / 100.0)
        * (1 - _f(getattr(facture, "ristourne", 0)) / 100.0)
        * (1 - _f(getattr(facture, "escompte", 0)) / 100.0)
    )


def _totaux_facture(facture) -> tuple[float, float]:
    total = total_ventilation(ventilation_facture(facture, appliquer_escompte=True))
    return float(total["base"]), float(total["ttc"])


def _totaux_avoir(avoir) -> tuple[float, float]:
    total = total_ventilation(ventilation_avoir(avoir, appliquer_escompte=True))
    return float(total["base"]), float(total["ttc"])


def _article_cout(article) -> float:
    if article is None:
        return 0.0
    # Pour le pilotage, le coût de référence est explicite et volontairement
    # présenté comme une estimation : CMUP courant si l'article est stockable,
    # sinon prix d'achat paramétré.
    if bool(getattr(article, "is_stockable", False)) and _f(getattr(article, "cmup", 0)) > 0:
        return _f(article.cmup)
    return _f(getattr(article, "prix_achat_ht", 0))


def construire_dashboard_commercial(
    db: Session,
    societe_id: int,
    exercice: int,
    date_reference: date | None = None,
) -> dict:
    import models

    date_reference = date_reference or date.today()

    factures = (
        db.query(models.Facture)
        .options(joinedload(models.Facture.lignes))
        .filter(
            models.Facture.societe_id == societe_id,
            models.Facture.exercice == exercice,
            models.Facture.est_validee.is_(True),
            models.Facture.est_proforma.is_(False),
            models.Facture.statut != models.StatutFactureEnum.annulee,
        )
        .all()
    )
    facture_ids = [f.id for f in factures]

    avoirs = []
    if facture_ids:
        avoirs = (
            db.query(models.Avoir)
            .options(joinedload(models.Avoir.lignes))
            .filter(
                models.Avoir.societe_id == societe_id,
                models.Avoir.facture_id.in_(facture_ids),
                models.Avoir.statut != models.StatutAvoirEnum.annule,
            )
            .all()
        )

    articles = {
        a.id: a
        for a in db.query(models.Article).filter(models.Article.societe_id == societe_id).all()
    }

    # Structures de synthèse.
    mois = {
        m: {
            "mois": m,
            "ventes_ht": 0.0,
            "ventes_ttc": 0.0,
            "achats_ht": 0.0,
            "achats_ttc": 0.0,
        }
        for m in range(1, 13)
    }
    clients: Dict[object, dict] = {}
    fournisseurs: Dict[object, dict] = {}
    articles_ca: Dict[object, dict] = {}

    ventes_ht = ventes_ttc = achats_ht = achats_ttc = 0.0
    nb_ventes = nb_achats = 0
    marge_estimee = 0.0

    facture_par_id = {f.id: f for f in factures}

    for f in factures:
        typ = _enum_value(f.type)
        ht, ttc = _totaux_facture(f)
        m = f.date.month if f.date else None
        cle_tiers = f.tiers_id or f"nom:{f.tiers}"
        if typ == "vente":
            ventes_ht += ht
            ventes_ttc += ttc
            nb_ventes += 1
            if m:
                mois[m]["ventes_ht"] += ht
                mois[m]["ventes_ttc"] += ttc
            row = clients.setdefault(cle_tiers, {
                "tiers_id": f.tiers_id, "tiers": f.tiers, "ca_ht": 0.0, "ca_ttc": 0.0, "nb_factures": 0,
            })
            row["ca_ht"] += ht; row["ca_ttc"] += ttc; row["nb_factures"] += 1
        elif typ == "achat":
            achats_ht += ht
            achats_ttc += ttc
            nb_achats += 1
            if m:
                mois[m]["achats_ht"] += ht
                mois[m]["achats_ttc"] += ttc
            row = fournisseurs.setdefault(cle_tiers, {
                "tiers_id": f.tiers_id, "tiers": f.tiers, "achats_ht": 0.0, "achats_ttc": 0.0, "nb_factures": 0,
            })
            row["achats_ht"] += ht; row["achats_ttc"] += ttc; row["nb_factures"] += 1

        # Ventilation articles nette des remises de pied de facture.
        coef = _coef_pied(f)
        for l in f.lignes or []:
            net = _net_ligne(l) * coef
            if typ == "vente":
                key = l.article_id or f"desc:{(l.description or '').strip().lower()}"
                item = articles_ca.setdefault(key, {
                    "article_id": l.article_id,
                    "designation": l.description or "Sans désignation",
                    "quantite": 0.0,
                    "ca_ht": 0.0,
                    "cout_estime": 0.0,
                })
                item["quantite"] += _f(l.quantite)
                item["ca_ht"] += net
                cout = _article_cout(articles.get(l.article_id)) * _f(l.quantite)
                item["cout_estime"] += cout
                marge_estimee += net - cout

    # Les avoirs actifs diminuent les montants commerciaux et la marge estimée.
    for av in avoirs:
        f = facture_par_id.get(av.facture_id)
        if f is None:
            continue
        typ = _enum_value(f.type)
        ht, ttc = _totaux_avoir(av)
        m = av.date.month if av.date else None
        cle_tiers = f.tiers_id or f"nom:{f.tiers}"
        if typ == "vente":
            ventes_ht -= ht; ventes_ttc -= ttc
            if m:
                mois[m]["ventes_ht"] -= ht; mois[m]["ventes_ttc"] -= ttc
            row = clients.get(cle_tiers)
            if row:
                row["ca_ht"] -= ht; row["ca_ttc"] -= ttc
        elif typ == "achat":
            achats_ht -= ht; achats_ttc -= ttc
            if m:
                mois[m]["achats_ht"] -= ht; mois[m]["achats_ttc"] -= ttc
            row = fournisseurs.get(cle_tiers)
            if row:
                row["achats_ht"] -= ht; row["achats_ttc"] -= ttc

        if typ == "vente":
            # L'avoir reprend les réductions de pied via ses snapshots.
            coef = (
                (1 - _f(getattr(av, "remise_globale_snapshot", 0)) / 100.0)
                * (1 - _f(getattr(av, "ristourne_snapshot", 0)) / 100.0)
                * (1 - _f(getattr(av, "escompte_snapshot", 0)) / 100.0)
            )
            for l in av.lignes or []:
                net = _net_ligne(l) * coef
                key = l.article_id or f"desc:{(l.description or '').strip().lower()}"
                item = articles_ca.setdefault(key, {
                    "article_id": l.article_id,
                    "designation": l.description or "Sans désignation",
                    "quantite": 0.0,
                    "ca_ht": 0.0,
                    "cout_estime": 0.0,
                })
                item["quantite"] -= _f(l.quantite)
                item["ca_ht"] -= net
                cout = _article_cout(articles.get(l.article_id)) * _f(l.quantite)
                item["cout_estime"] -= cout
                marge_estimee -= net - cout

    ventes_ht = max(ventes_ht, 0.0)
    ventes_ttc = max(ventes_ttc, 0.0)
    achats_ht = max(achats_ht, 0.0)
    achats_ttc = max(achats_ttc, 0.0)

    situation = construire_situation(db, societe_id, exercice, date_reference=date_reference)
    resume_vente = situation.get("resume", {}).get("vente", {})
    resume_achat = situation.get("resume", {}).get("achat", {})

    # Enrichissement tiers avec encours / retard issus du moteur de recouvrement.
    encours_client = {r.get("tiers_id") or f"nom:{r.get('tiers')}": r for r in resume_vente.get("tiers", [])}
    encours_fourn = {r.get("tiers_id") or f"nom:{r.get('tiers')}": r for r in resume_achat.get("tiers", [])}
    for key, row in clients.items():
        s = encours_client.get(key, {})
        row["encours"] = None if resume_vente.get('calcul_incomplet') else _f(s.get("montant"))
        row["retard_max"] = None if resume_vente.get('calcul_incomplet') else int(s.get("retard_max") or 0)
        if resume_vente.get('calcul_incomplet'):
            row['encours_anomalie'] = 'Encours clients indéterminable : consulter les diagnostics RAS.'
    for key, row in fournisseurs.items():
        s = encours_fourn.get(key, {})
        row["encours"] = None if resume_achat.get('calcul_incomplet') else _f(s.get("montant"))
        row["retard_max"] = None if resume_achat.get('calcul_incomplet') else int(s.get("retard_max") or 0)
        if resume_achat.get('calcul_incomplet'):
            row['encours_anomalie'] = 'Encours fournisseurs indéterminable : consulter les diagnostics RAS.'

    top_clients = sorted(clients.values(), key=lambda x: x["ca_ht"], reverse=True)[:10]
    top_fournisseurs = sorted(fournisseurs.values(), key=lambda x: x["achats_ht"], reverse=True)[:10]
    top_articles = sorted(
        [x for x in articles_ca.values() if x["ca_ht"] > 0.005],
        key=lambda x: x["ca_ht"], reverse=True,
    )[:10]

    total_articles_ca = sum(x["ca_ht"] for x in articles_ca.values() if x["ca_ht"] > 0)
    for x in top_articles:
        x["marge_estimee"] = x["ca_ht"] - x["cout_estime"]
        x["taux_marge_estime"] = (x["marge_estimee"] / x["ca_ht"] * 100) if x["ca_ht"] else 0.0
        x["part_ca"] = (x["ca_ht"] / total_articles_ca * 100) if total_articles_ca else 0.0

    # Pipeline devis : le ratio se base sur les devis effectivement transformés
    # en BC ou facture, pas sur un simple libellé de statut côté UI.
    devis = (
        db.query(models.Devis)
        .options(joinedload(models.Devis.bons_commande), joinedload(models.Devis.lignes))
        .filter(models.Devis.societe_id == societe_id, models.Devis.exercice == exercice)
        .all()
    )
    nb_devis = len(devis)
    nb_convertis = sum(1 for d in devis if d.facture_id or bool(d.bons_commande))
    valeur_devis = sum(sum(_f(l.quantite) * _f(l.prix_unitaire) for l in d.lignes or []) for d in devis)
    valeur_convertie = sum(
        sum(_f(l.quantite) * _f(l.prix_unitaire) for l in d.lignes or [])
        for d in devis if d.facture_id or bool(d.bons_commande)
    )

    # Arrondis de sortie homogènes.
    def money(v): return round(float(v or 0), 2)
    for row in mois.values():
        for k in ("ventes_ht", "ventes_ttc", "achats_ht", "achats_ttc"):
            row[k] = money(row[k])
    for rows, fields in (
        (top_clients, ("ca_ht", "ca_ttc", "encours")),
        (top_fournisseurs, ("achats_ht", "achats_ttc", "encours")),
        (top_articles, ("quantite", "ca_ht", "cout_estime", "marge_estimee", "taux_marge_estime", "part_ca")),
    ):
        for row in rows:
            for field in fields:
                if field != 'encours' or row.get(field) is not None:
                    row[field] = money(row.get(field))

    taux_marge = (marge_estimee / ventes_ht * 100) if ventes_ht else 0.0
    return {
        "exercice": exercice,
        "date_reference": date_reference,
        "resume": {
            "ca_ht": money(ventes_ht),
            "ventes_ttc": money(ventes_ttc),
            "achats_ht": money(achats_ht),
            "achats_ttc": money(achats_ttc),
            "nb_factures_vente": nb_ventes,
            "nb_factures_achat": nb_achats,
            "panier_moyen_ht": money(ventes_ht / nb_ventes if nb_ventes else 0),
            "marge_estimee": money(marge_estimee),
            "taux_marge_estime": money(taux_marge),
            "encours_clients": None if resume_vente.get('calcul_incomplet') else money(resume_vente.get("reste")),
            "retard_clients": None if resume_vente.get('calcul_incomplet') else money(resume_vente.get("en_retard")),
            "encours_fournisseurs": None if resume_achat.get('calcul_incomplet') else money(resume_achat.get("reste")),
            "retard_fournisseurs": None if resume_achat.get('calcul_incomplet') else money(resume_achat.get("en_retard")),
            "taux_recouvrement_clients": None if resume_vente.get('calcul_incomplet') else money(resume_vente.get("taux_reglement")),
            "nb_clients_en_retard": None if resume_vente.get('calcul_incomplet') else int(resume_vente.get("nb_retard") or 0),
            "calcul_incomplet_clients": bool(resume_vente.get('calcul_incomplet')),
            "calcul_incomplet_fournisseurs": bool(resume_achat.get('calcul_incomplet')),
        },
        "mensuel": list(mois.values()),
        "top_clients": top_clients,
        "top_fournisseurs": top_fournisseurs,
        "top_articles": top_articles,
        "diagnostics_ras": [{k: row.get(k) for k in ('id', 'numero', 'type', 'ras_anomalie')}
                            for row in situation.get('factures', []) if row.get('ras_anomalie')],
        "pipeline": {
            "nb_devis": nb_devis,
            "nb_convertis": nb_convertis,
            "taux_conversion": money(nb_convertis / nb_devis * 100 if nb_devis else 0),
            "valeur_devis_ht": money(valeur_devis),
            "valeur_convertie_ht": money(valeur_convertie),
        },
        "methodologie": {
            "marge": "Estimation par ligne : CA net HT moins CMUP courant des articles stockables, sinon prix d'achat HT paramétré. Les services sans coût paramétré ont un coût estimé nul.",
            "encours": "Calcul FACT.7/8 : règlements, avoirs, acomptes, RAS et échéanciers pris en compte.",
        },
    }
