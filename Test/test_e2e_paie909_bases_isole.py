from contextlib import closing
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie909_bases_isole import (
    application,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,preparer,F)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('largeur',[1440,390])
def test_909_bases_fiscales_connectees_inconnus_historique_et_retrait_acces_edge(application,largeur):
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
            eid,rid,q,s,_=preparer(eq);avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    ctx=browser.new_context(viewport={'width':largeur,'height':1000});page=ctx.new_page();erreurs,serveur=observer(page,app['api_url'])
                    connexion_personnel(page,app,mail,secret);page.goto(app['web_url']+'/personnel-paie/charges-sociales/simulations')
                    page.get_by_role('button',name=f'Voir le détail des cotisations {s["id"]}',exact=True).click()
                    page.get_by_role('link',name='Préparer les bases fiscales',exact=True).click()
                    for connu in [True,False]:
                        page.get_by_role('button',name='Préparer les bases fiscales',exact=True).click();d=page.get_by_role('dialog')
                        expect(d.get_by_label('Identifiant de la simulation sociale',exact=True)).to_have_value(str(s['id']))
                        d.get_by_role('button',name='Charger le social',exact=True).click()
                        d.get_by_label('Part imposable de la base salariale · P909 (MAD)',exact=True).fill('9000.10')
                        if connu:d.get_by_label('Part de base éligible aux frais professionnels · P909 (MAD)',exact=True).fill('9000.10')
                        d.get_by_label('Référence du contrôle fiscal · P909',exact=True).fill('CTRL-FICTIF909')
                        d.get_by_label('Motif de la préparation fiscale',exact=True).fill('Recette fictive909')
                        for coche in d.get_by_role('checkbox').all():coche.check()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        d.get_by_role('button',name='Calculer et conserver les bases',exact=True).click();expect(d).to_have_count(0)
                        expect(page.get_by_test_id('fiscal-brut_imposable').first).to_have_text('9.300,11 MAD')
                        expect(page.get_by_test_id('fiscal-base_frais_professionnels').first).to_have_text('9.000,10 MAD' if connu else 'À compléter')
                        expect(page.get_by_test_id('fiscal-cotisations_salariales_deductibles').first).to_have_text('60,00 MAD')
                        expect(page.get_by_test_id('fiscal-cotisations_salariales_non_deductibles').first).to_have_text('294,00 MAD')
                        expect(page.get_by_test_id('fiscal-revenu_avant_frais_autres_deductions').first).to_have_text('9.240,11 MAD')
                        page.get_by_text('Qualifications fiscales conservées',exact=True).click()
                        expect(page.get_by_role('link',name='Source IR de GAIN_FICTIF909',exact=True)).to_have_attribute('href','https://www.finances.gov.ma/')
                        expect(page.get_by_role('link',name='Source — Frais professionnels',exact=True)).to_be_visible()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        page.get_by_text('Qualifications fiscales conservées',exact=True).click()
                        if connu:ancien=ok(prep.get(F))['elements'][0]['id']
                    assert ok(prep.get(f'{F}/{ancien}'))['contenu']['totaux']['base_frais_professionnels']=='9000.10'
                    expect(page.get_by_text('Frais professionnels déduits : À compléter · RNI définitif : Non déterminé · IR et net : Non calculés.',exact=True)).to_be_visible()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(R/f'docs/personnel-paie/preuves/909_{largeur}_bases.png'))
                    page.get_by_role('button',name='Contrôle annuel IR',exact=True).click();expect(page.get_by_role('button',name='Nouveau contrôle annuel IR',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Bases fiscales',exact=True).click();expect(page.get_by_role('button',name='Préparer les bases fiscales',exact=True)).to_be_visible()
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès fictif909'}));page.get_by_role('button',name='Actualiser',exact=True).click()
                    expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération')
                    assert prep.get(F).status_code==403 and '9000.10' not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)')
                    assert comptabilite(app,sid)==avant and not erreurs and not serveur,(erreurs,serveur)
                finally:browser.close()
