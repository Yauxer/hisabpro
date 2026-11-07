from contextlib import closing
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie891_variables_isole import (
    application,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,avec_salaire,rubrique,V)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
def test_891_variable_saisie_et_decision_personnel_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,mailv,secretv=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            droit=None
            for uid in [u['id'],v['id']]:
                for cap in CAPS:
                    g=grant(admin,uid,cap)
                    if uid==u['id'] and cap=='personnel.lire_remuneration':droit=g['id']
            activer(admin);sid=ok(admin.get('/api/auth/me'))['societe_id'];eq={'a':prep,'b':valid,'uid':u['id'],'bid':v['id'],'sid':sid}
            eid,_=avec_salaire(eq);rid=rubrique(eq,formule='MONTANT' if largeur==1440 else 'QUANTITE_TAUX');avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    cp=browser.new_context(viewport={'width':largeur,'height':1000});cv=browser.new_context(viewport={'width':largeur,'height':1000});page=cp.new_page();review=cv.new_page()
                    ep,sp=observer(page,app['api_url']);ev,sv=observer(review,app['api_url'])
                    connexion_personnel(page,app,mail,secret);connexion_personnel(review,app,mailv,secretv)
                    page.goto(app['web_url']+'/personnel-paie/elements/variables');page.get_by_label('Mois des variables',exact=True).fill('2026-11')
                    page.get_by_role('button',name='Saisir une variable',exact=True).click();d=page.get_by_role('dialog')
                    d.get_by_label('Période de la variable',exact=True).fill('2026-11');d.get_by_label('Date d’effet de la variable',exact=True).fill('2026-11-15')
                    d.get_by_label('Salarié de la variable',exact=True).select_option(str(eid));d.get_by_label('Rubrique de la variable',exact=True).select_option(str(rid))
                    if largeur==1440:d.get_by_label('Montant de la variable (MAD)',exact=True).fill('800.01')
                    else:
                        d.get_by_label('Quantité de la variable',exact=True).fill('3');d.get_by_label('Taux unitaire de la variable (MAD)',exact=True).fill('0.335')
                    d.get_by_label('Référence justificatif ATTESTATION_FICTIVE',exact=True).fill('JUSTIFICATIF-UI-FICTIF891')
                    d.get_by_label('Référence de la source de la variable',exact=True).fill('SOURCE-UI-FICTIVE891');d.get_by_label('Motif de saisie de la variable',exact=True).fill('Saisie fictive891')
                    d.get_by_role('button',name='Enregistrer le brouillon',exact=True).click();expect(d).to_have_count(0)
                    item=ok(prep.get(V))['elements'][0];i=item['id'];assert item['montant']==('800.01' if largeur==1440 else '1.01')
                    page.get_by_role('button',name=f'Consulter la variable {i}',exact=True).click();expect(page.get_by_text('Rémunération contractuelle à cette date : 9000.10 MAD',exact=False)).to_be_visible()
                    page.get_by_role('button',name=f'Soumettre la variable {i}',exact=True).click();d=page.get_by_role('dialog');d.get_by_label('Motif de l’action sur la variable',exact=True).fill('Soumission fictive891');d.get_by_role('button',name='Confirmer l’action',exact=True).click();expect(d).to_have_count(0)
                    review.goto(app['web_url']+'/personnel-paie/elements/variables');review.get_by_label('Mois des variables',exact=True).fill('2026-11');review.get_by_role('button',name=f'Consulter la variable {i}',exact=True).click()
                    expect(review.get_by_text('ATTESTATION_FICTIVE : JUSTIFICATIF-UI-FICTIF891',exact=True)).to_be_visible()
                    review.get_by_role('button',name=f'Approuver la variable {i}',exact=True).click();d=review.get_by_role('dialog')
                    d.get_by_label('Motif de l’action sur la variable',exact=True).fill('Approbation indépendante fictive891');d.get_by_label('Référence du contrôle de la variable',exact=True).fill('CONTROLE-UI-FICTIF891')
                    d.get_by_label('Je suis indépendant du préparateur et du bénéficiaire de cette variable.',exact=True).check();d.get_by_label('J’ai vérifié la source et les justificatifs de cette variable.',exact=True).check()
                    d.get_by_role('button',name='Confirmer l’action',exact=True).click();expect(d).to_have_count(0)
                    page.get_by_role('button',name='Actualiser',exact=True).click();expect(page.get_by_label('Mois des variables',exact=True)).to_have_value('2026-11')
                    expect(page.get_by_role('region',name=f'Variable {i}',exact=True).get_by_text('Approuvée',exact=False)).to_be_visible();assert ok(prep.get(f'{V}/{i}'))['statut']=='APPROUVE'
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(R/f'docs/personnel-paie/preuves/891_{largeur}_variables.png'))
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès fictif891'}));page.get_by_role('button',name='Actualiser',exact=True).click()
                    expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération');assert prep.get(V).status_code==403
                    assert comptabilite(app,sid)==avant and not ep and not sp and not ev and not sv,(ep,sp,ev,sv)
                finally:browser.close()
