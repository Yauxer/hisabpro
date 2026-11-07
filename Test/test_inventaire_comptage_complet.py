"""Les photographies de stock ne perdent ni articles ni quantités invalides."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import models
from services import stock_service, stock_movement_service
from routers import inventaire


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for model in [models.FamilleArticle, models.Article, models.MouvementStock,
                  models.InventaireStock, models.InventaireStockLigne]:
        model.__table__.create(engine)
    monkeypatch.setattr(stock_movement_service, "_verifier_periode_stock", lambda *args: None)
    with Session(engine) as session:
        for id_, sid, stockable, actif in [(1, 3, True, True), (2, 3, True, True),
                                         (3, 4, True, True), (4, 3, False, True),
                                         (5, 3, True, False)]:
            session.add(models.Article(id=id_, societe_id=sid, code=f"A{id_}",
                designation=f"Article {id_}", stock_actuel=10, cmup=100,
                prix_achat_ht=100, actif=actif, is_stockable=stockable))
        session.commit()
        yield session
    engine.dispose()


def comptage(lignes, jour="2026-12-31"):
    return SimpleNamespace(date=jour, reference="INV-TEST", note="Recette synthétique",
                           lignes=[SimpleNamespace(article_id=i, quantite_reelle=q) for i, q in lignes])


def snapshot(db, data):
    ex = SimpleNamespace(annee=2026, date_debut=date(2026, 1, 1), date_fin=date(2026, 12, 31))
    return stock_service.creer_snapshot_inventaire(db, 3, ex, data, None)


@pytest.mark.parametrize("article_id", [99, 3, 4, 5])
def test_article_inconnu_autre_societe_service_inactif_refuse_avant_creation(db, article_id):
    with pytest.raises(ValueError, match="introuvable"):
        snapshot(db, comptage([(1, 9), (article_id, 0)]))
    assert db.query(models.InventaireStock).count() == 0
    assert db.query(models.MouvementStock).count() == 0
    assert db.get(models.Article, 1).stock_actuel == 10


def test_article_doublonne_refuse_avant_creation(db):
    with pytest.raises(ValueError, match="plusieurs fois"):
        snapshot(db, comptage([(1, 9), (1, 8), (2, 10)]))
    assert db.query(models.InventaireStock).count() == 0


@pytest.mark.parametrize("quantite", [float("nan"), float("inf"), -1, Decimal("-0.00001"), True])
def test_quantite_invalide_ne_cree_pas_snapshot_ni_correction(db, quantite):
    with pytest.raises(ValueError):
        snapshot(db, comptage([(1, 9), (2, quantite)]))
    assert db.query(models.InventaireStock).count() == 0
    assert db.query(models.MouvementStock).count() == 0
    assert db.get(models.Article, 1).stock_actuel == 10


def test_comptage_cloture_incomplet_refuse_sans_assumer_article_manquant_zero(db):
    with pytest.raises(ValueError, match="clôture incomplet.*A2"):
        snapshot(db, comptage([(1, 0)]))
    assert db.query(models.InventaireStock).count() == 0
    assert db.get(models.Article, 2).stock_actuel == 10


def test_comptage_intermediaire_partiel_reste_possible(db):
    inv, ecarts = snapshot(db, comptage([(1, 9)], "2026-06-30"))
    assert len(inv.lignes) == 1
    assert inv.total_valeur == Decimal("900.00")
    assert inv.total_perte == Decimal("100.00")
    assert ecarts[0]["ecart"] == -1
    assert db.get(models.Article, 2).stock_actuel == 10


def test_comptage_complet_fige_valeur_sans_melanger_societes(db):
    inv, ecarts = snapshot(db, comptage([(1, 9), (2, 0)]))
    assert inv.total_valeur == Decimal("900.00")
    assert inv.total_perte == Decimal("1100.00")
    assert len(inv.lignes) == 2
    assert len(ecarts) == 2
    assert db.get(models.Article, 3).stock_actuel == 10


def test_simulation_refuse_article_inconnu_instead_of_partial_success(db):
    data = inventaire.InventaireIn(date="2026-06-30", lignes=[
        inventaire.LigneComptage(article_id=1, quantite_reelle=9),
        inventaire.LigneComptage(article_id=99, quantite_reelle=0)])
    with pytest.raises(HTTPException) as exc:
        inventaire.simuler_inventaire(data, {"societe_id": 3}, db)
    assert exc.value.status_code == 400


def test_simulation_et_snapshot_ont_la_meme_precision_quantite(db):
    data = inventaire.InventaireIn(date="2026-12-31", reference="INV-TEST", lignes=[
        inventaire.LigneComptage(article_id=1, quantite_reelle=9.99995),
        inventaire.LigneComptage(article_id=2, quantite_reelle=10)])
    simulation = inventaire.simuler_inventaire(data, {"societe_id": 3}, db)
    inv, ecarts = snapshot(db, data)
    assert simulation["nb_ecarts"] == len(ecarts) == 0
    assert simulation["valeur_stock_compte"] == float(inv.total_valeur) == 2000
