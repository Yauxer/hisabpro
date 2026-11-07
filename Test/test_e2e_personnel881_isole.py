"""Deux profils Personnel réels :aucun fournisseur de données comptables monté."""
from contextlib import closing
from pathlib import Path
import json,re
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_personnel881_profil_isole import (
    application,application108,application107,application875,application873,application093,application092,
    application091,application090,application089,application087,migration,client,ok,role_client,grant,activer,CAPS,W,P)
from test_e2e_administration_isole import observer,ouvrir_navigation
from test_e2e_personnel879_isole import soumettre_ui,approuver_ui,derniere

R=Path(__file__).resolve().parents[1]

def connexion_personnel(page,app,email,secret):
    page.goto(app['web_url']);page.get_by_placeholder('admin@societe.ma').fill(email)
    page.locator('input[type="password"]').fill(secret);page.get_by_role('button',name='Se connecter',exact=True).click()
    try:
        page.wait_for_url('**/personnel-paie/personnel');expect(page.get_by_role('button',name='Créer un salarié',exact=True)).to_be_visible()
    except Exception:
        print('Écran connexion Personnel',page.url,page.locator('body').inner_text())
        page.screenshot(path=str(R/'.codex-tests/personnel881_connexion_echec.png'))
        raise

@pytest.mark.parametrize('largeur',[1440,390])
def test_881_deux_profils_personnel_sans_comptabilite_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,mailv,secretv=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            for uid in (u['id'],v['id']):
                for cap in CAPS:grant(admin,uid,cap)
            activer(admin)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    a=browser.new_context(viewport={'width':largeur,'height':1000});b=browser.new_context(viewport={'width':largeur,'height':1000})
                    page=a.new_page();review=b.new_page();erreurs,serveur=observer(page,app['api_url']);ev,sv=observer(review,app['api_url'])
                    appels=[];page.on('request',lambda r:appels.append(r.url.removeprefix(app['api_url']).split('?')[0]) if r.url.startswith(app['api_url']) else None)
                    connexion_personnel(page,app,mail,secret);connexion_personnel(review,app,mailv,secretv)
                    ouvrir_navigation(page);nav=page.get_by_role('complementary',name='Navigation principale')
                    expect(nav.get_by_role('button',name='Facturation',exact=True)).to_have_count(0)
                    expect(nav.get_by_role('button',name='Comptabilité',exact=True)).to_have_count(0)
                    expect(nav.get_by_role('link',name='Paramètres',exact=True)).to_have_count(0)
                    expect(nav.get_by_role('link',name='Tableau de bord',exact=True)).to_have_count(0)
                    expect(nav.get_by_text('Espace historique Paie & GRH',exact=True)).to_have_count(0)
                    nav.get_by_role('button',name='Personnel & Paie',exact=True).click()
                    if nav.get_by_role('link',name='Personnel',exact=True).is_visible():nav.get_by_role('link',name='Personnel',exact=True).click()
                    else:
                        nav.get_by_role('button',name='Personnel & Paie',exact=True).click();nav.get_by_role('link',name='Personnel',exact=True).click()
                    page.get_by_role('button',name='Créer un salarié',exact=True).click();d=page.get_by_role('dialog')
                    d.get_by_label('Matricule',exact=True).fill(f'P881-{largeur}')
                    d.get_by_label('Nom complet',exact=True).fill('Personnel cloisonné fictif881')
                    d.get_by_label('Compte utilisateur du salarié',exact=True).select_option('sans')
                    d.get_by_label('Je confirme l’absence de compte utilisateur pour ce salarié.',exact=True).check()
                    d.get_by_label('Référence du contrôle de rattachement',exact=True).fill('ATTESTATION-FICTIVE881')
                    d.get_by_label('Motif de création ou de reprise',exact=True).fill('Recette profils dédiés881')
                    d.get_by_role('button',name='Créer le brouillon',exact=True).click()
                    expect(page.get_by_role('heading',name='Personnel cloisonné fictif881',exact=True)).to_be_visible()
                    eid=ok(prep.get(W))['elements'][0]['employe_id'];i=derniere(prep,eid);soumettre_ui(page,i)
                    review.goto(app['web_url']+'/personnel-paie/demandes');approuver_ui(review,i)
                    page.get_by_role('button',name='Actualiser',exact=True).click();expect(page.get_by_text('Conditions à compléter ou à valider',exact=True)).to_be_visible()
                    # Une valeur locale falsifiée ne rend ni les pages ni les données accessibles.
                    page.evaluate("localStorage.setItem('hisabpro_role','admin')")
                    page.goto(app['web_url']+'/journal');page.wait_for_url('**/personnel-paie/personnel')
                    expect(page.get_by_role('button',name='Créer un salarié',exact=True)).to_be_visible()
                    assert not any(x.startswith(('/api/ecritures','/api/factures','/api/plan-comptable','/api/exercices','/api/societe/moi','/api/societe/modules')) for x in appels),appels
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    page.screenshot(path=str(R/f'docs/personnel-paie/preuves/881_{largeur}.png'))
                    assert not erreurs and not serveur and not ev and not sv,(erreurs,serveur,ev,sv)
                    (R/f'.codex-tests/personnel881_{largeur}_preuve.json').write_text(json.dumps({'largeur':largeur,'deux_profils_personnel':True,'approbation_ui':True,'aucun_chargement_comptable':True,'role_local_falsifie_sans_effet':True,'debordement':False,'donnees_reelles':False},indent=2),encoding='utf8')
                    page.get_by_role('link',name='Mon compte',exact=True).click()
                    page.get_by_label('Mot de passe actuel',exact=True).fill(secret)
                    nouveau='Secret-Fictif-UI881-Renouvele!'
                    page.get_by_label('Nouveau mot de passe',exact=True).fill(nouveau)
                    page.get_by_label('Confirmer le nouveau mot de passe',exact=True).fill(nouveau)
                    page.get_by_role('button',name='Modifier mon mot de passe',exact=True).click()
                    expect(page.get_by_role('button',name='Revenir à la connexion',exact=True)).to_be_visible()
                    assert prep.get('/api/auth/me').status_code==401
                    page.get_by_role('button',name='Revenir à la connexion',exact=True).click()
                    connexion_personnel(page,app,mail,nouveau)
                finally:browser.close()

def test_881_contexte_interrompu_reprise_reelle_edge(application):
    app=application
    with closing(client(app)[0]) as admin:
        api,u,mail,secret=role_client(app,admin,'personnel')
        with closing(api):
            for cap in CAPS:grant(admin,u['id'],cap)
            activer(admin)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    page=browser.new_page(viewport={'width':390,'height':1000});erreurs,serveur=observer(page,app['api_url'])
                    panne={'active':True,'tentatives':0}
                    def transport(route):
                        panne['tentatives']+=1
                        if panne['active']:route.abort()
                        else:route.continue_()
                    page.route(app['api_url']+W+'/contexte',transport)
                    page.goto(app['web_url']);page.get_by_placeholder('admin@societe.ma').fill(mail)
                    page.locator('input[type="password"]').fill(secret);page.get_by_role('button',name='Se connecter',exact=True).click()
                    expect(page.get_by_role('alert')).to_contain_text('Connexion au serveur indisponible')
                    panne['active']=False
                    page.get_by_role('button',name='Réessayer le contexte Personnel',exact=True).click()
                    page.wait_for_url('**/personnel-paie/personnel');expect(page.get_by_role('button',name='Créer un salarié',exact=True)).to_be_visible()
                    assert panne['tentatives']>=2 and not erreurs and not serveur
                finally:browser.close()
