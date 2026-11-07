"""Accès réels au registre095 : navigateur sans réponse métier simulée."""
from contextlib import closing
import re
import uuid
from playwright.sync_api import sync_playwright, expect
import pytest
import httpx
from sqlalchemy import text
from test_avances_salaries_isole import (
    application,application093,application092,application091,application090,
    application089,application087,migration,employe,mouvement,affecter,originaux,PATH,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


def registre(app):
    with app['engine'].connect() as db:
        return db.execute(text('SELECT row_to_json(a)::text FROM grh_avances_affectations a ORDER BY id')).scalars().all()


def ouvrir(page,app):
    page.goto(app['web_url']+'/cnss')
    page.get_by_role('button',name='Avances des salariés',exact=True).click()
    zone=page.get_by_role('region',name='Avances des salariés',exact=True)
    expect(zone.get_by_role('table',name='Mouvements des avances')).to_be_visible()
    return zone


@pytest.mark.parametrize('largeur',[1440,390])
def test_lecteur_consulte_soldes_sans_actions_et_post_refuse(application,largeur):
    api,_,password=client(application)
    with closing(api):
        sid=ok(api.get('/api/societe/moi'))['id'];p=employe(api,'Bénéficiaire lecture fictif483')
        _,d=mouvement(api,1000);a=affecter(api,p,d)['id'];_,libre=mouvement(api,200)
        email='lecteur483-'+uuid.uuid4().hex[:8]+'@example.com'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecteur fictif483','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        avant=originaux(application,sid);avant_reg=registre(application)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
                errors,server=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
                zone=ouvrir(page,application)
                expect(zone.get_by_role('table',name='Soldes des avances')).to_contain_text('Bénéficiaire lecture fictif483')
                expect(zone.get_by_text('1 mouvement(s) non affecté(s)',exact=False)).to_be_visible()
                expect(zone.get_by_role('button',name='Affecter',exact=True)).to_have_count(0)
                expect(zone.get_by_role('button',name='Annuler le rattachement',exact=True)).to_have_count(0)
                codes=page.evaluate('''async ({url,p,ligne,a}) => {
                    const headers={Authorization:'Bearer '+localStorage.getItem('hisabpro_token'),'Content-Type':'application/json'};
                    const x=await fetch(url+'/api/employes/avances',{method:'POST',headers,body:JSON.stringify({employe_id:p,ligne_id:ligne,motif:'Refus lecteur fictif'})});
                    const y=await fetch(url+'/api/employes/avances/'+a+'/annuler',{method:'POST',headers,body:JSON.stringify({motif:'Refus lecteur fictif'})});
                    return [x.status,y.status];
                }''',{'url':application['api_url'],'p':p,'ligne':libre,'a':a})
                assert codes==[403,403]
                zone.get_by_role('button',name='Actualiser les avances').click()
                expect(zone.get_by_role('table',name='Soldes des avances')).to_contain_text('1.000,00 MAD')
                assert not errors and not server,(errors,server)
            finally:browser.close()
        assert originaux(application,sid)==avant and registre(application)==avant_reg


@pytest.mark.parametrize('largeur',[1440,390])
def test_switch_societe_abandonne_formulaire_et_conserve_registres(application,largeur):
    api,email,password=client(application)
    with closing(api):
        soca=ok(api.get('/api/societe/moi'));pa=employe(api,'Bénéficiaire A fictif483')
        _,da=mouvement(api,111);aa=affecter(api,pa,da)['id'];_,libre=mouvement(api,22)
        nomb='Société B avances483 '+uuid.uuid4().hex[:6]
        sb=ok(api.post('/api/societes/nouvelle',json={'raison_sociale':nomb}),201)['id']
        tokenb=ok(api.post(f'/api/societes/switcher/{sb}'))['access_token']
        api.headers['Authorization']='Bearer '+tokenb
        pb=employe(api,'Bénéficiaire B fictif483');_,db=mouvement(api,333);affecter(api,pb,db)
        avant_a=originaux(application,soca['id']);avant_b=originaux(application,sb);avant_reg=registre(application)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
                errors,server=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
                zone=ouvrir(page,application)
                expect(zone.get_by_role('table',name='Soldes des avances')).to_contain_text('Bénéficiaire A fictif483')
                row=zone.get_by_role('table',name='Mouvements des avances').get_by_role('row').filter(has_text=f'Ligne {libre}')
                row.get_by_role('button',name='Affecter',exact=True).click()
                form=zone.get_by_role('form',name='Affecter un mouvement')
                form.get_by_label('Salarié bénéficiaire').select_option(str(pa))
                form.get_by_label('Motif du rattachement').fill('Formulaire A non enregistré fictif483')
                page.get_by_role('button',name=soca['raison_sociale'],exact=True).click()
                with page.expect_navigation(wait_until='domcontentloaded'):
                    page.get_by_role('button',name=re.compile(re.escape(nomb)+'$')).click()
                zone=ouvrir(page,application)
                expect(zone.get_by_role('table',name='Soldes des avances')).to_contain_text('Bénéficiaire B fictif483')
                expect(zone.get_by_role('table',name='Soldes des avances')).to_contain_text('333,00 MAD')
                expect(zone.get_by_text('Bénéficiaire A fictif483',exact=True)).to_have_count(0)
                expect(zone.get_by_role('form')).to_have_count(0)
                codes=page.evaluate('''async ({url,p,ligne,a}) => {
                    const headers={Authorization:'Bearer '+localStorage.getItem('hisabpro_token'),'Content-Type':'application/json'};
                    const x=await fetch(url+'/api/employes/avances',{method:'POST',headers,body:JSON.stringify({employe_id:p,ligne_id:ligne,motif:'Refus société fictif'})});
                    const y=await fetch(url+'/api/employes/avances/'+a+'/annuler',{method:'POST',headers,body:JSON.stringify({motif:'Refus société fictif'})});
                    return [x.status,y.status];
                }''',{'url':application['api_url'],'p':pa,'ligne':libre,'a':aa})
                assert codes==[404,404]
                page.get_by_role('button',name=nomb,exact=True).click()
                with page.expect_navigation(wait_until='domcontentloaded'):
                    page.get_by_role('button',name=re.compile(re.escape(soca['raison_sociale'])+'$')).click()
                zone=ouvrir(page,application)
                expect(zone.get_by_role('table',name='Soldes des avances')).to_contain_text('111,00 MAD')
                expect(zone.get_by_text('1 mouvement(s) non affecté(s)',exact=False)).to_be_visible()
                expect(zone.get_by_role('form')).to_have_count(0)
                assert 'Formulaire A non enregistré fictif483' not in zone.inner_text()
                assert not errors and not server,(errors,server)
            finally:browser.close()
        assert originaux(application,soca['id'])==avant_a and originaux(application,sb)==avant_b
        assert registre(application)==avant_reg
