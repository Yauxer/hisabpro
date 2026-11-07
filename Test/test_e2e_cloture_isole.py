"""Clôture via vraie UI/API/PG éphémère, sans simulation métier.

Le dossier synthétique reprend l'oracle API session132 ; ce parcours réduit
ne remplace ni l'exercice annuel complet ni la recette utilisateur.
"""
from decimal import Decimal
import uuid

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from services.fec_exercice_service import controler_fec_exercice
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application
from test_session132_operations_postgres import (
    reponse_ok,
    test_api_pg_factures_reglement_avoir_stock_et_journal_coherents as preparer_parcours,
)


def test_cloture_controles_AN_auxiliaires_et_verrouillage_ui_reels(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = f"cloture-{suffix}@example.com", "ClotureE2E132!"
    with httpx.Client(base_url=application["api_url"], timeout=30) as api:
        inscription = reponse_ok(api.post("/api/auth/register", json={
            "nom": "Administrateur clôture fictive", "email": email, "password": password,
            "raison_sociale": f"Clôture E2E {suffix}"}))
        api.headers["Authorization"] = "Bearer " + inscription["access_token"]
        with Session(application["engine"]) as db:
            utilisateur = db.query(models.Utilisateur).filter_by(email=email).one()
            sid = utilisateur.societe_id
            article = models.Article(societe_id=sid, code="CLOT-E2E", designation="Article synthétique",
                stock_actuel=0, cmup=0, prix_achat_ht=100, is_stockable=True,
                compte_achat="6111", compte_vente="7111")
            db.add(article)
            db.commit()
            dossier = {"societe_id": sid, "article_id": article.id}
        preparer_parcours(application["engine"], dossier, api)
        brouillon = reponse_ok(api.post("/api/ecritures", json={
            "date": "2025-12-31", "journal": "OD", "reference": "CAPITAL-E2E",
            "libelle": "Capital synthétique clôture E2E", "lignes": [
                {"compte": "5141", "debit": 10000}, {"compte": "1111", "credit": 10000}]}), 201)
        avant = reponse_ok(api.get("/api/cloture/etat?exercice=2025"))
        assert avant["nb_ecritures_brouillon"] == 1 and not avant["est_clos"]
        assert api.post("/api/cloture/cloturer?exercice=2025").status_code == 400
        playwright = pytest.importorskip("playwright.sync_api")
        executable = chromium_executable()
        if not executable:
            pytest.skip("Chromium/Edge requis")
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application["api_url"])
                dialogs = []
                def accepter(dialog):
                    dialogs.append((dialog.type, dialog.message))
                    dialog.accept()
                page.on("dialog", accepter)
                connexion(page, application["web_url"], email, password)
                page.goto(application["web_url"] + "/cloture", wait_until="domcontentloaded")
                page.get_by_label("Exercice actif", exact=True).select_option("2025")
                page.get_by_text("1 écriture(s) encore en brouillon", exact=True).wait_for()
                bouton = page.get_by_role("button", name="Clôturer l'exercice 2025", exact=True)
                playwright.expect(bouton).to_be_disabled()
                page.goto(application["web_url"] + "/journal", wait_until="domcontentloaded")
                page.get_by_role("button", name="Valider", exact=True).wait_for()
                with page.expect_response(lambda r: r.url.endswith("/api/ecritures/valider-lot")) as validation:
                    page.get_by_role("button", name="Valider les brouillons", exact=True).click()
                assert validation.value.status == 200, validation.value.text()
                assert validation.value.json()["nb_validees"] == 1
                with Session(application["engine"]) as db:
                    assert db.get(models.Ecriture, brouillon["id"]).est_validee
                    avant_lignes = {(l.id, l.compte, l.debit, l.credit, l.tiers_id,
                                    l.compte_auxiliaire_snapshot, l.libelle_auxiliaire_snapshot)
                        for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(
                            models.Ecriture.societe_id == sid, models.Ecriture.exercice == 2025).all()}
                page.goto(application["web_url"] + "/cloture", wait_until="domcontentloaded")
                bouton = page.get_by_role("button", name="Clôturer l'exercice 2025", exact=True)
                playwright.expect(bouton).to_be_enabled()
                page.get_by_text("✓ FEC conforme", exact=False).wait_for()
                with page.expect_response(lambda r: "/api/cloture/cloturer?exercice=2025" in r.url) as cloture:
                    bouton.click()
                assert cloture.value.status == 200, cloture.value.text()
                assert cloture.value.json()["resultat_net"] == -2700
                assert cloture.value.json()["a_nouveaux_sur"] == 2026
                page.get_by_text("Exercice 2025 clôturé définitivement", exact=False).wait_for()
                assert any(kind == "confirm" and "verrouillé définitivement" in message
                           for kind, message in dialogs)
                with Session(application["engine"]) as db:
                    trace = db.query(models.ClotureExercice).filter_by(societe_id=sid, exercice=2025).one()
                    exercice = db.query(models.ExerciceComptable).filter_by(societe_id=sid, annee=2025).one()
                    assert exercice.statut == "cloture" and all(p.statut == "fermee" for p in exercice.periodes)
                    assert trace.resultat_net == Decimal("-2700")
                    an = db.get(models.Ecriture, trace.ecriture_an_id)
                    assert an.est_validee and an.journal == models.JournalEnum.AN and an.exercice == 2026
                    soldes_an = {}
                    for ligne in an.lignes:
                        soldes_an[ligne.compte] = soldes_an.get(ligne.compte, Decimal(0)) + ligne.debit - ligne.credit
                        if ligne.compte in {"3421", "4411"}:
                            assert ligne.tiers_id and ligne.compte_auxiliaire_snapshot
                    assert soldes_an == {"1111": Decimal(-10000), "3111": Decimal(700),
                        "3421": Decimal(360), "34552": Decimal(200), "4411": Decimal(-1200),
                        "4453": Decimal(-3000), "4455": Decimal(-120), "5141": Decimal(10360),
                        "1199": Decimal(2700)}
                    assert sum(soldes_an.values()) == 0
                    apres_lignes = {(l.id, l.compte, l.debit, l.credit, l.tiers_id,
                                     l.compte_auxiliaire_snapshot, l.libelle_auxiliaire_snapshot)
                        for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(
                            models.Ecriture.societe_id == sid, models.LigneEcriture.id.in_(
                                [l[0] for l in avant_lignes])).all()}
                    assert apres_lignes == avant_lignes
                    soldes_activite = db.execute(text("""SELECT l.compte,SUM(l.debit-l.credit)
                        FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id
                        WHERE e.societe_id=:sid AND e.exercice=2025 GROUP BY l.compte"""), {"sid": sid}).all()
                    assert all(solde == 0 for compte, solde in soldes_activite if compte.startswith(("6", "7", "8")))
                    for annee in (2025, 2026):
                        controle = controler_fec_exercice(db, sid, annee)
                        assert controle["conforme_export"], controle["bloquants"]
                page.get_by_label("Exercice actif", exact=True).select_option("2026")
                page.get_by_role("heading", name="Clôture de l'exercice 2026", exact=True).wait_for()
                page.goto(application["web_url"] + "/journal", wait_until="domcontentloaded")
                page.get_by_text("AN-2026", exact=True).wait_for()
                page.reload(wait_until="domcontentloaded")
                page.get_by_text("AN-2026", exact=True).wait_for()
                page.goto(application["web_url"] + "/cloture", wait_until="domcontentloaded")
                page.get_by_role("heading", name="Clôture de l'exercice 2026", exact=True).wait_for()
                playwright.expect(page.get_by_label("Exercice actif", exact=True)).to_have_value("2026")
                for annee in (2025, 2026):
                    export = api.get(f"/api/fec/export?exercice={annee}")
                    assert export.status_code == 200, export.text
                    assert len(export.content) > 100
                assert api.post("/api/cloture/cloturer?exercice=2025").status_code == 400
                refuse = api.post("/api/ecritures", json={"date": "2025-12-31", "journal": "OD",
                    "reference": "APRES-CLOTURE", "libelle": "Tentative synthétique interdite",
                    "lignes": [{"compte": "5141", "debit": 1}, {"compte": "1111", "credit": 1}]})
                assert refuse.status_code == 423, refuse.text
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print("Page clôture fictive :", page.url, page.locator("body").inner_text()[:7000])
                print("Erreurs JavaScript/API :", errors, server_errors, "Dialogues :", dialogs)
                print("Log API isolée :", application["api_log"].read_text(encoding="utf-8", errors="replace")[-10000:])
                raise
            finally:
                browser.close()

