"""Routes bancaires réelles, données synthétiques et SQL générique en mémoire.

Les contraintes et triggers PostgreSQL restent à vérifier sur une base isolée.
"""
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import Column, Date, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base

import models
import schemas
from routers import rapprochement as banque

Base = declarative_base()


class Exercice(Base):
    __tablename__ = "exercices_recette_banque"
    id = Column(Integer, primary_key=True)
    societe_id = Column(Integer)
    annee = Column(Integer)
    date_debut = Column(Date)
    date_fin = Column(Date)
    statut = Column(String)


class Cloture(Base):
    __tablename__ = "clotures_recette_banque"
    id = Column(Integer, primary_key=True)
    societe_id = Column(Integer)
    exercice = Column(Integer)


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for model in [models.RapprochementLigne, models.RapprochementEtat,
                  models.Ecriture, models.LigneEcriture]:
        model.__table__.create(engine)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(banque.models, "ExerciceComptable", Exercice)
    monkeypatch.setattr(banque.models, "ClotureExercice", Cloture)
    with Session(engine) as session:
        yield session
    engine.dispose()


def exercice(db, annee=2026, statut="ouvert", societe_id=3):
    db.add(Exercice(societe_id=societe_id, annee=annee,
                   date_debut=date(annee, 1, 1), date_fin=date(annee, 12, 31),
                   statut=statut))
    db.flush()


def situation(db, debut=date(2026, 1, 1), fin=date(2026, 12, 31)):
    return banque.situation_rapprochement("5141", debut, fin,
                                         {"societe_id": 3, "id": 1}, db)


def test_lecture_seule_sur_cloture_historique_meme_statut_exercice_ouvert(db):
    exercice(db)
    db.add(Cloture(societe_id=3, exercice=2026))
    db.flush()
    assert situation(db)["lecture_seule"] is True


def test_lecture_seule_si_plage_chevauche_exercice_cloture(db):
    exercice(db, 2025, "cloture")
    exercice(db)
    assert situation(db, date(2025, 12, 1), date(2026, 1, 31))["lecture_seule"] is True


def test_autre_societe_cloturee_ne_bloque_pas_le_releve(db):
    exercice(db)
    exercice(db, statut="cloture", societe_id=4)
    db.add(Cloture(societe_id=4, exercice=2026))
    db.flush()
    assert situation(db)["lecture_seule"] is False


def test_dates_inversees_restent_erreur_et_non_lecture_seule(db):
    with pytest.raises(HTTPException) as exc:
        banque._plage_est_cloturee(db, 3, date(2026, 12, 31), date(2026, 1, 1))
    assert exc.value.status_code == 400


def releve_rapproche(db):
    ecriture = models.Ecriture(societe_id=3, exercice=2025, date=date(2025, 12, 31),
        journal="BQ", libelle="Encaissement synthétique", est_validee=True,
        numero_ecriture="BQ-TEST", lignes=[models.LigneEcriture(compte="5141", debit=100, credit=0)])
    db.add(ecriture)
    db.flush()
    ligne = models.RapprochementLigne(societe_id=3, compte="5141", date=date(2026, 1, 2),
        montant=100, sens="credit", rapprochee=True, ecriture_ligne_id=ecriture.lignes[0].id,
        rapproche_par=1)
    db.add(ligne)
    db.flush()
    return ligne


def test_patch_ne_derapproche_pas_une_ecriture_cloturee(db):
    exercice(db, 2025, "cloture")
    exercice(db)
    ligne = releve_rapproche(db)
    lien = ligne.ecriture_ligne_id
    with pytest.raises(HTTPException) as exc:
        banque.modifier_ligne(ligne.id, schemas.RapprochementLigneUpdate(rapprochee=False),
                              {"societe_id": 3, "id": 1}, db)
    assert exc.value.status_code == 409
    assert ligne.ecriture_ligne_id == lien
    assert ligne.rapprochee is True


def test_patch_derapproche_sur_dates_ouvertes(db):
    exercice(db, 2025)
    exercice(db)
    ligne = releve_rapproche(db)
    result = banque.modifier_ligne(ligne.id, schemas.RapprochementLigneUpdate(rapprochee=False),
                                   {"societe_id": 3, "id": 1}, db)
    assert result.ecriture_ligne_id is None
    assert result.rapprochee is False


@pytest.mark.parametrize("montant", ["NaN", "Infinity", "-Infinity", "0", "-1",
                                     "0.004", "invalide", None, "1e100"])
def test_montants_invalides_refuses_clairement(montant):
    with pytest.raises(HTTPException) as exc:
        banque._montant_releve_valide(montant)
    assert exc.value.status_code == 400


def test_import_valide_entierement_avant_premiere_insertion(db):
    exercice(db)
    data = banque.ImportRapprochementIn(compte="5141", lignes=[
        banque.LigneImportIn(date=date(2026, 1, 2), libelle="Valide", montant=100, sens="credit"),
        banque.LigneImportIn(date=date(2026, 1, 3), libelle="Trop petit", montant="0.004", sens="debit"),
    ])
    with pytest.raises(HTTPException) as exc:
        banque.importer_lignes(data, {"societe_id": 3, "id": 1}, db)
    assert exc.value.status_code == 400
    assert db.query(models.RapprochementLigne).count() == 0


@pytest.mark.parametrize("montant", [float("nan"), float("inf"), 0.004])
def test_creation_refuse_montant_invalide_sans_donnee(db, montant):
    exercice(db)
    data = schemas.RapprochementLigneCreate(compte="5141", date=date(2026, 1, 2),
                                          montant=montant, sens="credit")
    with pytest.raises(HTTPException):
        banque.ajouter_ligne(data, {"societe_id": 3, "id": 1}, db)
    assert db.query(models.RapprochementLigne).count() == 0


def test_creation_arrondit_montant_au_centime(db):
    exercice(db)
    data = schemas.RapprochementLigneCreate(compte="5141", date=date(2026, 1, 2),
                                          montant=Decimal("123.456"), sens="credit")
    ligne = banque.ajouter_ligne(data, {"societe_id": 3, "id": 1}, db)
    assert ligne.montant == 123.46
