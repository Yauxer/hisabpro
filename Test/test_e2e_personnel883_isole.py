"""Date d'entrée et régimes approuvés dans Edge,API,PG isolé."""
from pathlib import Path
from contextlib import closing
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_personnel883_regimes_isole import (
    application,application109,application108,application107,application875,application873,application093,
    application092,application091,application090,application089,application087,migration,client,ok,role_client,grant,activer,CAPS,W,P)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_personnel879_isole import derniere,soumettre_ui,approuver_ui
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
def test_883_contrat_social_declare_et_masque_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,mailv,secretv=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            droits={}
            for uid in (u['id'],v['id']):
                for cap in CAPS:grant(admin,uid,cap)
                droits[uid]=grant(admin,uid,'personnel.lire_identifiants_sensibles')['id']
            activer(admin)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    a=browser.new_context(viewport={'width':largeur,'height':1000});b=browser.new_context(viewport={'width':largeur,'height':1000})
                    page=a.new_page();review=b.new_page();erreurs,serveur=observer(page,app['api_url']);ev,sv=observer(review,app['api_url'])
                    connexion_personnel(page,app,mail,secret);connexion_personnel(review,app,mailv,secretv)
                    page.get_by_role('button',name='Créer un salarié',exact=True).click();d=page.get_by_role('dialog')
                    d.get_by_label('Matricule',exact=True).fill(f'P883-UI-{largeur}');d.get_by_label('Nom complet',exact=True).fill('Salariée sociale FICTIVE883')
                    d.get_by_text('Coordonnées et informations personnelles (facultatif)',exact=True).click()
                    d.get_by_label('Date d’entrée connue',exact=True).fill('2025-12-15')
                    d.get_by_label('Compte utilisateur du salarié',exact=True).select_option('sans')
                    d.get_by_label('Je confirme l’absence de compte utilisateur pour ce salarié.',exact=True).check()
                    d.get_by_label('Référence du contrôle de rattachement',exact=True).fill('ATTEST-FICTIF883')
                    d.get_by_label('Motif de création ou de reprise',exact=True).fill('Création sociale fictive883')
                    d.get_by_role('button',name='Créer le brouillon',exact=True).click()
                    expect(page.get_by_role('heading',name='Salariée sociale FICTIVE883',exact=True)).to_be_visible()
                    eid=ok(prep.get(W))['elements'][0]['employe_id'];i=derniere(prep,eid);soumettre_ui(page,i)
                    review.goto(app['web_url']+'/personnel-paie/demandes');approuver_ui(review,i)
                    page.get_by_role('button',name='Actualiser',exact=True).click()
                    expect(page.get_by_text('Entrée connue : 15/12/2025',exact=True)).to_be_visible()
                    page.get_by_label('Consulter les conditions au',exact=True).fill('2026-12-31')
                    page.get_by_role('button',name='Proposer une modification',exact=True).click();d=page.get_by_role('dialog')
                    d.get_by_label('Nature de la proposition',exact=True).select_option('CONTRAT')
                    d.get_by_label('Type de contrat',exact=True).fill('CDI');d.get_by_label('Début du contrat',exact=True).fill('2026-01-01');d.get_by_label('Date d’effet',exact=True).fill('2026-01-01')
                    for label,valeur in [('Régime AMO déclaré','AMO-FICTIVE-UI883'),('Régime retraite déclaré','RETRAITE-FICTIVE-UI883'),('Régime mutuelle déclaré','MUTUELLE-FICTIVE-UI883')]:d.get_by_label(label,exact=True).fill(valeur)
                    d.get_by_label('Référence du justificatif',exact=True).fill('CONTRAT-FICTIF883');d.get_by_label('Motif de la proposition',exact=True).fill('Contrat et régimes déclarés fictifs883')
                    d.get_by_role('button',name='Enregistrer la proposition',exact=True).click();expect(d).to_have_count(0)
                    i=derniere(prep,eid);soumettre_ui(page,i);approuver_ui(review,i)
                    page.get_by_role('button',name='Actualiser',exact=True).click()
                    expect(page.get_by_text('AMO-FICTIVE-UI883',exact=True)).to_be_visible()
                    page.screenshot(path=str(R/f'docs/personnel-paie/preuves/883_{largeur}_regimes.png'))
                    ok(admin.post(P+f'/habilitations/{droits[u["id"]]}/revoquer',json={'motif':'Révocation sociale fictive883'}))
                    page.get_by_role('button',name='Actualiser',exact=True).click()
                    expect(page.get_by_role('heading',name='Régimes sociaux déclarés du contrat',exact=True)).to_be_visible()
                    expect(page.get_by_text('AMO-FICTIVE-UI883',exact=True)).to_have_count(0)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    assert not erreurs and not serveur and not ev and not sv,(erreurs,serveur,ev,sv)
                finally:browser.close()
