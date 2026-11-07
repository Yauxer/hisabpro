"""Habilitations réelles : masque, lecture seule, révocation et purge des détails."""
from contextlib import closing
import json
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, expect
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import champ
from navigation823_support import navigations_completes823
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_personnel_habilitations873_isole import (
    application, application093, application092, application091, application090,
    application089, application087, migration, employee, role_client, grant, activer,
    originaux, P, IDENTITE, REMUNERATION)


@pytest.mark.parametrize('largeur',[1440,390])
def test_873_protection_personnel_et_revocation_dans_edge(application,largeur,tmp_path,navigations_completes823):
    preuve={'largeur':largeur,'erreur':None,'donnees_reelles':False}
    cible=Path(__file__).resolve().parents[1]/f'.codex-tests/personnel873_edge_{largeur}_preuve.json'
    try:
        with closing(client(application)[0]) as api:
            e=employee(api);sid=ok(api.get('/api/auth/me'))['societe_id'];avant=originaux(application,sid)
            lecteur,u,email,secret=role_client(application,api);lecteur.close()
            grant(api,u['id'],IDENTITE);activer(api)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    page=browser.new_page(viewport={'width':largeur,'height':900});page.set_default_timeout(15000)
                    errors,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,secret)
                    page.goto(application['web_url']+'/cnss');expect(page.get_by_text('Personnel protégé',exact=False)).to_be_visible()
                    expect(page.get_by_role('button',name='Ajouter un salarié',exact=True)).to_have_count(0)
                    row=page.locator('tbody tr').filter(has_text=e['nom']);expect(row.get_by_text('Masqué',exact=True)).to_have_count(2)
                    row.get_by_role('button',name='Consulter',exact=False).click()
                    expect(champ(page,'Salaire brut mensuel')).to_have_value('');expect(champ(page,'Salaire brut mensuel')).to_be_disabled()
                    expect(champ(page,'Numéro CNSS')).to_have_value('')
                    page.get_by_role('button',name='Fermer la fiche',exact=True).click()
                    h=grant(api,u['id'],REMUNERATION)
                    page.get_by_role('button',name='Actualiser',exact=True).click()
                    expect(row.get_by_text('Masqué',exact=True)).to_have_count(1)
                    row.get_by_role('button',name='Consulter',exact=False).click()
                    expect(champ(page,'Salaire brut mensuel')).to_have_value('10000')
                    ok(api.post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Retrait pendant consultation fictive873'}))
                    page.get_by_role('button',name='Actualiser',exact=True).click()
                    expect(row.get_by_text('Masqué',exact=True)).to_have_count(2)
                    # Un détail local ouvert avant révocation ne doit pas retenir le salaire.
                    expect(page.get_by_role('button',name='Fermer la fiche',exact=True)).to_have_count(0)
                    row.get_by_role('button',name='Consulter',exact=False).click()
                    expect(champ(page,'Salaire brut mensuel')).to_have_value('')
                    assert not page.locator('input').evaluate_all("els=>els.some(e=>e.value==='10000')")
                    assert not errors and not serveur and originaux(application,sid)==avant
                    page.screenshot(path=str(cible.with_suffix('.png')),full_page=True)
                    preuve.update(masque_serveur_et_interface=True,lecture_seule=True,revocation_sans_reconnexion=True,
                                  detail_ouvert_purge=True,donnees_et_journal_conserves=True)
                finally:browser.close()
    except BaseException as exc:
        preuve['erreur']=repr(exc)
        raise
    finally:cible.write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
