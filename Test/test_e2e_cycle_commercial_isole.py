"""Devis → BC → BL → facture : UI/API réelles et PostgreSQL éphémère."""
import uuid
from decimal import Decimal

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def test_cycle_vente_stock_facture_et_tracabilite_ui(application):
    suffix = uuid.uuid4().hex[:8]
    client, article = f"Client cycle fictif {suffix}", f"Marchandise fictive {suffix}"
    email, password = f"cycle-{suffix}@example.com", "CycleE2E132!"
    with httpx.Client(base_url=application["api_url"]) as api:
        response = api.post("/api/auth/register", json={"nom": "Recette cycle", "email": email,
                            "password": password, "raison_sociale": "Cycle fictif " + suffix})
        assert response.status_code == 200, response.text
        api.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        response = api.post("/api/tiers", json={"nom": client, "type": "client", "delai_paiement": 30})
        assert response.status_code == 201, response.text
        tid = response.json()["id"]
        response = api.post("/api/articles", json={"code": "E2E-" + suffix, "designation": article,
                            "prix_vente_ht": 500, "prix_achat_ht": 300, "tva": 20,
                            "stock_actuel": 10, "is_stockable": True, "compte_vente": "7111"})
        assert response.status_code == 201, response.text
        aid = response.json()["id"]
        with Session(application["engine"]) as db:
            sid = db.get(models.Article, aid).societe_id
            assert (db.get(models.Societe, sid).stock_declencheur_vente or "facture") == "facture"
        stock_et_ecritures(application, aid, sid, 10, 1, 0)
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
                page.goto(application["web_url"] + "/commercial", wait_until="domcontentloaded")
                page.get_by_role("button", name="Nouveau devis", exact=True).click()
                modal = page.get_by_role("dialog", name="Nouveau devis", exact=True)
                modal.get_by_placeholder("Nom du client...", exact=True).fill(client)
                modal.get_by_role("option").filter(has_text=client).click()
                modal.get_by_placeholder("Article ou description...", exact=True).fill(article)
                modal.locator("li").filter(has_text=article).click()
                modal.get_by_label("Quantité", exact=True).fill("2")
                with page.expect_response(lambda r: r.url.endswith("/api/devis") and r.request.method == "POST") as creation:
                    modal.get_by_role("button", name="Créer le devis", exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                devis = creation.value.json()
                did = devis["id"]
                assert Decimal(str(devis["total_ht"])) == 1000
                modal.wait_for(state="hidden")
                row = page.locator("tbody tr").filter(has_text=client)
                with page.expect_response(lambda r: r.url.endswith(f"/api/devis/{did}") and r.request.method == "PATCH") as acceptation:
                    row.get_by_title("Marquer accepté", exact=True).click()
                assert acceptation.value.status == 200, acceptation.value.text()
                row.get_by_role("button", name="Créer BC", exact=True).click()
                modal = page.get_by_role("dialog", name="Nouveau bon de commande", exact=True)
                with page.expect_response(lambda r: r.url.endswith("/api/bons-commande") and r.request.method == "POST") as commande:
                    modal.get_by_role("button", name="Créer la commande", exact=True).click()
                assert commande.value.status == 201, commande.value.text()
                bc = commande.value.json()
                bcid = bc["id"]
                assert bc["devis_id"] == did
                modal.wait_for(state="hidden")
                page.get_by_role("button", name="Bons de commande", exact=True).click()
                row.get_by_title("Créer un bon de livraison sur le reliquat", exact=True).click()
                modal = page.get_by_role("dialog", name="Bon de livraison depuis " + bc["numero"], exact=True)
                playwright.expect(modal.locator('input[type="number"]')).to_have_value("2")
                with page.expect_response(lambda r: r.url.endswith(f"/api/bons-commande/{bcid}/convertir-bl")) as livraison:
                    modal.get_by_role("button", name="Créer le bon de livraison", exact=True).click()
                assert livraison.value.status == 200, livraison.value.text()
                bl = livraison.value.json()
                blid = bl["id"]
                modal.wait_for(state="hidden")
                page.get_by_role("button", name="Bons de livraison", exact=True).click()
                for titre in ("Confirmer l'expédition ou la prestation réalisée", "Confirmer la remise au client"):
                    with page.expect_response(lambda r: r.url.endswith(f"/api/bons-livraison/{blid}") and r.request.method == "PATCH") as logistique:
                        row.get_by_title(titre, exact=True).click()
                    assert logistique.value.status == 200, logistique.value.text()
                stock_et_ecritures(application, aid, sid, 10, 1, 0)
                row.get_by_role("button", name="Facturer", exact=True).click()
                modal = page.get_by_role("dialog")
                playwright.expect(modal.locator('input[type="number"]')).to_have_value("2")
                with page.expect_response(lambda r: r.url.endswith(f"/api/bons-livraison/{blid}/convertir-facture")) as facturation:
                    modal.get_by_role("button", name="Créer la facture", exact=True).click()
                assert facturation.value.status == 200, facturation.value.text()
                facture = facturation.value.json()
                fid = facture["id"]
                assert not facture["est_validee"] and not facture["numero"]
                assert Decimal(str(facture["total_ttc"])) == 1200
                modal.wait_for(state="hidden")
                stock_et_ecritures(application, aid, sid, 10, 1, 0)
                page.goto(application["web_url"] + "/factures", wait_until="domcontentloaded")
                with page.expect_response(lambda r: r.url.endswith(f"/api/factures/{fid}/valider")) as validation:
                    row.get_by_title("Valider définitivement", exact=True).click()
                assert validation.value.status == 200, validation.value.text()
                stock_et_ecritures(application, aid, sid, 8, 2, 0)
                with page.expect_response(lambda r: r.url.endswith(f"/api/factures/{fid}/comptabiliser")) as compta:
                    row.get_by_title("Générer l'écriture comptable de cette facture", exact=True).click()
                assert compta.value.status == 200, compta.value.text()
                stock_et_ecritures(application, aid, sid, 8, 2, 1)
                page.goto(application["web_url"] + "/journal", wait_until="domcontentloaded")
                playwright.expect(page.get_by_role("button", name="Valider", exact=True)).to_have_count(1)
                with page.expect_response(lambda r: r.url.endswith("/api/ecritures/valider-lot")) as definitive:
                    page.get_by_role("button", name="Valider les brouillons", exact=True).click()
                assert definitive.value.status == 200 and definitive.value.json()["nb_validees"] == 1
                avant = verifier_liens(application, did, bcid, blid, fid, aid, sid, tid)
                response = api.get("/api/devis", params={"exercice": bc["exercice"]})
                assert response.status_code == 200, response.text
                devis_persistant = next(d for d in response.json() if d["id"] == did)
                assert devis_persistant["statut"] == "converti" and devis_persistant["bon_commande_id"] == bcid
                page.goto(application["web_url"] + "/commercial", wait_until="domcontentloaded")
                page.get_by_role("button", name="Bons de commande", exact=True).click()
                playwright.expect(row).to_contain_text("100%")
                assert row.get_by_title("Créer un bon de livraison sur le reliquat", exact=True).count() == 0
                page.get_by_role("button", name="Bons de livraison", exact=True).click()
                playwright.expect(row).to_contain_text("100%")
                assert row.get_by_role("button", name="Facturer", exact=True).count() == 0
                page.reload(wait_until="domcontentloaded")
                page.get_by_role("button", name="Bons de livraison", exact=True).click()
                playwright.expect(row).to_contain_text("100%")
                stock_et_ecritures(application, aid, sid, 8, 2, 1)
                assert verifier_liens(application, did, bcid, blid, fid, aid, sid, tid) == avant
                assert not errors and not server_errors, (errors, server_errors)
            except Exception:
                print("Cycle fictif :", page.url, page.locator("body").inner_text()[:6500])
                print("Erreurs JavaScript/API :", errors, server_errors)
                print(application["api_log"].read_text(encoding="utf-8", errors="replace")[-7000:])
                raise
            finally:
                browser.close()


def stock_et_ecritures(application, aid, sid, stock, mouvements, ecritures):
    with Session(application["engine"]) as db:
        assert db.get(models.Article, aid).stock_actuel == stock
        assert db.query(models.MouvementStock).filter_by(article_id=aid, societe_id=sid).count() == mouvements
        assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == ecritures


def verifier_liens(application, did, bcid, blid, fid, aid, sid, tid):
    with Session(application["engine"]) as db:
        devis, bc, bl, facture = (db.get(modele, id) for modele, id in (
            (models.Devis, did), (models.BonCommande, bcid), (models.BonLivraison, blid), (models.Facture, fid)))
        # Le statut converti est dérivé par _fmt_devis du lien BC existant.
        assert devis.statut in {"accepte", "converti"} and bc.devis_id == did and bl.bon_commande_id == bcid
        assert bl.statut == "livre" and bl.facture_id == fid and facture.est_validee and facture.est_comptabilisee
        assert bc.lignes[0].source_ligne_devis_id == devis.lignes[0].id
        assert bl.lignes[0].source_ligne_bc_id == bc.lignes[0].id
        ligne = facture.lignes[0]
        assert ligne.source_ligne_bc_id == bc.lignes[0].id and ligne.source_ligne_bl_id == bl.lignes[0].id
        assert ligne.article_id == aid and ligne.quantite == 2 and ligne.prix_unitaire == 500
        ec = db.query(models.Ecriture).filter_by(societe_id=sid).one()
        assert ec.est_validee
        assert {l.compte: (l.debit, l.credit) for l in ec.lignes} == {
            "3421": (1200, 0), "7111": (0, 1000), "4455": (0, 200)}
        tiers = next(l for l in ec.lignes if l.compte == "3421")
        assert tiers.tiers_id == tid and tiers.compte_auxiliaire_snapshot
        sortie = db.query(models.MouvementStock).filter_by(article_id=aid, source_type="facture").one()
        assert sortie.source_id == fid and sortie.source_ligne_id == ligne.id
        assert sortie.facture_id == fid and sortie.type == "sortie" and sortie.quantite == 2
        assert sortie.stock_avant == 10 and sortie.stock_apres == 8 and sortie.cle_idempotence
        return {(l.id, l.ecriture_id, l.compte, l.debit, l.credit) for l in ec.lignes}
