"""Parcours UI du coffre :politique,pièce,banque,validation indépendante et révocation."""
from pathlib import Path
from contextlib import closing
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_personnel887_banque_isole import (
    application,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,W,P,C,creation,decision,soumettre,PDF,comptabilite)
from test_e2e_administration_isole import connexion,observer
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_personnel879_isole import soumettre_ui,ouvrir_demande

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
def test_887_coffre_complet_edge(application,largeur):
    app=application;secret_rib='FICTIF-UI-887-1122'
    admin,email_admin,secret_admin=client(app)
    with closing(admin):
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,mailv,secretv=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            aid=ok(admin.get('/api/auth/me'))['id'];droits={}
            for uid in [aid,u['id'],v['id']]:
                for cap in CAPS:grant(admin,uid,cap)
                droits[uid]=grant(admin,uid,'personnel.lire_identifiants_sensibles')['id']
            activer(admin)
            e=ok(admin.post(W,json=creation('P887-UI',nom='Banque et pièces FICTIVES887')),201);eid=e['employe_id']
            soumettre(admin,e['demande']['id'],0);ok(valid.post(f'{W}/demandes/{e["demande"]["id"]}/approuver',json=decision(0)))
            avant=comptabilite(app,ok(admin.get('/api/auth/me'))['societe_id'])
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    ca=browser.new_context(viewport={'width':largeur,'height':1000});cp=browser.new_context(viewport={'width':largeur,'height':1000});cv=browser.new_context(viewport={'width':largeur,'height':1000})
                    ap=ca.new_page();page=cp.new_page();review=cv.new_page();erreurs,serveur=observer(page,app['api_url']);ev,sv=observer(review,app['api_url']);ea,sa=observer(ap,app['api_url'])
                    # Compte administrateur de la société de recette.
                    info=ok(admin.get('/api/auth/me'))
                    connexion(ap,app['web_url'],email_admin,secret_admin)
                    ap.goto(app['web_url']+'/personnel-paie/acces');ap.get_by_role('button',name='Déclarer la politique du coffre',exact=True).click();d=ap.get_by_role('dialog')
                    for label,valeur in [('Référence de la procédure de garde des clés','GARDE-UI-FICTIVE887'),('Référence de la politique de conservation','CONSERVATION-UI-FICTIVE887'),('Référence de rotation et sauvegarde','RESTAURATION-UI-FICTIVE887'),('Motif de la déclaration','Procédures fictives de recette887')]:d.get_by_label(label,exact=True).fill(valeur)
                    d.get_by_label('Je confirme disposer de procédures de garde des clés,de conservation et de sauvegarde/restauration.',exact=True).check()
                    d.get_by_role('button',name='Enregistrer la déclaration',exact=True).click();expect(d).to_have_count(0)
                    connexion_personnel(page,app,mail,secret);connexion_personnel(review,app,mailv,secretv)
                    page.goto(app['web_url']+f'/personnel-paie/personnel/{eid}')
                    page.get_by_role('button',name='Déposer une pièce privée',exact=True).click();d=page.get_by_role('dialog')
                    d.get_by_label('Catégorie de la pièce',exact=True).select_option('banque')
                    d.get_by_label('Fichier privé PDF,PNG ouJPEG',exact=True).set_input_files({'name':'NOM-PERSONNEL-FICTIF887.pdf','mimeType':'application/pdf','buffer':PDF})
                    d.get_by_role('button',name='Chiffrer et déposer',exact=True).click();expect(d).to_have_count(0)
                    piece=ok(prep.get(f'{C}/{eid}/pieces'))[0]['id']
                    with page.expect_download() as dl:page.get_by_role('button',name=f'Télécharger la pièce {piece}',exact=True).click()
                    telechargement=dl.value;chemin=app['directory']/f'piece887_{largeur}.pdf';telechargement.save_as(chemin)
                    assert chemin.read_bytes()==PDF and telechargement.suggested_filename==f'piece-personnel-{piece}.pdf'
                    page.get_by_role('button',name='Proposer des coordonnées bancaires',exact=True).click();d=page.get_by_role('dialog')
                    for label,valeur in [('Date d’effet bancaire','2026-01-01'),('RIB / IBAN attesté',secret_rib),('Banque (facultatif)','Banque FICTIVE887'),('Titulaire (facultatif)','Titulaire FICTIF887'),('Référence du justificatif bancaire','JUSTIFICATIF-UI-FICTIF887'),('Motif de la proposition bancaire','Nouvelle proposition fictive887')]:d.get_by_label(label,exact=True).fill(valeur)
                    d.get_by_label('Pièce chiffrée associée (facultatif)',exact=True).select_option(str(piece))
                    d.get_by_role('button',name='Enregistrer la proposition bancaire',exact=True).click();expect(d).to_have_count(0)
                    i=ok(prep.get(W+'/demandes',params={'employe_id':eid}))['elements'][0]['id'];soumettre_ui(page,i)
                    review.goto(app['web_url']+'/personnel-paie/demandes');d=ouvrir_demande(review,i)
                    expect(d.get_by_text(secret_rib,exact=True)).to_have_count(0)
                    d.get_by_role('button',name='Consulter les coordonnées proposées',exact=True).click();expect(d.get_by_text(secret_rib,exact=True)).to_be_visible()
                    with review.expect_download() as justif:d.get_by_role('button',name='Télécharger le justificatif associé',exact=True).click()
                    fichier_justif=app['directory']/f'justificatif887_{largeur}.pdf';justif.value.save_as(fichier_justif);assert fichier_justif.read_bytes()==PDF
                    d.get_by_role('button',name='Approuver',exact=True).click()
                    d.get_by_label('Motif de la décision',exact=True).fill('Contrôle indépendant fictif887');d.get_by_label('Référence du contrôle indépendant',exact=True).fill('CTRL-UI-FICTIF887')
                    d.get_by_label('J’ai vérifié les coordonnées bancaires proposées et leur justificatif.',exact=True).check()
                    d.get_by_label('Je confirme être indépendant du préparateur et du bénéficiaire de cette demande.',exact=True).check()
                    d.get_by_role('button',name='Confirmer l’approbation',exact=True).click();expect(d).to_have_count(0)
                    page.get_by_role('button',name='Actualiser',exact=True).click();page.get_by_role('button',name='Consulter les coordonnées approuvées',exact=True).click()
                    expect(page.get_by_text(secret_rib,exact=True)).to_be_visible();page.get_by_role('button',name='Masquer les coordonnées',exact=True).click()
                    expect(page.get_by_text(secret_rib,exact=True)).to_have_count(0)
                    page.get_by_role('heading',name='Banque et pièces privées',exact=True).scroll_into_view_if_needed()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    page.screenshot(path=str(R/f'docs/personnel-paie/preuves/887_{largeur}_coffre.png'))
                    ok(admin.post(P+f'/habilitations/{droits[u["id"]]}/revoquer',json={'motif':'Fin accès privé fictif887'}))
                    page.get_by_role('button',name='Actualiser',exact=True).click();expect(page.get_by_text('Masquées selon vos habilitations.',exact=True)).to_be_visible()
                    assert secret_rib not in page.locator('body').inner_text() and secret_rib not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)')
                    assert comptabilite(app,info['societe_id'])==avant
                    assert not erreurs and not serveur and not ev and not sv and not ea and not sa,(erreurs,serveur,ev,sv,ea,sa)
                finally:browser.close()
