"""Transitions réelles sur ORM isolé : la date bancaire est celle de l'opération.

La résolution des exercices/périodes est injectée ; leurs triggers PostgreSQL ne
sont pas reproduits dans SQLite.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from pydantic import ValidationError

import models
from routers import commercial


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for model in [models.Reglement, models.Facture, models.LigneFacture,
                  models.Ecriture, models.LigneEcriture]:
        model.__table__.create(engine)
    monkeypatch.setattr(commercial, "_exercice_ref", lambda db, sid, jour: jour.year)
    monkeypatch.setattr(commercial, "rattacher_tiers_aux_lignes", lambda *a, **k: None)
    monkeypatch.setattr(commercial, "compte_tresorerie", lambda *a, **k: "5141")
    monkeypatch.setattr(commercial, "compte_tiers_facture", lambda *a, **k: "3421")
    monkeypatch.setattr(commercial, "compte_tiers", lambda *a, **k: "3421")
    monkeypatch.setattr(commercial, "_maj_statut_facture", lambda *a: None)
    monkeypatch.setattr(commercial, "_verifier_date_operation_ouverte", lambda *a: None)
    with Session(engine) as session:
        yield session
    engine.dispose()


def reglement(db, mode="cheque", statut="portefeuille", achat=False):
    facture = models.Facture(societe_id=3, numero="FA-TEST", type="achat" if achat else "vente",
                            tiers="Tiers fictif", date=date(2025, 1, 1), exercice=2025)
    db.add(facture)
    db.flush()
    r = models.Reglement(societe_id=3, numero="REG-TEST", facture_id=facture.id,
                         date=date(2025, 1, 2), tiers="Tiers fictif", montant=120,
                         mode=mode, statut=statut, reference="REF-TEST",
                         date_echeance=date(2025, 2, 1) if mode == "effet" else None)
    db.add(r)
    db.flush()
    return r


def transition(db, r, action, jour=date(2025, 2, 5), frais=0):
    return commercial.transition_reglement(r.id, commercial.TransitionIn(
        action=action, date_effective=jour, frais=frais), {"societe_id": 3, "id": 1}, db)


@pytest.mark.parametrize("mode,src,dst", [("cheque", "51111", "51112"), ("effet", "3425", "51132")])
def test_remise_utilise_date_du_bordereau_et_exercice_historique(db, monkeypatch, mode, src, dst):
    dates_controlees = []
    monkeypatch.setattr(commercial, "_verifier_date_operation_ouverte",
                        lambda db, sid, jour, *args: dates_controlees.append(jour))
    r = reglement(db, mode=mode)
    transition(db, r, "remettre", date(2025, 1, 5))
    ec = db.query(models.Ecriture).one()
    assert ec.date == ec.date_piece == date(2025, 1, 5)
    assert ec.exercice == 2025
    assert dates_controlees == [date(2025, 1, 5)]
    assert {l.compte: (Decimal(str(l.debit)), Decimal(str(l.credit))) for l in ec.lignes} == {
        dst: (Decimal("120"), Decimal("0")), src: (Decimal("0"), Decimal("120"))}
    assert r.statut == "encaissement"
    assert r.date_echeance == (date(2025, 2, 1) if mode == "effet" else None)


@pytest.mark.parametrize("mode,statut,src", [("cheque", "portefeuille", "51111"),
    ("cheque", "encaissement", "51112"), ("effet", "portefeuille", "3425"),
    ("effet", "encaissement", "51132")])
def test_rejet_date_reelle_reouvre_creance_et_preserve_echeance(db, mode, statut, src):
    r = reglement(db, mode=mode, statut=statut)
    transition(db, r, "rejeter", frais=5)
    ec = db.query(models.Ecriture).one()
    assert ec.date == ec.date_piece == date(2025, 2, 5)
    assert ec.exercice == 2025
    assert {l.compte: (Decimal(str(l.debit)), Decimal(str(l.credit))) for l in ec.lignes} == {
        "3421": (Decimal("125"), Decimal("0")), src: (Decimal("0"), Decimal("120")),
        "7127": (Decimal("0"), Decimal("5"))}
    assert r.statut == "rejete"
    assert r.date_encaissement is None
    assert r.date_echeance == (date(2025, 2, 1) if mode == "effet" else None)


@pytest.mark.parametrize("action,achat,statut_final", [("encaisser", False, "encaisse"),
                                                       ("payer", True, "paye")])
def test_encaissement_et_paiement_conservent_date_effective(db, action, achat, statut_final):
    r = reglement(db, mode="effet", statut="a_payer" if achat else "encaissement", achat=achat)
    transition(db, r, action)
    assert r.statut == statut_final
    assert r.date_encaissement == date(2025, 2, 5)
    assert db.query(models.Ecriture).one().date == date(2025, 2, 5)


@pytest.mark.parametrize("action", ["remettre", "rejeter"])
def test_ui_ancienne_sans_date_reste_compatible(db, action):
    r = reglement(db)
    transition(db, r, action, jour=None)
    assert db.query(models.Ecriture).one().date == date.today()


@pytest.mark.parametrize("action", ["remettre", "rejeter"])
@pytest.mark.parametrize("jour", ["avant_reception", "demain"])
def test_date_avant_reception_ou_future_refusee_sans_mutation(db, action, jour):
    jour = date(2025, 1, 1) if jour == "avant_reception" else date.today() + timedelta(days=1)
    r = reglement(db)
    with pytest.raises(HTTPException) as exc:
        transition(db, r, action, jour)
    assert exc.value.status_code == 400
    assert r.statut == "portefeuille"
    assert db.query(models.Ecriture).count() == 0


def test_periode_fermee_refuse_remise_historique(db, monkeypatch):
    def periode_fermee(*args):
        raise HTTPException(423, "Période fermée")
    monkeypatch.setattr(commercial, "_verifier_date_operation_ouverte", periode_fermee)
    r = reglement(db)
    with pytest.raises(HTTPException) as exc:
        transition(db, r, "remettre")
    assert exc.value.status_code == 423
    assert r.statut == "portefeuille"
    assert db.query(models.Ecriture).count() == 0


def test_remise_repetee_ne_genere_pas_deux_ecritures(db):
    r = reglement(db)
    transition(db, r, "remettre")
    with pytest.raises(HTTPException):
        transition(db, r, "remettre")
    assert db.query(models.Ecriture).count() == 1


@pytest.mark.parametrize("frais", [float("nan"), float("inf"), -1])
def test_frais_non_finis_ou_negatifs_refuses(frais):
    with pytest.raises(ValidationError):
        commercial.TransitionIn(action="encaisser", frais=frais)


def test_frais_depassement_centime_ne_cree_pas_debit_bancaire_negatif(db):
    r = reglement(db)
    with pytest.raises(HTTPException) as exc:
        transition(db, r, "encaisser", frais=120.01)
    assert exc.value.status_code == 422
    assert db.query(models.Ecriture).count() == 0
