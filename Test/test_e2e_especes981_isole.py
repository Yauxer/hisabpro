"""981 — alerte « espèces au-delà de 5 000 DH par jour et par fournisseur » : UI Edge et API réelles, PostgreSQL éphémère, données fictives."""
from datetime import date
import uuid

import httpx
import pytest

from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ  # noqa: F401


def test_981_alerte_especes_non_bloquante(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = f"especes-{suffix}@example.com", "EspecesE2E981!"
    jour = date.today().isoformat()
    nom = f"Fournisseur espèces {suffix}"
    with httpx.Client(base_url=application["api_url"]) as api:
        r = api.post("/api/auth/register", json={"nom": "Administrateur espèces", "email": email,
                     "password": password, "raison_sociale": f"Espèces fictives {suffix}"})
        assert r.status_code == 200, r.text
        api.headers["Authorization"] = "Bearer " + r.json()["access_token"]
        assert api.post("/api/ecritures", json={"date": jour, "journal": "CA", "libelle": "Apport fictif981", "est_validee": True,
                        "reference": "APP-E2E-981", "lignes": [{"compte": "5161", "debit": 30000, "credit": 0},
                                                               {"compte": "1111", "debit": 0, "credit": 30000}]}).status_code == 201
        t = api.post("/api/tiers", json={"nom": nom, "type": "fournisseur"}).json()
        f = api.post("/api/factures", json={"type": "achat", "tiers": nom, "tiers_id": t["id"], "date": jour, "ras_taux": 0, "reference": "FA-E2E-981",
                     "lignes": [{"description": "Matériaux fictifs", "quantite": 1, "prix_unitaire": 10000, "tva": 20}]}).json()
        assert api.post(f"/api/factures/{f['id']}/valider").status_code == 200
        assert api.post(f"/api/factures/{f['id']}/comptabiliser").status_code == 200
        r = api.post("/api/reglements", json={"facture_id": f["id"], "tiers": nom, "date": jour, "montant": 4000, "mode": "especes",
                     "reference": "ESP-1", "comptabiliser": True})
        assert r.status_code == 201, r.text
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
            page.goto(application["web_url"] + "/factures", wait_until="domcontentloaded")
            row = page.locator("tbody tr").filter(has_text=nom).first
            row.locator('button[title="Payer le fournisseur"]').click()
            modal = page.get_by_role("dialog")
            champ(modal, "Montant *").fill("2000")
            champ(modal, "Date *").fill(jour)
            champ(modal, "Mode", "select").select_option("especes")
            alerte = modal.get_by_role("alert", name="Limite des paiements en espèces")
            alerte.get_by_text("au-delà de 5 000 DH par jour").wait_for()
            alerte.get_by_text("Le paiement reste possible").wait_for()
            champ(modal, "Mode", "select").select_option("virement")
            alerte.wait_for(state="detached")                 # plus d'alerte avec un moyen admis
            champ(modal, "Mode", "select").select_option("especes")
            alerte.wait_for()
            with page.expect_response(lambda r: r.url.endswith("/api/reglements") and r.request.method == "POST") as rep:
                modal.get_by_role("button", name="Enregistrer", exact=True).click()
            assert rep.value.status == 201, rep.value.text()  # non bloquant
            page.goto(application["web_url"] + "/tresorerie", wait_until="domcontentloaded")
            carte = page.get_by_label("Espèces aux fournisseurs au-delà des limites")
            carte.get_by_text(nom).wait_for()
            assert not errors, errors
            assert not server_errors, server_errors
        except Exception:
            print("Page fictive :", page.url, page.locator("body").inner_text()[:5000])
            print("Erreurs JavaScript/API :", errors, server_errors)
            print("Log API isolée :", application["api_log"].read_text(encoding="utf-8", errors="replace")[-6000:])
            raise
        finally:
            browser.close()
