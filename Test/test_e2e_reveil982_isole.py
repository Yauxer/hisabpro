"""982 — serveur lent au réveil : réveil anticipé et message d'attente à la connexion.

UI Edge et API réelles, PostgreSQL éphémère, données fictives. Le serveur endormi
est simulé en retardant les réponses dans le navigateur ; rien n'est remplacé.
"""
import uuid

import httpx
import pytest

from browser_support import chromium_executable
from test_e2e_administration_isole import observer
from test_e2e_facturation_isole import application  # noqa: F401


def test_982_reveil_api_et_base(application):
    r = httpx.get(application["api_url"] + "/api/health/reveil")
    assert r.status_code == 200 and r.json() == {"status": "ok", "base": "ok"}, r.text


def test_982_message_pendant_le_reveil_puis_connexion(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = f"reveil-{suffix}@example.com", "ReveilE2E982!"
    r = httpx.post(application["api_url"] + "/api/auth/register", json={"nom": "Administrateur réveil", "email": email,
                   "password": password, "raison_sociale": f"Réveil fictif {suffix}"})
    assert r.status_code == 200, r.text
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
            # Serveur « endormi » : les requêtes restent en attente jusqu'à ce que le test les libère.
            reveils, connexions = [], []
            page.route("**/api/health/reveil", lambda route: reveils.append(route))
            page.route("**/api/auth/login", lambda route: connexions.append(route))
            page.goto(application["web_url"], wait_until="domcontentloaded")
            statut = page.get_by_role("status").filter(has_text="Démarrage du serveur")
            statut.wait_for()                                   # message affiché pendant le réveil
            assert len(reveils) == 1                            # un seul réveil, lancé dès l'ouverture
            page.get_by_placeholder("admin@societe.ma").fill(email)   # saisie possible pendant le réveil
            page.locator('input[type="password"]').fill(password)
            reveils.pop().continue_()
            statut.wait_for(state="detached")                   # disparaît une fois le serveur prêt
            page.get_by_role("button", name="Se connecter", exact=True).click()
            page.get_by_role("button", name="Réveil du serveur…").wait_for()   # connexion longue : bouton explicite
            page.get_by_role("status").filter(has_text="Démarrage du serveur").wait_for()
            while not connexions:
                page.wait_for_timeout(100)
            connexions.pop().continue_()
            page.wait_for_url("**/dashboard", wait_until="domcontentloaded")
            assert not errors, errors
            assert not server_errors, server_errors
        except Exception:
            print("Page fictive :", page.url, page.locator("body").inner_text()[:3000])
            print("Log API isolée :", application["api_log"].read_text(encoding="utf-8", errors="replace")[-4000:])
            raise
        finally:
            browser.close()
