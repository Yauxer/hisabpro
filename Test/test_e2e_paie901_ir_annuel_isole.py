from contextlib import closing
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie901_ir_annuel_isole import (
    application,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,F)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('largeur',[1440,390])
def test_901_controle_annuel_exact_inconnus_et_historique_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel')
        with closing(prep):
            droit=None
            for cap in CAPS:
                h=grant(admin,u['id'],cap)
                if cap=='personnel.lire_remuneration':droit=h['id']
            activer(admin);sid=ok(admin.get('/api/auth/me'))['societe_id'];avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    contexte=browser.new_context(viewport={'width':largeur,'height':1000});page=contexte.new_page();erreurs,serveur=observer(page,app['api_url'])
                    connexion_personnel(page,app,mail,secret);page.goto(app['web_url']+'/personnel-paie/fiscalite')
                    expect(page.get_by_role('heading',name='Fiscalité salariale',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Consulter le barème et ses sources',exact=True).click();expect(page.get_by_role('heading',name='Barème général annuel 2026',exact=True)).to_be_visible();page.get_by_role('button',name='Fermer le barème',exact=True).click()
                    def calculer(rni,personnes):
                        page.get_by_role('button',name='Nouveau contrôle annuel IR',exact=True).click();d=page.get_by_role('dialog')
                        d.get_by_label('Revenu net imposable annuel déclaré (MAD)',exact=True).fill(rni)
                        if personnes is not None:d.get_by_label('Personnes fiscalement à charge confirmées',exact=True).select_option(str(personnes))
                        d.get_by_label('Référence du contrôle du RNI',exact=True).fill('RNI-FICTIF-UI901');d.get_by_label('Référence du contrôle des charges de famille',exact=True).fill('FAMILLE-FICTIVE-UI901')
                        d.get_by_label('Je confirme le RNI annuel déclaré et l’application du barème général, sans taux spécifique ni exonération non traitée.',exact=True).check()
                        if personnes is not None:d.get_by_label('J’ai vérifié l’éligibilité fiscale des personnes à charge déclarées, y compris une déclaration de zéro.',exact=True).check()
                        d.get_by_label('Motif du contrôle annuel',exact=True).fill('Contrôle annuel entièrement FICTIF901')
                        d.get_by_label('Je comprends que ce résultat arithmétique ne valide aucune paie ni déclaration.',exact=True).check()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        d.get_by_role('button',name='Calculer et conserver le contrôle',exact=True).click();expect(d).to_have_count(0)
                    calculer('200000.00',2);expect(page.get_by_test_id('ir-annuel-arithmetique')).to_have_text('45.400,00 MAD')
                    ancien=ok(prep.get(F))['elements'][0]['id'];original=ok(prep.get(f'{F}/{ancien}'))['contenu']
                    calculer('200000.00',None);expect(page.get_by_test_id('ir-annuel-arithmetique')).to_have_text('À compléter');expect(page.get_by_text('Nombre de personnes fiscalement éligibles et contrôle à confirmer ; ne pas le déduire de l’état civil.',exact=True)).to_be_visible()
                    calculer('40000.01',0);expect(page.get_by_test_id('ir-annuel-arithmetique')).to_have_text('0,001 MAD')
                    expect(page.get_by_text('Montant à déclarer : Non déterminé · Retenue mensuelle : Non calculée · Net à payer : Non calculé.',exact=True)).to_be_visible()
                    page.get_by_role('button',name=f'Consulter le contrôle {ancien}',exact=True).click();expect(page.get_by_test_id('ir-annuel-arithmetique')).to_have_text('45.400,00 MAD')
                    page.get_by_text('Détail exact par tranche',exact=True).click();page.get_by_role('heading',name=f'Résultat annuel 2026 · #{ancien}',exact=True).scroll_into_view_if_needed()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(R/f'docs/personnel-paie/preuves/901_{largeur}_ir_annuel.png'))
                    assert ok(prep.get(f'{F}/{ancien}'))['contenu']==original
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès fictif901'}));page.get_by_role('button',name='Actualiser',exact=True).click();expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération')
                    assert prep.get(F).status_code==403 and 'RNI-FICTIF-UI901' not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)')
                    assert comptabilite(app,sid)==avant and not erreurs and not serveur,(erreurs,serveur)
                finally:browser.close()
