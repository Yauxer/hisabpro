"""TVA encaissement : vraie UI/API et PostgreSQL éphémère, données fictives."""
from datetime import date
from decimal import Decimal
from io import BytesIO
import uuid

import httpx
import pytest
from pypdf import PdfReader
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def verifier_declaration(data, collectee, recuperable, due, credit=0):
    assert Decimal(str(data["collectee"]["total"])) == collectee
    assert Decimal(str(data["recuperable"]["total"])) == recuperable
    assert Decimal(str(data["tva_due"])) == due
    assert Decimal(str(data["credit_tva"])) == credit


def test_factures_paiements_partiels_periodes_et_parametres_tva_ui(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = f"tva-{suffix}@example.com", "TVAE2E132!"
    annee = date.today().year
    with httpx.Client(base_url=application["api_url"]) as api:
        response = api.post("/api/auth/register", json={"nom": "Administrateur TVA", "email": email,
                            "password": password, "raison_sociale": f"TVA fictive {suffix}"})
        assert response.status_code == 200, response.text
        api.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        response = api.patch("/api/societe/moi", json={"regime_tva": "encaissement"})
        assert response.status_code == 200, response.text
        sid = response.json()["id"]
        for nature, prix, paiement in (("vente", 1000, 600), ("achat", 500, 300)):
            nom = f"Tiers TVA {nature} {suffix}"
            response = api.post("/api/tiers", json={"nom": nom,
                                "type": "client" if nature == "vente" else "fournisseur",
                                "categorie_fiscale": "particulier" if nature == "vente" else "professionnel"})
            assert response.status_code == 201, response.text
            response = api.post("/api/factures", json={"type": nature, "date": f"{annee}-03-20",
                                "tiers": nom, "tiers_id": response.json()["id"], "reference": f"TVA-{nature}-{suffix}",
                                "lignes": [{"description": "Prestation fictive TVA", "quantite": 1,
                                "prix_unitaire": prix, "tva": 20}]})
            assert response.status_code == 201, response.text
            fid = response.json()["id"]
            response = api.post(f"/api/factures/{fid}/valider")
            assert response.status_code == 200, response.text
            response = api.post(f"/api/factures/{fid}/comptabiliser")
            assert response.status_code == 200, response.text
            assert api.post(f"/api/ecritures/{response.json()['ecriture_id']}/valider").status_code == 200
            response = api.post("/api/reglements", json={"date": f"{annee}-04-03", "facture_id": fid,
                                "tiers": nom, "montant": paiement, "mode": "virement",
                                "reference": f"VIR-TVA-{nature}-{suffix}", "comptabiliser": True})
            assert response.status_code == 201, response.text
            assert api.post(f"/api/ecritures/{response.json()['ecriture_id']}/valider").status_code == 200
        with Session(application["engine"]) as db:
            ecritures = db.query(models.Ecriture).filter_by(societe_id=sid).all()
            assert len(ecritures) == 4 and all(e.est_validee for e in ecritures)
            assert all(sum(l.debit for l in e.lignes) == sum(l.credit for l in e.lignes) for e in ecritures)
            lignes = [l for e in ecritures for l in e.lignes]
            assert sum(l.credit for l in lignes if l.compte == "4455") == 200
            assert sum(l.debit for l in lignes if l.compte == "34552") == 100
            assert sum(l.debit for l in lignes) == Decimal("2700")
            avant = {(l.id, l.ecriture_id, l.compte, l.debit, l.credit, l.tiers_id) for l in lignes}
            factures = db.query(models.Facture).filter_by(societe_id=sid).all()
            assert len(factures) == 2
            assert all(f.regime_tva == "encaissement" and f.statut.value == "partiellement_payee" for f in factures)
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
                page.goto(application["web_url"] + "/declaration-tva", wait_until="domcontentloaded")
                page.get_by_role("heading", name="Déclaration TVA", exact=True).wait_for()
                choisir_mois(page, 3, lambda data: verifier_declaration(data, 0, 0, 0))
                choisir_mois(page, 4, lambda data: verifier_declaration(data, 100, 50, 50))
                ventes = page.locator("tbody tr").filter(has_text="Ventes soumises à 20%")
                achats = page.locator("tbody tr").filter(has_text="Achats soumis à 20%")
                assert ventes.locator("td").all_text_contents() == ["Ventes soumises à 20%", "4455", "500,00", "100,00", "600,00"]
                assert achats.locator("td").all_text_contents() == ["Achats soumis à 20%", "3455", "250,00", "50,00", "300,00"]
                with page.expect_response(lambda r: "/api/tva/declaration?" in r.url and "trimestre=2" in r.url) as trimestre:
                    page.get_by_role("button", name="Trimestrielle", exact=True).click()
                    page.get_by_role("button", name="T2", exact=True).click()
                assert trimestre.value.status == 200, trimestre.value.text()
                verifier_declaration(trimestre.value.json(), 100, 50, 50)
                page.get_by_role("button", name="Vue annuelle", exact=True).wait_for()
                with page.expect_response(lambda r: "/api/tva/declaration?" in r.url and "trimestre=" not in r.url and "mois=" not in r.url) as annuel:
                    page.get_by_role("button", name="Vue annuelle", exact=True).click()
                assert annuel.value.status == 200, annuel.value.text()
                verifier_declaration(annuel.value.json(), 100, 50, 50)
                page.get_by_role("button", name="Préparation DGI", exact=True).click()
                page.get_by_text("Brouillon de contrôle", exact=True).wait_for()
                assert page.get_by_label("Raison sociale", exact=True).input_value() == f"TVA fictive {suffix}"
                assert page.get_by_label("N° IF", exact=True).input_value() == ''
                assert page.get_by_label("N° ICE", exact=True).input_value() == ''
                ventes_dgi = page.locator("label").filter(has_text="Total TVA exigible").locator("..").locator("input")
                achats_dgi = page.locator("label").filter(has_text="Total TVA récupérable").locator("..").locator("input")
                assert ventes_dgi.last.input_value() == "100,00"
                assert achats_dgi.last.input_value() == "50,00"
                # 967 : pas de faux bouton de télédéclaration ; le dépôt reste hors HisabPro.
                assert page.get_by_text("Dépôt sur le portail DGI (hors HisabPro)", exact=True).is_visible()
                # Paramètres fictifs explicites : 50*80%=40 récupérable,
                # 100-40-20 de crédit d'ouverture = 40 à payer sur l'année.
                page.locator("label").filter(has_text="Crédit TVA d’ouverture").locator("..").locator("input").fill("20")
                page.locator("label").filter(has_text="Prorata annuel de déduction").locator("..").locator("input").fill("80")
                with page.expect_response(lambda r: r.url.endswith(f"/api/tva/parametres/{annee}") and r.request.method == "PUT") as param:
                    page.get_by_role("button", name="Enregistrer", exact=True).click()
                assert param.value.status == 200, param.value.text()
                page.get_by_text("Crédit TVA antérieur", exact=True).wait_for()
                annuel_final = api.get(f"/api/tva/declaration?exercice={annee}")
                assert annuel_final.status_code == 200, annuel_final.text
                verifier_declaration(annuel_final.json(), 100, 40, 40)
                playwright.expect(page.locator("label").filter(has_text="TVA nette à payer après report")
                                  .locator("..").locator("input").last).to_have_value("40,00")
                # Instrumenter uniquement l'appel natif d'impression ; les API
                # et données restent réelles. Le rendu PDF est lu séparément.
                page.evaluate("""() => { window.__impressions = 0; const imprimer = window.print.bind(window);
                    window.print = () => { window.__impressions++; imprimer(); }; }""")
                page.get_by_role('button', name='Imprimer', exact=True).click()
                assert page.evaluate('window.__impressions') == 1
                pdf = PdfReader(BytesIO(page.pdf(format='A4', print_background=True)))
                texte = '\n'.join(p.extract_text() or '' for p in pdf.pages)
                assert f'TVA fictive {suffix}' in texte and 'sans dépôt DGI' in texte
                assert '100,00' in texte and '40,00' in texte
                assert 'IF : à compléter' in texte and 'ICE : à compléter' in texte
                page.reload(wait_until="domcontentloaded")
                page.get_by_role("heading", name="Déclaration TVA", exact=True).wait_for()
                playwright.expect(page.locator("label").filter(has_text="Crédit TVA d’ouverture").locator("..").locator("input")).to_have_value("20")
                playwright.expect(page.locator("label").filter(has_text="Prorata annuel de déduction").locator("..").locator("input")).to_have_value("80")
                with Session(application["engine"]) as db:
                    apres = {(l.id, l.ecriture_id, l.compte, l.debit, l.credit, l.tiers_id)
                             for l in db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid).all()}
                    assert apres == avant
                    params = db.query(models.TVAParametreExercice).filter_by(societe_id=sid, exercice=annee).one()
                    assert Decimal(str(params.credit_ouverture)) == 20
                    assert Decimal(str(params.prorata_deduction_pct)) == 80
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print("Page TVA fictive :", page.url, page.locator("body").inner_text()[:6000])
                print("Erreurs JavaScript/API :", errors, server_errors)
                print("Log API isolée :", application["api_log"].read_text(encoding="utf-8", errors="replace")[-8000:])
                raise
            finally:
                browser.close()


def choisir_mois(page, mois, verifier):
    with page.expect_response(lambda r: "/api/tva/declaration?" in r.url and f"mois={mois}" in r.url) as declaration:
        page.get_by_text("Mois", exact=True).locator("..").locator("select").select_option(str(mois))
    assert declaration.value.status == 200, declaration.value.text()
    verifier(declaration.value.json())
    page.get_by_text("Calcul de la déclaration…", exact=True).wait_for(state="hidden")


def test_lecture_consulte_et_imprime_sans_modifier_parametres_tva(application):
    from test_e2e_recouvrement_isole import dossier_synthetique
    dossier = dossier_synthetique(application)
    email = f"lecture-tva-{dossier['suffix']}@example.com"
    password = 'LectureTVA132!'
    annee = date.today().year
    with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer ' + dossier['token']}) as api:
        response = api.post('/api/utilisateurs', json={'nom': 'Lecteur TVA', 'email': email,
                            'mot_de_passe': password, 'role': 'lecture'})
        assert response.status_code == 201, response.text
        before = api.get(f'/api/tva/parametres/{annee}').json()
    playwright = pytest.importorskip('playwright.sync_api')
    executable = chromium_executable()
    if not executable:
        pytest.skip('Chromium/Edge requis')
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page()
            page.set_default_timeout(20000)
            errors, server_errors = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/declaration-tva', wait_until='domcontentloaded')
            page.get_by_role('heading', name='Déclaration TVA', exact=True).wait_for()
            assert page.get_by_role('button', name='Enregistrer', exact=True).count() == 0
            for label in ('Crédit TVA d’ouverture', 'Prorata annuel de déduction'):
                assert page.locator('label').filter(has_text=label).locator('..').locator('input').is_disabled()
            playwright.expect(page.get_by_role('button', name='Imprimer', exact=True)).to_be_enabled()
            status = page.evaluate("""async ({url,annee}) => { const r = await fetch(url+'/api/tva/parametres/'+annee,
                {method:'PUT',headers:{Authorization:'Bearer '+localStorage.getItem('hisabpro_token'),
                'Content-Type':'application/json'},body:JSON.stringify({credit_ouverture:123,prorata_deduction_pct:80})});return r.status; }""",
                {'url': application['api_url'], 'annee': annee})
            assert status == 403
            with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer ' + dossier['token']}) as api:
                assert api.get(f'/api/tva/parametres/{annee}').json() == before
            assert not errors and not server_errors
        finally:
            browser.close()
