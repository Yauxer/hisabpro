from contextlib import closing
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie907_qualification_ir_isole import (
    application,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,E,S)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('largeur',[1440,390])
def test_907_formulaires_fiscaux_catalogue_et_social_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,mailv,secretv=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            for uid in [u['id'],v['id']]:
                for cap in CAPS:grant(admin,uid,cap)
            activer(admin);sid=ok(admin.get('/api/auth/me'))['societe_id'];avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    ctx=browser.new_context(viewport={'width':largeur,'height':1000});page=ctx.new_page();erreurs,serveur=observer(page,app['api_url'])
                    connexion_personnel(page,app,mail,secret)
                    for route,button,nom,traitement,code in [('elements','Créer une rubrique','Frais professionnels','EXCLUS','RUB_UI907'),('charges-sociales','Créer une branche','Déductibilité IR','NON_DEDUCTIBLE','BR_UI907')]:
                        page.goto(app['web_url']+'/personnel-paie/'+route);page.get_by_role('button',name=button,exact=True).click();d=page.get_by_role('dialog')
                        champs=[('Début d’application','2026-01-01'),('Motif de la proposition','Recette fictive907')]
                        if route=='elements':
                            champs += [('Code de rubrique',code),('Libellé de rubrique','Rubrique fictive907')]+[(f'Conditions {k}','Règle fictive non qualifiée') for k in ['IR','CNSS','AMO']]
                        else:champs += [('Code de branche',code),('Code régime','REGIME_UI907'),('Libellé de branche','Branche fictive907'),('Organisme','Organisme fictif'),('Conditions et justification d’applicabilité','Règle fictive non qualifiée')]
                        for label,valeur in champs:d.get_by_label(label,exact=True).fill(valeur)
                        d.get_by_label('Définir la qualification — '+nom,exact=True).check()
                        d.get_by_label('Traitement — '+nom,exact=True).select_option(traitement)
                        d.get_by_label('Qualification — '+nom,exact=True).select_option('VALIDE')
                        for label,valeur in [('Conditions','Hypothèse FICTIVE907 sans portée légale'),('Référence du justificatif','FICTIF907'),('Texte','Texte FICTIF907'),('Article','FICTIF907'),('URL officielle','https://www.finances.gov.ma/'),('Empreinte SHA-256 de la preuve','a'*64),('Date de consultation','2026-01-01')]:d.get_by_label(label+' — '+nom,exact=True).fill(valeur)
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        d.get_by_role('button',name='Enregistrer la proposition',exact=True).click();expect(d).to_have_count(0)
                        page.get_by_role('button',name='Consulter '+code,exact=True).click()
                        expect(page.get_by_role('button',name='Approuver la version 1',exact=True)).to_be_disabled()
                    cv=browser.new_context(viewport={'width':largeur,'height':1000});pv=cv.new_page();ev,sv=observer(pv,app['api_url']);connexion_personnel(pv,app,mailv,secretv)
                    for route,nom,code in [('elements','Frais professionnels','RUB_UI907'),('charges-sociales','Déductibilité IR','BR_UI907')]:
                        pv.goto(app['web_url']+'/personnel-paie/'+route);pv.get_by_role('button',name='Consulter '+code,exact=True).click()
                        expect(pv.get_by_role('button',name='Approuver la version 1',exact=True)).to_be_disabled()
                    grant(admin,v['id'],'personnel.valider_regles_paie')
                    for route,nom,code in [('elements','Frais professionnels','RUB_UI907'),('charges-sociales','Déductibilité IR','BR_UI907')]:
                        pv.goto(app['web_url']+'/personnel-paie/'+route);pv.get_by_role('button',name='Consulter '+code,exact=True).click()
                        pv.get_by_role('button',name='Approuver la version 1',exact=True).click();d=pv.get_by_role('dialog')
                        d.get_by_label('Motif de la décision',exact=True).fill('Contrôle indépendant fictif907');d.get_by_label('Référence du contrôle',exact=True).fill('CTRL-FICTIF907')
                        d.get_by_label('Je confirme être indépendant du préparateur.',exact=True).check()
                        preuve=d.get_by_role('checkbox').last;expect(preuve).to_have_attribute('required','');preuve.check()
                        d.get_by_role('button',name='Confirmer l’approbation',exact=True).click();expect(d).to_have_count(0)
                        expect(pv.get_by_role('heading',name='Version 1 · Approuvée · 2026-01-01',exact=True)).to_be_visible()
                        assert pv.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        pv.screenshot(path=str(R/f'docs/personnel-paie/preuves/907_{largeur}_{route}.png'))
                    assert comptabilite(app,sid)==avant and not erreurs and not serveur and not ev and not sv,(erreurs,serveur,ev,sv)
                finally:browser.close()
