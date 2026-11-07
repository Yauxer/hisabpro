"""Acquisition/amortissement : UI Edge et API réelles, PostgreSQL éphémère."""
from datetime import date
from decimal import Decimal
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ


def test_acquisition_plan_acheve_dotations_centimes_et_journal_ui(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = f"immo-{suffix}@example.com", "ImmoE2E132!"
    designation = "Serveur fictif E2E " + suffix
    debut = date.today().year - 3
    annees = list(range(debut, debut + 3))
    with httpx.Client(base_url=application["api_url"]) as api:
        response = api.post("/api/auth/register", json={"nom": "Administrateur immobilisations", "email": email,
                            "password": password, "raison_sociale": f"Immobilisations fictives {suffix}"})
        assert response.status_code == 200, response.text
        api.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        for annee in annees:
            response = api.post("/api/exercices", json={"annee": annee,
                                "date_debut": f"{annee}-01-01", "date_fin": f"{annee}-12-31"})
            assert response.status_code == 201, response.text
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
                page.on("dialog", lambda dialog: dialog.accept())
                connexion(page, application["web_url"], email, password)
                page.goto(application["web_url"] + "/immobilisations", wait_until="domcontentloaded")
                page.get_by_role("button", name="Nouvelle immobilisation", exact=True).click()
                modal = page.locator('[class*="modalOverlay"]').first
                modal.get_by_placeholder("Ex: Serveur Dell PowerEdge", exact=True).fill(designation)
                champ(modal, "Catégorie", "select").select_option("Matériel informatique")
                champ(modal, "Date d’acquisition *").fill(f"{debut}-01-01")
                champ(modal, "Prix d’acquisition HT *").fill("10000")
                champ(modal, "Durée (années)").fill("3")
                with page.expect_response(lambda r: r.url.endswith("/api/immobilisations") and r.request.method == "POST") as creation:
                    modal.get_by_role("button", name="Créer", exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                data = creation.value.json()
                iid, acquisition_id = data["id"], data["ecriture_acquisition_id"]
                assert Decimal(str(data["valeur_brute"])) == 10000
                assert Decimal(str(data["tva_recuperable"])) == 2000
                assert Decimal(str(data["total_ttc"])) == 12000
                modal.wait_for(state="hidden")
                registre = page.locator("tr").filter(has=page.get_by_text(designation, exact=True)).first
                registre.wait_for()
                with Session(application["engine"]) as db:
                    acquisition = db.get(models.Ecriture, acquisition_id)
                    sid = acquisition.societe_id
                    assert not acquisition.est_validee
                    assert {l.compte: (l.debit, l.credit) for l in acquisition.lignes} == {
                        "2355": (10000, 0), "34551": (2000, 0), "4481": (0, 12000)}
                registre.click()
                page.get_by_text(f"Tableau d’amortissement — {designation}", exact=True).wait_for()
                tableau = page.locator("table").filter(has=page.get_by_role("columnheader", name="Prorata", exact=True)).last
                valeurs = [("3.333,33 MAD", "3.333,33 MAD", "6.666,67 MAD"),
                           ("3.333,33 MAD", "6.666,66 MAD", "3.333,34 MAD"),
                           ("3.333,34 MAD", "10.000,00 MAD", "0,00 MAD")]
                for annee, attendu in zip(annees, valeurs):
                    ligne = tableau.locator("tbody tr").filter(has=page.get_by_role("cell", name=str(annee), exact=True))
                    ligne.get_by_role("button", name="Générer", exact=True).wait_for()
                    assert ligne.locator("td").all_text_contents()[3:6] == list(attendu)
                    with page.expect_response(lambda r: f"/api/immobilisations/{iid}/generer-ecriture?annee={annee}" in r.url) as dotation:
                        ligne.get_by_role("button", name="Générer", exact=True).click()
                    assert dotation.value.status == 200, dotation.value.text()
                    assert Decimal(str(dotation.value.json()["dotation"])) == (Decimal("3333.34") if annee == annees[-1] else Decimal("3333.33"))
                    registre.wait_for()
                page.goto(application["web_url"] + "/journal", wait_until="domcontentloaded")
                for annee in annees:
                    page.locator("select").filter(has=page.locator(f'option[value="{annee}"]')).first.select_option(str(annee))
                    nb = 2 if annee == debut else 1
                    playwright.expect(page.get_by_role("button", name="Valider", exact=True)).to_have_count(nb)
                    with page.expect_response(lambda r: r.url.endswith("/api/ecritures/valider-lot") and r.request.method == "POST") as validation:
                        page.get_by_role("button", name="Valider les brouillons", exact=True).click()
                    assert validation.value.status == 200, validation.value.text()
                    assert validation.value.json()["nb_validees"] == nb
                avant = verifier_comptabilite(application, sid, iid)
                page.goto(application["web_url"] + "/immobilisations", wait_until="domcontentloaded")
                registre.wait_for()
                assert "10.000,00 MAD" in registre.locator("td").nth(4).inner_text()
                assert registre.locator("td").nth(5).inner_text() == "0,00 MAD\n10.000,00 amorti"
                with page.expect_response(lambda r: f"/api/immobilisations/generer-dotations-annee?annee={annees[-1]}" in r.url) as reprise:
                    page.get_by_role("button", name=f"Dotations {annees[-1]}", exact=True).click()
                assert reprise.value.status == 200, reprise.value.text()
                assert reprise.value.json()["nb_generees"] == 0
                assert reprise.value.json()["nb_ignorees"] == 1
                assert Decimal(str(reprise.value.json()["total_dotation"])) == 0
                page.reload(wait_until="domcontentloaded")
                registre.wait_for()
                registre.click()
                tableau.locator("tbody tr").last.get_by_role("cell", name="0,00 MAD", exact=True).wait_for()
                assert verifier_comptabilite(application, sid, iid) == avant
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print("Page immobilisations fictive :", page.url, page.locator("body").inner_text()[:6000])
                print("Erreurs JavaScript/API :", errors, server_errors)
                print("Log API isolée :", application["api_log"].read_text(encoding="utf-8", errors="replace")[-8000:])
                raise
            finally:
                browser.close()


def verifier_comptabilite(application, sid, iid):
    with Session(application["engine"]) as db:
        ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).all()
        assert len(ecritures) == 4 and all(e.est_validee for e in ecritures)
        assert all(sum(l.debit for l in e.lignes) == sum(l.credit for l in e.lignes) for e in ecritures)
        lignes = [l for e in ecritures for l in e.lignes]
        assert sum(l.debit for l in lignes if l.compte == "2355") == 10000
        assert sum(l.credit for l in lignes if l.compte == "28355") == 10000
        assert sum(l.debit for l in lignes if l.compte == "61935") == 10000
        assert sum(l.debit for l in lignes if l.compte == "2355") - sum(l.credit for l in lignes if l.compte == "28355") == 0
        immo = db.get(models.Immobilisation, iid)
        assert immo.actif and immo.date_sortie is None and immo.duree_amort == 3
        return {(l.id, l.ecriture_id, l.compte, l.debit, l.credit) for l in lignes}
