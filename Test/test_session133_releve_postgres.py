"""Import et rapprochement API réels sur le seul cluster PostgreSQL isolé."""
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

import models
from routers import rapprochement
from services.exercices_service import ensure_exercice
from test_session132_operations_postgres import engine, dossier, client, reponse_ok
from test_session133_releve_import import lire


@pytest.fixture
def banque(client):
    client.app.include_router(rapprochement.router)
    return client


def ecriture(client, date, reference, debit, credit, montant):
    return reponse_ok(client.post("/api/ecritures", json={"date": date, "reference": reference, "journal": "BQ",
        "libelle": f"Pièce bancaire fictive {reference}", "est_validee": True,
        "lignes": [{"compte": debit, "debit": montant}, {"compte": credit, "credit": montant}]}), 201)


def test_api_pg_csv_fr_import_soldes_et_pointage_sont_coherents(engine, dossier, banque):
    ouverture = ecriture(banque, "2026-01-01", "OUVERTURE-PG", "5141", "1111", 10000)
    entree = ecriture(banque, "2026-04-03", "VIREMENT-PG", "5141", "1111", 1234.56)
    sortie = ecriture(banque, "2026-04-04", "FRAIS-PG", "61473", "5141", 34.56)
    lignes = lire(csv="Date;Libellé;Débit;Crédit\n03/04/2026;002;;1 234,56\n04/04/2026;Frais;34,56;")["lignes"]
    donnees = {"compte": "5141", "lignes": lignes}
    resultat = reponse_ok(banque.post("/api/rapprochement/import", json=donnees), 201)
    assert resultat["nb_creees"] == 2 and resultat["nb_ignorees"] == 0
    ids = [l["id"] for l in resultat["lignes"]]
    reponse_ok(banque.put("/api/rapprochement/5141/etat", json={"date_debut": "2026-04-01",
        "date_fin": "2026-04-30", "solde_initial": 10000, "solde_final": 11200}))
    compte_entree = next(l for l in entree["lignes"] if l["compte"] == "5141")["id"]
    compte_sortie = next(l for l in sortie["lignes"] if l["compte"] == "5141")["id"]
    reponse_ok(banque.post(f"/api/rapprochement/{ids[0]}/rapprocher", json={"ecriture_ligne_id": compte_entree}))
    reponse_ok(banque.post(f"/api/rapprochement/{ids[1]}/rapprocher", json={"ecriture_ligne_id": compte_sortie}))
    etat = reponse_ok(banque.get("/api/rapprochement/5141/situation?date_debut=2026-04-01&date_fin=2026-04-30"))
    assert etat["solde_comptable_final"] == etat["solde_final"] == 11200
    assert etat["solde_initial"] == 10000
    assert all(l["rapprochee"] for l in etat["lignes_releve"])
    assert Decimal(str(sum(l["montant"] * (1 if l["sens"] == "credit" else -1) for l in etat["lignes_releve"]))) == 1200
    reprise = reponse_ok(banque.post("/api/rapprochement/import", json=donnees), 201)
    assert reprise["nb_creees"] == 0 and reprise["nb_ignorees"] == 2
    with Session(engine) as db:
        assert db.query(models.RapprochementLigne).filter_by(societe_id=dossier["societe_id"]).count() == 2
        assert db.query(models.Ecriture).filter_by(societe_id=dossier["societe_id"]).count() == 3


@pytest.mark.parametrize("invalide,code", [
    ({"date": "2026-04-04", "libelle": "Montant zéro", "montant": 0, "sens": "debit"}, 422),
    ({"date": "2026-04-04", "libelle": "Sens absent", "montant": 10, "sens": "inconnu"}, 400),
    ({"date": "2026-02-30", "libelle": "Date impossible", "montant": 10, "sens": "debit"}, 422),
    ({"date": "2025-04-04", "libelle": "Archive clôturée", "montant": 10, "sens": "debit"}, 409),
])
def test_api_pg_ligne_invalide_refuse_lot_entier(engine, dossier, banque, invalide, code):
    if code == 409:
        with Session(engine) as db:
            ex = ensure_exercice(db, dossier["societe_id"], 2025)
            db.flush()  # Créer les périodes avant de figer l'exercice synthétique.
            ex.statut = "cloture"
            for periode in db.query(models.PeriodeComptable).filter_by(exercice_id=ex.id):
                periode.statut = "fermee"
            db.commit()
    resultat = banque.post("/api/rapprochement/import", json={"compte": "5141", "lignes": [
        {"date": "2026-04-03", "libelle": "Ligne correcte", "montant": 1234.56, "sens": "credit"}, invalide]})
    assert resultat.status_code == code, resultat.text
    with Session(engine) as db:
        assert db.query(models.RapprochementLigne).filter_by(societe_id=dossier["societe_id"]).count() == 0
