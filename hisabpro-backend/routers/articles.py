from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date
from database import get_db
from auth import get_current_user, requiert_ecriture
import models, schemas
from services.stock_movement_service import nombre_source_stock
from services.tva_regles_service import taux_autorises
from services.plan_comptable import compte_utilisable

router = APIRouter(prefix="/api/articles", tags=["articles"])
router_familles = APIRouter(prefix="/api/familles", tags=["familles"])




def _valider_comptes_plan(db: Session, societe_id: int, valeurs: dict, champs):
    for champ in champs:
        numero = str(valeurs.get(champ) or '').strip()
        if numero and not compte_utilisable(db, societe_id, numero):
            raise HTTPException(422, f"Le compte {numero} ({champ}) est absent ou désactivé dans le plan comptable de la société.")
def _valider_taux_reference(taux):
    """Valide le taux proposé par une fiche article/famille à la date courante.

    Le 0 % reste autorisé comme valeur de référence ; sa qualification fiscale
    précise est obligatoirement demandée sur le document commercial.
    """
    try:
        valeur = float(taux if taux is not None else 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Taux de TVA invalide")
    autorises = {float(x) for x in taux_autorises(date.today())}
    if valeur not in autorises:
        liste = ", ".join(f"{x:g} %" for x in sorted(autorises))
        raise HTTPException(status_code=422, detail=f"Taux TVA non proposé pour l'année courante. Taux disponibles : {liste}.")



# ── Familles ──────────────────────────────────────────────────────────────────

@router_familles.get("", response_model=List[schemas.FamilleOut])
def lister_familles(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(models.FamilleArticle).filter_by(
        societe_id=current_user["societe_id"], actif=True
    ).order_by(models.FamilleArticle.libelle).all()


@router_familles.post("", response_model=schemas.FamilleOut, status_code=201)
def creer_famille(
    data: schemas.FamilleCreate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    _valider_taux_reference(data.tva_defaut)
    _valider_comptes_plan(db, current_user["societe_id"], data.model_dump(),
                          ("compte_vente", "compte_achat", "compte_stock", "compte_variation_stock"))

    existante = db.query(models.FamilleArticle).filter_by(
        societe_id=current_user["societe_id"], code=data.code
    ).first()
    if existante:
        raise HTTPException(status_code=400, detail=f"Code famille '{data.code}' déjà utilisé")

    famille = models.FamilleArticle(
        societe_id=current_user["societe_id"],
        **data.model_dump()
    )
    db.add(famille)
    db.commit()
    db.refresh(famille)
    return famille


@router_familles.delete("/{famille_id}", status_code=204)
def supprimer_famille(
    famille_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    famille = db.query(models.FamilleArticle).filter_by(
        id=famille_id, societe_id=current_user["societe_id"]
    ).first()
    if not famille:
        raise HTTPException(status_code=404, detail="Famille introuvable")
    famille.actif = False
    db.commit()


# ── Articles ──────────────────────────────────────────────────────────────────

@router.get("", response_model=List[schemas.ArticleOut])
def lister_articles(
    recherche:  Optional[str] = Query(None),
    famille_id: Optional[int] = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(models.Article).options(
        joinedload(models.Article.famille)
    ).filter_by(societe_id=current_user["societe_id"], actif=True)

    if famille_id:
        q = q.filter(models.Article.famille_id == famille_id)
    if recherche:
        q = q.filter(
            models.Article.designation.ilike(f"%{recherche}%") |
            models.Article.code.ilike(f"%{recherche}%")
        )

    return q.order_by(models.Article.created_at.desc()).all()


@router.post("", response_model=schemas.ArticleOut, status_code=201)
def creer_article(
    data: schemas.ArticleCreate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    _valider_taux_reference(data.tva)

    existant = db.query(models.Article).filter_by(
        societe_id=current_user["societe_id"], code=data.code, actif=True
    ).first()
    if existant:
        raise HTTPException(status_code=400, detail=f"Code article '{data.code}' déjà utilisé")

    payload = data.model_dump()
    _valider_comptes_plan(db, current_user["societe_id"], payload, ("compte_vente", "compte_achat"))
    stock_initial = float(payload.pop("stock_actuel", 0) or 0)
    if not payload.get("is_stockable", True) and stock_initial:
        raise HTTPException(status_code=400, detail="Un service non stockable ne peut pas avoir de stock initial")

    # FORM.1 : même le stock initial passe par le moteur unique afin de conserver
    # une piste de mouvements complète dès la création de l'article.
    article = models.Article(
        societe_id=current_user["societe_id"],
        stock_actuel=0.0,
        **payload
    )
    db.add(article)
    try:
        db.flush()
        if stock_initial:
            import valorisation
            valorisation.corriger_stock_cible(
                db,
                current_user["societe_id"],
                article,
                stock_initial,
                reference="STOCK-INITIAL",
                note="Stock initial à la création de l'article",
                source_type="stock_initial",
                source_id=article.id,
                cle_idempotence=f"stock_initial:article:{article.id}",
                user_id=current_user.get("id"),
            )
        db.commit()
    except (ValueError, RuntimeError) as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    db.refresh(article)
    return db.query(models.Article).options(
        joinedload(models.Article.famille)
    ).filter_by(id=article.id).first()


@router.patch("/{article_id}", response_model=schemas.ArticleOut)
def modifier_article(
    article_id: int,
    data: schemas.ArticleUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    article = db.query(models.Article).filter_by(
        id=article_id, societe_id=current_user["societe_id"]
    ).populate_existing().with_for_update().first()
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")

    updates = data.model_dump(exclude_unset=True)
    if "tva" in updates:
        _valider_taux_reference(updates["tva"])
    _valider_comptes_plan(db, current_user["societe_id"], updates, ("compte_vente", "compte_achat"))
    if "stock_actuel" in updates:
        raise HTTPException(
            status_code=409,
            detail="Le stock actuel ne se modifie pas dans la fiche article. Utilisez l'ajustement de stock traçable.",
        )
    for champ in ("actif", "is_stockable"):
        if champ in updates and updates[champ] is None:
            raise HTTPException(status_code=422, detail=f"Le champ {champ} doit être vrai ou faux.")
    stock_connu = None
    if updates.get("is_stockable") is False or updates.get("actif") is False:
        try:
            stock_connu = nombre_source_stock(article.stock_actuel, "stock_actuel")
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
    if updates.get("is_stockable") is False and stock_connu != 0:
        raise HTTPException(
            status_code=409,
            detail="Ramenez le stock à 0 avant de convertir cet article en service non stockable.",
        )
    if updates.get("actif") is False and stock_connu != 0:
        raise HTTPException(status_code=409, detail="Un article avec du stock ne peut pas être archivé. Traitez d'abord le stock par un mouvement traçable.")
    for k, v in updates.items():
        setattr(article, k, v)

    db.commit()
    db.refresh(article)
    return db.query(models.Article).options(
        joinedload(models.Article.famille)
    ).filter_by(id=article_id).first()


@router.delete("/{article_id}", status_code=204)
def supprimer_article(
    article_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    article = db.query(models.Article).filter_by(
        id=article_id, societe_id=current_user["societe_id"]
    ).populate_existing().with_for_update().first()
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    try:
        stock_connu = nombre_source_stock(article.stock_actuel, "stock_actuel")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if stock_connu != 0:
        raise HTTPException(status_code=409, detail="Un article avec du stock ne peut pas être archivé. Traitez d'abord le stock par un mouvement traçable.")
    article.actif = False
    db.commit()


# ── Stock : alertes et mouvements ─────────────────────────────────────────────

@router.get("/stock/alertes")
def alertes_stock(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Classe les stocks connus et signale les quantités historiques inconnues."""
    from services.inventaire_nombres_service import nombre
    articles = db.query(models.Article).filter_by(
        societe_id=current_user["societe_id"], actif=True, is_stockable=True
    ).all()

    rupture, faible, inconnus, diagnostics = [], [], [], []
    for a in articles:
        nombres_diagnostics = {}
        stock = nombre(a.stock_actuel, 'stock_actuel', nombres_diagnostics, negatif=True)
        ligne = {
            "id": a.id, "code": a.code, "designation": a.designation,
            "stock_actuel": stock, "unite": a.unite,
            "emplacement": a.emplacement,
            "stock_diagnostic": nombres_diagnostics.get('stock_actuel'),
            "nombres_diagnostics": nombres_diagnostics,
        }
        if stock is None:
            inconnus.append(ligne)
            diagnostics.append({'article_id': a.id, 'code': a.code, 'champ': 'stock_actuel',
                                'message': nombres_diagnostics['stock_actuel']})
        elif stock <= 0:
            rupture.append(ligne)
        elif stock < 5:
            faible.append(ligne)
    return {"rupture": rupture, "faible": faible, "inconnus": inconnus, "diagnostics": diagnostics}


@router.get("/{article_id}/mouvements", response_model=List[schemas.MouvementStockOut])
def mouvements_article(
    article_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Historique des mouvements de stock pour un article."""
    article = db.query(models.Article).filter_by(
        id=article_id, societe_id=current_user["societe_id"]
    ).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")

    return db.query(models.MouvementStock).filter_by(
        article_id=article_id,
        societe_id=current_user["societe_id"],
    ).order_by(models.MouvementStock.created_at.desc()).limit(50).all()


@router.patch("/{article_id}/stock", response_model=schemas.ArticleOut)
def ajuster_stock(
    article_id: int,
    data: dict,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Correction manuelle du stock (inventaire)."""
    article = db.query(models.Article).filter_by(
        id=article_id, societe_id=current_user["societe_id"]
    ).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")

    # Le moteur valide le nombre avant toute mutation ; un float() hors du try
    # transformait une saisie invalide en erreur serveur au lieu d'un refus clair.
    nouvelle_qte = data.get("stock_actuel", article.stock_actuel)

    # Patch 06C : aucune mutation silencieuse de stock. Même une correction
    # manuelle passe par le moteur unique et devient une ligne de sous-ledger.
    import valorisation
    try:
        valorisation.corriger_stock_cible(
            db,
            current_user["societe_id"],
            article,
            nouvelle_qte,
            reference=data.get("reference", "CORRECTION"),
            note=data.get("note", "Correction manuelle de stock"),
            date_mouvement=data.get("date"),
            source_type="correction_manuelle",
            source_id=article.id,
            user_id=current_user.get("id"),
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    db.refresh(article)
    return db.query(models.Article).options(
        joinedload(models.Article.famille)
    ).filter_by(id=article_id).first()
