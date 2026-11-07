"""Recouvrement UI connecté ; enregistrements internes, aucun message envoyé."""
from datetime import date, timedelta
from decimal import Decimal
import json
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def dossier_synthetique(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = f"suivi-{suffix}@example.com", "RelanceE2E132!"
    nom = f"Client suivi fictif {suffix}"
    with httpx.Client(base_url=application["api_url"]) as api:
        response = api.post("/api/auth/register", json={"nom": "Administrateur suivi", "email": email,
                            "password": password, "raison_sociale": f"Suivi fictif {suffix}"})
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        api.headers["Authorization"] = "Bearer " + token
        response = api.post("/api/tiers", json={"type": "client", "nom": nom,
                            "categorie_fiscale": "particulier", "delai_paiement": 0})
        assert response.status_code == 201, response.text
        jour = date.today().isoformat()
        response = api.post("/api/factures", json={"type": "vente", "date": jour, "tiers": nom,
                            "tiers_id": response.json()["id"], "date_echeance": jour, "delai_paiement": 0,
                            "lignes": [{"description": "Service fictif", "quantite": 1,
                            "prix_unitaire": 1000, "tva": 20}]})
        assert response.status_code == 201, response.text
        fid = response.json()["id"]
        assert api.post(f"/api/factures/{fid}/valider").status_code == 200
    return {"nom": nom, "email": email, "password": password, "fid": fid, "token": token, "suffix": suffix}


@pytest.mark.parametrize("filtre", ["Montant", "Jours", "Échéance jusqu’au"])
def test_filtres_avances_composes_avec_ouvertes(application, filtre):
    dossier = dossier_synthetique(application)
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
            connexion(page, application["web_url"], dossier["email"], dossier["password"])
            page.goto(application["web_url"] + "/situation", wait_until="domcontentloaded")
            page.get_by_role("button", name="Échéances & impayés", exact=True).click()
            row = page.locator("tbody tr").filter(has_text=dossier["nom"])
            row.wait_for()
            if filtre == "Montant":
                page.get_by_placeholder("Montant", exact=True).fill("1201")
            elif filtre == "Jours":
                page.get_by_placeholder("Jours", exact=True).fill("1")
            else:
                page.get_by_label("Échéance jusqu’au", exact=True).fill((date.today() - timedelta(days=1)).isoformat())
            playwright.expect(row).to_have_count(0)
            page.get_by_text("Aucune facture ne correspond aux filtres.", exact=True).wait_for()
            page.get_by_role("button", name="Effacer les filtres", exact=True).click()
            row.wait_for()
            assert not errors, errors
            assert not server_errors, server_errors
        finally:
            browser.close()


def test_lecture_consulte_recouvrement_sans_actions_mutation(application):
    dossier = dossier_synthetique(application)
    email = f"lecture-relance-{dossier['suffix']}@example.com"
    password = "LectureRelance132!"
    with httpx.Client(base_url=application["api_url"], headers={"Authorization": "Bearer " + dossier["token"]}) as api:
        response = api.post("/api/utilisateurs", json={"nom": "Lecteur recouvrement", "email": email,
                            "mot_de_passe": password, "role": "lecture"})
        assert response.status_code == 201, response.text
        response = api.post("/api/recouvrement/relances", json={"facture_id": dossier["fid"],
                            "montant_promis": 400, "canal": "telephone", "commentaire": "Suivi lisible par lecteur"})
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
            connexion(page, application["web_url"], email, password)
            page.goto(application["web_url"] + "/situation", wait_until="domcontentloaded")
            page.get_by_role("button", name="Échéances & impayés", exact=True).click()
            page.locator("tbody tr").filter(has_text=dossier["nom"]).wait_for()
            statut = page.evaluate("""async ({url,fid}) => {const r=await fetch(url+'/api/recouvrement/relances',
                {method:'POST',headers:{Authorization:'Bearer '+localStorage.getItem('hisabpro_token'),
                'Content-Type':'application/json'},body:JSON.stringify({facture_id:fid,canal:'telephone'})});return r.status}""",
                {"url": application["api_url"], "fid": dossier["fid"]})
            assert statut == 403
            playwright.expect(page.get_by_role("button", name="Relancer", exact=True)).to_have_count(0)
            page.get_by_role("button", name="Relances", exact=True).click()
            page.get_by_text("Suivi lisible par lecteur", exact=True).wait_for()
            assert page.get_by_role("button", name="Modifier", exact=True).count() == 0
            assert page.get_by_role("button", name="Annuler la relance", exact=True).count() == 0
            assert not errors, errors
            assert not server_errors, server_errors
        finally:
            browser.close()


@pytest.mark.parametrize("methode", ["POST", "PATCH"])
def test_promesse_nan_rejetee_api_reelle_sans_mutation(application, methode):
    dossier = dossier_synthetique(application)
    def instantane():
        with Session(application["engine"]) as db:
            facture = db.get(models.Facture, dossier["fid"])
            colonnes = lambda obj: tuple((col.name, getattr(obj, col.name)) for col in obj.__table__.columns)
            relances = db.query(models.RelanceRecouvrement).filter_by(facture_id=dossier["fid"]).order_by(models.RelanceRecouvrement.id).all()
            assert db.query(models.Ecriture).filter_by(societe_id=facture.societe_id).count() == 0
            return (colonnes(facture), tuple(colonnes(l) for l in facture.lignes),
                    tuple(colonnes(r) for r in relances))
    with httpx.Client(base_url=application["api_url"], headers={"Authorization": "Bearer " + dossier["token"]}) as api:
        url = "/api/recouvrement/relances"
        payload = {"facture_id": dossier["fid"], "montant_promis": float("nan"), "canal": "telephone"}
        if methode == "PATCH":
            creation = api.post(url, json={"facture_id": dossier["fid"], "montant_promis": 400,
                                          "canal": "telephone", "commentaire": "Promesse fictive initiale"})
            assert creation.status_code == 201, creation.text
            url += "/" + str(creation.json()["id"])
            payload = {"montant_promis": float("nan"), "commentaire": "Ne doit pas être persisté"}
        avant = instantane()
        response = api.request(methode, url, content=json.dumps(payload), headers={"Content-Type": "application/json"})
        assert response.status_code == 422, response.text
        assert instantane() == avant


def test_annuler_relance_historique_apres_solde_facture_api(application):
    dossier = dossier_synthetique(application)
    with httpx.Client(base_url=application["api_url"], headers={"Authorization": "Bearer " + dossier["token"]}) as api:
        response = api.post("/api/recouvrement/relances", json={"facture_id": dossier["fid"],
                            "montant_promis": 400, "canal": "telephone", "commentaire": "Promesse avant règlement"})
        assert response.status_code == 201, response.text
        rid = response.json()["id"]
        response = api.post("/api/reglements", json={"date": date.today().isoformat(), "facture_id": dossier["fid"],
                            "tiers": dossier["nom"], "montant": 1200, "mode": "virement",
                            "reference": "VIR-SOLDE-FICTIF", "comptabiliser": False})
        assert response.status_code == 201, response.text
        response = api.patch(f"/api/recouvrement/relances/{rid}", json={"commentaire": "Facture réglée, suivi clos"})
        assert response.status_code == 200, response.text
        response = api.patch(f"/api/recouvrement/relances/{rid}", json={"statut": "annulee"})
        assert response.status_code == 200, response.text
        with Session(application["engine"]) as db:
            relance = db.get(models.RelanceRecouvrement, rid)
            assert relance.statut == "annulee" and relance.montant_promis == Decimal("400")
            assert relance.commentaire == "Facture réglée, suivi clos"
            assert db.get(models.Facture, dossier["fid"]).statut.value == "payee"


def test_creation_historique_correction_annulation_relance_ui(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = f"relance-{suffix}@example.com", "RelanceE2E132!"
    nom = f"Client relance fictif {suffix}"
    jour = date.today()
    promesse = (jour + timedelta(days=5)).isoformat()
    suivante = (jour + timedelta(days=7)).isoformat()
    with httpx.Client(base_url=application["api_url"]) as api:
        response = api.post("/api/auth/register", json={"nom": "Administrateur relance", "email": email,
                            "password": password, "raison_sociale": f"Recouvrement fictif {suffix}"})
        assert response.status_code == 200, response.text
        api.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        response = api.post("/api/tiers", json={"type": "client", "nom": nom,
                            "categorie_fiscale": "particulier", "delai_paiement": 0})
        assert response.status_code == 201, response.text
        tiers_id = response.json()["id"]
        response = api.post("/api/factures", json={"type": "vente", "date": jour.isoformat(),
                            "tiers": nom, "tiers_id": tiers_id, "date_echeance": jour.isoformat(),
                            "delai_paiement": 0, "lignes": [{"description": "Service fictif",
                            "quantite": 1, "prix_unitaire": 1000, "tva": 20}]})
        assert response.status_code == 201, response.text
        fid = response.json()["id"]
        response = api.post(f"/api/factures/{fid}/valider")
        assert response.status_code == 200, response.text
        with Session(application["engine"]) as db:
            sid = db.get(models.Tiers, tiers_id).societe_id
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
                page.goto(application["web_url"] + "/situation", wait_until="domcontentloaded")
                page.get_by_role("button", name="Échéances & impayés", exact=True).click()
                row = page.locator("tbody tr").filter(has_text=nom)
                row.get_by_role("button", name="Relancer", exact=True).click()
                modal = page.get_by_role("dialog", name=f"Relancer {nom}")
                modal.get_by_label("Canal", exact=False).select_option("telephone")
                modal.get_by_label("Date promise", exact=True).fill(promesse)
                modal.get_by_label("Montant promis (MAD)", exact=True).fill("400")
                modal.get_by_label("Prochaine relance", exact=True).fill(suivante)
                modal.get_by_label("Commentaire", exact=True).fill("Appel fictif saisi, aucun contact extérieur")
                with page.expect_response(lambda r: r.url.endswith("/api/recouvrement/relances") and r.request.method == "POST") as creation:
                    modal.get_by_role("button", name="Enregistrer la relance", exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                rid = creation.value.json()["id"]
                modal.wait_for(state="hidden")
                page.get_by_role("button", name="Relances", exact=True).click()
                historique = page.locator("tbody tr").filter(has_text=nom)
                historique.get_by_text("Appel fictif saisi, aucun contact extérieur", exact=True).wait_for()
                with Session(application["engine"]) as db:
                    relance = db.get(models.RelanceRecouvrement, rid)
                    assert relance.facture_id == fid and relance.societe_id == sid
                    assert relance.canal == "telephone" and relance.montant_promis == Decimal("400")
                    assert relance.date_promesse_reglement.isoformat() == promesse
                    assert relance.prochaine_relance.isoformat() == suivante
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
                page.reload(wait_until="domcontentloaded")
                page.get_by_role("button", name="Relances", exact=True).click()
                historique.get_by_text("Appel fictif saisi, aucun contact extérieur", exact=True).wait_for()
                # Modification depuis l'UI ; aucun appel direct ne remplace
                # l'action utilisateur dans ce parcours connecté.
                historique.get_by_role("button", name="Modifier", exact=True).click()
                edition = page.get_by_role("dialog")
                edition.get_by_label("Commentaire", exact=False).fill("Promesse corrigée fictive")
                edition.get_by_label("Montant promis (MAD)", exact=True).fill("500")
                with page.expect_response(lambda r: r.url.endswith(f"/api/recouvrement/relances/{rid}") and r.request.method == "PATCH") as modification:
                    edition.get_by_role("button", name="Enregistrer", exact=True).click()
                assert modification.value.status == 200, modification.value.text()
                edition.wait_for(state="hidden")
                historique.get_by_text("Promesse corrigée fictive", exact=True).wait_for()
                with page.expect_response(lambda r: r.url.endswith(f"/api/recouvrement/relances/{rid}") and r.request.method == "PATCH") as annulation:
                    historique.get_by_role("button", name="Annuler la relance", exact=True).click()
                assert annulation.value.status == 200, annulation.value.text()
                historique.get_by_text("Annulée", exact=True).wait_for()
                page.reload(wait_until="domcontentloaded")
                page.get_by_role("button", name="Relances", exact=True).click()
                historique.get_by_text("Annulée", exact=True).wait_for()
                with Session(application["engine"]) as db:
                    relance = db.get(models.RelanceRecouvrement, rid)
                    assert relance.statut == "annulee" and relance.montant_promis == Decimal("500")
                    assert relance.commentaire == "Promesse corrigée fictive"
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print("Page relance fictive :", page.url, page.locator("body").inner_text()[:5000])
                print("Erreurs JavaScript/API :", errors, server_errors)
                print("Log API isolée :", application["api_log"].read_text(encoding="utf-8", errors="replace")[-8000:])
                raise
            finally:
                browser.close()
