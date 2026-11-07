from contextlib import closing
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie897_social_isole import (
    application,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,creer,approuver,dec,S)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('largeur',[1440,390])
def test_897_saisie_sociale_versions_conflit_et_acces_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,mailv,secretv=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            droit=None
            for uid in [u['id'],v['id']]:
                for cap in CAPS:
                    g=grant(admin,uid,cap)
                    if uid==u['id'] and cap=='personnel.lire_remuneration':droit=g['id']
            activer(admin);sid=ok(admin.get('/api/auth/me'))['societe_id'];eq={'a':prep,'b':valid,'uid':u['id'],'bid':v['id'],'sid':sid};avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    contexte=browser.new_context(viewport={'width':largeur,'height':1000});page=contexte.new_page();erreurs,serveur=observer(page,app['api_url'])
                    connexion_personnel(page,app,mail,secret);page.goto(app['web_url']+'/personnel-paie/charges-sociales')
                    expect(page.get_by_role('heading',name='Charges sociales',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Créer une branche',exact=True).click();d=page.get_by_role('dialog')
                    for label,valeur in [('Code de branche','BRANCHE_UI897'),('Code régime','REGIME_FICTIF'),('Libellé de branche','Branche entièrement FICTIVE897'),('Organisme','Organisme fictif'),('Début d’application','2026-01-01'),('Conditions et justification d’applicabilité','Données fictives de recette, sans portée réglementaire.'),('Motif de la proposition','Création fictive UI897')]:d.get_by_label(label,exact=True).fill(valeur)
                    d.get_by_label('Applicabilité',exact=True).select_option('APPLICABLE');d.get_by_label('Mode de calcul',exact=True).select_option('TAUX')
                    d.get_by_label('Assiette de la branche',exact=True).select_option('CNSS')
                    d.get_by_label('Taux salarial (%)',exact=True).fill('1.234567');d.get_by_label('Taux patronal (%)',exact=True).fill('2.5')
                    d.get_by_label('Plafonnement',exact=True).select_option('MONTANT');d.get_by_label('Plafond (MAD)',exact=True).fill('5000.00')
                    d.get_by_label('Composants couverts (codes séparés par virgules)',exact=True).fill('CT_FICTIF, IPE_FICTIF')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    d.get_by_role('button',name='Enregistrer la proposition',exact=True).click();expect(d).to_have_count(0)
                    page.get_by_role('button',name='Consulter BRANCHE_UI897',exact=True).click();detail=page.get_by_role('region',name='Versions BRANCHE_UI897',exact=True)
                    expect(detail.get_by_text('Composants : CT_FICTIF, IPE_FICTIF',exact=True)).to_be_visible()
                    expect(detail.get_by_role('button',name='Approuver la version 1',exact=True)).to_be_disabled()
                    root=ok(prep.get(S))['elements'][0];v1=ok(prep.get(f'{S}/{root["id"]}'))['versions'][0]
                    # Décideur distinct, réellement connecté dans le navigateur.
                    cv=browser.new_context(viewport={'width':largeur,'height':1000});pv=cv.new_page();ev,sv=observer(pv,app['api_url'])
                    connexion_personnel(pv,app,mailv,secretv);pv.goto(app['web_url']+'/personnel-paie/charges-sociales');pv.get_by_role('button',name='Consulter BRANCHE_UI897',exact=True).click()
                    pv.get_by_role('button',name='Approuver la version 1',exact=True).click();dv=pv.get_by_role('dialog')
                    dv.get_by_label('Motif de la décision',exact=True).fill('Contrôle fictif indépendant');dv.get_by_label('Référence du contrôle',exact=True).fill('CTRL-FICTIF897')
                    dv.get_by_label('Je confirme être indépendant du préparateur.',exact=True).check();dv.get_by_role('button',name='Confirmer l’approbation',exact=True).click();expect(dv).to_have_count(0)
                    expect(pv.get_by_role('heading',name='Version 1 · Approuvée · 2026-01-01',exact=True)).to_be_visible()
                    conflit=creer(eq,'IPE_DOUBLE',composants=['IPE_FICTIF']);pv.get_by_role('button',name='Actualiser',exact=True).click();pv.get_by_role('button',name='Consulter IPE_DOUBLE',exact=True).click()
                    pv.get_by_role('button',name='Approuver la version 1',exact=True).click();dv=pv.get_by_role('dialog');dv.get_by_label('Motif de la décision',exact=True).fill('Essai double couverture fictif');dv.get_by_label('Référence du contrôle',exact=True).fill('FICTIF');dv.get_by_label('Je confirme être indépendant du préparateur.',exact=True).check();dv.get_by_role('button',name='Confirmer l’approbation',exact=True).click()
                    expect(dv.get_by_role('alert')).to_contain_text('déjà couvert');dv.get_by_role('button',name='Annuler',exact=True).click()
                    page.get_by_role('button',name='Actualiser',exact=True).click();page.get_by_role('button',name='Consulter BRANCHE_UI897',exact=True).click();page.get_by_role('button',name='Proposer une nouvelle version',exact=True).click();d=page.get_by_role('dialog')
                    expect(d.get_by_label('Début d’application',exact=True)).to_have_value('');d.get_by_label('Début d’application',exact=True).fill('2027-01-01');d.get_by_label('Taux salarial (%)',exact=True).fill('1.5');d.get_by_label('Motif de la proposition',exact=True).fill('Version fictive future');d.get_by_role('button',name='Enregistrer la proposition',exact=True).click();expect(d).to_have_count(0)
                    expect(page.get_by_role('heading',name='Version 2 · Proposée · 2027-01-01',exact=True)).to_be_visible()
                    assert ok(prep.get(f'{S}/{root["id"]}'))['versions'][1]['contenu']['taux_salarial']=='1.234567'
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(R/f'docs/personnel-paie/preuves/897_{largeur}_social.png'))
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès fictif897'}));page.get_by_role('button',name='Actualiser',exact=True).click();expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération')
                    assert prep.get(S).status_code==403 and '1.234567' not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)')
                    assert comptabilite(app,sid)==avant and not erreurs and not serveur and not ev and not sv,(erreurs,serveur,ev,sv)
                finally:browser.close()
