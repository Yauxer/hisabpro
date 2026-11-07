"""Relation déclarée, API/Edge réels ; PostgreSQL natif nonce sous LOGIN limité."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from pathlib import Path
import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_reprises_provisions615_isole import (
    application as application100,application099,application098,application097,application093,
    application092,application091,application090,application089,application087,migration)
from test_avances_salaries_isole import appliquer
from recette_restauration_consolidee_084 import empreintes_tables
from test_restauration_runtime_acl_089 import catalogue_acl
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_journal_cloture_concurrente_isole import moteur
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable

PATH='/api/societes/liaisons'


@pytest.fixture(scope='module')
def application(application100):
    app=application100
    with closing(client(app)[0]) as api:assert api.get(PATH).status_code==503
    avant=empreintes_tables(app['engine']);acl=catalogue_acl(app['engine'])
    appliquer(app,'101_societes_liees.sql')
    apres=empreintes_tables(app['engine']);droits=catalogue_acl(app['engine'])
    assert all(apres[k]==v for k,v in avant.items())
    assert all(all(v in droits[k] for v in vs) for k,vs in acl.items())
    appliquer(app,'101_societes_liees.sql')
    assert empreintes_tables(app['engine'])==apres and catalogue_acl(app['engine'])==droits
    yield app
    # Rejeu sur les nouvelles lignes non vides, pas uniquement sur installation vierge.
    avant=empreintes_tables(app['engine']);droits=catalogue_acl(app['engine'])
    appliquer(app,'101_societes_liees.sql')
    assert empreintes_tables(app['engine'])==avant and catalogue_acl(app['engine'])==droits


def paire(app):
    a,email,password=client(app)
    sid=ok(a.get('/api/auth/me'))['societe_id'];uid=ok(a.get('/api/auth/me'))['id']
    bid=ok(a.post('/api/societes/nouvelle',json={'raison_sociale':'Acheteur fictif633 '+uuid4().hex[:8]}),201)['id']
    b=httpx.Client(base_url=app['api_url'],headers={'Authorization':'Bearer '+ok(a.post(f'/api/societes/switcher/{bid}'))['access_token']})
    c=ok(a.post('/api/tiers',json={'type':'client','nom':'Acheteur représenté fictif633'}),201)['id']
    f=ok(b.post('/api/tiers',json={'type':'fournisseur','nom':'Vendeur représenté fictif633'}),201)['id']
    data={'acheteur_id':bid,'client_id':c,'fournisseur_id':f,'cle':str(uuid4()),'justification':'Relation commerciale fictive expressément vérifiée','association_verifiee':True}
    return a,b,data,{'sid':sid,'bid':bid,'uid':uid,'email':email,'password':password}


def test_633_creation_rejeu_retrait_et_recreation(application):
    a,b,d,ids=paire(application)
    try:
        avant=donnees_metier(application)
        opts=ok(a.get(f'{PATH}/options/{ids["bid"]}'))
        assert opts['clients'][0]['id']==d['client_id'] and opts['fournisseurs'][0]['id']==d['fournisseur_id']
        assert donnees_metier(application)==avant
        l=ok(a.post(PATH,json=d),201);assert l['active'] and l['vendeur_id']==ids['sid']
        assert ok(a.post(PATH,json=d),201)==l
        assert ok(a.get(PATH))==ok(b.get(PATH))==[l]
        assert a.post(PATH,json={**d,'justification':'Autre'}).status_code==409
        assert a.post(PATH,json={**d,'cle':str(uuid4())}).status_code==409
        before=donnees_metier(application)
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT count(*) FROM factures WHERE societe_id IN (:s,:b)'),{'s':ids['sid'],'b':ids['bid']})==0
            assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id IN (:s,:b)'),{'s':ids['sid'],'b':ids['bid']})==0
        assert donnees_metier(application)==before
        r=ok(b.post(f'{PATH}/{l["id"]}/retirer',json={'motif':'Fin de relation fictive'}))
        assert not r['active']
        assert ok(b.post(f'{PATH}/{l["id"]}/retirer',json={'motif':'Fin de relation fictive'}))==r
        assert b.post(f'{PATH}/{l["id"]}/retirer',json={'motif':'Autre'}).status_code==409
        assert not ok(a.get(PATH))[0]['active']
        l2=ok(a.post(PATH,json={**d,'cle':str(uuid4())}),201)
        assert l2['active'] and l2['id']!=l['id']
        assert ok(a.post(PATH,json=d),201)['active'] is False
    finally:a.close();b.close()


def test_633_consultation_seule_edge_sans_mutation(application):
    from playwright.sync_api import sync_playwright,expect
    a,b,d,ids=paire(application)
    try:
        l=ok(a.post(PATH,json=d),201)
        with application['engine'].begin() as db:
            db.execute(text("UPDATE utilisateurs SET role='lecture' WHERE id=:id"),{'id':ids['uid']})
        avant=donnees_metier(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            page=browser.new_page(viewport={'width':390,'height':1000})
            errors,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],ids['email'],ids['password'])
            page.goto(application['web_url']+'/parametres');page.get_by_role('button',name='Sociétés liées',exact=True).click()
            panel=page.get_by_role('region',name='Sociétés liées')
            expect(panel.get_by_text(l['vendeur']+' → '+l['acheteur'],exact=True)).to_be_visible()
            assert panel.locator('form').count()==0
            assert panel.get_by_role('button',name='Enregistrer la liaison').count()==0
            assert a.post(PATH,json=d).status_code==403
            assert a.post(f'{PATH}/{l["id"]}/retirer',json={'motif':'Refus lecteur'}).status_code==403
            assert not errors and not serveur,(errors,serveur)
            browser.close()
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


@pytest.mark.parametrize('changement',[{'acheteur_id':True},{'client_id':True},{'justification':'  '},{'association_verifiee':False},{'vendeur_id':1}])
def test_633_entrees_refusees_sans_mutation(application,changement):
    a,b,d,ids=paire(application)
    try:
        avant=donnees_metier(application)
        assert a.post(PATH,json={**d,**changement}).status_code==422
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_633_tiers_etranger_type_ice_et_soi_refuses(application):
    a,b,d,ids=paire(application)
    try:
        avant=donnees_metier(application)
        for c in ({'client_id':d['fournisseur_id']},{'fournisseur_id':d['client_id']},{'acheteur_id':ids['sid']}):
            assert a.post(PATH,json={**d,**c}).status_code==422
            assert donnees_metier(application)==avant
        with application['engine'].begin() as db:
            db.execute(text("UPDATE tiers SET ice='111111111111111' WHERE id=:id"),{'id':d['client_id']})
            db.execute(text("UPDATE societes SET ice='222222222222222' WHERE id=:id"),{'id':ids['bid']})
        avant=donnees_metier(application)
        assert a.post(PATH,json=d).status_code==422
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_633_droits_relus_retrait_unilateral_et_pas_de_fuite(application):
    a,b,d,ids=paire(application);x,_,_=client(application)
    try:
        l=ok(a.post(PATH,json=d),201)
        assert ok(x.get(PATH))==[]
        assert x.get(f'{PATH}/options/{ids["bid"]}').status_code==403
        assert x.post(f'{PATH}/{l["id"]}/retirer',json={'motif':'Intrusion'}).status_code==404
        with application['engine'].begin() as db:
            db.execute(text("UPDATE utilisateurs_societes SET role='lecture' WHERE utilisateur_id=:u AND societe_id=:s"),{'u':ids['uid'],'s':ids['bid']})
        avant=donnees_metier(application)
        assert a.get(f'{PATH}/options/{ids["bid"]}').status_code==403
        assert a.post(PATH,json={**d,'cle':str(uuid4())}).status_code==403
        assert b.post(PATH,json=d).status_code==403
        assert donnees_metier(application)==avant
        with application['engine'].begin() as db:
            db.execute(text('UPDATE utilisateurs_societes SET actif=false WHERE utilisateur_id=:u AND societe_id=:s'),{'u':ids['uid'],'s':ids['bid']})
        assert ok(a.get(PATH))==[]
        r=ok(a.post(f'{PATH}/{l["id"]}/retirer',json={'motif':'Consentement retiré'}))
        assert set(r)=={'id','active','motif_retrait'} and not r['active']
    finally:a.close();b.close();x.close()


def test_633_creation_concurrente_et_registres_immutables(application):
    a,b,d,ids=paire(application)
    try:
        with ThreadPoolExecutor(2) as p:
            rs=list(p.map(lambda _:a.post(PATH,json=d),range(2)))
        ls=[ok(r,201) for r in rs];assert ls[0]==ls[1]
        l=ls[0];e=moteur(application)
        try:
            for sql in ('UPDATE societes_liees SET justification=justification WHERE id=:id','DELETE FROM societes_liees WHERE id=:id','TRUNCATE societes_liees CASCADE'):
                with pytest.raises(DBAPIError):
                    with e.begin() as db:db.execute(text(sql),{'id':l['id']})
            # Le propriétaire est lui aussi empêché de réécrire l'historique.
            with pytest.raises(DBAPIError):
                with application['engine'].begin() as db:db.execute(text('UPDATE societes_liees SET justification=justification WHERE id=:id'),{'id':l['id']})
            with pytest.raises(DBAPIError):
                with e.begin() as db:db.execute(text('INSERT INTO societes_liees(vendeur_id,acheteur_id,client_id,fournisseur_id,cle,justification,created_by) VALUES(:v,:a,:c,:f,CAST(:cle AS uuid),:j,:u)'),{'v':ids['bid'],'a':ids['sid'],'c':d['client_id'],'f':d['fournisseur_id'],'cle':str(uuid4()),'j':'Faux','u':ids['uid']})
        finally:e.dispose()
        assert ok(a.get(PATH))==[l]
    finally:a.close();b.close()


@pytest.mark.parametrize('largeur',[1440,390])
def test_633_parametres_liaison_creation_retrait_edge(application,largeur):
    from playwright.sync_api import sync_playwright,expect
    a,b,d,ids=paire(application)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            page=browser.new_page(viewport={'width':largeur,'height':1000});errors,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],ids['email'],ids['password'])
            page.goto(application['web_url']+'/parametres');page.get_by_role('button',name='Sociétés liées',exact=True).click()
            panel=page.get_by_role('region',name='Sociétés liées')
            panel.get_by_label('Société acheteuse',exact=True).select_option(str(ids['bid']))
            panel.get_by_label('Client chez le vendeur',exact=True).select_option(str(d['client_id']))
            panel.get_by_label('Fournisseur chez l’acheteur',exact=True).select_option(str(d['fournisseur_id']))
            panel.get_by_label('Justification de la liaison',exact=True).fill(d['justification'])
            panel.get_by_role('checkbox').check()
            with page.expect_response(lambda r:r.url.endswith(PATH) and r.request.method=='POST') as rep:
                panel.get_by_role('button',name='Enregistrer la liaison',exact=True).click()
            assert rep.value.status==201
            l=rep.value.json();expect(panel.get_by_text('Liaison enregistrée. Aucune facture ni écriture créée.',exact=True)).to_be_visible()
            panel.get_by_role('button',name=f'Retirer la liaison {l["id"]}',exact=True).click()
            panel.get_by_label('Motif du retrait',exact=True).fill('Retrait navigateur fictif633')
            panel.get_by_role('button',name='Confirmer le retrait',exact=True).click()
            expect(panel.get_by_text('Retirée : Retrait navigateur fictif633',exact=False)).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert not errors,errors
            assert not serveur,serveur
            browser.close()
    finally:a.close();b.close()
