"""Clôture et AN sur PostgreSQL neuf ; règles métier et routes non simulées."""
from decimal import Decimal
import pytest

from sqlalchemy import text
from sqlalchemy.orm import Session

import models
from routers import cloture
from services.fec_exercice_service import controler_fec_exercice
from test_session132_operations_postgres import (
    engine, dossier, client, reponse_ok,
    test_api_pg_factures_reglement_avoir_stock_et_journal_coherents as preparer_parcours,
)


@pytest.mark.parametrize("collectif_net_nul", [False, True])
def test_api_pg_cloture_2025_genere_AN_2026_et_preserve_integrite(engine, dossier, client, collectif_net_nul):
    client.app.include_router(cloture.router)
    preparer_parcours(engine, dossier, client)
    auxiliaires_attendus = {}
    if collectif_net_nul:
        vente = next(f for f in reponse_ok(client.get("/api/factures?exercice=2025")) if f["type"] == "vente")
        solde = reponse_ok(client.post("/api/reglements", json={"date": "2025-05-05", "facture_id": vente["id"],
            "tiers": "Client fictif PG", "montant": 360, "mode": "virement", "reference": "VIR-SOLDE-PG", "comptabiliser": True}), 201)
        reponse_ok(client.post(f"/api/ecritures/{solde['ecriture_id']}/valider"))
        with Session(engine) as db:
            a = models.Tiers(societe_id=dossier["societe_id"], type="client", nom="Client A historique", categorie_fiscale="particulier")
            b = models.Tiers(societe_id=dossier["societe_id"], type="client", nom="Client B historique", categorie_fiscale="particulier")
            db.add_all([a, b])
            db.commit()
            a_id, b_id = a.id, b.id
        ec = reponse_ok(client.post("/api/ecritures", json={"date": "2025-12-31", "journal": "OD",
            "libelle": "Soldes individuels synthétiques opposés", "reference": "AUX-PG-01",
            "est_validee": True, "lignes": [{"compte": "3421", "debit": 500, "tiers_id": a_id},
                                           {"compte": "3421", "credit": 500, "tiers_id": b_id}]}), 201)
        auxiliaires_attendus = {l["tiers_id"]: (Decimal(str(l["debit"] - l["credit"])), l["compte_auxiliaire_snapshot"],
                                               l["libelle_auxiliaire_snapshot"]) for l in ec["lignes"]}
        with Session(engine) as db:
            db.get(models.Tiers, a_id).nom = "Client A renommé après validation"
            db.commit()
        apercu = reponse_ok(client.get("/api/cloture/etat?exercice=2025"))["apercu_a_nouveaux"]
        assert {l["tiers_id"] for l in apercu if l["compte"] == "3421"} == {a_id, b_id}
    with Session(engine) as db:
        controle = controler_fec_exercice(db, dossier["societe_id"], 2025)
        assert controle["conforme_export"], controle["bloquants"]
    fin = reponse_ok(client.post("/api/cloture/cloturer?exercice=2025"))
    assert fin["a_nouveaux_sur"] == 2026
    with Session(engine) as db:
        trace = db.query(models.ClotureExercice).filter_by(societe_id=dossier["societe_id"], exercice=2025).one()
        exercice = db.query(models.ExerciceComptable).filter_by(societe_id=dossier["societe_id"], annee=2025).one()
        assert exercice.statut == "cloture"
        assert all(p.statut == "fermee" for p in db.query(models.PeriodeComptable).filter_by(exercice_id=exercice.id))
        solde = db.execute(text("""SELECT l.compte,SUM(l.debit-l.credit)
            FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id
            WHERE e.societe_id=:sid AND e.exercice=2025 GROUP BY l.compte"""),
            {"sid": dossier["societe_id"]}).all()
        assert all(montant == 0 for compte, montant in solde if compte.startswith(("6", "7", "8")))
        an = db.get(models.Ecriture, trace.ecriture_an_id)
        assert an.est_validee and an.journal == models.JournalEnum.AN
        assert an.exercice == 2026 and an.reference == "AN-2026"
        assert sum(Decimal(str(l.debit-l.credit)) for l in an.lignes) == 0
        for ligne in an.lignes:
            if ligne.compte == "3421" and auxiliaires_attendus:
                attendu = auxiliaires_attendus.pop(ligne.tiers_id)
                assert (ligne.debit - ligne.credit, ligne.compte_auxiliaire_snapshot, ligne.libelle_auxiliaire_snapshot) == attendu
        assert auxiliaires_attendus == {}
        assert fin["resultat_net"] == -2700  # Résultat300 - cotisation minimale3000, sans acomptes.
        assert trace.resultat_net == Decimal("-2700")
        assert db.get(models.Ecriture, trace.ecriture_resultat_id).journal == models.JournalEnum.CL
        controle_2026 = controler_fec_exercice(db, dossier["societe_id"], 2026)
        assert controle_2026["conforme_export"], controle_2026["bloquants"]
    assert client.post("/api/cloture/cloturer?exercice=2025").status_code == 400
    refuse = client.post("/api/ecritures", json={"date": "2025-12-31", "journal": "OD", "reference": "APRES-CLOTURE",
        "libelle": "Tentative après clôture", "lignes": [{"compte": "5141", "debit": 1}, {"compte": "1111", "credit": 1}]})
    assert refuse.status_code == 423, refuse.text
