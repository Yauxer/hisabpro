from contextlib import closing
from pathlib import Path
import re
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie893_campagnes_isole import (
    application,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,salarie,rubrique,envoyer,submit,choix,V,T)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
def test_893_campagne_brut_anomalie_recalcul_et_historique_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,_,_=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            droit=None
            for uid in [u['id'],v['id']]:
                for cap in CAPS:
                    g=grant(admin,uid,cap)
                    if uid==u['id'] and cap=='personnel.lire_remuneration':droit=g['id']
            activer(admin);sid=ok(admin.get('/api/auth/me'))['societe_id'];eq={'a':prep,'b':valid,'uid':u['id'],'bid':v['id'],'sid':sid}
            eid,_=salarie(eq);rid=rubrique(eq);variable=envoyer(eq,eid,rid);avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    contexte=browser.new_context(viewport={'width':largeur,'height':1000});page=contexte.new_page();erreurs,serveur=observer(page,app['api_url'])
                    connexion_personnel(page,app,mail,secret);page.goto(app['web_url']+'/personnel-paie/traitement')
                    expect(page.get_by_role('heading',name='Traitement de la paie',exact=True)).to_be_visible()
                    def calculer(motif):
                        page.get_by_role('button',name='Calculer le brut du mois',exact=True).click();d=page.get_by_role('dialog')
                        d.get_by_label('Mois de la simulation',exact=True).fill('2026-11');d.get_by_label(re.compile('P893 · Salariée FICTIVE893')).check()
                        d.get_by_label('Motif de la simulation',exact=True).fill(motif)
                        d.get_by_label('Je confirme que la sélection concerne des mois complets et que les variables de ce mois ont été préparées.',exact=True).check()
                        d.get_by_role('button',name='Calculer',exact=True).click();expect(d).to_have_count(0)
                    calculer('Première simulation FICTIVE893')
                    expect(page.get_by_test_id('brut-simulation')).to_have_text('À compléter')
                    expect(page.get_by_text('Des variables de ce mois restent à soumettre ou décider',exact=False)).to_be_visible()
                    root=ok(prep.get(T))['elements'][0];cid=root['id'];ancien=root['derniere_simulation_id']
                    submit(eq,variable['id']);ok(valid.post(f'{V}/{variable["id"]}/approuver',json=choix()))
                    calculer('Deuxième simulation FICTIVE893')
                    expect(page.get_by_test_id('brut-simulation')).to_have_text('9.800,11 MAD')
                    expect(page.get_by_text('Cotisations salariales : Non calculées',exact=False)).to_be_visible()
                    nouveau=ok(prep.get(T))['elements'][0];assert nouveau['derniere_version']==2 and nouveau['id']==cid
                    page.get_by_role('button',name=f'Historique des calculs {cid}',exact=True).click();page.get_by_role('button',name='Ouvrir la version 1',exact=True).click()
                    expect(page.get_by_test_id('brut-simulation')).to_have_text('À compléter');assert ok(prep.get(f'{T}/simulations/{ancien}'))['contenu']['totaux']['brut'] is None
                    page.get_by_role('button',name='Ouvrir la version 2',exact=True).click();expect(page.get_by_test_id('brut-simulation')).to_have_text('9.800,11 MAD')
                    page.get_by_role('heading',name='Calcul du brut · version 2',exact=True).scroll_into_view_if_needed()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(R/f'docs/personnel-paie/preuves/893_{largeur}_campagne.png'))
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès fictif893'}));page.get_by_role('button',name='Actualiser',exact=True).click()
                    expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération');assert prep.get(T).status_code==403
                    assert '9800.11' not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)')
                    assert comptabilite(app,sid)==avant and not erreurs and not serveur,(erreurs,serveur)
                finally:browser.close()
