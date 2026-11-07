# -*- coding: utf-8 -*-
"""Audit du grand livre de stock et du CMUP.

Patch 06B est volontairement en lecture seule : il contrôle la continuité des
mouvements déjà enregistrés sans réécrire l'historique. Les corrections seront
faites dans une étape séparée après diagnostic sur les vraies données.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, localcontext, InvalidOperation
import math
from services.inventaire_nombres_service import somme

CENT = Decimal("0.01")
Q4 = Decimal("0.0001")


def _d(v) -> Decimal:
    return Decimal(str(v))


def _q(v) -> Decimal:
    return _d(v).quantize(Q4, rounding=ROUND_HALF_UP)


def _m(v) -> Decimal:
    return _d(v).quantize(CENT, rounding=ROUND_HALF_UP)


def _close(a: Decimal, b: Decimal, tol: Decimal = Q4) -> bool:
    return abs(a - b) <= tol


def _anomalie(code: str, message: str, niveau: str = "erreur", mouvement_id=None):
    return {
        "code": code,
        "message": message,
        "niveau": niveau,
        "mouvement_id": mouvement_id,
    }


def auditer_mouvements_article(article, mouvements):
    # Les calculs intermédiaires doivent accepter les grands nombres finis ;
    # la représentation JSON est contrôlée séparément avant exposition.
    with localcontext() as ctx:
        ctx.prec = 1000
        return _auditer_mouvements_article(article, mouvements)


def _auditer_mouvements_article(article, mouvements):
    """Contrôle un article à partir de la chaîne de mouvements enregistrée.

    On ne suppose pas que le premier mouvement commence à zéro : le stock_avant
    du premier mouvement peut représenter un solde historique antérieur au suivi
    détaillé HisabPro. En revanche, chaque mouvement suivant doit repartir du
    stock_apres du précédent.
    """
    anomalies = []
    mouvements = list(mouvements or [])
    prev_stock = None
    prev_cmup = None
    diagnostics = []

    def inconnu(champ, mid=None, message=None):
        detail = message or 'Nombre historique absent, non fini ou invalide : à vérifier.'
        diagnostics.append({'champ': champ, 'mouvement_id': mid, 'message': detail})
        anomalies.append(_anomalie('nombre_indeterminable',
            f"{'Mouvement #' + str(mid) if mid is not None else 'Fiche article'}: {champ} — {detail}",
            niveau='warning', mouvement_id=mid))

    def lire(value, champ, mid=None):
        try:
            if value is None or isinstance(value, bool):
                raise ValueError
            d = _d(value)
            if not d.is_finite() or not math.isfinite(float(d)):
                raise ValueError
            return _q(d)
        except (ValueError, TypeError, OverflowError, InvalidOperation):
            inconnu(champ, mid)
            return None

    for index, m in enumerate(mouvements):
        mid = getattr(m, "id", None)
        typ = (getattr(m, "type", "") or "").strip().lower()
        source_type = (getattr(m, "source_type", None) or "").strip()
        quantite = lire(getattr(m, 'quantite', None), 'quantite', mid)
        avant = lire(getattr(m, 'stock_avant', None), 'stock_avant', mid)
        apres = lire(getattr(m, 'stock_apres', None), 'stock_apres', mid)
        cout = lire(getattr(m, 'cout_unitaire', None), 'cout_unitaire', mid)
        cmup_apres = lire(getattr(m, 'cmup_apres', None), 'cmup_apres', mid)
        # Ce champ n'était pas enregistré dans les mouvements legacy.
        cmup_avant_source = getattr(m, 'cmup_avant', None)
        cmup_avant = lire(cmup_avant_source, 'cmup_avant', mid) if source_type or cmup_avant_source is not None else None

        if quantite is not None and quantite <= 0:
            anomalies.append(_anomalie(
                "quantite_invalide",
                f"Mouvement #{mid}: quantité {quantite} non positive.",
                mouvement_id=mid,
            ))

        if typ not in {"entree", "sortie", "correction"}:
            anomalies.append(_anomalie(
                "type_inconnu",
                f"Mouvement #{mid}: type '{typ or 'vide'}' inconnu.",
                mouvement_id=mid,
            ))

        if avant is not None and prev_stock is not None and not _close(avant, prev_stock):
            anomalies.append(_anomalie(
                "rupture_continuite",
                f"Mouvement #{mid}: stock avant {avant} différent du stock après précédent {prev_stock}.",
                mouvement_id=mid,
            ))

        # Cohérence quantité / sens du mouvement.
        sources_stock = quantite is not None and quantite > 0 and avant is not None and apres is not None
        if typ == "entree" and sources_stock:
            attendu = _q(avant + quantite)
            if not _close(apres, attendu):
                anomalies.append(_anomalie(
                    "stock_apres_incoherent",
                    f"Mouvement #{mid}: entrée {quantite}, stock après attendu {attendu}, enregistré {apres}.",
                    mouvement_id=mid,
                ))
        elif typ == "sortie" and sources_stock:
            attendu = _q(avant - quantite)
            if not _close(apres, attendu):
                anomalies.append(_anomalie(
                    "stock_apres_incoherent",
                    f"Mouvement #{mid}: sortie {quantite}, stock après attendu {attendu}, enregistré {apres}.",
                    mouvement_id=mid,
                ))
        elif typ == "correction" and sources_stock:
            delta = _q(apres - avant)
            if not _close(abs(delta), quantite):
                anomalies.append(_anomalie(
                    "correction_incoherente",
                    f"Mouvement #{mid}: correction {quantite}, variation réelle {delta}.",
                    mouvement_id=mid,
                ))

        if apres is not None and apres < -Q4:
            anomalies.append(_anomalie(
                "stock_negatif",
                f"Mouvement #{mid}: stock après négatif ({apres}).",
                mouvement_id=mid,
            ))

        # Les mouvements produits par le moteur 06C enregistrent explicitement le
        # CMUP avant mouvement. Il doit reprendre le CMUP calculé à la ligne
        # précédente. Les lignes legacy n'avaient pas ce champ : on ne les juge
        # donc pas sur ce contrôle.
        if source_type and cmup_avant is not None and prev_cmup is not None and not _close(cmup_avant, prev_cmup, CENT):
            anomalies.append(_anomalie(
                "cmup_avant_rupture",
                f"Mouvement #{mid}: CMUP avant {cmup_avant}, CMUP après précédent {prev_cmup}.",
                mouvement_id=mid,
            ))

        # Valorisation. Les anciens mouvements non valorisés sont signalés comme
        # avertissements : ils expliquent souvent un CMUP historique incertain.
        if cout is not None and cout <= 0 and quantite is not None and quantite > 0:
            anomalies.append(_anomalie(
                "cout_manquant",
                f"Mouvement #{mid}: coût unitaire connu nul ou négatif ({cout}).",
                niveau="warning",
                mouvement_id=mid,
            ))

        if prev_cmup is not None and prev_cmup > 0 and typ == "sortie":
            if cout is not None and cout > 0 and not _close(cout, prev_cmup, CENT):
                anomalies.append(_anomalie(
                    "cout_sortie_cmup",
                    f"Mouvement #{mid}: sortie valorisée {cout}, CMUP attendu {prev_cmup}.",
                    mouvement_id=mid,
                ))
            if cmup_apres is not None and cmup_apres > 0 and not _close(cmup_apres, prev_cmup, CENT):
                anomalies.append(_anomalie(
                    "cmup_modifie_sortie",
                    f"Mouvement #{mid}: une sortie ne doit pas modifier le CMUP ({prev_cmup} → {cmup_apres}).",
                    mouvement_id=mid,
                ))

        if typ == "entree" and sources_stock and cout is not None and cout > 0:
            if prev_cmup is not None and prev_cmup > 0 and avant > 0:
                attendu_cmup = _q((avant * prev_cmup + quantite * cout) / (avant + quantite))
            elif index == 0 or prev_cmup is not None:
                attendu_cmup = cout
            else:
                attendu_cmup = None
            if attendu_cmup is not None and cmup_apres is not None and cmup_apres > 0 and not _close(cmup_apres, attendu_cmup, CENT):
                anomalies.append(_anomalie(
                    "cmup_entree_incoherent",
                    f"Mouvement #{mid}: CMUP après {cmup_apres}, attendu {attendu_cmup}.",
                    mouvement_id=mid,
                ))

        prev_stock = apres
        # Une inconnue rompt la chaîne CMUP ; ne pas conserver une ancienne
        # valeur ni inventer celle du mouvement depuis son coût unitaire.
        prev_cmup = cmup_apres

    stock_article = lire(getattr(article, 'stock_actuel', None), 'stock_actuel')
    cmup_article = lire(getattr(article, 'cmup', None), 'cmup')

    if mouvements:
        if stock_article is not None and prev_stock is not None and not _close(stock_article, prev_stock):
            anomalies.append(_anomalie(
                "stock_article_ecart",
                f"Fiche article {stock_article}, dernier mouvement {prev_stock}.",
            ))
        if prev_cmup is not None and cmup_article is not None and cmup_article > 0 and not _close(cmup_article, prev_cmup, CENT):
            anomalies.append(_anomalie(
                "cmup_article_ecart",
                f"CMUP fiche {cmup_article}, dernier CMUP mouvement {prev_cmup}.",
            ))
    elif stock_article is not None and abs(stock_article) > Q4:
        anomalies.append(_anomalie(
            "stock_sans_historique",
            f"Stock actuel {stock_article} sans aucun mouvement détaillé.",
            niveau="warning",
        ))

    valeur_stock = None
    if stock_article is not None and cmup_article is not None:
        valeur_stock = float(_m(stock_article * cmup_article))
        if not math.isfinite(valeur_stock):
            valeur_stock = None
            inconnu('valeur_stock', message='Produit non représentable : vérifier les sources.')

    nb_erreurs = sum(1 for a in anomalies if a["niveau"] == "erreur")
    nb_warnings = sum(1 for a in anomalies if a["niveau"] == "warning")
    statut = "erreur" if nb_erreurs else "warning" if nb_warnings else "ok"

    return {
        "article_id": getattr(article, "id", None),
        "code": getattr(article, "code", "") or "",
        "designation": getattr(article, "designation", "") or "",
        "stock_actuel": float(stock_article) if stock_article is not None else None,
        "cmup_actuel": float(cmup_article) if cmup_article is not None else None,
        "valeur_stock": valeur_stock,
        "audit_complet": not diagnostics,
        "valorisation_complete": valeur_stock is not None,
        "nombres_diagnostics": diagnostics,
        "nb_mouvements": len(mouvements),
        "statut": statut,
        "nb_erreurs": nb_erreurs,
        "nb_warnings": nb_warnings,
        "anomalies": anomalies,
    }


def auditer_ledger_stock(db, societe_id: int, anomalies_uniquement: bool = False):
    import models

    articles = (
        db.query(models.Article)
        .filter_by(societe_id=societe_id, actif=True, is_stockable=True)
        .order_by(models.Article.designation, models.Article.id)
        .all()
    )

    lignes = []
    total_mouvements = 0
    for article in articles:
        mvts = (
            db.query(models.MouvementStock)
            .filter_by(societe_id=societe_id, article_id=article.id)
            .order_by(models.MouvementStock.date_mouvement, models.MouvementStock.id)
            .all()
        )
        ligne = auditer_mouvements_article(article, mvts)
        total_mouvements += ligne["nb_mouvements"]
        if not anomalies_uniquement or ligne["statut"] != "ok":
            lignes.append(ligne)

    # Résumé calculé sur tous les articles, même si l'affichage est filtré.
    tous = []
    if anomalies_uniquement:
        for article in articles:
            mvts = (
                db.query(models.MouvementStock)
                .filter_by(societe_id=societe_id, article_id=article.id)
                .order_by(models.MouvementStock.date_mouvement, models.MouvementStock.id)
                .all()
            )
            tous.append(auditer_mouvements_article(article, mvts))
    else:
        tous = lignes

    diagnostics_total = {}
    valeur_totale = somme([x['valeur_stock'] for x in tous], 'valeur_stock', diagnostics_total)
    return {
        "articles_controles": len(tous),
        "mouvements_controles": sum(x["nb_mouvements"] for x in tous),
        "articles_ok": sum(1 for x in tous if x["statut"] == "ok"),
        "articles_warning": sum(1 for x in tous if x["statut"] == "warning"),
        "articles_erreur": sum(1 for x in tous if x["statut"] == "erreur"),
        "anomalies_total": sum(x["nb_erreurs"] + x["nb_warnings"] for x in tous),
        "valeur_stock": valeur_totale,
        "audit_complet": all(x['audit_complet'] for x in tous) and not diagnostics_total,
        "valorisation_complete": valeur_totale is not None,
        "nombres_diagnostics": diagnostics_total,
        "mouvements_06c": db.query(models.MouvementStock).filter(
            models.MouvementStock.societe_id == societe_id,
            models.MouvementStock.source_type.isnot(None),
        ).count(),
        "mouvements_legacy": db.query(models.MouvementStock).filter(
            models.MouvementStock.societe_id == societe_id,
            models.MouvementStock.source_type.is_(None),
        ).count(),
        "lignes": lignes,
    }
