"""Avoir physique puis contrepassation, vraie UI/API et PostgreSQL éphémère."""
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


def test_avoir_retour_comptabilise_annulation_stock_et_piste_ui(application):
    suffix = uuid.uuid4().hex[:8]
    nom, designation = "Client retour fictif " + suffix, "Article retour fictif " + suffix
    email, password = f"retour-{suffix}@example.com", "RetourE2E132!"
    with httpx.Client(base_url=application["api_url"]) as api:
        response = api.post("/api/auth/register", json={"nom": "Administrateur retours", "email": email,
                            "password": password, "raison_sociale": "Retours fictifs " + suffix})
        assert response.status_code == 200, response.text
        api.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        response = api.post("/api/tiers", json={"nom": nom, "type": "client"})
        assert response.status_code == 201, response.text
        tid = response.json()["id"]
        response = api.post("/api/articles", json={"code": "RET-" + suffix, "designation": designation,
                            "prix_vente_ht": 500, "prix_achat_ht": 300, "tva": 20,
                            "stock_actuel": 10, "is_stockable": True, "compte_vente": "7111"})
        assert response.status_code == 201, response.text
        aid = response.json()["id"]
        response = api.post("/api/factures", json={"type": "vente", "date": date.today().isoformat(),
                            "tiers": nom, "tiers_id": tid, "lignes": [{"article_id": aid,
                            "description": designation, "quantite": 2, "prix_unitaire": 500, "tva": 20}]})
        assert response.status_code == 201, response.text
        fid = response.json()["id"]
        assert api.post(f"/api/factures/{fid}/valider").status_code == 200
        response = api.post(f"/api/factures/{fid}/comptabiliser")
        assert response.status_code == 200, response.text
        assert api.post(f"/api/ecritures/{response.json()['ecriture_id']}/valider").status_code == 200
        with Session(application["engine"]) as db:
            sid = db.get(models.Article, aid).societe_id
            assert db.get(models.Article, aid).stock_actuel == 8
            original = snapshot_lignes(db, sid)
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
                page.goto(application["web_url"] + "/factures", wait_until="domcontentloaded")
                page.locator("tbody tr").filter(has_text=nom).click()
                page.get_by_role("button", name="Créer un avoir", exact=True).click()
                modal = page.get_by_role("dialog", name="Créer un avoir", exact=False)
                modal.get_by_placeholder("Retour marchandise, remise après facture...").fill("Retour fictif d'une unité")
                modal.get_by_role("checkbox", name="Retour physique de marchandise", exact=False).check()
                ligne = modal.locator("tbody tr").filter(has_text=designation)
                ligne.get_by_role("checkbox").check()
                ligne.locator('input[type="number"]').fill("1")
                with page.expect_response(lambda r: r.url.endswith("/api/avoirs") and r.request.method == "POST") as creation:
                    modal.get_by_role("button", name="Créer l'avoir", exact=False).click()
                assert creation.value.status == 201, creation.value.text()
                avoir = creation.value.json()
                avid = avoir["id"]
                assert Decimal(str(avoir["total_ttc"])) == 600
                assert avoir["facture_id"] == fid and avoir["retour_stock"] and not avoir["est_comptabilisee"]
                modal.wait_for(state="hidden")
                with Session(application["engine"]) as db:
                    assert db.get(models.Article, aid).stock_actuel == 8
                    assert snapshot_lignes(db, sid) == original
                page.goto(application["web_url"] + "/avoirs", wait_until="domcontentloaded")
                row = page.locator("tbody tr").filter(has_text=nom)
                row.click()
                with page.expect_response(lambda r: r.url.endswith(f"/api/avoirs/{avid}/comptabiliser")) as compta:
                    page.get_by_role("button", name="Comptabiliser", exact=True).last.click()
                assert compta.value.status == 200, compta.value.text()
                with Session(application["engine"]) as db:
                    assert db.get(models.Article, aid).stock_actuel == 9
                    av = db.get(models.Avoir, avid)
                    assert av.lignes[0].facture_ligne_id == db.get(models.Facture, fid).lignes[0].id
                    ec = db.query(models.Ecriture).filter_by(societe_id=sid, journal="AV", reference=av.numero).one()
                    assert not ec.est_validee
                    assert {l.compte: (l.debit, l.credit) for l in ec.lignes} == {
                        "7111": (500, 0), "4455": (100, 0), "3421": (0, 600)}
                    ecid = ec.id
                page.goto(application["web_url"] + "/journal", wait_until="domcontentloaded")
                playwright.expect(page.get_by_role("button", name="Valider", exact=True)).to_have_count(1)
                with page.expect_response(lambda r: r.url.endswith("/api/ecritures/valider-lot")) as validation:
                    page.get_by_role("button", name="Valider les brouillons", exact=True).click()
                assert validation.value.status == 200 and validation.value.json()["nb_validees"] == 1
                with Session(application["engine"]) as db:
                    assert db.get(models.Ecriture, ecid).est_validee
                    avant_annulation = snapshot_lignes(db, sid)
                verifier_solde(api, fid, 600, 600)
                page.goto(application["web_url"] + "/avoirs", wait_until="domcontentloaded")
                row.click()
                with page.expect_response(lambda r: r.url.endswith(f"/api/avoirs/{avid}/annuler")) as annulation:
                    page.get_by_role("button", name="Annuler l'avoir", exact=True).click()
                assert annulation.value.status == 200, annulation.value.text()
                inverse_id = annulation.value.json()["ecriture_annulation_id"]
                with Session(application["engine"]) as db:
                    assert db.get(models.Article, aid).stock_actuel == 8
                    assert avant_annulation <= snapshot_lignes(db, sid)
                    inverse = db.get(models.Ecriture, inverse_id)
                    assert not inverse.est_validee
                    av = db.get(models.Avoir, avid)
                    assert av.statut == "annule" and av.ecriture_annulation_id == inverse_id
                    source = db.get(models.Ecriture, ecid)
                    assert {l.compte: (l.debit, l.credit) for l in inverse.lignes} == {
                        l.compte: (l.credit, l.debit) for l in source.lignes}
                    retour = db.query(models.MouvementStock).filter_by(article_id=aid, source_type="avoir", source_id=avid).one()
                    compensation = db.query(models.MouvementStock).filter_by(article_id=aid, annule_mouvement_id=retour.id).one()
                    assert retour.type == "entree" and retour.quantite == 1 and retour.stock_avant == 8 and retour.stock_apres == 9
                    assert compensation.type == "correction" and compensation.quantite == 1
                    assert compensation.stock_avant == 9 and compensation.stock_apres == 8
                    # Le ledger pointe vers l'avoir ; la facture est liée par celui-ci.
                    assert av.facture_id == fid and retour.facture_id is None and retour.source_ligne_id == av.lignes[0].id
                verifier_solde(api, fid, 0, 1200)
                page.goto(application["web_url"] + "/journal", wait_until="domcontentloaded")
                playwright.expect(page.get_by_role("button", name="Valider", exact=True)).to_have_count(1)
                with page.expect_response(lambda r: r.url.endswith("/api/ecritures/valider-lot")) as validation_inverse:
                    page.get_by_role("button", name="Valider les brouillons", exact=True).click()
                assert validation_inverse.value.status == 200 and validation_inverse.value.json()["nb_validees"] == 1
                with Session(application["engine"]) as db:
                    assert db.get(models.Ecriture, inverse_id).est_validee
                    avant_reprise = snapshot_lignes(db, sid)
                    assert db.query(models.MouvementStock).filter_by(article_id=aid).count() == 4
                response = api.post(f"/api/avoirs/{avid}/annuler")
                assert response.status_code == 200 and response.json()["ecriture_annulation_id"] == inverse_id
                page.goto(application["web_url"] + "/avoirs", wait_until="domcontentloaded")
                page.reload(wait_until="domcontentloaded")
                playwright.expect(row).to_contain_text("Annulé")
                row.click()
                assert page.get_by_role("button", name="Annuler l'avoir", exact=True).count() == 0
                with Session(application["engine"]) as db:
                    assert snapshot_lignes(db, sid) == avant_reprise
                    assert db.get(models.Article, aid).stock_actuel == 8
                    assert db.query(models.MouvementStock).filter_by(article_id=aid).count() == 4
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 3
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                print("Retour fictif :", page.url, page.locator("body").inner_text()[:6000])
                print("Erreurs JavaScript/API :", errors, server_errors)
                print(application["api_log"].read_text(encoding="utf-8", errors="replace")[-6000:])
                raise
            finally:
                browser.close()


def snapshot_lignes(db, sid):
    return {(l.id, l.ecriture_id, l.compte, l.debit, l.credit, l.tiers_id, l.compte_auxiliaire_snapshot)
            for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid).all()}


def verifier_solde(api, fid, avoirs, reste):
    response = api.get(f"/api/factures/{fid}/reglements")
    assert response.status_code == 200, response.text
    assert Decimal(str(response.json()["total_avoirs"])) == avoirs
    assert Decimal(str(response.json()["solde_restant"])) == reste
