# -*- coding: utf-8 -*-
"""Compatibilité publique de la valorisation stock.

Depuis le Patch 06C, le moteur réel vit dans ``services.stock_movement_service``.
Les anciens imports ``import valorisation`` continuent donc de fonctionner sans
laisser plusieurs implémentations modifier le stock en parallèle.
"""
from services.stock_movement_service import (
    annuler_mouvements_source,
    corriger_stock_cible,
    cout_entree_par_defaut,
    cout_net_ligne,
    cout_sortie,
    enregistrer_mouvement,
    mouvements_actifs_source,
    valeur_stock,
)


def appliquer_entree(article, quantite: float, cout_unitaire=None) -> float:
    """Helper historique sans écriture DB, conservé pour compatibilité calculatoire.

    Les mutations métier doivent utiliser ``enregistrer_mouvement``.
    """
    quantite = abs(float(quantite or 0))
    if quantite <= 0:
        return float(getattr(article, "cmup", 0) or 0)
    cout = float(cout_unitaire if cout_unitaire is not None else cout_entree_par_defaut(article))
    stock_avant = float(getattr(article, "stock_actuel", 0) or 0)
    cmup_avant = float(getattr(article, "cmup", 0) or 0)
    if stock_avant <= 0:
        nouveau = cout
    else:
        nouveau = (stock_avant * cmup_avant + quantite * cout) / (stock_avant + quantite)
    article.cmup = round(nouveau, 4)
    return article.cmup
