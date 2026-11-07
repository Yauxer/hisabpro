from pathlib import Path
from contextlib import closing
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie915_ir_source_isole import (
    application,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,source_annuelle,F,I)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('largeur',[1440,390])
def test_915_rni_sans_ressaisie_liens_source_ir_et_revocation_edge(application,largeur):
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
            _,_,source=source_annuelle(eq);avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    ctx=browser.new_context(viewport={'width':largeur,'height':1000});page=ctx.new_page();erreurs,serveur=observer(page,app['api_url'])
                    connexion_personnel(page,app,mail,secret);page.goto(app['web_url']+f'/personnel-paie/fiscalite?vue=frais-annuels&controle_frais_id={source["id"]}')
                    expect(page.get_by_test_id('rni-annuel-source')).to_have_text('83.881,02 MAD')
                    page.get_by_role('link',name='Contrôler l’IR de ce RNI',exact=True).click();d=page.get_by_role('dialog')
                    expect(d.get_by_label('Identifiant du contrôle des frais annuels',exact=True)).to_have_value(str(source['id']))
                    d.get_by_role('button',name='Charger le RNI annuel',exact=True).click();expect(d.get_by_text('RNI constitué avant arrondis : 83.881,02 MAD',exact=True)).to_be_visible()
                    d.get_by_label('Personnes fiscalement à charge confirmées',exact=True).select_option('2')
                    d.get_by_label('Référence du contrôle des charges de famille',exact=True).fill('FAMILLE-FICTIVE915-EDGE')
                    d.get_by_label('Motif du contrôle IR sourcé',exact=True).fill('Contrôle FICTIF915, aucune base réelle')
                    for coche in d.get_by_role('checkbox').all():coche.check()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    d.get_by_role('button',name='Calculer et conserver l’IR annuel sourcé',exact=True).click();expect(d).to_have_count(0)
                    expect(page.get_by_test_id('ir-rni-source')).to_have_text('83.881,02 MAD');expect(page.get_by_test_id('ir-base-source-arrondie')).to_have_text('83.890,00 MAD')
                    expect(page.get_by_test_id('ir-annuel-arithmetique')).to_have_text('5.967,00 MAD')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    page.screenshot(path=str(R/f'docs/personnel-paie/preuves/915_{largeur}_ir_source.png'))
                    page.get_by_role('link',name='Consulter le contrôle des frais annuels source',exact=True).click();expect(page.get_by_test_id('rni-annuel-source')).to_have_text('83.881,02 MAD')
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès fictif915'}));page.get_by_role('button',name='Actualiser',exact=True).click();expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération')
                    assert prep.get(I).status_code==403 and '83881.0200' not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)')
                    assert comptabilite(app,sid)==avant and not erreurs and not serveur,(erreurs,serveur)
                finally:browser.close()
