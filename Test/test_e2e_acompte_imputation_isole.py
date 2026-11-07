"""Acomptes : API réelles et UI connectée à PostgreSQL éphémère."""
from datetime import date
from decimal import Decimal
from contextlib import closing
from pathlib import Path
import json
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application as application_base, champ, verifier_ecritures
from postgres_isole import verifier_cible_isolee


@pytest.fixture(scope="module")
def application(application_base):
    cible = application_base["cluster"]
    verifier_cible_isolee(cible["url"], cible["directory"], cible["nonce"])
    connection = application_base["engine"].raw_connection()
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute((Path(__file__).resolve().parents[1] / "hisabpro-backend" /
                            "041_factC_cycle_documentaire.sql").read_text(encoding="utf-8"))
    finally:
        connection.close()
    yield application_base


def preparer_client(application):
    suffix = uuid.uuid4().hex[:8]
    email, password, nom = f"acompte-{suffix}@example.com", "AcompteE2E132!", "Client acompte fictif " + suffix
    api = httpx.Client(base_url=application["api_url"])
    response = api.post("/api/auth/register", json={"nom": "Administrateur acomptes", "email": email,
                        "password": password, "raison_sociale": "Acomptes fictifs " + suffix})
    assert response.status_code == 200, response.text
    api.headers["Authorization"] = "Bearer " + response.json()["access_token"]
    response = api.post("/api/tiers", json={"nom": nom, "type": "client"})
    assert response.status_code == 201, response.text
    tid = response.json()["id"]
    with Session(application["engine"]) as db:
        sid = db.get(models.Tiers, tid).societe_id
    return api, sid, tid, nom, email, password


def creer_facture(api, tid, nom):
    response = api.post("/api/factures", json={"type": "vente", "date": date.today().isoformat(),
                        "tiers": nom, "tiers_id": tid, "lignes": [{"description": "Prestation fictive",
                        "quantite": 1, "prix_unitaire": 1000, "tva": 20}]})
    assert response.status_code == 201, response.text
    fid = response.json()["id"]
    assert api.post(f"/api/factures/{fid}/valider").status_code == 200
    response = api.post(f"/api/factures/{fid}/comptabiliser")
    assert response.status_code == 200, response.text
    return fid


def acompte_payload(tid, nom):
    return {"type": "client", "tiers": nom, "tiers_id": tid, "date": date.today().isoformat(),
            "montant": 400, "taux_tva": 20, "mode": "virement", "comptabiliser": False}


def snapshot(application, sid):
    with Session(application["engine"]) as db:
        return ([(a.id, a.montant, a.statut) for a in db.query(models.Acompte).filter_by(societe_id=sid).order_by(models.Acompte.id)],
                [(i.id, i.montant, i.statut) for i in db.query(models.ImputationAcompte).filter_by(societe_id=sid).order_by(models.ImputationAcompte.id)],
                {(l.id, l.ecriture_id, l.compte, l.debit, l.credit) for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid)})


@pytest.mark.parametrize("champ_invalide,valeur", [("montant", float("nan")), ("montant", float("inf")),
                         ("montant", True), ("taux_tva", float("nan")), ("taux_tva", float("inf")), ("taux_tva", True)])
def test_creation_acompte_montants_finis_rejet_api(application, champ_invalide, valeur):
    api, sid, tid, nom, _, _ = preparer_client(application)
    with closing(api):
        avant = snapshot(application, sid)
        payload = acompte_payload(tid, nom)
        payload[champ_invalide] = valeur
        response = api.post("/api/acomptes", content=json.dumps(payload), headers={"Content-Type": "application/json"})
        apres = snapshot(application, sid)
        print("Création invalide", champ_invalide, repr(valeur), "HTTP", response.status_code,
              "comptes avant/après", len(avant[0]), len(apres[0]), response.text[:250])
        assert response.status_code == 422, response.text
        assert apres == avant


@pytest.mark.parametrize("valeur", [float("nan"), float("inf"), True])
def test_imputation_acompte_montant_fini_rejet_api(application, valeur):
    api, sid, tid, nom, _, _ = preparer_client(application)
    with closing(api):
        response = api.post("/api/acomptes", json=acompte_payload(tid, nom))
        if response.status_code != 201:
            print(application["api_log"].read_text(encoding="utf-8", errors="replace")[-6500:])
        assert response.status_code == 201, response.text
        acid = response.json()["id"]
        fid = creer_facture(api, tid, nom)
        avant = snapshot(application, sid)
        response = api.post(f"/api/acomptes/{acid}/imputer", content=json.dumps({"facture_id": fid,
                            "montant": valeur, "comptabiliser": False}), headers={"Content-Type": "application/json"})
        apres = snapshot(application, sid)
        print("Imputation invalide", repr(valeur), "HTTP", response.status_code,
              "imputations avant/après", len(avant[1]), len(apres[1]), response.text[:250])
        assert response.status_code == 422, response.text
        assert apres == avant


def test_acompte_facture_imputation_reglement_et_lettrage_ui(application):
    api, sid, tid, nom, email, password = preparer_client(application)
    with closing(api):
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
                page.goto(application["web_url"] + "/acomptes", wait_until="domcontentloaded")
                page.get_by_role("button", name="Nouvel acompte", exact=True).click()
                modal = page.get_by_role("dialog", name="Nouvel acompte", exact=True)
                modal.locator('input[role="combobox"]').fill(nom)
                modal.get_by_role("option").filter(has_text=nom).click()
                champ(modal, "Montant (MAD)").fill("400")
                modal.get_by_placeholder("N° chèque, virement...").fill("VIR-AC-FICTIF")
                with page.expect_response(lambda r: r.url.endswith("/api/acomptes") and r.request.method == "POST") as creation:
                    modal.get_by_role("button", name="Enregistrer l’acompte", exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                acompte = creation.value.json()
                acid = acompte["id"]
                assert acompte["montant_disponible"] == 400 and acompte["est_comptabilisee"]
                modal.wait_for(state="hidden")
                row = page.locator("tbody tr").filter(has_text=nom)
                row.wait_for()
                with Session(application["engine"]) as db:
                    ec = db.query(models.Ecriture).filter_by(societe_id=sid).one()
                    assert not ec.est_validee
                    assert {l.compte: (l.debit, l.credit) for l in ec.lignes} == {"5141": (400, 0), "4421": (0, 400)}
                fid = creer_facture(api, tid, nom)
                page.reload(wait_until="domcontentloaded")
                row.get_by_title("Imputer sur une facture", exact=True).click()
                modal = page.get_by_role("dialog", name="Imputer ", exact=False)
                modal.locator("select").select_option(str(fid))
                playwright.expect(champ(modal, "Montant à imputer (MAD)")).to_have_value("400.00")
                with page.expect_response(lambda r: r.url.endswith(f"/api/acomptes/{acid}/imputer")) as imputation:
                    modal.get_by_role("button", name="Imputer l’acompte", exact=True).click()
                assert imputation.value.status == 200, imputation.value.text()
                assert imputation.value.json()["montant_disponible"] == 0
                modal.wait_for(state="hidden")
                verifier_ecritures(application, sid, 3, tid, "3421", 800)
                avant_doublon = snapshot(application, sid)
                response = api.post(f"/api/acomptes/{acid}/imputer", json={"facture_id": fid, "montant": 400})
                assert response.status_code == 409, response.text
                assert snapshot(application, sid) == avant_doublon
                page.goto(application["web_url"] + "/factures", wait_until="domcontentloaded")
                row.get_by_title("Encaisser le client", exact=True).click()
                modal = page.get_by_role("dialog")
                assert Decimal(champ(modal, "Montant *").input_value()) == Decimal('800')
                modal.get_by_placeholder("N° chèque, virement...").fill("VIR-SOLDE-FICTIF")
                with page.expect_response(lambda r: r.url.endswith("/api/reglements") and r.request.method == "POST") as reglement:
                    modal.get_by_role("button", name="Enregistrer", exact=True).click()
                assert reglement.value.status == 201, reglement.value.text()
                modal.wait_for(state="hidden")
                verifier_ecritures(application, sid, 4, tid, "3421", 0)
                response = api.get(f"/api/factures/{fid}/reglements")
                assert response.status_code == 200, response.text
                assert response.json()["total_acomptes"] == 400 and response.json()["total_regle"] == 800
                assert response.json()["solde_restant"] == 0
                page.goto(application["web_url"] + "/journal", wait_until="domcontentloaded")
                playwright.expect(page.get_by_role("button", name="Valider", exact=True)).to_have_count(4)
                with page.expect_response(lambda r: r.url.endswith("/api/ecritures/valider-lot")) as validation:
                    page.get_by_role("button", name="Valider les brouillons", exact=True).click()
                assert validation.value.status == 200 and validation.value.json()["nb_validees"] == 4
                verifier_ecritures(application, sid, 4, tid, "3421", 0, definitives=True)
                avant_lettrage = snapshot(application, sid)
                page.goto(application["web_url"] + "/lettrage", wait_until="domcontentloaded")
                champ(page, "Compte", "select").select_option("3421")
                champ(page, "Tiers", "select").select_option(label=nom)
                playwright.expect(page.locator('tbody input[type="checkbox"]')).to_have_count(3)
                for box in page.locator('tbody input[type="checkbox"]').all():
                    box.check()
                with page.expect_response(lambda r: "/api/lettrage" in r.url and r.request.method == "POST") as lettrage:
                    page.get_by_role("button", name="Lettrer 3 lignes", exact=True).click()
                assert lettrage.value.status == 200, lettrage.value.text()
                page.get_by_text("3 lettrée(s)", exact=True).wait_for()
                assert snapshot(application, sid) == avant_lettrage
                with Session(application["engine"]) as db:
                    acompte_db = db.get(models.Acompte, acid)
                    imputation_db = db.query(models.ImputationAcompte).filter_by(acompte_id=acid).one()
                    assert imputation_db.facture_id == fid and imputation_db.montant == 400 and imputation_db.est_comptabilisee
                    assert acompte_db.statut == "impute" and acompte_db.est_imputee_compta
                    lignes = db.query(models.LigneEcriture).join(models.Ecriture).filter(
                        models.Ecriture.societe_id == sid, models.LigneEcriture.compte == "3421").all()
                    assert len(lignes) == 3 and len({l.code_lettrage for l in lignes}) == 1
                    assert all(l.code_lettrage for l in lignes)
                    toutes = db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid).all()
                    assert sum(l.debit - l.credit for l in toutes if l.compte == "4421") == 0
                    assert sum(l.debit - l.credit for l in toutes if l.compte == "5141") == 1200
                page.reload(wait_until="domcontentloaded")
                champ(page, "Compte", "select").select_option("3421")
                champ(page, "Tiers", "select").select_option(label=nom)
                page.get_by_text("3 lettrée(s)", exact=True).wait_for()
                page.goto(application["web_url"] + "/acomptes", wait_until="domcontentloaded")
                row.wait_for()
                assert row.get_by_title("Imputer sur une facture", exact=True).count() == 0
                row.get_by_title("Voir le détail et l'historique", exact=True).click()
                page.get_by_role("dialog").get_by_text("400,00", exact=False).first.wait_for()
                assert snapshot(application, sid) == avant_lettrage
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                print("Acompte fictif :", page.url, page.locator("body").inner_text()[:6000])
                print("Erreurs JavaScript/API :", errors, server_errors)
                print(application["api_log"].read_text(encoding="utf-8", errors="replace")[-6000:])
                raise
            finally:
                browser.close()
