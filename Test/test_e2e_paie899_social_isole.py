from contextlib import closing
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie899_social_isole import (
    application,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,preparer,rubrique,envoyer,submit,choix,V,T,C,brut)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('largeur',[1440,390])
def test_899_brut_vers_social_sources_et_historique_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,_,_=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            droit=None
            for uid in [u['id'],v['id']]:
                for cap in CAPS:
                    h=grant(admin,uid,cap)
                    if uid==u['id'] and cap=='personnel.lire_remuneration':droit=h['id']
            activer(admin);sid=ok(admin.get('/api/auth/me'))['societe_id'];eq={'a':prep,'b':valid,'uid':u['id'],'bid':v['id'],'sid':sid}
            eid,rid,q,_,_=preparer(eq);avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    contexte=browser.new_context(viewport={'width':largeur,'height':1000});page=contexte.new_page();erreurs,serveur=observer(page,app['api_url'])
                    connexion_personnel(page,app,mail,secret);page.goto(app['web_url']+'/personnel-paie/traitement');page.get_by_role('button',name=f'Voir le détail du calcul {q["id"]}',exact=True).click()
                    page.get_by_role('link',name='Préparer les cotisations de ce brut',exact=True).click()
                    expect(page.get_by_role('heading',name='Charges sociales',exact=True)).to_be_visible()
                    def calculer(source,motif):
                        page.get_by_role('button',name='Calculer les cotisations',exact=True).click();d=page.get_by_role('dialog')
                        d.get_by_label('Identifiant de la simulation du brut',exact=True).fill(str(source));d.get_by_role('button',name='Charger le brut',exact=True).click()
                        d.get_by_label('Régime déclaré pour cette sélection',exact=True).select_option('REGIME_SOC899')
                        d.get_by_label('Part de base soumise CNSS · P899 (MAD)',exact=True).fill('9000.10');d.get_by_label('Part de base soumise AMO · P899 (MAD)',exact=True).fill('9000.10')
                        d.get_by_label('Référence du contrôle · P899',exact=True).fill('CTRL-FICTIF-UI899')
                        d.get_by_label('Je confirme pour P899 le régime déclaré, les parts de base soumises et les conditions de toutes les rubriques utilisées.',exact=True).check()
                        d.get_by_label('Motif de la simulation sociale',exact=True).fill(motif)
                        d.get_by_label('Je comprends qu’il s’agit d’une simulation pédagogique, sans validation juridique ni net à payer.',exact=True).check()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        d.get_by_role('button',name='Calculer et conserver',exact=True).click();expect(d).to_have_count(0)
                    calculer(q['id'],'Calcul social fictif899')
                    expect(page.get_by_test_id('social-salarial')).to_have_text('354,00 MAD');expect(page.get_by_test_id('social-patronal')).to_have_text('512,00 MAD')
                    expect(page.get_by_text('Assiette CNSS : 9.500,11 MAD · Assiette AMO : 9.800,11 MAD · Brut : 9.800,11 MAD',exact=True)).to_be_visible()
                    ancien=ok(prep.get(C))['elements'][0]['id'];original=ok(prep.get(f'{C}/{ancien}'))['contenu']
                    extra=rubrique(eq,'EXTRA_UI899',periodicite='ponctuelle');variable=envoyer(eq,eid,extra,montant='100.00',source_reference='EXTRA-UI-FICTIF899')
                    calculer(q['id'],'Source ancienne à bloquer FICTIF899');expect(page.get_by_test_id('social-salarial')).to_have_text('À compléter')
                    expect(page.get_by_text('Sources courantes différentes du snapshot du brut ; créer une nouvelle simulation du brut.',exact=True)).to_be_visible()
                    submit(eq,variable['id']);ok(valid.post(f'{V}/{variable["id"]}/approuver',json=choix()));q2=brut(eq,[eid])
                    calculer(q2['id'],'Recalcul après nouveau brut FICTIF899');expect(page.get_by_test_id('social-salarial')).to_have_text('357,00 MAD');expect(page.get_by_test_id('social-patronal')).to_have_text('516,00 MAD')
                    page.get_by_role('button',name=f'Voir le détail des cotisations {ancien}',exact=True).click();expect(page.get_by_test_id('social-salarial')).to_have_text('354,00 MAD')
                    assert ok(prep.get(f'{C}/{ancien}'))['contenu']==original and original['totaux']['net_a_payer'] is None
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(R/f'docs/personnel-paie/preuves/899_{largeur}_social.png'))
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès fictif899'}));page.get_by_role('button',name='Actualiser',exact=True).click();expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération')
                    assert prep.get(C).status_code==403 and 'CTRL-FICTIF-UI899' not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)')
                    assert comptabilite(app,sid)==avant and not erreurs and not serveur,(erreurs,serveur)
                finally:browser.close()
