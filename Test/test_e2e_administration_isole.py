"""Recette UI complète Edge -> FastAPI -> PostgreSQL, aucune API interceptée."""
from datetime import date
import re
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text

import models
from browser_support import chromium_executable
from e2e_isole_support import application_isolee


@pytest.fixture(scope="module")
def application():
    with application_isolee() as app:
        yield app
    assert all(process.poll() is not None for process in app["processus"])
    assert not app["web_thread"].is_alive()
    assert not app["cluster"]["directory"].exists()
    assert not app["directory"].exists()


def connexion(page, web_url, email, password):
    page.goto(web_url, wait_until="domcontentloaded")
    page.get_by_placeholder("admin@societe.ma").fill(email)
    page.locator('input[type="password"]').fill(password)
    page.get_by_role("button", name="Se connecter", exact=True).click()
    page.wait_for_url("**/dashboard", wait_until="domcontentloaded")
    page.get_by_role('main').wait_for()
    ouvrir_navigation(page)
    page.get_by_role("button", name="Déconnexion", exact=True).wait_for()
    if page.get_by_role('button', name='Ouvrir la navigation', exact=True).is_visible():
        page.keyboard.press('Escape')


def ouvrir_navigation(page):
    bouton = page.get_by_role('button', name='Ouvrir la navigation', exact=True)
    if bouton.is_visible() and bouton.get_attribute('aria-expanded') != 'true':
        bouton.click()


def deconnexion(page):
    ouvrir_navigation(page)
    page.get_by_role('button', name='Déconnexion', exact=True).click()


def observer(page, api_url):
    errors, server_errors = [], []
    # Les CDN décoratifs sont inaccessibles dans cet environnement. Aucun
    # asset local ni appel API métier n'est intercepté ou remplacé.
    for domaine in ("fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net"):
        page.route(f"https://{domaine}/**", lambda route: route.abort())
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("response", lambda response: server_errors.append((response.url, response.status))
            if response.url.startswith(api_url) and response.status >= 500 else None)
    return errors, server_errors


def test_creation_societe_plan_utilisateur_exercice_et_switch_ui_reels(application):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Chromium/Edge requis")
    suffix = uuid.uuid4().hex[:8]
    email, password = f"admin-e2e-{suffix}@example.com", "RecetteE2E132!"
    societe = f"Société E2E {suffix}"
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page()
            page.set_default_timeout(20000)
            errors, server_errors = observer(page, application["api_url"])
            page.goto(application["web_url"], wait_until="domcontentloaded")
            page.get_by_role("button", name="Créer un compte", exact=True).click()
            page.get_by_placeholder("Prénom NOM").fill("Administrateur E2E")
            page.get_by_placeholder("Ma Société SARL").fill(societe)
            page.get_by_placeholder("Casablanca").fill("Casablanca")
            page.get_by_placeholder("admin@societe.ma").fill(email)
            page.locator('input[type="password"]').fill(password)
            page.get_by_role("button", name="Créer mon compte", exact=True).click()
            page.wait_for_url("**/dashboard")
            page.get_by_role("button", name="Déconnexion", exact=True).wait_for()
            with Session(application["engine"]) as db:
                company = db.query(models.Societe).filter_by(raison_sociale=societe).one()
                sid = company.id
                assert db.query(models.CompteSociete).filter_by(societe_id=sid).count() == 4
                exercice = db.query(models.ExerciceComptable).filter_by(societe_id=sid).one()
                assert len(exercice.periodes) == 12
            page.goto(application["web_url"] + "/plan-comptes", wait_until="domcontentloaded")
            page.get_by_role("heading", name="Plan comptable de la société").wait_for()
            page.get_by_text("Capital social", exact=True).wait_for()
            page.get_by_role("button", name="Compléter le plan CGNC", exact=True).click()
            page.get_by_text("Capital social", exact=True).wait_for()
            page.goto(application["web_url"] + "/parametres", wait_until="domcontentloaded")
            page.get_by_role("button", name="Utilisateurs", exact=True).click()
            page.get_by_role("button", name="Ajouter un utilisateur", exact=True).click()
            page.get_by_text("Nom complet", exact=True).locator("..").locator("input").fill("Lecteur E2E")
            page.get_by_text("Adresse e-mail", exact=True).locator("..").locator("input").fill(f"lecture-{suffix}@example.com")
            page.locator('input[autocomplete="new-password"]').fill("LectureE2E132!")
            page.locator("label").filter(has_text=re.compile("^Rôle$")).locator("..").locator("select").select_option("lecture")
            page.get_by_role("button", name="Créer le compte", exact=True).click()
            page.locator("tbody tr").filter(has_text="Lecteur E2E").wait_for()
            page.goto(application["web_url"] + "/cloture", wait_until="domcontentloaded")
            page.get_by_role("button", name="Créer un exercice", exact=True).click()
            annee = date.today().year + 1
            page.get_by_label("Année de clôture du nouvel exercice").fill(str(annee))
            page.get_by_label("Date de début du nouvel exercice").fill(f"{annee}-01-01")
            page.get_by_label("Date de clôture du nouvel exercice").fill(f"{annee}-12-31")
            page.get_by_role("button", name="Créer cet exercice", exact=True).click()
            page.get_by_role("status").filter(has_text=f"Exercice {annee} disponible").wait_for()
            assert page.get_by_label("Exercice actif", exact=True).input_value() == str(annee)
            page.get_by_role("button", name=societe, exact=True).click()
            page.get_by_role("button", name="Nouvelle société", exact=True).click()
            seconde = f"Autre société E2E {suffix}"
            page.get_by_placeholder("Raison sociale *").fill(seconde)
            page.get_by_role("button", name="Créer", exact=True).click()
            page.get_by_role("button", name=seconde, exact=True).wait_for()
            with Session(application["engine"]) as db:
                second = db.query(models.Societe).filter_by(raison_sociale=seconde).one()
                assert db.query(models.CompteSociete).filter_by(societe_id=second.id).count() == 4
                assert db.query(models.ExerciceComptable).filter_by(societe_id=second.id).count() == 1
                assert db.query(models.ExerciceComptable).filter_by(societe_id=sid).count() == 2
                audit = db.execute(text("SELECT count(*) FROM audit_actions WHERE succes AND chemin LIKE '/api/%' AND methode='POST'")).scalar()
                assert audit >= 5
            page.get_by_role("button", name="Déconnexion", exact=True).click()
            page.get_by_role("button", name="Se connecter", exact=True).wait_for()
            connexion(page, application["web_url"], email, password)
            page.get_by_role("button", name=societe, exact=True).wait_for()
            assert not errors, errors
            assert not server_errors, server_errors
        except Exception:
            print("Page E2E synthétique :", page.url, page.locator("body").inner_text()[:2000])
            print("Erreurs JavaScript/API :", errors, server_errors)
            raise
        finally:
            browser.close()


def test_login_lecture_ui_et_refus_mutations_reelles(application):
    # Prérequis créés par de vraies requêtes HTTP ; seule la connexion et la
    # navigation du lecteur sont le parcours UI de ce deuxième scénario.
    suffix = uuid.uuid4().hex[:8]
    with httpx.Client(base_url=application["api_url"]) as api:
        response = api.post("/api/auth/register", json={"nom": "Admin lecteur E2E", "email": f"admin-read-{suffix}@example.com",
                            "password": "RecetteE2E132!", "raison_sociale": f"Recette lecteur E2E {suffix}"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        email = f"read-{suffix}@example.com"
        response = api.post("/api/utilisateurs", headers={"Authorization": "Bearer " + token},
                            json={"nom": "Consultation E2E", "email": email, "mot_de_passe": "LectureE2E132!", "role": "lecture"})
        assert response.status_code == 201
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
            connexion(page, application["web_url"], email, "LectureE2E132!")
            page.goto(application["web_url"] + "/plan-comptes", wait_until="domcontentloaded")
            page.get_by_text("Capital social", exact=True).wait_for()
            assert page.get_by_role("button", name="Compléter le plan CGNC", exact=True).count() == 0
            assert page.get_by_role("button", name="Ajouter une subdivision", exact=True).count() == 0
            page.goto(application["web_url"] + "/parametres", wait_until="domcontentloaded")
            page.get_by_role("button", name="Utilisateurs", exact=True).click()
            page.get_by_text("Seuls les administrateurs", exact=False).wait_for()
            assert page.get_by_role("button", name="Ajouter un utilisateur", exact=True).count() == 0
            # Une tentative directe depuis le navigateur traverse le vrai CORS,
            # la vraie authentification et le RBAC côté PostgreSQL/API.
            statut = page.evaluate("async url => {const r=await fetch(url+'/api/plan-comptable/initialiser',{method:'POST',headers:{Authorization:'Bearer '+localStorage.getItem('hisabpro_token')}});return r.status}", application["api_url"])
            assert statut == 403
            assert not errors, errors
            assert not server_errors, server_errors
        except Exception:
            print("Page E2E lecteur synthétique :", page.url, page.locator("body").inner_text()[:2000])
            print("Erreurs JavaScript/API :", errors, server_errors)
            raise
        finally:
            browser.close()
