"""Icônes locales décoratives : noms accessibles et glyphes réels, PG nonce."""
import re
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def photographie(application, sid):
    with Session(application['engine']) as db:
        return tuple(db.query(modele).filter_by(societe_id=sid).count() for modele in (
            models.Article, models.Ecriture, models.MouvementStock, models.InventaireStock))


@pytest.mark.parametrize('largeur', [1365, 390])
def test_icones_locales_visibles_et_boutons_noms_accessibles_exacts(application, largeur):
    cible = application['cluster']
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    suffix = uuid.uuid4().hex[:8]
    email, password = 'icones-' + suffix + '@example.com', 'IconesFictives2026!'
    with httpx.Client(base_url=application['api_url']) as api:
        inscription = api.post('/api/auth/register', json={'nom': 'Icônes fictives', 'email': email,
            'password': password, 'raison_sociale': 'Icônes ' + suffix})
        assert inscription.status_code == 200, inscription.text
        api.headers['Authorization'] = 'Bearer ' + inscription.json()['access_token']
        sid = api.get('/api/societe/moi').json()['id']
        avant = photographie(application, sid)
        assert avant == (0, 0, 0, 0)
        executable = chromium_executable()
        if not executable:
            pytest.skip('Edge/Chromium requis')
        p = pytest.importorskip('playwright.sync_api')
        with p.sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=executable, headless=True)
            page = browser.new_page(viewport={'width': largeur, 'height': 1000})
            page.set_default_timeout(20000)
            errors, server_errors = observer(page, application['api_url'])
            ressources_erreurs = []
            page.on('response', lambda r: ressources_erreurs.append((r.url, r.status))
                if '/vendor/' in r.url and r.status >= 400 else None)
            try:
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/commercial')
                p.expect(page.get_by_role('button', name='Achat', exact=True)).to_have_count(1)
                p.expect(page.get_by_role('button', name='Vente', exact=True)).to_have_count(1)
                p.expect(page.get_by_role('button', name='Bons de commande', exact=True)).to_have_count(1)
                page.evaluate('() => document.fonts.ready')
                icones = page.evaluate('''() => [...document.querySelectorAll('button')]
                    .filter(b=>['Achat','Vente'].includes(b.innerText)).map(b=>{
                      const i=b.querySelector('i'), s=getComputedStyle(i,'::before'),r=i.getBoundingClientRect();
                      return {text:b.innerText,content:s.content,font:s.fontFamily,
                        visible:s.visibility,display:s.display,width:r.width,height:r.height,
                        loaded:document.fonts.check('14px tabler-icons')};})''')
                assert {i['text'] for i in icones} == {'Achat', 'Vente'}
                glyphes = {'Achat': '\uea13', 'Vente': '\uea24'}
                for i in icones:
                    assert glyphes[i['text']] in i['content'] and ' / ""' in i['content'], i
                    assert i['font'] == 'tabler-icons' and i['loaded'] and i['visible'] == 'visible', i
                    assert 0 < i['width'] <= 30 and 0 < i['height'] <= 30, i
                    assert i['display'] != 'none'
                arbre = page.locator('body').aria_snapshot()
                assert not re.search(r'button[^\n]*[\ue000-\uf8ff]', arbre), arbre
                page.get_by_role('button', name='Achat', exact=True).click()
                p.expect(page.get_by_role('button', name='Bons de réception', exact=True)).to_have_count(1)
                page.get_by_role('button', name='Vente', exact=True).click()
                p.expect(page.get_by_role('button', name='Nouveau devis', exact=True)).to_have_count(1)
                page.goto(application['web_url'] + '/factures')
                p.expect(page.get_by_role('button', name='Nouvelle facture', exact=True)).to_have_count(1)
                assert photographie(application, sid) == avant
                assert not errors and not server_errors and not ressources_erreurs, (errors, server_errors, ressources_erreurs)
            except Exception:
                print('Icônes UI:', page.url, page.locator('body').inner_text()[:7000])
                print('Arbre accessible:', page.locator('body').aria_snapshot())
                raise
            finally:
                browser.close()
