"""Mouvements physiques sur ORM isolé ; aucun verrou PostgreSQL n'est simulé.

Le test de relecture utilise deux sessions SQLite pour reproduire une fiche ORM
périmée. La concurrence du verrou FOR UPDATE doit encore être recettée en PG.
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

import models
from services import stock_movement_service as stock


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    models.Article.__table__.create(engine)
    models.MouvementStock.__table__.create(engine)
    monkeypatch.setattr(stock, "_verifier_periode_stock", lambda *args: None)
    with Session(engine) as session:
        session.add(models.Article(id=1, societe_id=3, code="A", designation="Article de test",
                                   stock_actuel=10, cmup=100, prix_achat_ht=100,
                                   is_stockable=True))
        session.commit()
        yield session
    engine.dispose()


def mouvement(db, **kwargs):
    args = dict(date_mouvement=date(2026, 1, 10), source_type="facture",
                source_id=12, source_ligne_id=2, cle_idempotence="test:12:2")
    args.update(kwargs)
    return stock.enregistrer_mouvement(db, 3, 1, args.pop("type_mvt", "entree"),
                                       args.pop("quantite", 2), **args)


@pytest.mark.parametrize("quantite", [-2, 0, float("nan"), float("inf"),
                                      -float("inf"), True, "invalide", "1e100"])
def test_quantite_invalide_ne_modifie_aucun_stock(db, quantite):
    with pytest.raises(ValueError):
        mouvement(db, quantite=quantite)
    assert db.get(models.Article, 1).stock_actuel == 10
    assert db.query(models.MouvementStock).count() == 0


@pytest.mark.parametrize("cout", [-10, -0.00001, float("nan"), float("inf"), True])
def test_cout_invalide_ne_modifie_aucun_stock(db, cout):
    with pytest.raises(ValueError):
        mouvement(db, cout_unitaire=cout)
    assert db.get(models.Article, 1).stock_actuel == 10
    assert db.query(models.MouvementStock).count() == 0


def test_sortie_ne_tolere_pas_un_stock_negatif_meme_une_unite_de_precision(db):
    with pytest.raises(ValueError, match="Stock insuffisant"):
        mouvement(db, type_mvt="sortie", quantite=10.0001)
    assert db.get(models.Article, 1).stock_actuel == 10


def test_entree_cmup_et_sortie_exacte(db):
    entree = mouvement(db, cout_unitaire=160)
    assert entree.stock_apres == 12
    assert entree.cmup_apres == 110
    sortie = mouvement(db, type_mvt="sortie", quantite=12,
                        cle_idempotence="test:sortie", source_id=13)
    assert sortie.stock_apres == 0
    assert sortie.cout_unitaire == 110


def test_reprise_identique_ne_double_pas_le_mouvement(db):
    premier = mouvement(db, cout_unitaire=160)
    second = mouvement(db, cout_unitaire=160)
    assert second.id == premier.id
    assert db.query(models.MouvementStock).count() == 1
    assert db.get(models.Article, 1).stock_actuel == 12


@pytest.mark.parametrize("changement", [dict(quantite=3), dict(type_mvt="sortie"),
    dict(cout_unitaire=161), dict(date_mouvement=date(2026, 1, 11)),
    dict(source_id=99), dict(source_ligne_id=99), dict(facture_id=99)])
def test_reprise_avec_autre_operation_est_refusee(db, changement):
    mouvement(db, cout_unitaire=160)
    params = {"cout_unitaire": 160, **changement}
    with pytest.raises(ValueError, match="idempotence"):
        mouvement(db, **params)
    assert db.get(models.Article, 1).stock_actuel == 12
    assert db.query(models.MouvementStock).count() == 1


def test_correction_reprise_et_cible_differente(db):
    params = dict(date_mouvement=date(2026, 1, 10), cle_idempotence="correction:1")
    premier = stock.corriger_stock_cible(db, 3, 1, 9, **params)
    assert stock.corriger_stock_cible(db, 3, 1, 9, **params).id == premier.id
    with pytest.raises(ValueError, match="idempotence"):
        stock.corriger_stock_cible(db, 3, 1, 8, **params)
    assert db.get(models.Article, 1).stock_actuel == 9


def test_correction_negative_inferieure_precision_refusee(db):
    with pytest.raises(ValueError, match="négative"):
        stock.corriger_stock_cible(db, 3, 1, Decimal("-0.00001"))


def test_fiche_deja_chargee_est_relue_avant_cmup(db):
    article = db.get(models.Article, 1)
    # Modification SQL indépendante de l'objet de l'identity map de la session.
    db.execute(update(models.Article).where(models.Article.id == 1)
               .values(stock_actuel=20, cmup=130), execution_options={"synchronize_session": False})
    assert article.stock_actuel == 10
    entree = mouvement(db, cout_unitaire=160)
    assert entree.stock_avant == 20
    assert entree.stock_apres == 22
    assert entree.cmup_avant == 130
    assert entree.cmup_apres == 132.7273


def test_relecture_idempotence_apres_attente_verrou(db, monkeypatch):
    premier = mouvement(db)
    recherche = stock._mouvement_idempotent
    appels = []
    def apparition_apres_verrou(*args):
        appels.append(args)
        return None if len(appels) == 1 else recherche(*args)
    monkeypatch.setattr(stock, "_mouvement_idempotent", apparition_apres_verrou)
    assert mouvement(db).id == premier.id
    assert len(appels) == 2
    assert db.get(models.Article, 1).stock_actuel == 12


def test_autre_societe_ne_peut_pas_utiliser_article(db):
    with pytest.raises(ValueError, match="cette société"):
        stock.enregistrer_mouvement(db, 4, 1, "entree", 1)
    assert db.get(models.Article, 1).stock_actuel == 10


def annuler(db, source_id, jour):
    return stock.annuler_mouvements_source(db, 3, source_type="facture",
                                           source_id=source_id, date_mouvement=jour)


def test_annulation_ne_passe_pas_avant_une_compensation_plus_recente(db):
    mouvement(db, source_id=12, date_mouvement=date(2026, 1, 1))
    mouvement(db, source_id=13, cle_idempotence="test:13",
              date_mouvement=date(2026, 1, 2))
    annuler(db, 13, date(2026, 1, 10))
    with pytest.raises(ValueError, match="rétroactif interdit"):
        annuler(db, 12, date(2026, 1, 3))
    assert db.get(models.Article, 1).stock_actuel == 12
    assert db.query(models.MouvementStock).count() == 3
    corrections = annuler(db, 12, date(2026, 1, 10))
    assert len(corrections) == 1
    assert db.get(models.Article, 1).stock_actuel == 10
    assert db.query(models.MouvementStock).count() == 4


def test_annulation_verrouille_avant_de_relire_la_queue(db, monkeypatch):
    original = mouvement(db)
    events = []
    verrou = stock._article_verrouille
    actifs = stock.mouvements_actifs_source
    def suivre_verrou(*args):
        events.append("verrou")
        return verrou(*args)
    def suivre_relecture(*args, **kwargs):
        events.append("actifs")
        return actifs(*args, **kwargs)
    monkeypatch.setattr(stock, "_article_verrouille", suivre_verrou)
    monkeypatch.setattr(stock, "mouvements_actifs_source", suivre_relecture)
    corrections = annuler(db, 12, date(2026, 1, 10))
    assert events == ["actifs", "verrou", "actifs"]
    assert corrections[0].annule_mouvement_id == original.id


def test_annulation_deja_realisee_pendant_attente_ne_double_pas(db, monkeypatch):
    mouvement(db)
    annuler(db, 12, date(2026, 1, 10))
    actifs = stock.mouvements_actifs_source
    original = db.query(models.MouvementStock).filter_by(source_type="facture").one()
    calls = []
    def premiere_lecture_perimee(*args, **kwargs):
        calls.append(1)
        return [original] if len(calls) == 1 else actifs(*args, **kwargs)
    monkeypatch.setattr(stock, "mouvements_actifs_source", premiere_lecture_perimee)
    assert annuler(db, 12, date(2026, 1, 10)) == []
    assert len(calls) == 2
    assert db.query(models.MouvementStock).count() == 2
    assert db.get(models.Article, 1).stock_actuel == 10
