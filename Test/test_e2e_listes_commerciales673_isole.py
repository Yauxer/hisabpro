"""Fin du périmètre commercial : vraies lectures, cycles et erreurs sur bac nonce."""
from contextlib import closing, contextmanager
from datetime import date
import re
import pytest
from sqlalchemy import text
from playwright.sync_api import sync_playwright, expect
from test_e2e_runtime_session_isole import application, application090, application089, application087, migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from test_permissions_tva_runtime_isole import donnees_metier
from test_restauration_runtime_acl_089 import catalogue_acl
from postgres_isole import verifier_cible_isolee
from browser_support import chromium_executable


LISTES = {
    'devis': ('Devis', 'devis', 'devis', 'Aucun devis'),
    'commandes': ('Bons de commande', 'bons-commande', 'bons_commande', 'Aucun bon de commande'),
    'livraisons': ('Bons de livraison', 'bons-livraison', 'bons_livraison', 'Aucun bon de livraison'),
    'factures': ('Factures', 'factures', 'factures', None),
    'receptions_client': ('Réception client', 'bons-livraison', 'bons_livraison', 'Aucun bon de livraison trouvé'),
}


def ouvrir(page, app, genre, sens='vente'):
    page.goto(app['web_url']+'/commercial')
    page.get_by_role('button', name='Achat' if sens == 'achat' else 'Vente', exact=True).click()
    page.get_by_role('button', name=LISTES[genre][0], exact=True).click()


def creer(api, genre, annee, ref, sens='vente'):
    ligne = {'description': 'Service fictif673', 'quantite': 1, 'prix_unitaire': 100, 'tva': 20,
             'quantite_prevue': 1, 'quantite_livree': 0}
    doc = ok(api.post('/api/'+LISTES[genre][1], json={
        'type': sens, 'date': f'{annee}-06-01', 'numero': ref,
        'tiers': 'TIERS FICTIF673 '+ref+' '+sens, 'lignes': [ligne],
    }), 201)
    # Une facture brouillon n'a volontairement aucun numéro définitif.
    # Repérer sa vraie identité de tiers unique sans modifier cette règle.
    doc['repere'] = doc['tiers'] if genre == 'factures' else doc['numero']
    return doc


@contextmanager
def refuser(app, table):
    assert table in {'devis','bons_commande','bons_livraison','factures'}
    c = app['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']) and app['role_sql']=='hisabpro'
    avant = catalogue_acl(app['engine'])
    with app['engine'].begin() as db:
        assert db.scalar(text("SELECT rolsuper FROM pg_roles WHERE rolname='hisabpro'")) is False
        db.execute(text(f'REVOKE SELECT ON {table} FROM hisabpro'))
    try:
        yield
    finally:
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        with app['engine'].begin() as db:db.execute(text(f'GRANT SELECT ON {table} TO hisabpro'))
        assert catalogue_acl(app['engine'])==avant


@pytest.mark.parametrize('sens,largeur', [('vente',1440),('achat',390)])
def test_673_factures_separees_par_cycle(application,sens,largeur):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        f = {s:creer(api,'factures',date.today().year,'FACTURE-FICTIVE673-'+s,s) for s in ('vente','achat')}
        assert len(ok(api.get('/api/factures',params={'exercice':date.today().year})))==2
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(10000)
            connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application)
            ouvrir(page,application,'factures',sens)
            expect(page.locator('tbody tr')).to_have_count(1,timeout=4000)
            expect(page.get_by_text(f[sens]['repere'],exact=True)).to_be_visible()
            autre='achat' if sens=='vente' else 'vente'
            expect(page.get_by_text(f[autre]['repere'],exact=True)).to_have_count(0)
            assert donnees_metier(application)==avant
        finally:browser.close()


@pytest.mark.parametrize('genre',LISTES)
@pytest.mark.parametrize('largeur',[1440,390])
def test_673_refus_natif_et_reprise(application,genre,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        doc=creer(api,genre,date.today().year,'FICTIF673-'+genre)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(10000)
            connexion(page,application['web_url'],email,password);page.wait_for_load_state('networkidle')
            avant=donnees_metier(application)
            endpoint='/api/'+LISTES[genre][1]+'?'
            with refuser(application,LISTES[genre][2]):
                assert api.get('/api/'+LISTES[genre][1],params={'exercice':date.today().year}).status_code==500
                with page.expect_request(lambda r:endpoint in r.url):ouvrir(page,application,genre)
                expect(page.get_by_role('alert').filter(has_text='Chargement impossible')).to_be_visible(timeout=4000)
                vide=LISTES[genre][3] or f'Aucune facture pour {date.today().year}'
                expect(page.get_by_text(vide,exact=True)).to_have_count(0)
                with page.expect_request(lambda r:endpoint in r.url):
                    page.get_by_role('button',name='Réessayer',exact=True).click()
                expect(page.get_by_role('alert')).to_be_visible()
                page.screenshot(path=str(tmp_path/f'erreur673_{genre}_{largeur}.png'),full_page=True)
            with page.expect_response(lambda r:endpoint in r.url) as retour:
                page.get_by_role('button',name='Réessayer',exact=True).click()
            assert retour.value.status==200
            expect(page.get_by_text(doc['repere'],exact=True)).to_be_visible()
            assert page.get_by_role('button',name='Actualiser la liste',exact=True).evaluate('''e =>
                [...e.parentElement.querySelectorAll('button,input')].every(n => {
                    const r=n.getBoundingClientRect();return r.left>=0 && r.right<=innerWidth
                })'''), 'Les commandes de la liste doivent rester visibles sur mobile.'
            page.screenshot(path=str(tmp_path/f'lecture673_{genre}_{largeur}.png'),full_page=True)
            assert donnees_metier(application)==avant
        finally:browser.close()


@pytest.mark.parametrize('genre',LISTES)
def test_673_vide_reel_relecture(application,genre):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();page.set_default_timeout(10000)
            connexion(page,application['web_url'],email,password)
            ouvrir(page,application,genre)
            vide=LISTES[genre][3] or f'Aucune facture pour {date.today().year}'
            expect(page.get_by_text(vide,exact=True)).to_be_visible()
            avant=donnees_metier(application)
            with page.expect_response(lambda r:'/api/'+LISTES[genre][1]+'?' in r.url) as retour:
                page.get_by_role('button',name='Actualiser la liste',exact=True).click()
            assert retour.value.status==200 and retour.value.json()==[]
            expect(page.get_by_text(vide,exact=True)).to_be_visible()
            expect(page.get_by_role('alert')).to_have_count(0)
            assert donnees_metier(application)==avant
        finally:browser.close()


@pytest.mark.parametrize('genre',LISTES)
def test_673_ancien_exercice_ignore(application,genre,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        an=date.today().year
        ok(api.post('/api/exercices',json={'annee':an-1,'date_debut':f'{an-1}-01-01','date_fin':f'{an-1}-12-31'}),201)
        vieux=creer(api,genre,an,'FICTIF673-GET-ANCIEN')
        cible=creer(api,genre,an-1,'FICTIF673-EXERCICE-CIBLE')
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':1000});page.set_default_timeout(10000)
            erreurs,serveurs=observer(page,application['api_url'])
            page.context.tracing.start(screenshots=True,snapshots=True,sources=True)
            connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application);retenues=[]
            def retenir(route):
                response=route.fetch();assert response.status==200
                retenues.append((route,response))
            page.route(re.compile(r'/api/'+LISTES[genre][1]+r'\?exercice='+str(an)),retenir,times=1)
            ouvrir(page,application,genre)
            for _ in range(100):
                if retenues:break
                page.wait_for_timeout(50)
            assert len(retenues)==1
            with page.expect_response(lambda r:f'/api/{LISTES[genre][1]}?exercice={an-1}' in r.url):
                page.locator('select').filter(has=page.locator(f'option[value="{an-1}"]')).first.select_option(str(an-1))
            expect(page.get_by_text(cible['repere'],exact=True)).to_be_visible()
            retenues[0][0].fulfill(response=retenues[0][1]);page.wait_for_load_state('networkidle')
            expect(page.get_by_text(vieux['repere'],exact=True)).to_have_count(0)
            expect(page.get_by_text(cible['repere'],exact=True)).to_be_visible()
            assert donnees_metier(application)==avant
            assert not erreurs and not serveurs,(erreurs,serveurs)
        finally:
            if 'page' in locals():
                try:
                    page.screenshot(path=str(tmp_path/f'contexte673_{genre}.png'),full_page=True)
                    page.context.tracing.stop(path=str(tmp_path/f'contexte673_{genre}.zip'))
                finally:browser.close()
            else:browser.close()


def test_673_factures_toutes_les_pages_et_cycles(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        achat=creer(api,'factures',date.today().year,'FICTIF673-ACHAT-PLUS-ANCIEN','achat')
        for i in range(101):creer(api,'factures',date.today().year,f'FICTIF673-VENTE-{i:03}')
        assert len(ok(api.get('/api/factures',params={'exercice':date.today().year})))==100
        assert len(ok(api.get('/api/factures',params={'exercice':date.today().year,'skip':100})))==2
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();page.set_default_timeout(15000)
            connexion(page,application['web_url'],email,password)
            avant=donnees_metier(application)
            ouvrir(page,application,'factures','vente')
            expect(page.locator('tbody tr')).to_have_count(101)
            expect(page.get_by_text('101 factures',exact=True)).to_be_visible()
            page.get_by_role('button',name='Achat',exact=True).click()
            page.get_by_role('button',name='Factures',exact=True).click()
            expect(page.locator('tbody tr')).to_have_count(1)
            expect(page.get_by_text(achat['repere'],exact=True)).to_be_visible()
            assert donnees_metier(application)==avant
        finally:browser.close()


def test_673_reception_client_factures_indisponibles_signalees(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        creer(api,'receptions_client',date.today().year,'FICTIF673-BL-DEPENDANCE')
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();page.set_default_timeout(10000)
            connexion(page,application['web_url'],email,password);page.wait_for_load_state('networkidle')
            avant=donnees_metier(application)
            with refuser(application,'factures'):
                ouvrir(page,application,'receptions_client')
                expect(page.get_by_role('alert').filter(has_text='Chargement impossible')).to_be_visible(timeout=4000)
                expect(page.get_by_text('Aucun bon de livraison trouvé',exact=True)).to_have_count(0)
            page.get_by_role('button',name='Réessayer',exact=True).click()
            expect(page.get_by_text('FICTIF673-BL-DEPENDANCE',exact=True)).to_be_visible()
            assert donnees_metier(application)==avant
        finally:browser.close()
