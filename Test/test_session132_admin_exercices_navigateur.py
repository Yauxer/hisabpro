"""Gestion réelle React + contexte réel ; réponses HTTP synthétiques interceptées."""
from pathlib import Path
import json
import subprocess
import pytest
from browser_support import chromium_executable

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    target = tmp_path_factory.mktemp("exercices-react") / "exercices.js"
    script = r'''
const esbuild=require('esbuild');
esbuild.buildSync({stdin:{contents:`import React from 'react';
import {createRoot} from 'react-dom/client';
import {ExerciceProvider} from './src/data/ExerciceContext.jsx';
import GestionExercices from './src/components/GestionExercices.jsx';
createRoot(document.getElementById('root')).render(<ExerciceProvider><GestionExercices/></ExerciceProvider>);`,
loader:'jsx',resolveDir:process.cwd()},bundle:true,jsx:'automatic',format:'iife',platform:'browser',outfile:process.argv[1],
define:{'import.meta.env.VITE_API_URL':'"http://recette.test"','import.meta.env.VITE_APP_VERSION':'"recette"'}});
'''
    result = subprocess.run(["node", "-e", script, str(target)], cwd=ROOT, text=True, encoding="utf-8", capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return target.read_text(encoding="utf-8")


@pytest.fixture
def page_recette(bundle):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Navigateur Chromium absent")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page(viewport={"width": 390, "height": 900})
            erreurs = []
            page.on("pageerror", lambda exc: erreurs.append(str(exc)))
            appels = []
            rows = [{"id": 1, "annee": 2026, "libelle": "2026", "date_debut": "2026-01-01", "date_fin": "2026-12-31", "statut": "ouvert"}]

            def route_api(route):
                req = route.request
                appels.append((req.method, req.url))
                if req.method == "GET":
                    route.fulfill(json=rows)
                    return
                if req.url.endswith("/synchroniser"):
                    route.fulfill(json=rows)
                    return
                data = req.post_data_json if req.post_data else {
                    "annee": 2027, "date_debut": "2027-01-01", "date_fin": "2027-12-31"}
                if data["annee"] == 2026:
                    route.fulfill(status=409, json={"detail": "L'exercice 2026 existe déjà."})
                    return
                row = {"id": 2, "statut": "a_venir", "libelle": str(data["annee"]), **data}
                rows.append(row)
                route.fulfill(status=201, json=row)

            page.route("**/api/exercices**", route_api)
            page.route("http://recette.test/", lambda route: route.fulfill(body='<div id="root"></div>', content_type="text/html"))
            page.goto("http://recette.test/")

            def ouvrir(role):
                page.evaluate("role=>{localStorage.setItem('hisabpro_token','recette');localStorage.setItem('hisabpro_role',role);localStorage.setItem('hisabpro_exercice','2026')}", role)
                page.add_script_tag(content=bundle)
                page.get_by_label("Exercice actif").locator("option").filter(has_text="2026").wait_for(state="attached")

            yield page, ouvrir, appels, erreurs
            assert not erreurs
        finally:
            browser.close()


def test_creation_dates_explicites_et_selection_sans_rechargement(page_recette):
    page, ouvrir, appels, _ = page_recette
    ouvrir("admin")
    page.get_by_role("button", name="Créer un exercice", exact=True).click()
    page.get_by_label("Année de clôture du nouvel exercice").fill("2027")
    page.get_by_label("Date de début du nouvel exercice").fill("2026-07-01")
    page.get_by_label("Date de clôture du nouvel exercice").fill("2027-06-30")
    page.get_by_role("button", name="Créer cet exercice", exact=True).click()
    page.get_by_role("status").filter(has_text="Exercice 2027 disponible").wait_for()
    assert page.get_by_label("Exercice actif").input_value() == "2027"
    assert page.evaluate("localStorage.getItem('hisabpro_exercice')") == "2027"
    assert sum(method == "POST" for method, _ in appels) == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= 390


def test_doublon_conserve_formulaire_et_affiche_message_serveur(page_recette):
    page, ouvrir, _, _ = page_recette
    ouvrir("admin")
    page.get_by_role("button", name="Créer un exercice", exact=True).click()
    page.get_by_label("Année de clôture du nouvel exercice").fill("2026")
    page.get_by_role("button", name="Créer cet exercice", exact=True).click()
    page.get_by_role("alert").filter(has_text="existe déjà").wait_for()
    assert page.get_by_label("Année de clôture du nouvel exercice").input_value() == "2026"
    assert page.get_by_label("Exercice actif").input_value() == "2026"


def test_lecture_seule_ne_declenche_aucune_preparation(page_recette):
    page, ouvrir, appels, _ = page_recette
    ouvrir("lecture")
    assert page.get_by_role("button").count() == 0
    assert all(method == "GET" for method, _ in appels)


def test_preparer_suivant_et_synchronisation_explicitement_declenches(page_recette):
    page, ouvrir, appels, _ = page_recette
    ouvrir("admin")
    assert all(method == "GET" for method, _ in appels)
    page.get_by_role("button", name="Préparer l'exercice suivant", exact=True).click()
    page.get_by_role("status").filter(has_text="Exercice 2027 disponible").wait_for()
    assert page.get_by_label("Exercice actif").input_value() == "2027"
    page.get_by_role("button", name="Synchroniser le calendrier", exact=True).click()
    page.get_by_role("status").filter(has_text="Calendrier synchronisé").wait_for()
    assert any(method == "POST" and url.endswith("/2026/preparer-suivant") for method, url in appels)
    assert any(method == "POST" and url.endswith("/synchroniser") for method, url in appels)
