# -*- coding: utf-8 -*-
"""Inventaire physique et rapprochement comptable des stocks.

HisabPro utilise un inventaire intermittent pour les marchandises : les achats sont
comptabilisés en charges pendant l'exercice et, à la clôture, le compte de stock 31xx
est ajusté à la valeur du stock physique. La contrepartie est le compte de variation
6114 (ou celui paramétré sur la famille d'articles).

Le rapprochement se fait sur le stock *brut*. Les dépréciations 391x sont suivies
séparément et diminuent ensuite la valeur nette au bilan.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session, joinedload

import models

from services.stock_utils import CENT, Q4, money, qty, construire_lignes_rapprochement
from services.stock_movement_service import D, q4
from services.inventaire_nombres_service import (
    projection_article, projection_snapshot_ligne, diagnostics_lignes, nombre, somme,
)


def comptes_article(article) -> tuple[str, str]:
    famille = getattr(article, "famille", None)
    compte_stock = (getattr(famille, "compte_stock", None) or "3111").strip()
    compte_variation = (getattr(famille, "compte_variation_stock", None) or "6114").strip()
    return compte_stock, compte_variation


def articles_comptage(db: Session, societe_id: int, lignes, *, complet=False, verrouiller=False):
    """Prévalide le comptage avant de créer une photographie ou un mouvement.

    Une ligne inconnue n'est jamais assimilée à un stock nul. La photographie de
    clôture couvre tous les articles de la feuille ; les comptages intermédiaires
    peuvent rester partiels.
    """
    if not lignes:
        raise ValueError("Aucune ligne de comptage transmise.")
    reels = {}
    for saisie in lignes:
        if saisie.article_id in reels:
            raise ValueError(f"L'article {saisie.article_id} est présent plusieurs fois dans le comptage.")
        if saisie.quantite_reelle is None:
            raise ValueError(f"Quantité inconnue pour l'article {saisie.article_id}.")
        quantite = D(saisie.quantite_reelle)
        if quantite < 0:
            raise ValueError(f"Quantité négative interdite pour l'article {saisie.article_id}.")
        reels[saisie.article_id] = q4(quantite)
    requete = db.query(models.Article).options(joinedload(models.Article.famille)).filter_by(
        societe_id=societe_id, actif=True, is_stockable=True)
    if not complet:
        requete = requete.filter(models.Article.id.in_(reels))
    requete = requete.order_by(models.Article.id)
    if verrouiller:
        requete = requete.populate_existing().with_for_update(of=models.Article)
    articles = {a.id: a for a in requete.all()}
    inconnus = set(reels) - set(articles)
    if inconnus:
        ids = ", ".join(str(i) for i in sorted(inconnus))
        raise ValueError(f"Article(s) introuvable(s), inactif(s) ou non stockable(s) pour cette société : {ids}.")
    manquants = set(articles) - set(reels)
    if complet and manquants:
        codes = ", ".join(articles[i].code for i in sorted(manquants)[:10])
        raise ValueError(f"Inventaire de clôture incomplet : {len(manquants)} article(s) à compter ({codes}).")
    # Tous les nombres sont vérifiés avant l'ajout du snapshot et même lorsque
    # le comptage égale le stock : aucun coût historique NULL ne devient zéro.
    total = total_perte = total_excedent = Decimal('0.00')
    for aid, article in articles.items():
        p = projection_article(article)
        diag = dict(p['nombres_diagnostics'])
        cout = nombre(article.cmup, 'cmup', diag)
        if cout == 0:
            cout = nombre(article.prix_achat_ht, 'prix_achat_ht', diag)
        if diag:
            raise ValueError(f"Inventaire impossible : article {article.code}, "
                             f"{', '.join(diag)} à vérifier.")
        try:
            theorique = q4(article.stock_actuel)
            cmup = q4(article.cmup)
            cout = q4(cout)
            reel = reels[aid]
            # Prévalider la précision du moteur et des montants avant mutation.
            ecart = q4(reel - theorique)
            perte = money(abs(ecart) * cout)
            if ecart < 0:
                total_perte = money(total_perte + perte)
            else:
                total_excedent = money(total_excedent + perte)
            valeur = money(reel * (cmup or cout))
            total = money(total + valeur)
            if any(abs(v) >= Decimal('1e14') for v in (theorique, reel, ecart, cmup, cout)) or any(
                abs(v) >= Decimal('1e16') for v in (perte, valeur, total, total_perte, total_excedent)):
                raise ValueError('Précision des colonnes de photographie dépassée.')
        except (InvalidOperation, ValueError, OverflowError) as exc:
            raise ValueError(f"Inventaire impossible : article {article.code}, "
                             "quantité ou valorisation dépasse la précision autorisée, à vérifier.") from exc
    return articles, reels


def soldes_comptes_valides(db: Session, societe_id: int, exercice: int, exclure_ecriture_id: int | None = None):
    soldes = defaultdict(lambda: Decimal("0.00"))
    q = (
        db.query(models.Ecriture)
        .options(joinedload(models.Ecriture.lignes))
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == exercice,
            models.Ecriture.est_validee.is_(True),
        )
    )
    if exclure_ecriture_id:
        q = q.filter(models.Ecriture.id != exclure_ecriture_id)
    for ec in q.all():
        for l in ec.lignes:
            soldes[l.compte] += money(l.debit) - money(l.credit)
    return {k: money(v) for k, v in soldes.items()}


def inventaire_cloture(db: Session, societe_id: int, exercice: int, date_fin: date):
    return (
        db.query(models.InventaireStock)
        .options(joinedload(models.InventaireStock.lignes))
        .filter(
            models.InventaireStock.societe_id == societe_id,
            models.InventaireStock.exercice == exercice,
            models.InventaireStock.date_inventaire == date_fin,
        )
        .order_by(models.InventaireStock.id.desc())
        .first()
    )


def valeur_physique_live(db: Session, societe_id: int):
    articles = (
        db.query(models.Article)
        .options(joinedload(models.Article.famille))
        .filter_by(societe_id=societe_id, actif=True, is_stockable=True)
        .all()
    )
    lignes = []
    for a in articles:
        projection = projection_article(a)
        compte_stock, compte_variation = comptes_article(a)
        lignes.append({
            "article_id": a.id,
            "code": a.code,
            "designation": a.designation,
            "quantite": projection['stock'],
            "cmup": projection['cmup'],
            "valeur": projection['valeur'],
            "nombres_diagnostics": projection['nombres_diagnostics'],
            "compte_stock": compte_stock,
            "compte_variation": compte_variation,
            "emplacement": a.emplacement,
        })
    total = somme([l['valeur'] for l in lignes], 'total_valeur', {})
    return Decimal(str(total)) if total is not None else None, lignes


def etat_stock_cloture(db: Session, societe_id: int, exercice_obj):
    inv = inventaire_cloture(db, societe_id, exercice_obj.annee, exercice_obj.date_fin)
    if inv:
        total_diagnostics = {}
        physique = nombre(inv.total_valeur, 'total_valeur', total_diagnostics, negatif=True, decimales=2)
        lignes = [{
            "article_id": l.article_id,
            "code": l.code,
            "designation": l.designation,
            **projection_snapshot_ligne(l),
            "compte_stock": l.compte_stock,
            "compte_variation": l.compte_variation,
        } for l in inv.lignes]
    else:
        total_diagnostics = {}
        physique, lignes = valeur_physique_live(db, societe_id)
    diagnostics = diagnostics_lignes(lignes)
    diagnostics.extend({'article_id': None, 'code': None, 'champ': c, 'message': m}
                       for c, m in total_diagnostics.items())
    if physique is None and not diagnostics:
        diagnostics.append({'article_id': None, 'code': None, 'champ': 'total_valeur',
                            'message': 'Total de valorisation non fini : à vérifier.'})
    complete = physique is not None and not diagnostics
    if not complete:
        physique = None
    else:
        physique = Decimal(str(physique))

    soldes = soldes_comptes_valides(db, societe_id, exercice_obj.annee)
    brut = money(sum((s for c, s in soldes.items() if c.startswith("31")), Decimal("0.00")))
    depreciation = money(sum((-s for c, s in soldes.items() if c.startswith("391") and s < 0), Decimal("0.00")))
    net = money(brut - depreciation)
    try:
        ecart_brut = money(physique - brut) if physique is not None else None
    except InvalidOperation:
        ecart_brut = None
        physique = None
        complete = False
        diagnostics.append({'article_id': None, 'code': None, 'champ': 'ecart_brut',
                            'message': 'Valorisation dépasse la précision comptable : à vérifier.'})

    ecriture = None
    if inv and inv.ecriture_stock_id:
        ecriture = db.query(models.Ecriture).filter_by(
            id=inv.ecriture_stock_id, societe_id=societe_id
        ).first()

    inventaire_requis = bool(lignes) or abs(brut) > CENT
    rapproche = complete and ((not inventaire_requis) or bool(inv is not None and abs(ecart_brut) <= CENT))
    return {
        "exercice": exercice_obj.annee,
        "date_fin": exercice_obj.date_fin.isoformat(),
        "nb_articles": len(lignes),
        "inventaire_requis": inventaire_requis,
        "inventaire_valide": inv is not None,
        "inventaire_id": inv.id if inv else None,
        "inventaire_reference": inv.reference if inv else None,
        "valeur_physique_brute": float(physique) if physique is not None else None,
        "valeur_comptable_brute": float(brut),
        "depreciations": float(depreciation),
        "valeur_comptable_nette": float(net),
        "ecart_brut": float(ecart_brut) if ecart_brut is not None else None,
        "valorisation_complete": complete,
        "diagnostics": diagnostics,
        "stock_rapproche": rapproche,
        "ecriture_stock_id": ecriture.id if ecriture else None,
        "ecriture_stock_validee": bool(ecriture.est_validee) if ecriture else False,
        "lignes": lignes,
    }


def creer_snapshot_inventaire(db: Session, societe_id: int, exercice_obj, data, user_id: int | None):
    """Valide un comptage, régularise les quantités et conserve une photographie."""
    import valorisation

    if not data.lignes:
        raise ValueError("Aucune ligne de comptage transmise.")

    jour = date.fromisoformat(data.date) if data.date else date.today()
    if not (exercice_obj.date_debut <= jour <= exercice_obj.date_fin):
        raise ValueError(
            f"La date d'inventaire {jour.isoformat()} n'appartient pas à l'exercice {exercice_obj.annee}."
        )

    articles, reels = articles_comptage(
        db, societe_id, data.lignes, complet=jour == exercice_obj.date_fin, verrouiller=True)

    reference_saisie = (data.reference or "").strip()
    reference_base = reference_saisie or f"INV-STOCK-{jour.strftime('%Y%m%d')}"
    reference = reference_base
    existant = db.query(models.InventaireStock).filter_by(
        societe_id=societe_id, reference=reference
    ).first()
    if existant and reference_saisie:
        raise ValueError(f"La référence d'inventaire '{reference}' existe déjà.")
    # Une référence générée automatiquement est suffixée afin de conserver
    # l'historique des comptages successifs au lieu d'écraser une photographie.
    suffixe = 2
    while existant:
        reference = f"{reference_base}-{suffixe}"
        suffixe += 1
        existant = db.query(models.InventaireStock).filter_by(
            societe_id=societe_id, reference=reference
        ).first()

    inv = models.InventaireStock(
        societe_id=societe_id,
        exercice=exercice_obj.annee,
        date_inventaire=jour,
        reference=reference,
        note=(data.note or "").strip() or None,
        cree_par=user_id,
        validee_le=datetime.now(),
    )
    db.add(inv)
    db.flush()

    total_valeur = total_perte = total_excedent = Decimal("0.00")
    regularises = []

    for saisie in data.lignes:
        article = articles[saisie.article_id]

        theorique = qty(article.stock_actuel)
        reel = reels[saisie.article_id]
        if reel < 0:
            raise ValueError(f"Quantité négative interdite pour {article.designation}.")
        ecart = qty(reel - theorique)
        cmup_avant = Decimal(str(article.cmup or 0))

        # Patch 06C : le comptage physique ne modifie jamais directement
        # ``Article.stock_actuel``. Toute différence significative devient une
        # correction traçable dans le moteur unique ; une différence sous la
        # tolérance est neutralisée sans mutation silencieuse.
        if abs(ecart) > Q4 / 2:
            cout = Decimal(str(valorisation.cout_sortie(article) or 0))
            mvt = valorisation.corriger_stock_cible(
                db,
                societe_id,
                article,
                float(reel),
                reference=reference,
                note=f"Régularisation inventaire physique {jour.isoformat()}",
                cout_unitaire=float(cout),
                date_mouvement=jour,
                source_type="inventaire_physique",
                source_id=inv.id,
                source_ligne_id=saisie.article_id,
                cle_idempotence=f"inventaire:{inv.id}:article:{article.id}",
                user_id=user_id,
            )
            valeur_ecart = money(abs(ecart) * Decimal(str(mvt.cout_unitaire or 0)))
            if ecart < 0:
                total_perte += valeur_ecart
                valeur_ecart_signee = -valeur_ecart
            else:
                total_excedent += valeur_ecart
                valeur_ecart_signee = valeur_ecart
            regularises.append({
                "article_id": article.id,
                "code": article.code,
                "designation": article.designation,
                "ecart": float(ecart),
                "valeur_ecart": float(valeur_ecart_signee),
            })
        else:
            valeur_ecart_signee = Decimal("0.00")
            # On conserve l'état théorique : l'écart est inférieur à la précision
            # de gestion et ne justifie pas un mouvement de stock.
            reel = theorique

        cmup_final = Decimal(str(article.cmup or cmup_avant or 0))
        valeur_stock = money(reel * cmup_final)
        total_valeur += valeur_stock
        compte_stock, compte_variation = comptes_article(article)

        db.add(models.InventaireStockLigne(
            inventaire_id=inv.id,
            article_id=article.id,
            code=article.code,
            designation=article.designation,
            quantite_theorique=theorique,
            quantite_reelle=reel,
            ecart_quantite=ecart,
            cmup=cmup_final,
            valeur_stock=valeur_stock,
            valeur_ecart=valeur_ecart_signee,
            compte_stock=compte_stock,
            compte_variation=compte_variation,
        ))

    inv.total_valeur = money(total_valeur)
    inv.total_perte = money(total_perte)
    inv.total_excedent = money(total_excedent)
    db.flush()
    return inv, regularises



def generer_ecriture_stock_cloture(db: Session, societe_id: int, exercice_obj, user_id: int | None):
    inv = inventaire_cloture(db, societe_id, exercice_obj.annee, exercice_obj.date_fin)
    if not inv:
        raise ValueError(
            f"Aucun inventaire physique validé au {exercice_obj.date_fin.isoformat()}. "
            "Validez d'abord le comptage de fin d'exercice."
        )

    etat = etat_stock_cloture(db, societe_id, exercice_obj)
    if not etat['valorisation_complete']:
        raise ValueError("Inventaire impossible : valorisation historique à vérifier avant comptabilisation.")

    sources = db.query(models.Ecriture).filter_by(
        societe_id=societe_id, exercice=exercice_obj.annee
    )
    if inv.ecriture_stock_id:
        existante = sources.filter_by(id=inv.ecriture_stock_id).populate_existing().with_for_update().first()
        if existante is None:
            raise ValueError(
                "Le lien comptable de l'inventaire ne correspond pas à cette société et cet exercice. "
                "Vérifiez son origine avant toute régénération."
            )
    else:
        candidates = sources.filter_by(reference=f"STOCK-CLOTURE-{exercice_obj.annee}").order_by(
            models.Ecriture.id
        ).populate_existing().with_for_update().all()
        if len(candidates) > 1:
            raise ValueError(
                "Plusieurs écritures portent la référence de stock de cet exercice sans lien certain. "
                "Vérifiez le Journal ; aucune pièce n'a été remplacée."
            )
        existante = candidates[0] if candidates else None
    if existante:
        if existante.source != "stock":
            raise ValueError(
                "L'origine de l'écriture n'est pas identifiée comme stock. "
                "Vérifiez le lien et la référence dans le Journal ; aucune pièce n'a été remplacée."
            )
        if existante.est_validee:
            raise ValueError(
                "L'écriture de stock de clôture est déjà définitive. Elle ne peut plus être régénérée : "
                "utilisez une contrepassation traçable dans le Journal si une correction est nécessaire."
            )
        if inv.ecriture_stock_id == existante.id:
            inv.ecriture_stock_id = None
        db.delete(existante)
        db.flush()

    # Un même compte de stock ne peut pas être piloté par plusieurs comptes de
    # variation différents : ce serait ambigu au moment du rapprochement.
    cibles = defaultdict(lambda: {"valeur": Decimal("0.00"), "variations": set()})
    for l in inv.lignes:
        c = (l.compte_stock or "3111").strip()
        v = (l.compte_variation or "6114").strip()
        cibles[c]["valeur"] += money(l.valeur_stock)
        cibles[c]["variations"].add(v)

    for compte, info in cibles.items():
        if len(info["variations"]) != 1:
            raise ValueError(
                f"Le compte de stock {compte} est associé à plusieurs comptes de variation. "
                "Corrigez le paramétrage des familles d'articles."
            )

    soldes = soldes_comptes_valides(db, societe_id, exercice_obj.annee)
    # Refus explicite d'un stock comptable sans article correspondant : ne jamais
    # solder silencieusement un compte 31xx que le module Stocks ne sait pas expliquer.
    orphelins = [
        (c, s) for c, s in soldes.items()
        if c.startswith("31") and abs(s) > CENT and c not in cibles
    ]
    if orphelins:
        txt = ", ".join(f"{c} ({s:+.2f})" for c, s in orphelins[:5])
        raise ValueError(
            f"Des soldes de stock comptables ne sont rattachés à aucune famille d'articles : {txt}."
        )

    lignes_data = construire_lignes_rapprochement(cibles, soldes)
    lignes = [models.LigneEcriture(**x) for x in lignes_data]

    if not lignes:
        inv.ecriture_stock_id = None
        return None

    ecriture = models.Ecriture(
        societe_id=societe_id,
        date=exercice_obj.date_fin,
        journal="OD",
        libelle=f"Régularisation du stock final {exercice_obj.annee}",
        reference=f"STOCK-CLOTURE-{exercice_obj.annee}",
        exercice=exercice_obj.annee,
        source="stock",
        est_validee=False,
        lignes=lignes,
    )
    db.add(ecriture)
    db.flush()
    inv.ecriture_stock_id = ecriture.id
    db.flush()
    return ecriture
