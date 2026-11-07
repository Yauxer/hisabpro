"""Compte personnel et accès invité : API isolée et React réel dans Edge."""
import pytest
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from test_session132_admin_acces_invites import acces, headers
from test_session132_admin_navigateur import bundle


@pytest.mark.parametrize("compte_actif,acces_actif", [(False, True), (False, False), (True, False), (True, True)])
def test_annuaire_et_bascule_separent_compte_global_et_acces_local(acces, compte_actif, acces_actif):
    client, engine = acces
    with Session(engine) as db:
        db.get(models.Utilisateur, 3).actif = compte_actif
        db.query(models.UtilisateurSociete).filter_by(utilisateur_id=3, societe_id=1).one().actif = acces_actif
        db.commit()
    rows = client.get("/api/utilisateurs", headers=headers()).json()
    invite = next(row for row in rows if row["id"] == 3)
    assert invite["actif"] == (compte_actif and acces_actif)
    assert invite["actif_compte"] == compte_actif
    assert invite["actif_acces"] == acces_actif
    response = client.patch("/api/utilisateurs/3", json={"actif": not acces_actif}, headers=headers())
    assert response.status_code == 200
    assert response.json()["actif_acces"] == (not acces_actif)
    assert response.json()["actif_compte"] == compte_actif
    with Session(engine) as db:
        assert db.get(models.Utilisateur, 3).actif == compte_actif


@pytest.mark.parametrize("acces_actif", [True, False])
def test_bascule_ui_invite_desactive_globalement_modifie_seulement_acces(bundle, acces_actif):
    playwright = pytest.importorskip("playwright.sync_api")
    executable = chromium_executable()
    if not executable:
        pytest.skip("Navigateur Chromium absent")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page()
            page.set_default_timeout(5000)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.set_content('<div id="root"></div>')
            page.evaluate("actif=>{window.testUsers=[{id:3,nom:'Invité désactivé',email:'invite@example.com',role:'lecture',actif:false,acces_invite:true,actif_compte:false,actif_acces:actif}]}", acces_actif)
            page.add_script_tag(content=bundle)
            page.get_by_text("Compte désactivé", exact=True).wait_for()
            titre = "Désactiver l'accès" if acces_actif else "Activer l'accès"
            page.get_by_title(titre, exact=True).click()
            page.wait_for_function("window.lastModified!==undefined")
            assert page.evaluate("window.lastModified") == {"id": 3, "body": {"actif": not acces_actif}}
            page.get_by_title("Activer l'accès" if acces_actif else "Désactiver l'accès", exact=True).wait_for()
            assert page.get_by_text("Compte désactivé", exact=True).count() == 1
            assert not errors
        finally:
            browser.close()
