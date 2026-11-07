"""Tests des filtres ORM sur une base mémoire strictement isolée.

Ils vérifient le SQL générique date/société/validation et la logique des services,
sans prétendre valider les triggers, migrations ou contraintes PostgreSQL.
"""
from datetime import date, datetime
from decimal import Decimal
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
import models
from services import etic_service as etic


@pytest.fixture
def db(monkeypatch):
    # Les contraintes calendaires PostgreSQL ne sont pas reproduites en SQLite.
    # La borne fixe isole ici les filtres des pièces et mouvements uniquement.
    monkeypatch.setattr(etic, "_bornes", lambda *a: (date(2026, 1, 1), date(2026, 12, 31)))
    engine = create_engine("sqlite+pysqlite:///:memory:")
    tables = [models.Facture, models.LigneFacture,
              models.EcheanceFacture, models.Ecriture, models.LigneEcriture,
              models.EcritureJustificatif, models.LigneAuxiliaireComplement,
              models.Reglement, models.Acompte, models.ImputationAcompte,
              models.Avoir, models.LigneAvoir, models.UtilisationAvoir]
    for model in tables:
        model.__table__.create(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


def facture_source(db, *, type_="vente", societe_id=3, numero="FA-1", jour=date(2026, 6, 1)):
    f = models.Facture(societe_id=societe_id, numero=numero, type=type_, date=jour,
        exercice=jour.year, tiers="Tiers synthétique", tiers_id=1,
        est_validee=True, est_comptabilisee=True, date_echeance=date(2026, 7, 1),
        lignes=[models.LigneFacture(description="Test", quantite=1, prix_unitaire=100, tva=20)])
    db.add(f)
    db.flush()
    compte = "3421" if type_ == "vente" else "4411"
    e = ecriture_source(db, f, jour, Decimal("120"), "VT" if type_ == "vente" else "AC", compte)
    return f, e


def ecriture_source(db, f, jour, montant, journal="BQ", compte="3421", reference=None, validee=True):
    est_vente = f.type == "vente"
    net = montant if est_vente else -montant
    e = models.Ecriture(societe_id=f.societe_id, exercice=jour.year, date=jour,
        journal=journal, libelle="Écriture synthétique", reference=reference or f.numero,
        est_validee=validee, lignes=[models.LigneEcriture(compte=compte,
            debit=max(net, 0), credit=max(-net, 0), tiers_id=1)])
    db.add(e)
    db.flush()
    return e


@pytest.mark.parametrize("jour,reste", [(date(2026, 12, 31), 90), (date(2027, 1, 1), 120)])
def test_reglement_SQL_ignore_evenement_post_cloture(db, jour, reste):
    f, _ = facture_source(db)
    e = ecriture_source(db, f, jour, -Decimal(30))
    db.add(models.Reglement(societe_id=3, facture_id=f.id, tiers="Tiers synthétique",
        date=jour, montant=30, statut="complet", ecriture_id=e.id, est_comptabilisee=True))
    db.flush()
    got = etic._ventilation_factures_par_compte(db, 3, 2026, "vente")["3421"]
    assert got["total_source"] == got["echues"] == reste


@pytest.mark.parametrize("validee", [True, False])
def test_reglement_SQL_exige_ecriture_validee(db, validee):
    f, _ = facture_source(db)
    e = ecriture_source(db, f, date(2026, 7, 1), -Decimal(30), validee=validee)
    db.add(models.Reglement(societe_id=3, facture_id=f.id, tiers="Tiers synthétique",
        date=e.date, montant=30, statut="complet", ecriture_id=e.id, est_comptabilisee=True))
    db.flush()
    got = etic._ventilation_factures_par_compte(db, 3, 2026, "vente")["3421"]
    assert got["total_source"] == 90
    assert got["echues"] == (90 if validee else 0)


def test_sources_autre_societe_n_interferent_pas(db):
    f, _ = facture_source(db)
    facture_source(db, societe_id=4)
    db.add(models.Reglement(societe_id=4, facture_id=f.id, tiers="Autre société",
        date=date(2026, 7, 1), montant=30, statut="complet"))
    db.flush()
    got = etic._ventilation_factures_par_compte(db, 3, 2026, "vente")["3421"]
    assert got["nb_factures"] == 1
    assert got["echues"] == 120


@pytest.mark.parametrize("jour,reste", [(date(2026, 12, 31), 120), (date(2027, 1, 1), 90)])
def test_annulation_SQL_utilise_date_comptable_meme_si_horodatage_different(db, jour, reste):
    f, _ = facture_source(db)
    e = ecriture_source(db, f, date(2026, 7, 1), -Decimal(30))
    inverse = ecriture_source(db, f, jour, Decimal(30), reference="ANN-REG")
    inverse.contrepassation_de_id = e.id
    db.add(models.Reglement(societe_id=3, facture_id=f.id, tiers="Tiers synthétique",
        date=e.date, montant=30, statut="annule", ecriture_id=e.id,
        ecriture_annulation_id=inverse.id, date_annulation=datetime(2027, 2, 1), est_comptabilisee=True))
    db.flush()
    got = etic._ventilation_factures_par_compte(db, 3, 2026, "vente")["3421"]
    assert got["total_source"] == got["echues"] == reste


@pytest.mark.parametrize("jour,reste", [(date(2026, 12, 31), 90), (date(2027, 1, 1), 120)])
def test_avoir_SQL_ne_reduit_pas_N_si_piece_en_N1(db, jour, reste):
    f, _ = facture_source(db)
    av = models.Avoir(societe_id=3, facture_id=f.id, type="vente", numero="AV-02",
        date=jour, exercice=jour.year, tiers="Tiers synthétique", est_comptabilisee=True,
        lignes=[models.LigneAvoir(description="Test", quantite=1, prix_unitaire=25, tva=20)])
    db.add(av)
    ecriture_source(db, f, jour, -Decimal(30), journal="AV", reference="AV-02")
    db.flush()
    got = etic._ventilation_factures_par_compte(db, 3, 2026, "vente")["3421"]
    assert got["total_source"] == got["echues"] == reste


def test_facture_anterieure_retrouve_sa_principale_historique(db):
    facture_source(db, jour=date(2025, 6, 1))
    got = etic._ventilation_factures_par_compte(db, 3, 2026, "vente")["3421"]
    assert got["echues"] == 120
