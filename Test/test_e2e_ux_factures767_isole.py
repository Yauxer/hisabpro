"""Filtres et état vide Factures : Edge -> vraie API -> PG temporaire nonce."""
from datetime import date
from pathlib import Path
import json
from uuid import uuid4

import pytest
from playwright.sync_api import sync_playwright, expect
from browser_support import chromium_executable
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import connexion, observer
from test_ras_lecture_conservation import client
from diagnostic_lecture_factures_historiques import photographie

ROOT=Path(__file__).resolve().parents[1]
RECHERCHE='Rechercher une facture par numéro ou tiers'


def ok(r,status=200):
    assert r.status_code==status,r.text
    return r.json()


def table_factures(page):
    return page.locator('table').filter(has=page.get_by_role('columnheader',name='N° Facture',exact=True))


def peupler(api):
    annee=date.today().year
    client_=ok(api.post('/api/tiers',json={'nom':'Client UX fictif767','type':'client'}),201)
    fournisseur=ok(api.post('/api/tiers',json={'nom':'Fournisseur UX fictif767','type':'fournisseur'}),201)
    for sens,tiers,jour,pu in [('vente',client_,'01-10',100),('vente',client_,'02-20',200),('achat',fournisseur,'03-15',80)]:
        ok(api.post('/api/factures',json={'type':sens,'date':f'{annee}-{jour}','tiers':tiers['nom'],
            'tiers_id':tiers['id'],'reference':f'PIECE-FICTIVE767-{jour}',
            'lignes':[{'description':'Service fictif UX767','quantite':1,'prix_unitaire':pu,'tva':20}]}),201)


@pytest.mark.parametrize('largeur',[1440,390])
def test_filtres_combines_retour_liste_et_focus_sans_modifier_les_donnees(application,largeur):
    api,email,password=client(application)
    try:
        peupler(api);avant=photographie(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1100});page.set_default_timeout(15000)
                errors,server_errors=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/factures')
                tableau=table_factures(page);expect(tableau.locator('tbody tr')).to_have_count(3)
                mutations=[];page.on('request',lambda r:mutations.append(r.url) if r.method in ('POST','PATCH','PUT','DELETE') and '/api/' in r.url else None)
                search=page.get_by_role('searchbox',name=RECHERCHE,exact=True)
                search.fill('UX fictif767')
                page.get_by_role('button',name='Ventes',exact=True).focus();page.keyboard.press('Enter')
                expect(page.get_by_role('button',name='Ventes',exact=True)).to_have_attribute('aria-pressed','true')
                expect(tableau.locator('tbody tr')).to_have_count(2)
                du=page.get_by_label('Date de début des factures et indicateurs',exact=True)
                au=page.get_by_label('Date de fin des factures et indicateurs',exact=True)
                du.fill(f'{date.today().year}-02-01');au.fill(f'{date.today().year}-02-28')
                expect(tableau.locator('tbody tr')).to_have_count(1)
                page.get_by_role('button',name='Payées',exact=True).click()
                expect(page.get_by_text('Aucune facture trouvée',exact=True)).to_be_visible()
                expect(page.get_by_text('Aucune facture ne correspond aux critères sélectionnés.',exact=False)).to_be_visible()
                expect(tableau).to_have_count(0)
                page.get_by_role('button',name='Effacer la recherche',exact=True).click()
                expect(search).to_have_value('');expect(search).to_be_focused()
                expect(page.get_by_role('button',name='Ventes',exact=True)).to_have_attribute('aria-pressed','true')
                expect(page.get_by_role('button',name='Payées',exact=True)).to_have_attribute('aria-pressed','true')
                expect(du).to_have_value(f'{date.today().year}-02-01')
                search.fill('introuvable-767')
                retour=page.get_by_role('button',name='Afficher toutes les factures de cet exercice',exact=True)
                retour.scroll_into_view_if_needed();box=retour.bounding_box()
                assert box and box['x']>=0 and box['x']+box['width']<=largeur
                carte=page.get_by_text('Aucune facture trouvée',exact=True).locator('..').locator('..')
                assert carte.evaluate('(e)=>e.scrollTop===0 && e.scrollHeight<=e.clientHeight+1')
                page.screenshot(path=str(ROOT/f'.codex-tests/ux767_vide_{largeur}.png'),full_page=True)
                page.get_by_role('button',name='Afficher toutes les factures de cet exercice',exact=True).click()
                expect(tableau.locator('tbody tr')).to_have_count(3)
                expect(search).to_have_value('');expect(search).to_be_focused()
                expect(du).to_have_value('');expect(au).to_have_value('')
                for label in ['Tous','Tous statuts']:expect(page.get_by_role('button',name=label,exact=True)).to_have_attribute('aria-pressed','true')
                expect(page.get_by_role('button',name='Réinitialiser les filtres',exact=True)).to_have_count(0)
                # Le même retour est disponible avant même d'arriver à une liste vide.
                page.get_by_role('button',name='Achats',exact=True).click()
                expect(tableau.locator('tbody tr')).to_have_count(1)
                page.get_by_role('button',name='Réinitialiser les filtres',exact=True).click()
                expect(tableau.locator('tbody tr')).to_have_count(3)
                expect(page.get_by_role('status').filter(has_text='3 factures')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                assert not mutations and not errors and not server_errors,(mutations,errors,server_errors)
                page.screenshot(path=str(ROOT/f'.codex-tests/ux767_liste_{largeur}.png'),full_page=True)
            finally:browser.close()
        assert photographie(application)==avant
        (ROOT/f'.codex-tests/ux767_{largeur}_preuve.json').write_text(json.dumps({'largeur':largeur,'filtres_combines_et_reinitialisation':True,'focus_et_clavier':True,'mutations_api':0,'donnees_comptables_inchangees':True}),encoding='utf8')
    finally:api.close()


@pytest.mark.parametrize('role,largeur',[('admin',1440),('lecture',390)])
def test_vrai_exercice_vide_action_adaptee_aux_droits(application,role,largeur):
    api,email,password=client(application)
    try:
        if role=='lecture':
            email=f'lecture767-{uuid4().hex[:8]}@example.com';password='Lecture767!Local'
            ok(api.post('/api/utilisateurs',json={'nom':'Lecture UX fictive','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        avant=photographie(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1100});page.set_default_timeout(15000)
                errors,server_errors=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/factures')
                expect(page.get_by_text('Aucune facture enregistrée pour cet exercice.',exact=True)).to_be_visible()
                bouton=page.get_by_role('button',name='Créer une première facture',exact=True)
                if role=='admin':
                    bouton.click();expect(page.get_by_role('dialog')).to_be_visible();page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0)
                else:
                    expect(bouton).to_have_count(0);expect(page.get_by_role('button',name='Nouvelle facture',exact=True)).to_be_disabled()
                search=page.get_by_role('searchbox',name=RECHERCHE,exact=True);search.fill('sans résultat')
                page.get_by_role('button',name='Réinitialiser les filtres',exact=True).click()
                expect(search).to_have_value('');expect(search).to_be_focused()
                expect(page.get_by_text('Aucune facture enregistrée pour cet exercice.',exact=True)).to_be_visible()
                assert not errors and not server_errors,(errors,server_errors)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            finally:browser.close()
        assert photographie(application)==avant
    finally:api.close()
