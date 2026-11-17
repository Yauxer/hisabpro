"""980 — page Trésorerie et « Alimenter la caisse » : UI Edge et API réelles, PostgreSQL éphémère, données fictives."""
from datetime import date
import re
import uuid

import httpx
import pytest

from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application  # noqa: F401


def test_980_page_tresorerie_alimenter_caisse(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = f"treso-{suffix}@example.com", "TresoE2E980!"
    with httpx.Client(base_url=application["api_url"]) as api:
        r = api.post("/api/auth/register", json={"nom": "Administrateur trésorerie", "email": email,
                     "password": password, "raison_sociale": f"Trésorerie fictive {suffix}"})
        assert r.status_code == 200, r.text
        api.headers["Authorization"] = "Bearer " + r.json()["access_token"]
        r = api.post("/api/ecritures", json={"date": date.today().isoformat(), "journal": "BQ", "libelle": "Apport fictif980",
                     "est_validee": True, "reference": "APP-E2E-980",
                     "lignes": [{"compte": "5141", "debit": 20000, "credit": 0}, {"compte": "1111", "debit": 0, "credit": 20000}]})
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
            page.goto(application["web_url"] + "/tresorerie", wait_until="domcontentloaded")
            page.get_by_role("heading", name="Trésorerie", exact=True).wait_for()
            page.get_by_role("link", name="Trésorerie").first.wait_for()  # entrée du menu Comptabilité
            banques = page.locator('[class*="kpiCard"]').filter(has_text="Banques")
            banques.get_by_text(re.compile(r"20[\s.]?000,00")).wait_for()

            page.get_by_role("button", name="Alimenter la caisse").click()
            modal = page.get_by_role("dialog")
            modal.get_by_placeholder("0,00").fill("1500")
            modal.get_by_label("Écritures qui seront passées").get_by_text("5115").first.wait_for()
            with page.expect_response(lambda r: r.url.endswith("/api/tresorerie/virements") and r.request.method == "POST") as rep:
                modal.get_by_role("button", name="Enregistrer").click()
            assert rep.value.status == 201, rep.value.text()
            caisses = page.locator('[class*="kpiCard"]').filter(has_text="Caisses")
            caisses.get_by_text(re.compile(r"1[\s.]?500,00")).wait_for()
            banques.get_by_text(re.compile(r"18[\s.]?500,00")).wait_for()
            page.get_by_text("Derniers mouvements de banque et de caisse").wait_for()
            assert not errors, errors
            assert not server_errors, server_errors
        except Exception:
            print("Page trésorerie fictive :", page.url, page.locator("body").inner_text()[:5000])
            print("Erreurs JavaScript/API :", errors, server_errors)
            print("Log API isolée :", application["api_log"].read_text(encoding="utf-8", errors="replace")[-6000:])
            raise
        finally:
            browser.close()
