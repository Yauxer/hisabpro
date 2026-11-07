# -*- coding: utf-8 -*-
"""Moteur unique des mouvements de stock HisabPro (Patch 06C).

Toutes les mutations de ``Article.stock_actuel`` et du CMUP doivent passer ici.
Le service apporte :
- verrouillage SQL de la fiche article (anti-concurrence),
- validation quantité / stock négatif,
- CMUP déterministe,
- date métier du mouvement,
- traçabilité de la source,
- clé d'idempotence contre les doubles clics / retries,
- annulation par mouvement compensatoire, sans effacer l'historique.

Les mouvements historiques antérieurs au patch restent intacts.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

import models

Q4 = Decimal("0.0001")


def D(value) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("La valeur de stock doit être un nombre fini.")
    try:
        resultat = Decimal(str(0 if value is None else value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("La valeur de stock doit être un nombre fini.") from exc
    if not resultat.is_finite():
        raise ValueError("La valeur de stock doit être un nombre fini.")
    return resultat


def q4(value) -> Decimal:
    try:
        return D(value).quantize(Q4, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("La valeur de stock dépasse la précision autorisée.") from exc


def _as_date(value) -> date:
    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError("Date de mouvement de stock invalide.")


def cout_net_ligne(ligne) -> float:
    """Coût unitaire net d'une ligne d'achat après remises/rabais."""
    pu = D(getattr(ligne, "prix_unitaire", 0))
    r1 = D(getattr(ligne, "remise", 0))
    r2 = D(getattr(ligne, "remise2", 0))
    rb = D(getattr(ligne, "rabais", 0))
    net = pu * (Decimal("1") - r1 / 100) * (Decimal("1") - r2 / 100) - rb
    return float(q4(max(net, Decimal("0"))))


def nombre_source_stock(value, champ: str, *, cout: bool = False) -> Decimal:
    """Qualifie une source historique sans transformer une absence en zéro."""
    if value is None:
        raise ValueError(f"La valeur historique {champ} est absente : vérifiez la fiche article avant tout mouvement.")
    valeur = D(value)
    if cout and valeur < 0:
        raise ValueError(f"La valeur historique {champ} ne peut pas être négative.")
    return valeur


def _sources_article(article):
    return (q4(nombre_source_stock(article.stock_actuel, "stock_actuel")),
            q4(nombre_source_stock(article.cmup, "cmup", cout=True)))


def cout_entree_par_defaut(article) -> float:
    prix = nombre_source_stock(getattr(article, "prix_achat_ht", None), "prix_achat_ht", cout=True)
    if prix == 0:
        prix = nombre_source_stock(getattr(article, "cmup", None), "cmup", cout=True)
    return float(q4(prix))


def cout_sortie(article) -> float:
    cout = nombre_source_stock(getattr(article, "cmup", None), "cmup", cout=True)
    if cout == 0:
        cout = nombre_source_stock(getattr(article, "prix_achat_ht", None), "prix_achat_ht", cout=True)
    return float(q4(cout))


def valeur_stock(article) -> float:
    return float((q4(getattr(article, "stock_actuel", 0)) * q4(getattr(article, "cmup", 0))).quantize(Decimal("0.01")))


def _verifier_periode_stock(db: Session, societe_id: int, jour: date):
    """Réutilise les garde-fous exercice/période déjà présents dans HisabPro."""
    try:
        from services.exercices_service import verifier_date_ecriture, trouver_exercice_pour_date
        # Exclusion native PostgreSQL commune au comptage/comptabilisation et
        # partagée avec la clôture. SQLite reste réservé aux tests métier purs.
        if db.get_bind().dialect.name == "postgresql":
            from services.exercice_verrou_service import verrouiller_operation_stock
            ex = trouver_exercice_pour_date(db, societe_id, jour)
            verrouiller_operation_stock(db, societe_id, ex.annee, partage=True)
            db.refresh(ex)
        verifier_date_ecriture(db, societe_id, jour, action="enregistrer")
    except ImportError:
        return
    except ValueError as exc:
        message = str(exc).replace(" une écriture.", " un mouvement de stock.")
        raise ValueError(message) from exc


def _article_verrouille(db: Session, societe_id: int, article):
    article_id = getattr(article, "id", article)
    if not article_id:
        raise ValueError("Article de stock invalide.")
    row = (
        db.query(models.Article)
        .filter_by(id=int(article_id), societe_id=societe_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not row:
        raise ValueError("Article introuvable pour cette société.")
    if not row.actif:
        raise ValueError(f"L'article {row.designation} est archivé. Réactivez-le avant tout mouvement de stock.")
    if not getattr(row, "is_stockable", False):
        raise ValueError(f"L'article {row.designation} n'est pas stockable.")
    return row


def _dernier_mouvement(db: Session, societe_id: int, article_id: int):
    # Les lignes legacy sont backfillées par la migration 012.
    return (
        db.query(models.MouvementStock)
        .filter_by(societe_id=societe_id, article_id=article_id)
        .order_by(models.MouvementStock.date_mouvement.desc(), models.MouvementStock.id.desc())
        .first()
    )


def _verifier_chronologie(db: Session, societe_id: int, article_id: int, jour: date):
    dernier = _dernier_mouvement(db, societe_id, article_id)
    if dernier and dernier.date_mouvement and jour < dernier.date_mouvement:
        raise ValueError(
            f"Mouvement rétroactif interdit pour cet article : dernier mouvement daté du "
            f"{dernier.date_mouvement.strftime('%d/%m/%Y')}. "
            "Saisissez les mouvements dans l'ordre chronologique afin de préserver le CMUP."
        )


def _mouvement_idempotent(db: Session, societe_id: int, cle: Optional[str]):
    if not cle:
        return None
    return db.query(models.MouvementStock).filter_by(
        societe_id=societe_id, cle_idempotence=cle
    ).first()


def _verifier_reprise_mouvement(mouvement, article, type_mvt, quantite, *,
                                date_mouvement=None, cout_unitaire=None,
                                source_type=None, source_id=None,
                                source_ligne_id=None, facture_id=None,
                                stock_cible=None):
    """Une clé déjà utilisée ne peut désigner une autre opération physique."""
    article_id = getattr(article, "id", article)
    compatible = mouvement.article_id == int(article_id) and mouvement.type == type_mvt
    if stock_cible is not None:
        compatible = compatible and q4(mouvement.stock_apres) == stock_cible
    else:
        compatible = compatible and q4(mouvement.quantite) == quantite
    if date_mouvement is not None:
        compatible = compatible and mouvement.date_mouvement == _as_date(date_mouvement)
    if cout_unitaire is not None:
        compatible = compatible and q4(mouvement.cout_unitaire) == q4(cout_unitaire)
    for champ, valeur in (("source_type", source_type), ("source_id", source_id),
                         ("source_ligne_id", source_ligne_id), ("facture_id", facture_id)):
        if valeur is not None:
            compatible = compatible and getattr(mouvement, champ) == valeur
    if not compatible:
        raise ValueError("Cette clé d'idempotence est déjà utilisée pour un autre mouvement de stock.")
    return mouvement


def _cout_valide(value) -> Decimal:
    valeur = D(value)
    if valeur < 0:
        raise ValueError("Le coût unitaire de stock ne peut pas être négatif.")
    return q4(valeur)


def _nouveau_mouvement(
    db: Session,
    *,
    societe_id: int,
    article,
    type_mvt: str,
    quantite: Decimal,
    stock_avant: Decimal,
    stock_apres: Decimal,
    cout: Decimal,
    cmup_avant: Decimal,
    cmup_apres: Decimal,
    jour: date,
    reference: str,
    note: str,
    facture_id: Optional[int],
    source_type: Optional[str],
    source_id: Optional[int],
    source_ligne_id: Optional[int],
    cle_idempotence: Optional[str],
    user_id: Optional[int],
    annule_mouvement_id: Optional[int] = None,
):
    mvt = models.MouvementStock(
        societe_id=societe_id,
        article_id=article.id,
        type=type_mvt,
        quantite=float(q4(quantite)),
        stock_avant=float(q4(stock_avant)),
        stock_apres=float(q4(stock_apres)),
        cout_unitaire=float(q4(cout)),
        cmup_avant=float(q4(cmup_avant)),
        cmup_apres=float(q4(cmup_apres)),
        date_mouvement=jour,
        reference=(reference or "")[:100],
        note=(note or "")[:300],
        facture_id=facture_id,
        source_type=(source_type or None),
        source_id=source_id,
        source_ligne_id=source_ligne_id,
        cle_idempotence=(cle_idempotence or None),
        cree_par=user_id,
        annule_mouvement_id=annule_mouvement_id,
    )
    db.add(mvt)
    db.flush()
    return mvt


def enregistrer_mouvement(
    db: Session,
    societe_id: int,
    article,
    type_mvt: str,
    quantite: float,
    reference: str = "",
    note: str = "",
    facture_id: Optional[int] = None,
    cout_unitaire: Optional[float] = None,
    *,
    date_mouvement=None,
    source_type: Optional[str] = None,
    source_id: Optional[int] = None,
    source_ligne_id: Optional[int] = None,
    cle_idempotence: Optional[str] = None,
    user_id: Optional[int] = None,
    autoriser_stock_negatif: bool = False,
):
    """Enregistre une entrée ou une sortie via le moteur unique.

    ``type_mvt`` doit être ``entree`` ou ``sortie``. Les corrections physiques
    utilisent :func:`corriger_stock_cible` afin que leur sens soit explicite.
    """
    type_mvt = (type_mvt or "").strip().lower()
    if type_mvt not in {"entree", "sortie"}:
        raise ValueError("Le moteur 06C attend un mouvement 'entree' ou 'sortie'.")

    qty = q4(quantite)
    if qty <= 0:
        raise ValueError("La quantité du mouvement de stock doit être strictement positive.")

    if cout_unitaire is not None:
        _cout_valide(cout_unitaire)

    def reprise(mouvement):
        return _verifier_reprise_mouvement(
            mouvement, article, type_mvt, qty, date_mouvement=date_mouvement,
            cout_unitaire=cout_unitaire, source_type=source_type, source_id=source_id,
            source_ligne_id=source_ligne_id, facture_id=facture_id,
        )

    existant = _mouvement_idempotent(db, societe_id, cle_idempotence)
    if existant:
        return reprise(existant)

    jour = _as_date(date_mouvement)
    _verifier_periode_stock(db, societe_id, jour)
    row = _article_verrouille(db, societe_id, article)
    # Une requête concurrente peut avoir créé le mouvement pendant l'attente du
    # verrou article. Relire la clé avant d'appliquer une deuxième mutation.
    existant = _mouvement_idempotent(db, societe_id, cle_idempotence)
    if existant:
        return reprise(existant)
    _verifier_chronologie(db, societe_id, row.id, jour)

    stock_avant, cmup_avant = _sources_article(row)

    if type_mvt == "sortie":
        if not autoriser_stock_negatif and qty > stock_avant:
            raise ValueError(
                f"Stock insuffisant pour {row.designation} : disponible {stock_avant}, sortie demandée {qty}."
            )
        cout = _cout_valide(cout_unitaire if cout_unitaire is not None else cout_sortie(row))
        stock_apres = q4(stock_avant - qty)
        cmup_apres = cmup_avant
    else:
        cout = _cout_valide(cout_unitaire if cout_unitaire is not None else cout_entree_par_defaut(row))
        stock_apres = q4(stock_avant + qty)
        if stock_avant <= 0:
            cmup_apres = cout
        elif stock_apres != 0:
            cmup_apres = q4((stock_avant * cmup_avant + qty * cout) / stock_apres)
        else:
            cmup_apres = cout

    row.stock_actuel = float(stock_apres)
    row.cmup = float(cmup_apres)

    return _nouveau_mouvement(
        db,
        societe_id=societe_id,
        article=row,
        type_mvt=type_mvt,
        quantite=qty,
        stock_avant=stock_avant,
        stock_apres=stock_apres,
        cout=cout,
        cmup_avant=cmup_avant,
        cmup_apres=cmup_apres,
        jour=jour,
        reference=reference,
        note=note,
        facture_id=facture_id,
        source_type=source_type,
        source_id=source_id,
        source_ligne_id=source_ligne_id,
        cle_idempotence=cle_idempotence,
        user_id=user_id,
    )


def corriger_stock_cible(
    db: Session,
    societe_id: int,
    article,
    nouvelle_quantite: float,
    *,
    reference: str = "CORRECTION",
    note: str = "Correction de stock",
    cout_unitaire: Optional[float] = None,
    date_mouvement=None,
    source_type: str = "correction",
    source_id: Optional[int] = None,
    source_ligne_id: Optional[int] = None,
    cle_idempotence: Optional[str] = None,
    user_id: Optional[int] = None,
):
    """Amène le stock à une quantité cible sans mutation silencieuse.

    Une correction positive ne doit pas créer artificiellement un nouveau coût :
    elle conserve le CMUP courant (prix d'achat seulement en repli si CMUP nul).
    """
    if nouvelle_quantite is None:
        raise ValueError("La quantité cible de stock doit être renseignée.")
    cible_brute = D(nouvelle_quantite)
    if cible_brute < 0:
        raise ValueError("Une correction de stock ne peut pas fixer une quantité négative.")
    cible = q4(cible_brute)

    if cout_unitaire is not None:
        _cout_valide(cout_unitaire)

    def reprise(mouvement):
        return _verifier_reprise_mouvement(
            mouvement, article, "correction", None, stock_cible=cible,
            date_mouvement=date_mouvement, cout_unitaire=cout_unitaire,
            source_type=source_type, source_id=source_id, source_ligne_id=source_ligne_id,
        )

    existant = _mouvement_idempotent(db, societe_id, cle_idempotence)
    if existant:
        return reprise(existant)

    jour = _as_date(date_mouvement)
    _verifier_periode_stock(db, societe_id, jour)
    row = _article_verrouille(db, societe_id, article)
    existant = _mouvement_idempotent(db, societe_id, cle_idempotence)
    if existant:
        return reprise(existant)
    _verifier_chronologie(db, societe_id, row.id, jour)

    stock_avant, cmup_avant = _sources_article(row)
    delta = q4(cible - stock_avant)
    if abs(delta) <= Q4 / 2:
        return None

    cout = _cout_valide(cout_unitaire if cout_unitaire is not None else cout_sortie(row))
    cmup_apres = cmup_avant if cmup_avant > 0 else cout

    row.stock_actuel = float(cible)
    row.cmup = float(cmup_apres)

    return _nouveau_mouvement(
        db,
        societe_id=societe_id,
        article=row,
        type_mvt="correction",
        quantite=abs(delta),
        stock_avant=stock_avant,
        stock_apres=cible,
        cout=cout,
        cmup_avant=cmup_avant,
        cmup_apres=cmup_apres,
        jour=jour,
        reference=reference,
        note=note,
        facture_id=None,
        source_type=source_type,
        source_id=source_id,
        source_ligne_id=source_ligne_id,
        cle_idempotence=cle_idempotence,
        user_id=user_id,
    )


def _cmup_avant_legacy(mvt) -> Decimal:
    """Reconstitue le CMUP avant une ancienne entrée si le champ 06C est vide."""
    explicite = getattr(mvt, "cmup_avant", None)
    if explicite is not None:
        return q4(explicite)

    typ = (getattr(mvt, "type", "") or "").lower()
    apres = q4(getattr(mvt, "stock_apres", 0))
    avant = q4(getattr(mvt, "stock_avant", 0))
    qty = q4(getattr(mvt, "quantite", 0))
    cmup_apres = q4(getattr(mvt, "cmup_apres", 0))
    cout = q4(getattr(mvt, "cout_unitaire", 0))

    if typ == "entree" and avant > 0 and apres > 0 and cmup_apres > 0:
        return q4((apres * cmup_apres - qty * cout) / avant)
    return cmup_apres


def _est_annule(db: Session, mouvement_id: int) -> bool:
    return db.query(models.MouvementStock.id).filter(
        models.MouvementStock.annule_mouvement_id == mouvement_id
    ).first() is not None


def mouvements_actifs_source(
    db: Session,
    societe_id: int,
    *,
    source_type: str,
    source_id: int,
    fallback_facture_id: Optional[int] = None,
):
    conditions = [and_(
        models.MouvementStock.source_type == source_type,
        models.MouvementStock.source_id == source_id,
    )]
    if fallback_facture_id is not None:
        # Compatibilité avec les mouvements créés avant 06C.
        conditions.append(and_(
            models.MouvementStock.facture_id == fallback_facture_id,
            models.MouvementStock.annule_mouvement_id.is_(None),
        ))

    rows = (
        db.query(models.MouvementStock)
        .filter(models.MouvementStock.societe_id == societe_id)
        .filter(or_(*conditions))
        .filter(models.MouvementStock.annule_mouvement_id.is_(None))
        .order_by(models.MouvementStock.date_mouvement.asc(), models.MouvementStock.id.asc())
        .all()
    )
    return [m for m in rows if not _est_annule(db, m.id)]


def annuler_mouvements_source(
    db: Session,
    societe_id: int,
    *,
    source_type: str,
    source_id: int,
    fallback_facture_id: Optional[int] = None,
    reference: str = "",
    note: str = "",
    date_mouvement=None,
    user_id: Optional[int] = None,
):
    """Annule les mouvements actifs d'une pièce par mouvements compensatoires.

    Garde-fou essentiel : les mouvements de la pièce doivent constituer la fin de
    chaîne de chaque article. HisabPro refuse sinon de réécrire un historique CMUP
    déjà suivi de mouvements ultérieurs.
    """
    mvts = mouvements_actifs_source(
        db, societe_id,
        source_type=source_type,
        source_id=source_id,
        fallback_facture_id=fallback_facture_id,
    )
    if not mvts:
        return []

    # Verrouiller avant de contrôler la queue : une entrée concurrente ne doit
    # pas être insérée entre la vérification et la restauration du CMUP.
    # L'ordre commun évite les inversions de verrous sur les pièces multiarticles.
    articles = {
        article_id: _article_verrouille(db, societe_id, article_id)
        for article_id in sorted({m.article_id for m in mvts})
    }
    mvts = mouvements_actifs_source(
        db, societe_id, source_type=source_type, source_id=source_id,
        fallback_facture_id=fallback_facture_id,
    )
    if not mvts:
        return []
    if any(m.article_id not in articles for m in mvts):
        raise ValueError("Les mouvements de la pièce ont changé ; rechargez la pièce avant son annulation.")

    # Les mouvements à annuler doivent être exactement la queue active de la
    # chaîne, sans mouvement ultérieur tiers.
    par_article = {}
    for m in mvts:
        par_article.setdefault(m.article_id, []).append(m)

    for article_id, selection in par_article.items():
        actifs = (
            db.query(models.MouvementStock)
            .filter_by(societe_id=societe_id, article_id=article_id)
            .filter(models.MouvementStock.annule_mouvement_id.is_(None))
            .order_by(models.MouvementStock.date_mouvement.asc(), models.MouvementStock.id.asc())
            .all()
        )
        actifs = [m for m in actifs if not _est_annule(db, m.id)]
        ids_selection = [m.id for m in selection]
        ids_queue = [m.id for m in actifs[-len(selection):]] if len(actifs) >= len(selection) else []
        if ids_queue != ids_selection:
            article = db.query(models.Article).filter_by(id=article_id, societe_id=societe_id).first()
            nom = article.designation if article else str(article_id)
            raise ValueError(
                f"Impossible d'annuler/modifier cette pièce pour « {nom} » : "
                "des mouvements de stock plus récents existent. Créez un document correctif "
                "ou annulez d'abord les mouvements ultérieurs."
            )

    jour_demande = _as_date(date_mouvement)
    # Une correction insérée après une ligne legacy ne doit jamais être datée
    # avant celle-ci, sinon l'ordre métier du ledger deviendrait incohérent.
    dates_source = [m.date_mouvement for m in mvts if getattr(m, "date_mouvement", None)]
    jour = max([jour_demande] + dates_source) if dates_source else jour_demande
    _verifier_periode_stock(db, societe_id, jour)
    for article_id in par_article:
        # Une compensation antérieure reste dans le ledger même si sa source
        # n'appartient plus à la queue active. Sa date ne peut être dépassée à rebours.
        _verifier_chronologie(db, societe_id, article_id, jour)
        _sources_article(articles[article_id])
    # Qualifier toutes les sources avant la première compensation : un coût
    # absent ne vaut pas zéro et une seconde ligne inconnue ne doit pas laisser
    # une première compensation appliquée dans la transaction appelante.
    cmup_restitues = {}
    for original in mvts:
        for champ in ("stock_avant", "stock_apres", "quantite", "cout_unitaire", "cmup_apres"):
            q4(nombre_source_stock(getattr(original, champ, None), champ,
                                  cout=champ in {"cout_unitaire", "cmup_apres"}))
        if original.cmup_avant is not None:
            q4(nombre_source_stock(original.cmup_avant, "cmup_avant", cout=True))
        # L'absence legacy de CMUP avant reste dérivable avec la formule
        # existante, uniquement à partir de ses sources désormais qualifiées.
        cmup_restitues[original.id] = _cmup_avant_legacy(original)
    corrections = []

    # Ordre inverse pour restaurer exactement les états successifs.
    for original in reversed(mvts):
        cle = f"annulation-mvt:{original.id}"
        deja = _mouvement_idempotent(db, societe_id, cle)
        if deja:
            corrections.append(deja)
            continue

        article = articles[original.article_id]
        stock_courant = q4(article.stock_actuel)
        attendu_courant = q4(original.stock_apres)
        if abs(stock_courant - attendu_courant) > Q4:
            raise ValueError(
                f"Chaîne de stock incohérente pour {article.designation} : "
                f"stock actuel {stock_courant}, état attendu {attendu_courant} avant annulation."
            )

        stock_retabli = q4(original.stock_avant)
        cmup_courant = q4(article.cmup)
        cmup_retabli = cmup_restitues[original.id]
        if cmup_retabli <= 0 and cmup_courant > 0:
            cmup_retabli = cmup_courant

        article.stock_actuel = float(stock_retabli)
        article.cmup = float(cmup_retabli)

        correction = _nouveau_mouvement(
            db,
            societe_id=societe_id,
            article=article,
            type_mvt="correction",
            quantite=abs(stock_courant - stock_retabli),
            stock_avant=stock_courant,
            stock_apres=stock_retabli,
            cout=q4(original.cout_unitaire),
            cmup_avant=cmup_courant,
            cmup_apres=cmup_retabli,
            jour=jour,
            reference=reference or original.reference or "",
            note=note or f"Annulation du mouvement #{original.id}",
            facture_id=None,
            source_type=f"{source_type}_annulation",
            source_id=source_id,
            source_ligne_id=getattr(original, "source_ligne_id", None),
            cle_idempotence=cle,
            user_id=user_id,
            annule_mouvement_id=original.id,
        )
        corrections.append(correction)

    return corrections
