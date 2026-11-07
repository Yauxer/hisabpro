from pathlib import Path
from contextlib import closing
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie913_frais_annuels_isole import (
    application,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,annee_prete,F)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('largeur',[1440,390])
def test_913_choix_mois_frais_annuels_inconnus_et_retrait_acces_edge(application,largeur):
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
            eid,_,ps=annee_prete(eq);avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    ctx=browser.new_context(viewport={'width':largeur,'height':1000});page=ctx.new_page();erreurs,serveur=observer(page,app['api_url'])
                    connexion_personnel(page,app,mail,secret);page.goto(app['web_url']+'/personnel-paie/fiscalite')
                    page.get_by_role('button',name='Cumuls et frais annuels',exact=True).click()
                    for complet in [True,False]:
                        page.get_by_role('button',name='Nouveau contrôle des frais annuels',exact=True).click();d=page.get_by_role('dialog')
                        d.get_by_label('Salarié dont les bases sont préparées',exact=True).select_option(str(eid));d.get_by_role('button',name='Charger les préparations',exact=True).click()
                        d.get_by_role('button',name='Choisir les mois à version unique',exact=True).click()
                        if not complet:d.get_by_label('Préparation de Janvier 2026',exact=True).select_option('')
                        d.get_by_label('Référence du contrôle des revenus annuels',exact=True).fill('ANNEE-FICTIVE913')
                        d.get_by_label('Autres déductions annuelles établies (MAD)',exact=True).fill('0.00');d.get_by_label('Référence des autres déductions',exact=True).fill('AUCUNE-AUTRE-FICTIVE913')
                        d.get_by_label('Motif du contrôle des frais annuels',exact=True).fill('Contrôle annuel FICTIF913')
                        for coche in d.get_by_role('checkbox').all():coche.check()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        d.get_by_role('button',name='Calculer et conserver le cumul',exact=True).click();expect(d).to_have_count(0)
                        expect(page.get_by_test_id('frais-annuels-montant')).to_have_text('27.000,30 MAD' if complet else 'À compléter')
                        expect(page.get_by_test_id('rni-annuel-source')).to_have_text('83.881,02 MAD' if complet else 'À compléter')
                        if complet:
                            ancien=ok(prep.get(F))['elements'][0]['id'];expect(page.get_by_test_id('cumul-brut_imposable')).to_have_text('111.601,32 MAD')
                            page.screenshot(path=str(R/f'docs/personnel-paie/preuves/913_{largeur}_annuel.png'))
                    assert ok(prep.get(f'{F}/{ancien}'))['contenu']['rni_annuel_arithmetique_avant_arrondis']=='83881.0200'
                    expect(page.get_by_text('Douze périodes mensuelles distinctes requises ; aucun mois multiplié ni période manquante remplacée par zéro.',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Bases fiscales',exact=True).click();expect(page.get_by_role('button',name='Préparer les bases fiscales',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Contrôle annuel IR',exact=True).click();expect(page.get_by_role('button',name='Nouveau contrôle annuel IR',exact=True)).to_be_visible()
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès fictif913'}));page.get_by_role('button',name='Actualiser',exact=True).click();expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération')
                    assert prep.get(F).status_code==403 and '27000.3000' not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)')
                    assert comptabilite(app,sid)==avant and not erreurs and not serveur,(erreurs,serveur)
                finally:browser.close()
