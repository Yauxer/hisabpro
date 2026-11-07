"""Archivage sans disparition silencieuse de stock ; ORM entièrement isolé."""
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import models, schemas
from routers import articles
from services import stock_movement_service as stock


@pytest.fixture
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    models.FamilleArticle.__table__.create(engine)
    models.Article.__table__.create(engine)
    with Session(engine) as db:
        db.add(models.Article(id=1, societe_id=3, code="ARCH", designation="Article de recette",
                              stock_actuel=0, cmup=100, is_stockable=True))
        db.commit()
        yield db
    engine.dispose()


@pytest.mark.parametrize("quantite", [10, Decimal("0.0001"), Decimal("-0.0001")])
@pytest.mark.parametrize("action", ["supprimer", "archiver", "service"])
def test_stock_non_nul_ne_disparait_pas_des_etats(db, quantite, action):
    article = db.get(models.Article, 1)
    article.stock_actuel = quantite
    db.commit()
    with pytest.raises(HTTPException) as exc:
        if action == "supprimer":
            articles.supprimer_article(1, {"societe_id": 3}, db)
        else:
            payload = {"actif": False} if action == "archiver" else {"is_stockable": False}
            articles.modifier_article(1, schemas.ArticleUpdate(**payload), {"societe_id": 3}, db)
    assert exc.value.status_code == 409
    assert article.actif is True
    assert article.is_stockable is True
    assert stock.D(article.stock_actuel) == quantite


@pytest.mark.parametrize("champ", ["actif", "is_stockable"])
def test_null_ne_masque_pas_article(db, champ):
    with pytest.raises(HTTPException) as exc:
        articles.modifier_article(1, schemas.ArticleUpdate(**{champ: None}), {"societe_id": 3}, db)
    assert exc.value.status_code == 422


def test_archive_zero_peut_etre_reactive_sans_perte_historique(db):
    articles.supprimer_article(1, {"societe_id": 3}, db)
    assert db.get(models.Article, 1).actif is False
    article = articles.modifier_article(1, schemas.ArticleUpdate(actif=True), {"societe_id": 3}, db)
    assert article.actif is True
    assert article.stock_actuel == 0


def test_mouvement_archive_refuse_avant_modification(db):
    articles.supprimer_article(1, {"societe_id": 3}, db)
    with pytest.raises(ValueError, match="archivé"):
        stock._article_verrouille(db, 3, 1)
    assert db.get(models.Article, 1).stock_actuel == 0


def test_autre_societe_ne_peut_pas_archiver(db):
    with pytest.raises(HTTPException) as exc:
        articles.supprimer_article(1, {"societe_id": 4}, db)
    assert exc.value.status_code == 404
    assert db.get(models.Article, 1).actif is True
