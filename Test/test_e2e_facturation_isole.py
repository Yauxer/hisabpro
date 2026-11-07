"""Cycle vente/achat réel : Edge -> FastAPI -> PostgreSQL éphémère.

Prérequis synthétiques par API (société/tiers), aucun appel métier mocké.
"""
from datetime import date
from decimal import Decimal
from pathlib import Path
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from e2e_isole_support import application_isolee
from test_e2e_administration_isole import connexion, observer
from postgres_isole import verifier_cible_isolee
from test_session132_operations_postgres import MIGRATIONS


@pytest.fixture(scope="module")
def application():
    with application_isolee() as app:
        cible = app["cluster"]
        verifier_cible_isolee(cible["url"], cible["directory"], cible["nonce"])
        connection = app["engine"].raw_connection()
        try:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("CREATE ROLE hisabpro NOLOGIN")
                for migration in MIGRATIONS:
                    verifier_cible_isolee(cible["url"], cible["directory"], cible["nonce"])
                    cursor.execute((Path(__file__).resolve().parents[1] / "hisabpro-backend" / migration).read_text(encoding="utf-8"))
        finally:
            connection.close()
        with Session(app["engine"]) as db:
            db.add_all([models.CompteCGNCReference(numero=n, libelle=label,
                        classe=int(n[0]), type_compte="SP") for n, label in [
                        ("7111", "Ventes de marchandises"), ("6111", "Achats de marchandises"),
                        ("4455", "TVA facturée"), ("34552", "TVA récupérable sur charges")]
                        if db.get(models.CompteCGNCReference, n) is None])
            db.commit()
        yield app
    assert all(process.poll() is not None for process in app["processus"])
    assert not app["web_thread"].is_alive()
    assert not app["cluster"]["directory"].exists()
    assert not app["directory"].exists()


def champ(conteneur, label, tag="input"):
    return conteneur.locator("label").filter(has_text=label).locator("..").locator(tag).first


def verifier_ecritures(application, sid, nombre, tiers_id, compte, solde, definitives=False):
    with Session(application["engine"]) as db:
        ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).all()
        assert len(ecritures) == nombre
        for ecriture in ecritures:
            assert ecriture.est_validee is definitives
            assert sum(l.debit for l in ecriture.lignes) == sum(l.credit for l in ecriture.lignes)
        lignes = [l for e in ecritures for l in e.lignes if l.compte == compte]
        assert all(l.tiers_id == tiers_id and l.compte_auxiliaire_snapshot for l in lignes)
        assert sum(l.debit - l.credit for l in lignes) == Decimal(str(solde))


@pytest.mark.parametrize("type_facture", ["vente", "achat"])
def test_facture_validation_reglements_et_lettrage_ui_reels(application, type_facture):
    suffix = uuid.uuid4().hex[:8]
    nom = f"Tiers {type_facture} E2E {suffix}"
    email, password = f"facture-{suffix}@example.com", "FactureE2E132!"
    with httpx.Client(base_url=application["api_url"]) as api:
        response = api.post("/api/auth/register", json={"nom": "Administrateur recette", "email": email,
                            "password": password, "raison_sociale": f"Facturation E2E {suffix}"})
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        api.headers["Authorization"] = "Bearer " + token
        response = api.post("/api/tiers", json={"nom": nom,
                           "type": "client" if type_facture == "vente" else "fournisseur", "delai_paiement": 60})
        assert response.status_code == 201, response.text
        tiers_id = response.json()["id"]
        with Session(application["engine"]) as db:
            sid = db.query(models.Tiers).filter_by(id=tiers_id).one().societe_id
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
                dialogs, requests = [], []
                def accepter(dialog):
                    dialogs.append((dialog.type, dialog.message))
                    dialog.accept()
                page.on("dialog", accepter)
                page.on("request", lambda request: requests.append((request.method, request.url))
                        if request.url.startswith(application["api_url"]) else None)
                connexion(page, application["web_url"], email, password)
                page.goto(application["web_url"] + "/factures", wait_until="domcontentloaded")
                page.get_by_role("button", name="Nouvelle facture", exact=True).click()
                modal = page.get_by_role("dialog", name="Nouvelle facture", exact=True)
                if type_facture == "achat":
                    modal.get_by_role("button", name="Achat", exact=True).click()
                champ(modal, "Date *").fill(date.today().isoformat())
                modal.get_by_placeholder("Rechercher un", exact=False).fill(nom)
                modal.get_by_text(nom, exact=True).click()
                modal.get_by_placeholder("Description ou article...").fill("Marchandise synthétique E2E")
                editor = modal.locator(".hp-invoice-line-editor")
                editor.locator('input[type="number"]').nth(0).fill("2")
                editor.locator('input[type="number"]').nth(1).fill("500")
                if type_facture == "achat":
                    modal.get_by_placeholder("N° porté sur la facture du fournisseur").fill("FR-E2E-" + suffix)
                modal.get_by_role("button", name="Enregistrer en brouillon", exact=False).click()
                with page.expect_response(lambda r: r.url.endswith("/api/factures") and r.request.method == "POST") as creation:
                    modal.get_by_role("button", name="Enregistrer le brouillon", exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                fid = creation.value.json()["id"]
                modal.wait_for(state="hidden")
                row = page.locator("tbody tr").filter(has_text=nom)
                row.locator('button[title="Valider définitivement"]').wait_for()
                with Session(application["engine"]) as db:
                    facture = db.query(models.Facture).filter_by(id=fid).one()
                    assert not facture.est_validee and not facture.numero
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
                with page.expect_response(lambda r: r.url.endswith(f"/api/factures/{fid}/valider")) as validation:
                    row.locator('button[title="Valider définitivement"]').click()
                assert validation.value.status == 200, validation.value.text()
                row.locator('button[title="Générer l\'écriture comptable de cette facture"]').wait_for()
                with page.expect_response(lambda r: r.url.endswith(f"/api/factures/{fid}/comptabiliser")) as compta:
                    row.locator('button[title="Générer l\'écriture comptable de cette facture"]').click()
                assert compta.value.status == 200, compta.value.text()
                compte = "3421" if type_facture == "vente" else "4411"
                signe = 1 if type_facture == "vente" else -1
                verifier_ecritures(application, sid, 1, tiers_id, compte, signe * 1200)
                with Session(application["engine"]) as db:
                    facture_ec = db.query(models.Ecriture).filter_by(societe_id=sid).one()
                    attendu = ({"3421": (1200, 0), "7111": (0, 1000), "4455": (0, 200)}
                               if type_facture == "vente" else
                               {"4411": (0, 1200), "6111": (1000, 0), "34552": (200, 0)})
                    assert {l.compte: (l.debit, l.credit) for l in facture_ec.lignes} == attendu
                for index, montant in enumerate((400, 800)):
                    titre = "Encaisser le client" if type_facture == "vente" else "Payer le fournisseur"
                    row.locator(f'button[title="{titre}"]').click()
                    paiement = page.get_by_role("dialog")
                    champ(paiement, "Montant *").wait_for()
                    assert Decimal(champ(paiement, "Montant *").input_value()) == (1200 if index == 0 else 800)
                    champ(paiement, "Montant *").fill(str(montant))
                    paiement.get_by_placeholder("N° chèque, virement...").fill(f"VIR-{suffix}-{index+1}")
                    with page.expect_response(lambda r: r.url.endswith("/api/reglements") and r.request.method == "POST") as paiement_api:
                        paiement.get_by_role("button", name="Enregistrer", exact=True).click()
                    assert paiement_api.value.status == 201, paiement_api.value.text()
                    paiement.wait_for(state="hidden")
                    verifier_ecritures(application, sid, index + 2, tiers_id, compte, signe * (800 if index == 0 else 0))
                    with Session(application["engine"]) as db:
                        assert db.query(models.Facture).filter_by(id=fid).one().statut.value == ("partiellement_payee" if index == 0 else "payee")
                assert row.locator('button[title="' + titre + '"]').count() == 0
                page.goto(application["web_url"] + "/journal", wait_until="domcontentloaded")
                playwright.expect(page.get_by_role("button", name="Valider", exact=True)).to_have_count(3)
                with page.expect_response(lambda r: r.url.endswith("/api/ecritures/valider-lot") and r.request.method == "POST") as validation_lot:
                    page.get_by_role("button", name="Valider les brouillons", exact=True).click()
                assert validation_lot.value.status == 200, validation_lot.value.text()
                assert validation_lot.value.json()["nb_validees"] == 3
                verifier_ecritures(application, sid, 3, tiers_id, compte, 0, definitives=True)
                with Session(application["engine"]) as db:
                    avant_lettrage = {(l.id, l.ecriture_id, l.compte, l.debit, l.credit, l.tiers_id)
                                     for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(
                                     models.Ecriture.societe_id == sid).all()}
                page.goto(application["web_url"] + "/lettrage", wait_until="domcontentloaded")
                champ(page, "Compte", "select").select_option(compte)
                champ(page, "Tiers", "select").select_option(label=nom)
                page.locator('tbody input[type="checkbox"]').first.wait_for()
                assert page.locator('tbody input[type="checkbox"]').count() == 3
                for box in page.locator('tbody input[type="checkbox"]').all():
                    box.check()
                with page.expect_response(lambda r: "/api/lettrage" in r.url and r.request.method == "POST") as lettrage:
                    page.get_by_role("button", name="Lettrer 3 lignes", exact=True).click()
                assert lettrage.value.status == 200, lettrage.value.text()
                page.get_by_text("3 lettrée(s)", exact=True).wait_for()
                with Session(application["engine"]) as db:
                    lignes = db.query(models.LigneEcriture).join(models.Ecriture).filter(
                        models.Ecriture.societe_id == sid, models.LigneEcriture.compte == compte).all()
                    assert len(lignes) == 3
                    codes = {l.code_lettrage for l in lignes}
                    assert len(codes) == 1 and None not in codes
                    apres_lettrage = {(l.id, l.ecriture_id, l.compte, l.debit, l.credit, l.tiers_id)
                                     for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(
                                     models.Ecriture.societe_id == sid).all()}
                    assert apres_lettrage == avant_lettrage
                page.reload(wait_until="domcontentloaded")
                champ(page, "Compte", "select").select_option(compte)
                champ(page, "Tiers", "select").select_option(label=nom)
                page.get_by_text("3 lettrée(s)", exact=True).wait_for()
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print("Page E2E fictive :", page.url, page.locator("body").inner_text()[:5000])
                print("Erreurs JavaScript/API :", errors, server_errors)
                print("Dialogues/API fictifs :", dialogs, requests[-20:])
                print("Log API isolée :", application["api_log"].read_text(encoding="utf-8", errors="replace")[-12000:])
                raise
            finally:
                browser.close()
