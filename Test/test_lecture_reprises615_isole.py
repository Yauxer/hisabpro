from contextlib import closing
from uuid import uuid4
import httpx
import pytest
from playwright.sync_api import sync_playwright,expect
from test_reprises_provisions615_isole import (
    application,application099,application098,application097,application093,application092,
    application091,application090,application089,application087,migration,dotation,creer,demande,PATH)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_e2e_administration_isole import connexion,observer
from test_e2e_reprises_provisions615_isole import ouvrir
from browser_support import chromium_executable


@pytest.mark.parametrize('largeur',[1440,390])
def test_615_lecture_seule_suivi_sans_commandes_et_refus403(application,largeur,tmp_path):
    with closing(client(application)[0]) as api:
        a=dotation(api);s=creer(api,a['id']);r=s['reprises'][0]
        email='lecture615-ui-'+uuid4().hex[:8]+'@example.com';password='LectureFictive615!'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecteur fictif615','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
                erreurs,serveur=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                region=ouvrir(page,application,a['id'])
                expect(region).to_contain_text('600,00 MAD')
                expect(region).to_contain_text('Reprise à valider')
                expect(region.get_by_role('button',name='Vérifier la reprise',exact=True)).to_have_count(0)
                expect(region.get_by_role('button',name=f"Annuler la reprise {r['id']}",exact=True)).to_have_count(0)
                avant=donnees_metier(application)
                with page.expect_response(lambda rep:rep.request.method=='GET' and PATH in rep.url):
                    region.get_by_role('button',name='Actualiser les provisions',exact=True).click()
                expect(region).to_contain_text('600,00 MAD')
                assert donnees_metier(application)==avant
                with httpx.Client(base_url=application['api_url']) as lecteur:
                    token=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
                    lecteur.headers['Authorization']='Bearer '+token
                    assert lecteur.post(f"{PATH}/{a['id']}/{r['id']}/annuler",json={'date':'2026-02-02','motif':'Interdit'}).status_code==403
                    assert lecteur.post(f"{PATH}/{a['id']}/apercu",json=demande()).status_code==200
                assert donnees_metier(application)==avant
                page.screenshot(path=str(tmp_path/f'reprises615_lecture_{largeur}.png'),full_page=True)
                assert not erreurs and not serveur,(erreurs,serveur)
            finally:browser.close()
