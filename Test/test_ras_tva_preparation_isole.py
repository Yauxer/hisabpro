"""API réelles et PostgreSQL nonce : préparation mensuelle593."""
from contextlib import closing
from datetime import date
from io import BytesIO
import csv
import uuid
import httpx
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    preparer, paiement, capturer, demande,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_logo_societe import image_data

BASE='/api/tva/ras/preparation/'


def periode_suivante():
    d=date.today()
    return (d.year+1,1) if d.month==12 else (d.year,d.month+1)


def jeu(api):
    f,r=preparer(api,nature='achat');c1,_=capturer(api,r,nature='achat')
    ok(api.post(f"/api/ecritures/{c1['capture']['ecriture_id']}/valider"))
    r2=paiement(api,f,'525');c2,_=capturer(api,r2,nature='achat')
    ok(api.post(f"/api/reglements/{r2['id']}/annuler",json={'motif':'Annulation fictive593','date_annulation':date.today().isoformat()}))
    _,r3=preparer(api,nature='achat');c3,_=capturer(api,r3,nature='achat')
    _,r4=preparer(api);capturer(api,r4)
    return c1,c2,c3


def chemin():
    a,m=periode_suivante()
    return f'{BASE}{a}/{m}'


def test_593_totaux_exports_logo_identite_empreinte_et_isolation(application,tmp_path):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        c1,c2,c3=jeu(api);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        avant=donnees_metier(application);d=ok(api.get(chemin()))
        assert len(d['lignes'])==3 and [r['capture_id'] for r in d['lignes']]==[c3['capture']['id'],c2['capture']['id'],c1['capture']['id']]
        assert {k:t['montant'] for k,t in d['totaux']['achat'].items()}=={'saisies':'225.00','actives':'150.00','validees':'75.00','annulees':'75.00'}
        assert d['mois_paiement']==date.today().strftime('%Y-%m')
        assert ok(autre.get(chemin()))['lignes']==[]
        assert ok(api.get(f'{BASE}2026/1'))['lignes']==[]
        e=d['empreinte_sha256'];params={'empreinte':e};sorties={}
        a,m=periode_suivante()
        for fmt in ('csv','xlsx','pdf'):
            r=api.get(chemin()+'/export/'+fmt,params=params)
            assert r.status_code==200,r.text[:200]
            assert f'preparation_ras_tva_{a}_{m:02d}.{fmt}' in r.headers['content-disposition']
            sorties[fmt]=r.content
        rows=list(csv.reader(sorties['csv'].decode('utf-8-sig').splitlines(),delimiter=';'))
        assert any(row[:2]==['Total achat — Captures actives','150.00'] for row in rows)
        assert e in sorties['csv'].decode('utf-8-sig')
        w=load_workbook(BytesIO(sorties['xlsx']))
        assert w['Synthèse']['B6'].value==e and w['Synthèse']['C8'].value==150
        assert w['Synthèse']['D8'].value==75 and w['Synthèse']['E8'].value==75
        assert w['Captures'].max_row==4 and len(w['Logo société']._images)==1
        pdf=PdfReader(BytesIO(sorties['pdf']));texte='\n'.join(p.extract_text() or '' for p in pdf.pages)
        assert e in texte and '150,00' in texte and 'mois précédent' in texte and any(p.images for p in pdf.pages)
        assert 'Subies sur ventes' not in texte
        (tmp_path/'preparation593.pdf').write_bytes(sorties['pdf'])
        assert donnees_metier(application)==avant
        ok(api.post(f"/api/ecritures/{c3['capture']['ecriture_id']}/valider"))
        assert api.get(chemin()+'/export/pdf',params=params).status_code==409
        nouveau=ok(api.get(chemin()))
        assert nouveau['empreinte_sha256']!=e and nouveau['totaux']['achat']['validees']['montant']=='150.00'
        assert api.get(f'{BASE}2026/13').status_code==422
        assert api.get(f'{BASE}2025/12').status_code==422


def test_593_decembre_janvier_postgres_horloge_controlee(application,monkeypatch):
    # Seule l'horloge est contrôlée : aucune règle métier ni accès PostgreSQL
    # remplacé. Les scénarios Edge restent à l'horloge réelle.
    from database import get_db
    from routers import factures, commercial, ras_reglements, tva, tiers, auth as auth_routes
    from services import ras_tva_reglement_service
    class JourScenario(date):
        @classmethod
        def today(cls):return cls(2027,1,15)
    monkeypatch.setattr(factures,'date_cls',JourScenario)
    monkeypatch.setattr(commercial,'_date',JourScenario)
    monkeypatch.setattr(ras_reglements,'date',JourScenario)
    monkeypatch.setattr(ras_tva_reglement_service,'date',JourScenario)
    api,email,password=client(application)
    with closing(api):
        app=FastAPI()
        for router in (factures.router,commercial.router_regl,ras_reglements.router,tva.router,tiers.router,auth_routes.router):app.include_router(router)
        moteur=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'))
        def session():
            with Session(moteur) as db:yield db
        app.dependency_overrides[get_db]=session
        try:
            with TestClient(app,raise_server_exceptions=False) as local:
                token=ok(local.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
                local.headers['Authorization']='Bearer '+token
                verifier_decembre_janvier(local,application)
        finally:moteur.dispose()


def verifier_decembre_janvier(api,application):
    tid=ok(api.post('/api/tiers',json={'nom':'Fournisseur fictif593','type':'fournisseur'}),201)['id']
    f=ok(api.post('/api/factures',json={'type':'achat','date':'2026-12-31','tiers':'Fournisseur fictif593',
        'tiers_id':tid,'reference':'FICTIF-DEC593-'+uuid.uuid4().hex[:8],
        'lignes':[{'description':'Service fictif593','quantite':1,'prix_unitaire':1000,'tva':20}]}),201)
    ok(api.post(f"/api/factures/{f['id']}/valider"));ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
    r=ok(api.post('/api/reglements',json={'facture_id':f['id'],'tiers':f['tiers'],'date':'2026-12-31','montant':'525','mode':'virement','comptabiliser':True}),201)
    data=demande(date_attestation='2026-12-01');data['simulation']['date_paiement']='2026-12-31'
    c,_=capturer(api,r,data,nature='achat')
    avant=donnees_metier(application);d=ok(api.get(BASE+'2027/1'))
    assert [r['capture_id'] for r in d['lignes']]==[c['capture']['id']]
    assert d['mois_paiement']=='2026-12' and d['periode']=='2027-01'
    assert d['totaux']['achat']['actives']['montant']=='75.00'
    assert not d['lignes'][0]['diagnostics']
    assert ok(api.get(BASE+'2026/12'))['lignes']==[]
    assert donnees_metier(application)==avant


def test_593_lecture_seule_anonyme_et_connexion_unique(application):
    from database import get_db
    from routers.tva import router
    from routers.auth import router as auth_router
    with closing(client(application)[0]) as api:
        jeu(api);email='lecture593-'+uuid.uuid4().hex[:8]+'@example.com';password='Fictif593!Lecture'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecture593','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        moteur=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'),pool_size=1,max_overflow=0,pool_timeout=1)
        app=FastAPI();app.include_router(router);app.include_router(auth_router)
        def session():
            with Session(moteur) as db:yield db
        app.dependency_overrides[get_db]=session
        try:
            with TestClient(app,raise_server_exceptions=False) as local:
                assert local.get(chemin()).status_code==401
                token=ok(local.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
                headers={'Authorization':'Bearer '+token};avant=donnees_metier(application)
                d=ok(local.get(chemin(),headers=headers))
                assert len(d['lignes'])==3
                assert local.get(chemin()+'/export/pdf',headers=headers,params={'empreinte':d['empreinte_sha256']}).status_code==200
                assert donnees_metier(application)==avant
            assert moteur.pool.checkedout()==0
        finally:moteur.dispose()
