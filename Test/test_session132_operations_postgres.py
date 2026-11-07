"""Vrais verrous et routes sur PostgreSQL éphémère propre à ce test.

Les mutations n'atteignent jamais DATABASE_URL ni une instance existante. Le
marqueur, le rôle, l'URL et le chemin du cluster sont contrôlés avant DDL.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from pathlib import Path
from threading import Barrier, Event

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

import models
from services import stock_movement_service as stock
from services.exercices_service import ensure_exercice
from postgres_isole import cluster_isole, verifier_cible_isolee
from auth import get_current_user, requiert_ecriture
from database import get_db
from routers import factures, commercial, ecritures, inventaire, articles
import avoirs

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ["001_accounting_integrity.sql", "008_exercices_periodes.sql",
              "012_stock_movement_engine.sql", "013_audit_ecritures.sql",
              "014_ecriture_metadata.sql", "017_ecriture_numero_large_sequence.sql",
              "018_numero_ecriture_a_validation.sql", "029_factures_validation.sql",
              "019_journal_cloture_dedie.sql",
              "030_facturation_durcissement.sql", "038_compta3_avis24_durcissement.sql",
              "047_compta_final_audit.sql", "048_rapprochement_bancaire_final.sql",
              "053_comptabilite_auxiliaire_avis24.sql",
              "055_plan_comptable_societe_exercices_decales.sql", "059_ouverture_periodes_comptables.sql",
              "072_integrite_ecritures_definitives.sql", "072_integrite_ecritures_definitives.sql"]


@pytest.fixture(scope="module")
def engine():
    with cluster_isole() as cible:
        assert verifier_cible_isolee(cible["url"], cible["directory"], cible["nonce"])
        engine = create_engine(cible["url"], connect_args={"options": "-c statement_timeout=15000 -c lock_timeout=10000"})
        try:
            models.Base.metadata.create_all(engine)
            connection = engine.raw_connection()
            try:
                connection.autocommit = True
                with connection.cursor() as cursor:
                    cursor.execute("CREATE ROLE hisabpro NOLOGIN")
                    for nom in MIGRATIONS:
                        assert verifier_cible_isolee(cible["url"], cible["directory"], cible["nonce"])
                        cursor.execute((ROOT / "hisabpro-backend" / nom).read_text(encoding="utf-8"))
            finally:
                connection.close()
            yield engine
        finally:
            engine.dispose()


@pytest.fixture
def dossier(engine):
    with Session(engine, expire_on_commit=False) as db:
        societe = models.Societe(raison_sociale="Société fictive PG isolé", regime_tva="encaissement")
        db.add(societe)
        db.flush()
        ex = ensure_exercice(db, societe.id, 2026)
        article = models.Article(societe_id=societe.id, code="A-PG", designation="Article synthétique",
                                stock_actuel=10, cmup=100, prix_achat_ht=100, is_stockable=True,
                                compte_achat="6111", compte_vente="7111")
        utilisateur = models.Utilisateur(societe_id=societe.id, nom="Recette isolée",
            email=f"recette{societe.id}@example.invalid", hashed_password="non_utilise", role="admin")
        db.add_all([article, utilisateur, models.ModuleActif(societe_id=societe.id, module="comptabilite", actif=True)])
        db.commit()
        return {"societe_id": societe.id, "article_id": article.id, "exercice_id": ex.id,
                "user_id": utilisateur.id}


def concurrents(engine, dossier, operations):
    depart = Barrier(len(operations))
    def appliquer(operation):
        with Session(engine, expire_on_commit=False) as db:
            article = db.get(models.Article, dossier["article_id"])
            assert article.stock_actuel == 10  # Objet chargé avant toute attente.
            depart.wait(timeout=10)
            try:
                mvt = stock.enregistrer_mouvement(db, dossier["societe_id"], article,
                    operation["type"], operation["quantite"], cout_unitaire=operation.get("cout"),
                    date_mouvement=date(2026, 5, 1), cle_idempotence=operation["cle"],
                    source_type="recette_isolee", source_id=1)
                db.commit()
                return {"id": mvt.id}
            except ValueError as exc:
                db.rollback()
                return {"erreur": str(exc)}
    with ThreadPoolExecutor(max_workers=len(operations)) as executor:
        resultats = list(executor.map(appliquer, operations))
    return resultats


def test_verrou_pg_cmup_concurrent_et_objets_orm_perimes(engine, dossier):
    resultats = concurrents(engine, dossier, [
        {"type": "entree", "quantite": 10, "cout": 200, "cle": "entree:1"},
        {"type": "entree", "quantite": 10, "cout": 300, "cle": "entree:2"}])
    assert all("id" in r for r in resultats)
    with Session(engine) as db:
        article = db.get(models.Article, dossier["article_id"])
        assert article.stock_actuel == 30
        assert article.cmup == 200
        mouvements = db.query(models.MouvementStock).filter_by(article_id=article.id).order_by(models.MouvementStock.id).all()
        assert len(mouvements) == 2
        assert mouvements[0].stock_avant == 10
        assert mouvements[0].stock_apres == mouvements[1].stock_avant == 20
        assert mouvements[1].stock_apres == 30


def test_verrou_pg_refuse_seconde_sortie_insuffisante(engine, dossier):
    resultats = concurrents(engine, dossier, [
        {"type": "sortie", "quantite": 8, "cle": "sortie:1"},
        {"type": "sortie", "quantite": 8, "cle": "sortie:2"}])
    assert sum("id" in r for r in resultats) == 1
    assert sum("Stock insuffisant" in r.get("erreur", "") for r in resultats) == 1
    with Session(engine) as db:
        assert db.get(models.Article, dossier["article_id"]).stock_actuel == 2
        assert db.query(models.MouvementStock).filter_by(article_id=dossier["article_id"]).count() == 1


def test_verrou_pg_idempotence_concurrente_ne_mutile_pas_stock(engine, dossier):
    operation = {"type": "entree", "quantite": 5, "cout": 200, "cle": "retry:identique"}
    resultats = concurrents(engine, dossier, [operation, operation])
    assert all("id" in r for r in resultats)
    assert resultats[0]["id"] == resultats[1]["id"]
    with Session(engine) as db:
        article = db.get(models.Article, dossier["article_id"])
        assert article.stock_actuel == 15
        assert article.cmup == 133.3333
        assert db.query(models.MouvementStock).filter_by(article_id=article.id).count() == 1


def ecriture_brouillon(db, dossier, *, debit=100, credit=100):
    ec = models.Ecriture(societe_id=dossier["societe_id"], exercice=2026, date=date(2026, 5, 1),
        journal="OD", libelle="Écriture synthétique isolée", est_validee=False,
        lignes=[models.LigneEcriture(compte="5141", debit=debit, credit=0),
                models.LigneEcriture(compte="1111", debit=0, credit=credit)])
    db.add(ec)
    db.commit()
    return ec


@pytest.mark.parametrize("mutation", ["entete", "ligne", "suppression", "deplacement_ligne"])
def test_pg_ecriture_definitive_et_lignes_inalterables(engine, dossier, mutation):
    with Session(engine, expire_on_commit=False) as db:
        ec = ecriture_brouillon(db, dossier)
        ec.est_validee = True
        db.commit()
        db.refresh(ec)
        assert ec.numero_ecriture == "OD-2026-0001"
        if mutation == "deplacement_ligne":
            destination = ecriture_brouillon(db, dossier)
        with pytest.raises(DBAPIError):
            if mutation == "entete":
                db.execute(text("UPDATE ecritures SET libelle='Altération interdite' WHERE id=:id"), {"id": ec.id})
            elif mutation == "ligne":
                db.execute(text("UPDATE lignes_ecriture SET debit=200 WHERE ecriture_id=:id AND debit>0"), {"id": ec.id})
            elif mutation == "deplacement_ligne":
                db.execute(text("UPDATE lignes_ecriture SET ecriture_id=:nouveau WHERE ecriture_id=:id AND debit>0"),
                           {"id": ec.id, "nouveau": destination.id})
            else:
                db.execute(text("DELETE FROM ecritures WHERE id=:id"), {"id": ec.id})
            db.commit()
        db.rollback()
        assert db.execute(text("SELECT COUNT(*) FROM audit_ecritures WHERE ecriture_id=:id"), {"id": ec.id}).scalar() >= 3


@pytest.mark.parametrize("debit,credit", [(100, 99), (0, 0), (Decimal("NaN"), Decimal("NaN"))])
def test_pg_validation_SQL_directe_refuse_ecriture_desequilibree(engine, dossier, debit, credit):
    with Session(engine, expire_on_commit=False) as db:
        ec = ecriture_brouillon(db, dossier, debit=debit, credit=credit)
        with pytest.raises(DBAPIError):
            ec.est_validee = True
            db.commit()
        db.rollback()
        db.refresh(ec)
        assert ec.est_validee is False
        assert ec.numero_ecriture is None


def test_pg_validation_et_modification_ligne_concurrentes(engine, dossier):
    with Session(engine, expire_on_commit=False) as db:
        ec = ecriture_brouillon(db, dossier)
        ec_id = ec.id
        # L'UPDATE verrouille déjà le parent ; le second écrivain doit attendre
        # puis constater que la validation a rendu la ligne intangible.
        ec.est_validee = True
        db.flush()
        depart = Event()
        def changer_ligne():
            with Session(engine) as autre:
                depart.set()
                try:
                    autre.execute(text("UPDATE lignes_ecriture SET debit=200 WHERE ecriture_id=:id AND debit>0"),
                                  {"id": ec_id})
                    autre.commit()
                    return "modification acceptée"
                except DBAPIError:
                    autre.rollback()
                    return "modification refusée"
        with ThreadPoolExecutor(max_workers=1) as executor:
            resultat = executor.submit(changer_ligne)
            assert depart.wait(timeout=5)
            db.commit()
            assert resultat.result(timeout=15) == "modification refusée"
        assert db.execute(text("SELECT SUM(debit) FROM lignes_ecriture WHERE ecriture_id=:id"),
                          {"id": ec_id}).scalar() == 100


def test_pg_periode_fermee_et_exercice_cloture_bloquent_stock(engine, dossier):
    with Session(engine) as db:
        periode = db.query(models.PeriodeComptable).filter_by(exercice_id=dossier["exercice_id"], numero=5).one()
        periode.statut = "fermee"
        db.commit()
        with pytest.raises(ValueError, match="fermée|fermee|non ouverte"):
            stock.enregistrer_mouvement(db, dossier["societe_id"], dossier["article_id"],
                                       "entree", 1, date_mouvement=date(2026, 5, 1))
        assert db.get(models.Article, dossier["article_id"]).stock_actuel == 10


@pytest.fixture
def client(engine, dossier):
    app = FastAPI()
    for router in [factures.router, commercial.router_regl, ecritures.router, avoirs.router, inventaire.router, articles.router]:
        app.include_router(router)
    user = {"societe_id": dossier["societe_id"], "id": dossier["user_id"],
            "role": "admin", "nom": "Recette isolée", "email": "recette@example.invalid"}
    def session_test():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = session_test
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[requiert_ecriture] = lambda: user
    with TestClient(app) as test_client:
        yield test_client


def reponse_ok(response, code=200):
    assert response.status_code == code, response.text
    return response.json()


def test_api_pg_archivage_refuse_stock_puis_preserve_zero(engine, dossier, client):
    url = f"/api/articles/{dossier['article_id']}"
    assert client.delete(url).status_code == 409
    assert client.patch(url, json={"actif": False}).status_code == 409
    assert client.patch(url, json={"is_stockable": False}).status_code == 409
    with Session(engine) as db:
        article = db.get(models.Article, dossier["article_id"])
        assert article.actif and article.is_stockable and article.stock_actuel == 10
        stock.corriger_stock_cible(db, dossier["societe_id"], article, 0,
                                  date_mouvement=date(2026, 5, 1), cle_idempotence="archivage:zero")
        db.commit()
    assert client.delete(url).status_code == 204
    with Session(engine) as db:
        article = db.get(models.Article, dossier["article_id"])
        assert article.actif is False and article.stock_actuel == 0
        assert db.query(models.MouvementStock).filter_by(article_id=article.id).count() == 1
    reponse_ok(client.patch(url, json={"actif": True}))


def test_pg_archivage_et_entree_stock_sont_serialises(engine, dossier):
    with Session(engine) as db:
        article = db.query(models.Article).filter_by(id=dossier["article_id"]).with_for_update().one()
        # Nouveau dossier synthétique : aucun mouvement ni stock physique acquis.
        article.stock_actuel = 0
        article.actif = False
        db.flush()
        depart = Event()
        def entrer():
            with Session(engine) as autre:
                depart.set()
                try:
                    stock.enregistrer_mouvement(autre, dossier["societe_id"], dossier["article_id"],
                        "entree", 1, cout_unitaire=100, date_mouvement=date(2026, 5, 1))
                    autre.commit()
                    return "acceptée"
                except ValueError as exc:
                    autre.rollback()
                    return str(exc)
        with ThreadPoolExecutor(max_workers=1) as executor:
            resultat = executor.submit(entrer)
            assert depart.wait(timeout=5)
            db.commit()
            assert "archivé" in resultat.result(timeout=15)
        assert db.get(models.Article, dossier["article_id"]).stock_actuel == 0
        assert db.query(models.MouvementStock).filter_by(article_id=dossier["article_id"]).count() == 0


def test_api_pg_factures_reglement_avoir_stock_et_journal_coherents(engine, dossier, client):
    with Session(engine) as db:
        # Stock initial du scénario neuf, pas une réparation d'historique.
        article = db.get(models.Article, dossier["article_id"])
        article.stock_actuel = 0
        article.cmup = 0
        ensure_exercice(db, dossier["societe_id"], 2025)
        client_tiers = models.Tiers(societe_id=dossier["societe_id"], type="client", nom="Client fictif PG",
            adresse="Adresse de recette", categorie_fiscale="particulier", compte_client="3421")
        fournisseur = models.Tiers(societe_id=dossier["societe_id"], type="fournisseur", nom="Fournisseur fictif PG",
            adresse="Adresse de recette", categorie_fiscale="professionnel", compte_fournisseur="4411")
        db.add_all([client_tiers, fournisseur])
        db.commit()
        client_id, fournisseur_id = client_tiers.id, fournisseur.id

    achat = reponse_ok(client.post("/api/factures", json={"type": "achat", "date": "2025-05-01",
        "tiers": "Fournisseur fictif PG", "tiers_id": fournisseur_id, "reference": "ACH-PG-01",
        "date_echeance": "2025-06-01", "lignes": [{"article_id": dossier["article_id"],
        "description": "Article synthétique", "quantite": 10, "prix_unitaire": 100, "tva": 20}]}), 201)
    reponse_ok(client.post(f"/api/factures/{achat['id']}/valider"))
    ec_achat = reponse_ok(client.post(f"/api/factures/{achat['id']}/comptabiliser"))["ecriture_id"]
    reponse_ok(client.post(f"/api/ecritures/{ec_achat}/valider"))

    vente = reponse_ok(client.post("/api/factures", json={"type": "vente", "date": "2025-05-02",
        "tiers": "Client fictif PG", "tiers_id": client_id, "date_echeance": "2025-06-02",
        "lignes": [{"article_id": dossier["article_id"], "description": "Article synthétique",
        "quantite": 4, "prix_unitaire": 200, "tva": 20}]}), 201)
    reponse_ok(client.post(f"/api/factures/{vente['id']}/valider"))
    ec_vente = reponse_ok(client.post(f"/api/factures/{vente['id']}/comptabiliser"))["ecriture_id"]
    reponse_ok(client.post(f"/api/ecritures/{ec_vente}/valider"))

    paiement = reponse_ok(client.post("/api/reglements", json={"date": "2025-05-03",
        "facture_id": vente["id"], "tiers": "Client fictif PG", "montant": 360,
        "mode": "virement", "reference": "VIR-PG-01", "comptabiliser": True}), 201)
    assert paiement["ecriture_id"]
    reponse_ok(client.post(f"/api/ecritures/{paiement['ecriture_id']}/valider"))

    detail = next(f for f in reponse_ok(client.get("/api/factures?exercice=2025")) if f["id"] == vente["id"])
    avoir = reponse_ok(client.post("/api/avoirs", json={"facture_id": vente["id"],
        "date": "2025-05-04", "retour_stock": True, "motif": "Retour d'une unité fictive",
        "lignes": [{"facture_ligne_id": detail["lignes"][0]["id"], "quantite": 1}]}), 201)
    ec_avoir = reponse_ok(client.post(f"/api/avoirs/{avoir['id']}/comptabiliser"))["ecriture_id"]
    reponse_ok(client.post(f"/api/ecritures/{ec_avoir}/valider"))

    inventaire_fin = reponse_ok(client.post("/api/inventaire/valider", json={
        "date": "2025-12-31", "reference": "INV-PG-2025", "lignes": [
            {"article_id": dossier["article_id"], "quantite_reelle": 7}]}))
    assert inventaire_fin["total_valeur"] == 700
    ec_stock = reponse_ok(client.post("/api/inventaire/comptabiliser-stock?exercice=2025"))["ecriture_id"]
    reponse_ok(client.post(f"/api/ecritures/{ec_stock}/valider"))
    stock_cloture = reponse_ok(client.get("/api/inventaire/stock/cloture?exercice=2025"))
    assert stock_cloture["stock_rapproche"] is True
    assert stock_cloture["valeur_physique_brute"] == stock_cloture["valeur_comptable_brute"] == 700

    with Session(engine) as db:
        article = db.get(models.Article, dossier["article_id"])
        assert article.stock_actuel == 7
        assert article.cmup == 100
        assert db.query(models.MouvementStock).filter_by(article_id=article.id).count() == 3
        bilan = db.execute(text("""SELECT l.compte, SUM(l.debit-l.credit)
            FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id
            WHERE e.societe_id=:sid AND e.est_validee GROUP BY l.compte"""),
            {"sid": dossier["societe_id"]}).all()
        soldes = dict(bilan)
        assert soldes["6111"] == Decimal("1000")
        assert soldes["34552"] == Decimal("200")
        assert soldes["4411"] == Decimal("-1200")
        assert soldes["7111"] == Decimal("-600")
        assert soldes["4455"] == Decimal("-120")
        assert soldes["3421"] == Decimal("360")
        assert soldes["5141"] == Decimal("360")
        assert soldes["3111"] == Decimal("700")
        assert soldes["6114"] == Decimal("-700")
        # Résultat avant IS : ventes nettes600 - achats1000 + stock final700.
        assert -sum(s for c, s in soldes.items() if c.startswith(("6", "7"))) == 300
        assert sum(soldes.values()) == 0
        finale = db.get(models.Facture, vente["id"])
        situation = factures._situation_paiement_facture(db, dossier["societe_id"], finale)
        assert situation["solde_restant"] == 360
    assert client.post(f"/api/factures/{vente['id']}/comptabiliser").status_code == 409
