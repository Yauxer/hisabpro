from contextlib import closing
from decimal import Decimal
import pytest
from playwright.sync_api import sync_playwright,expect
from sqlalchemy import text
from test_reprises_provisions615_isole import (
    application,application099,application098,application097,application093,application092,
    application091,application090,application089,application087,migration,dotation,PATH)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion,observer
from test_e2e_annee_connectee_isole import valider_brouillons_ui
from test_e2e_prorata_inventaire_isole import photo
from browser_support import chromium_executable


def ouvrir(page,app,aid):
    page.goto(app['web_url']+'/cloture')
    page.get_by_text('Reprises partielles de provisions',exact=True).click()
    region=page.get_by_role('region',name='Reprises partielles de provisions',exact=True)
    expect(region.get_by_label('Dotation source',exact=True).locator(f'option[value="{aid}"]')).to_have_count(1)
    region.get_by_label('Dotation source',exact=True).select_option(str(aid))
    return region


@pytest.mark.parametrize('largeur',[1440,390])
def test_615_reprise_ui_partielle_validation_annulation_et_etats(application,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        a=dotation(api);source=photo(application,[a['ecriture_id']])
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            page.add_init_script("Object.defineProperty(globalThis.crypto,'randomUUID',{value:undefined})")
            page.on('dialog',lambda d:d.accept());erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            region=ouvrir(page,application,a['id'])
            expect(region).to_contain_text('Disponible dans le registre lié')
            region.get_by_label('Date de reprise',exact=True).fill('2026-02-01')
            region.get_by_label('Montant de reprise (MAD)',exact=True).fill('400')
            region.get_by_label('Justification de la reprise',exact=True).fill('Risque fictif diminué615')
            region.get_by_label('Référence de pièce (facultative)',exact=True).fill('JUSTIFICATIF-FICTIF615')
            region.get_by_label('Date de pièce (facultative)',exact=True).fill('2026-02-01')
            with page.expect_response(lambda r:r.request.method=='POST' and f"{PATH}/{a['id']}/apercu" in r.url) as rep:
                region.get_by_role('button',name='Vérifier la reprise',exact=True).click()
            assert rep.value.status==200,rep.value.text()
            expect(region.get_by_text('Compte 1518',exact=False)).to_be_visible()
            creer=region.get_by_role('button',name='Créer le brouillon de reprise',exact=True)
            expect(creer).to_be_disabled()
            region.get_by_label('J’ai vérifié les mouvements du compte et les justificatifs de la reprise.',exact=True).check()
            with page.expect_response(lambda r:r.request.method=='POST' and r.url.endswith(f"{PATH}/{a['id']}")) as rep:
                creer.click()
            assert rep.value.status==200,rep.value.text()
            r=rep.value.json()['reprises'][0]
            expect(region).to_contain_text('Brouillon de reprise créé')
            expect(region.locator('dl')).to_contain_text('600,00 MAD')
            valider_brouillons_ui(page,application,1)
            region=ouvrir(page,application,a['id'])
            expect(region).to_contain_text('Reprise validée')
            region.get_by_role('button',name=f"Annuler la reprise {r['id']}",exact=True).click()
            ann=region.get_by_role('form',name='Annulation de reprise',exact=True)
            ann.get_by_label('Date d’annulation',exact=True).fill('2026-02-02')
            ann.get_by_label('Motif d’annulation',exact=True).fill('Justification fictive corrigée615')
            with page.expect_response(lambda r:r.request.method=='POST' and r.url.endswith('/annuler')) as rep:
                ann.get_by_role('button',name='Créer l’inverse de reprise',exact=True).click()
            assert rep.value.status==200,rep.value.text()
            inv=rep.value.json()['reprises'][0]['inverse_id']
            expect(region).to_contain_text('Capacité maintenue jusqu’à validation des deux pièces.')
            valider_brouillons_ui(page,application,1)
            region=ouvrir(page,application,a['id'])
            expect(region).to_contain_text('Capacité libérée.')
            expect(region.locator('dl')).to_contain_text('1.000,00 MAD')
            assert photo(application,[a['ecriture_id']])==source
            # Pièces réelles exactes ; l'original et l'inverse se compensent en 2026.
            with application['engine'].connect() as db:
                ls=db.execute(text('SELECT compte,sum(debit-credit) solde FROM lignes_ecriture WHERE ecriture_id IN (:a,:b) GROUP BY compte'),{'a':r['ecriture_id'],'b':inv}).all()
                assert all(x.solde==Decimal(0) for x in ls)
            fec=api.get('/api/fec/export',params={'exercice':2026});assert fec.status_code==200,fec.text
            assert '7195' in fec.content.decode('utf-8-sig') and '1518' in fec.content.decode('utf-8-sig')
            etats=ok(api.get('/api/etats/liasse/2026'))['etats']
            assert etats['bilan']['equilibre']
            assert Decimal(str(etats['cpc']['resultat_net']))==0
            assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1')
            page.screenshot(path=str(tmp_path/f'reprises615_{largeur}.png'),full_page=True)
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()
