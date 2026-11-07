from pathlib import Path
from contextlib import closing
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie921_mensuel_isole import (
    application,application123,application122,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,preparation,M)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
def test_921_bases_vers_rni_equivalence_retour_inconnues_et_revocation_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,_,_=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            droit=None
            for uid in [u['id'],v['id']]:
                for cap in CAPS:
                    g=grant(admin,uid,cap)
                    if uid==u['id'] and cap=='personnel.lire_remuneration':droit=g['id']
            activer(admin);sid=ok(admin.get('/api/auth/me'))['societe_id'];eq={'a':prep,'b':valid,'admin':admin,'uid':u['id'],'bid':v['id'],'sid':sid}
            eid,_,source=preparation(eq);avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    ctx=browser.new_context(viewport={'width':largeur,'height':1000});page=ctx.new_page();erreurs,serveur=observer(page,app['api_url'])
                    connexion_personnel(page,app,mail,secret);page.goto(app['web_url']+f'/personnel-paie/fiscalite?vue=bases&preparation_fiscale_id={source["id"]}')
                    for complet in [True,False]:
                        page.get_by_role('link',name='Préparer le RNI mensuel de P909',exact=True).click();d=page.get_by_role('dialog')
                        expect(d.get_by_role('heading',name='P909 · Salariée FICTIVE893',exact=True)).to_be_visible()
                        if complet:
                            d.get_by_label('Frais professionnels du mois déclarés (MAD)',exact=True).fill('2250.03');d.get_by_label('Référence des frais du mois',exact=True).fill('FRAIS-DECLARES-FICTIFS921')
                        d.get_by_label('Autres déductions du mois déclarées (MAD)',exact=True).fill('0.00');d.get_by_label('Référence des autres déductions du mois',exact=True).fill('AUCUNE-AUTRE-FICTIVE921')
                        d.get_by_label('Référence du contrôle du mois',exact=True).fill('MOIS-FICTIF921');d.get_by_label('Personnes fiscalement à charge pour le mois',exact=True).select_option('2')
                        d.get_by_label('Référence de la famille pour le mois',exact=True).fill('FAMILLE-FICTIVE921');d.get_by_label('Motif du contrôle mensuel',exact=True).fill('Contrôle mensuel entièrement FICTIF921')
                        for coche in d.get_by_role('checkbox').all():coche.check()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        d.get_by_role('button',name='Conserver le contrôle mensuel',exact=True).click();expect(d).to_have_count(0)
                        expect(page.get_by_test_id('rni-mensuel-constitue')).to_have_text('6.990,08 MAD' if complet else 'À compléter')
                        expect(page.get_by_test_id('ir-mensuel-equivalent')).to_have_text('497,024 MAD' if complet else 'À compléter')
                        expect(page.get_by_text('Date de versement déclarée : Non renseignée',exact=True)).to_be_visible()
                        if complet:
                            page.get_by_text('Calcul et fractions exactes conservés',exact=True).click();expect(page.get_by_text('IR après réduction : 62128 / 125 MAD',exact=True)).to_be_visible()
                            page.get_by_role('region',name='Résultat contrôle mensuel '+str(ok(prep.get(M))['elements'][0]['id']),exact=True).scroll_into_view_if_needed()
                            page.screenshot(path=str(R/f'docs/personnel-paie/preuves/921_{largeur}_mensuel.png'))
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        page.get_by_role('link',name='Revenir aux bases fiscales sources',exact=True).click();expect(page.get_by_role('heading',name='Bases fiscales · version '+str(source['numero']),exact=True)).to_be_visible()
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès FICTIF921'}));page.get_by_role('button',name='Actualiser',exact=True).click();expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération')
                    assert prep.get(M).status_code==403 and '6990.08' not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)') and comptabilite(app,sid)==avant
                    assert not erreurs and not serveur,(erreurs,serveur)
                finally:browser.close()
