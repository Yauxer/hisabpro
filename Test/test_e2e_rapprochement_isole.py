"""Import CSV et rapprochement UI réelle sur PostgreSQL éphémère uniquement."""
from datetime import date
from decimal import Decimal
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def test_csv_credit_pointage_soldes_rechargement_et_doublon_ui_reels(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = f"banque-{suffix}@example.com", "BanqueE2E132!"
    jour = date.today()
    reference = "VIR-FICTIF-" + suffix
    libelle = "Apport fictif E2E " + suffix
    with httpx.Client(base_url=application["api_url"]) as api:
        response = api.post("/api/auth/register", json={"nom": "Administrateur banque", "email": email,
                            "password": password, "raison_sociale": f"Banque fictive {suffix}"})
        assert response.status_code == 200, response.text
        api.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        response = api.post("/api/ecritures", json={"date": jour.isoformat(), "journal": "BQ",
                            "libelle": libelle, "reference": reference, "est_validee": True,
                            "lignes": [{"compte": "5141", "debit": 1200}, {"compte": "1111", "credit": 1200}]})
        assert response.status_code == 201, response.text
        eid = response.json()["id"]
        lid = next(l["id"] for l in response.json()["lignes"] if l["compte"] == "5141")
        with Session(application["engine"]) as db:
            ecriture = db.get(models.Ecriture, eid)
            sid = ecriture.societe_id
            assert ecriture.est_validee
            avant = {(l.id, l.compte, l.debit, l.credit) for l in ecriture.lignes}
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
                connexion(page, application["web_url"], email, password)
                page.goto(application["web_url"] + "/rapprochement", wait_until="domcontentloaded")
                compta = page.locator("tbody tr").filter(has_text=reference)
                compta.get_by_text("À rapprocher", exact=True).wait_for()
                csv = f"Date;Libellé;Débit;Crédit\r\n{jour.strftime('%d/%m/%Y')};{libelle};;1 200,00\r\n"
                fichier = {"name": "releve-fictif-e2e.csv", "mimeType": "text/csv", "buffer": csv.encode("utf-8-sig")}
                page.get_by_role("button", name="Import Excel / CSV", exact=True).click()
                page.locator('input[type="file"]').set_input_files(fichier)
                page.get_by_role("button", name="Enregistrer le relevé", exact=True).wait_for()
                with page.expect_response(lambda r: r.url.endswith("/api/rapprochement/import") and r.request.method == "POST") as importation:
                    page.get_by_role("button", name="Enregistrer le relevé", exact=True).click()
                assert importation.value.status == 201, importation.value.text()
                resultat = importation.value.json()
                assert resultat["nb_creees"] == 1 and resultat["nb_ignorees"] == 0
                rid = resultat["lignes"][0]["id"]
                page.get_by_text("Import enregistré : 1 ligne(s), 0 doublon(s) ignoré(s).", exact=True).wait_for()
                releve = page.locator("tbody tr").filter(has_text=libelle).filter(has=page.locator("select"))
                releve.locator("select").wait_for()
                assert releve.get_by_text("+1.200,00", exact=True).count() == 1
                # Chaque perte de focus enregistre réellement les soldes déclarés.
                page.get_by_placeholder("Début de période", exact=True).fill("0")
                with page.expect_response(lambda r: r.url.endswith("/api/rapprochement/5141/etat") and r.request.method == "PUT") as initial:
                    page.get_by_placeholder("Facultatif : solde indiqué par la banque", exact=True).click()
                assert initial.value.status == 200, initial.value.text()
                page.get_by_placeholder("Facultatif : solde indiqué par la banque", exact=True).fill("1200")
                with page.expect_response(lambda r: r.url.endswith("/api/rapprochement/5141/etat") and r.request.method == "PUT") as final:
                    page.get_by_role("heading", name="Rapprochement bancaire", exact=True).click()
                assert final.value.status == 200, final.value.text()
                page.get_by_text("✓ Équilibré", exact=True).wait_for()
                page.get_by_text("✓ Initial + mouvements = final", exact=True).wait_for()
                with page.expect_response(lambda r: r.url.endswith(f"/api/rapprochement/{rid}/rapprocher") and r.request.method == "POST") as pointage:
                    releve.locator("select").select_option(str(lid))
                assert pointage.value.status == 200, pointage.value.text()
                compta.get_by_text("Rapprochée", exact=True).wait_for()
                playwright.expect(releve.locator("select")).to_have_value(str(lid))
                verifier_persistance(application, sid, eid, lid, rid, avant)
                page.reload(wait_until="domcontentloaded")
                compta.get_by_text("Rapprochée", exact=True).wait_for()
                playwright.expect(releve.locator("select")).to_have_value(str(lid))
                assert Decimal(page.get_by_placeholder("Début de période", exact=True).input_value()) == 0
                assert Decimal(page.get_by_placeholder("Facultatif : solde indiqué par la banque", exact=True).input_value()) == 1200
                page.get_by_text("✓ Équilibré", exact=True).wait_for()
                page.get_by_role("button", name="Import Excel / CSV", exact=True).click()
                page.locator('input[type="file"]').set_input_files(fichier)
                page.get_by_role("button", name="Enregistrer le relevé", exact=True).click()
                page.get_by_text("Import enregistré : 0 ligne(s), 1 doublon(s) ignoré(s).", exact=True).wait_for()
                verifier_persistance(application, sid, eid, lid, rid, avant)
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print("Page bancaire fictive :", page.url, page.locator("body").inner_text()[:6000])
                print("Erreurs JavaScript/API :", errors, server_errors)
                print("Log API isolée :", application["api_log"].read_text(encoding="utf-8", errors="replace")[-8000:])
                raise
            finally:
                browser.close()


def verifier_persistance(application, sid, eid, lid, rid, avant):
    with Session(application["engine"]) as db:
        releve = db.get(models.RapprochementLigne, rid)
        assert releve.societe_id == sid and releve.compte == "5141"
        assert releve.rapprochee and releve.ecriture_ligne_id == lid
        assert releve.sens == "credit" and Decimal(str(releve.montant)) == 1200
        assert releve.date_rapprochement and releve.rapproche_par
        assert db.query(models.RapprochementLigne).filter_by(societe_id=sid).count() == 1
        etat = db.query(models.RapprochementEtat).filter_by(societe_id=sid, compte="5141").one()
        assert etat.solde_initial == 0 and etat.solde_final == 1200
        ecriture = db.get(models.Ecriture, eid)
        assert ecriture.est_validee
        assert {(l.id, l.compte, l.debit, l.credit) for l in ecriture.lignes} == avant
        assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 1
