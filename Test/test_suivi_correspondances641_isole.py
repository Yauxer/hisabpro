"""Lecture groupée RO/RR, montants exacts, rôles/sociétés et vrais Edge."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date
from threading import Event
from uuid import uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from test_factures_liees635_isole import (
    application,application101,application100,application099,application098,application097,application093,
    application092,application091,application090,application089,application087,migration,vente,demande,chemin,PATH)
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_ras_lecture_conservation import client
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


def jeu(app):
    a,b,ids=vente(app)
    s=ok(a.post(chemin(ids),json=demande(a,ids)),201);ids['achat']=s['facture_achat_id'];ids['correspondance']=s['id']
    return a,b,ids


def url(ids):return f'{PATH}/{ids["liaison"]}/correspondances'


def payer(api,fid,montant=200,**kw):
    fs=ok(api.get('/api/factures',params={'exercice':date.today().year}));f=next(x for x in fs if x['id']==fid)
    return ok(api.post('/api/reglements',json={'facture_id':fid,'tiers':f['tiers'],'tiers_id':f['tiers_id'],'date':date.today().isoformat(),'montant':montant,'reference':'VIR-FICTIF641','mode':'virement','comptabiliser':False,**kw}),201)


def test_641_montants_distincts_actualises_retrait_et_aucune_mutation(application):
    a,b,ids=jeu(application)
    try:
        avant=donnees_metier(application);s=ok(a.get(url(ids)));assert s['total']==1 and s['page']==1
        for cote in ('vente','achat'):
            f=s['items'][0][cote]['finances'];assert (f['total_ttc'],f['solde_restant'],f['total_encaisse'],f['total_reglement_en_cours'])==('600.00','600.00','0.00','0.00')
        assert donnees_metier(application)==avant
        payer(a,ids['fid'])
        s=ok(a.get(url(ids)));assert s['items'][0]['vente']['finances']['solde_restant']=='400.00' and s['items'][0]['vente']['finances']['total_encaisse']=='200.00'
        assert s['items'][0]['achat']['finances']['solde_restant']=='600.00'
        assert ok(b.get(url(ids)))==s
        ok(b.post(f'/api/factures/{ids["achat"]}/valider'));payer(b,ids['achat'],600)
        s=ok(a.get(url(ids)));assert s['items'][0]['achat']['finances']['solde_restant']=='0.00'
        ok(a.post(f'{PATH}/{ids["liaison"]}/retirer',json={'motif':'Retrait suivi fictif641'}))
        avant=donnees_metier(application);s=ok(a.get(url(ids)));assert not s['active'] and s['total']==1
        assert donnees_metier(application)==avant
        assert a.get(url(ids),params={'page':0}).status_code==422
    finally:a.close();b.close()


def test_641_lecture_seule_du_suivi_edge_et_reponse_tardive_ecartee(application):
    from playwright.sync_api import sync_playwright,expect
    a,b,ids=jeu(application)
    try:
        with application['engine'].begin() as db:db.execute(text("UPDATE utilisateurs SET role='lecture' WHERE id=:id"),{'id':ids['uid']})
        avant=donnees_metier(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':390,'height':1000});errors,serveur=observer(page,application['api_url'])
                connexion(page,application['web_url'],ids['email'],ids['password'])
                page.goto(application['web_url']+'/parametres');page.get_by_role('button',name='Sociétés liées',exact=True).click()
                region=page.get_by_role('region',name='Sociétés liées',exact=True)
                page.locator('summary').filter(has_text=f'Factures de la liaison {ids["liaison"]}').click()
                panel=page.get_by_role('region',name=f'Factures de la liaison {ids["liaison"]}',exact=True)
                expect(panel).to_contain_text('Reste à régler 600,00 MAD')
                assert region.locator('form').count()==0
                token_a=page.evaluate("localStorage.getItem('hisabpro_token')")
                token_b=b.headers['Authorization'].split(' ',1)[1]
                def tardive(route):
                    reponse=route.fetch()  # Statut/corps de la vraie API conservés.
                    page.evaluate("t => localStorage.setItem('hisabpro_token', t)",token_b)
                    route.fulfill(response=reponse)
                page.route('**'+url(ids)+'?page=1',tardive,times=1)
                with page.expect_response(lambda r:url(ids) in r.url):panel.get_by_role('button',name='Actualiser les factures liées',exact=True).click()
                page.wait_for_timeout(250)
                expect(panel).not_to_contain_text('Reste à régler 600,00 MAD')
                assert panel.locator('article').count()==0
                page.evaluate("t => localStorage.setItem('hisabpro_token', t)",token_a)
                assert not errors and not serveur,(errors,serveur)
            finally:browser.close()
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_641_cheque_en_cours_non_assimile_a_encaissement(application):
    a,b,ids=jeu(application)
    try:
        payer(a,ids['fid'],600,mode='cheque',reference='CH-FICTIF641')
        f=ok(a.get(url(ids)))['items'][0]['vente']['finances']
        assert f['etat_solde']=='Solde couvert' and f['solde_restant']=='0.00'
        assert f['total_encaisse']=='0.00' and f['total_reglement_en_cours']=='600.00'
    finally:a.close();b.close()


def test_641_sous_centime_historique_signale_sans_arrondi_silencieux(application):
    a,b,ids=jeu(application)
    try:
        # Depuis642 la saisie est refusée ; reproduire une ancienne donnée sur
        # un règlement fictif non comptabilisé, sans désactiver de contrainte.
        r=payer(a,ids['fid'],10)
        with application['engine'].begin() as db:db.execute(text('UPDATE reglements SET montant=0.005 WHERE id=:id'),{'id':r['id']})
        avant=donnees_metier(application);s=ok(a.get(url(ids)))
        f=s['items'][0]['vente']['finances'];assert f['diagnostic'] and f['total_encaisse'] is None and f['solde_restant'] is None
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_641_pagination_descendante_sans_perte(application):
    a,b,ids=jeu(application)
    try:
        source=next(x for x in ok(a.get('/api/factures',params={'exercice':date.today().year})) if x['id']==ids['fid'])
        for i in range(10):
            f=ok(a.post('/api/factures',json={'type':'vente','date':date.today().isoformat(),'tiers':source['tiers'],'tiers_id':source['tiers_id'],'lignes':[{'article_id':ids['av'],'description':f'Facture pagination641-{i}','quantite':1,'prix_unitaire':10,'tva':20}]}),201)
            # Article non stockable pour les10autres ventes, pas de stock fictif infini.
            with application['engine'].begin() as db:db.execute(text('UPDATE articles SET is_stockable=false WHERE id=:id'),{'id':ids['av']})
            ok(a.post(f'/api/factures/{f["id"]}/valider'))
            v={**ids,'fid':f['id'],'corps':{'nature_tva_achat':'charge','tva_deductible_pct':'100','lignes':[{'source_ligne_id':f['lignes'][0]['id'],'article_id':ids['aa']}]}}
            ok(a.post(chemin(v),json=demande(a,v)),201)
        avant=donnees_metier(application);p1=ok(a.get(url(ids)));p2=ok(a.get(url(ids),params={'page':2}));p3=ok(a.get(url(ids),params={'page':3}))
        assert p1['total']==p2['total']==11 and len(p1['items'])==10 and len(p2['items'])==1 and p3['items']==[]
        xs=[x['id'] for x in p1['items']+p2['items']];assert xs==sorted(set(xs),reverse=True) and xs[-1]==ids['correspondance']
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_641_finances_invalides_diagnostic_pas_faux_zero(application):
    a,b,ids=jeu(application)
    try:
        # Prix non fini sur un brouillon du cluster fictif ; jamais modifier
        # une contrainte ou une pièce définitive pour construire la fixture.
        with application['engine'].begin() as db:db.execute(text("UPDATE lignes_facture SET prix_unitaire='Infinity'::double precision WHERE facture_id=:id"),{'id':ids['achat']})
        avant=donnees_metier(application);s=ok(a.get(url(ids)));f=s['items'][0]['achat']['finances']
        assert f['diagnostic'] and f['total_ttc'] is None and f['solde_restant'] is None
        assert s['items'][0]['vente']['finances']['total_ttc']=='600.00'
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_641_droits_relus_et_societe_etrangere_sans_fuite(application):
    a,b,ids=jeu(application);x,_,_=client(application)
    try:
        assert x.get(url(ids)).status_code==404
        with application['engine'].begin() as db:db.execute(text("UPDATE utilisateurs SET role='lecture' WHERE id=:id"),{'id':ids['uid']})
        avant=donnees_metier(application);assert ok(a.get(url(ids)))['total']==1;assert donnees_metier(application)==avant
        with application['engine'].begin() as db:db.execute(text('UPDATE utilisateurs_societes SET actif=false WHERE utilisateur_id=:u AND societe_id=:s'),{'u':ids['uid'],'s':ids['bid']})
        assert a.get(url(ids)).status_code==403
    finally:a.close();b.close();x.close()


def test_641_snapshot_ro_rr_et_connexion_unique_pendant_paiement(application,monkeypatch):
    from database import get_db
    from routers.factures_liees import router
    from routers.auth import router as auth_router
    import services.correspondances_suivi_service as service
    a,b,ids=jeu(application);lu,continuer=Event(),Event();original=service.finances;memo={}
    engine=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'),pool_size=1,max_overflow=0,pool_timeout=1)
    app=FastAPI();app.include_router(router,prefix=PATH);app.include_router(auth_router)
    def session():
        with Session(engine) as db:yield db
    app.dependency_overrides[get_db]=session
    def suspendre(db,fid,sid):
        r=original(db,fid,sid)
        assert db.scalar(text('SHOW transaction_read_only'))=='on' and db.scalar(text('SHOW transaction_isolation'))=='repeatable read'
        if not memo:
            memo['lu']=True;lu.set();assert continuer.wait(20),'Synchronisation de recette expirée'
        return r
    monkeypatch.setattr(service,'finances',suspendre)
    try:
        with TestClient(app) as local,ThreadPoolExecutor(1) as pool:
            token=ok(local.post('/api/auth/login',json={'email':ids['email'],'password':ids['password']}))['access_token'];headers={'Authorization':'Bearer '+token}
            fut=pool.submit(local.get,url(ids),headers=headers);assert lu.wait(15)
            payer(a,ids['fid'],200);continuer.set();ancien=ok(fut.result(20))
            assert ancien['items'][0]['vente']['finances']['solde_restant']=='600.00'
            nouveau=ok(local.get(url(ids),headers=headers));assert nouveau['items'][0]['vente']['finances']['solde_restant']=='400.00'
        assert engine.pool.checkedout()==0
    finally:continuer.set();engine.dispose();a.close();b.close()


@pytest.mark.parametrize('largeur',[1440,390])
def test_641_suivi_et_actualisation_sans_f5_edge(application,largeur,tmp_path):
    from playwright.sync_api import sync_playwright,expect
    a,b,ids=jeu(application)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});errors,serveur=observer(page,application['api_url'])
                connexion(page,application['web_url'],ids['email'],ids['password'])
                page.goto(application['web_url']+'/parametres');page.get_by_role('button',name='Sociétés liées',exact=True).click()
                page.locator('summary').filter(has_text=f'Factures de la liaison {ids["liaison"]}').click()
                panel=page.get_by_role('region',name=f'Factures de la liaison {ids["liaison"]}',exact=True)
                expect(panel.get_by_text('1 correspondance(s) · Liaison active',exact=True)).to_be_visible()
                v=panel.locator('[aria-label="Situation vendeur"]');ach=panel.locator('[aria-label="Situation acheteur"]')
                expect(v).to_contain_text('Reste à régler 600,00 MAD');expect(ach).to_contain_text('Reste à régler 600,00 MAD')
                payer(a,ids['fid'],200)
                with page.expect_response(lambda r:url(ids) in r.url):panel.get_by_role('button',name='Actualiser les factures liées',exact=True).click()
                expect(v).to_contain_text('Reste à régler 400,00 MAD');expect(v).to_contain_text('Encaissé / payé : 200,00 MAD')
                expect(ach).to_contain_text('Reste à régler 600,00 MAD')
                # Retrait dans la même page : ancien suivi actif invalidé sansF5.
                page.get_by_role('button',name=f'Retirer la liaison {ids["liaison"]}',exact=True).click()
                page.get_by_label('Motif du retrait',exact=True).fill('Fin suivi navigateur641')
                page.get_by_role('button',name='Confirmer le retrait',exact=True).click()
                expect(page.get_by_text('Retirée : Fin suivi navigateur641',exact=False)).to_be_visible()
                page.locator('summary').filter(has_text=f'Factures de la liaison {ids["liaison"]}').click()
                expect(panel).to_contain_text('Liaison retirée, historique conservé')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
                page.screenshot(path=str(tmp_path/f'suivi641-{largeur}.png'),full_page=True)
                assert not errors and not serveur,(errors,serveur)
            finally:browser.close()
    finally:a.close();b.close()
