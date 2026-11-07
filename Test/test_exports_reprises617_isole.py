"""PDF/Excel réels du registre100, aucune société ou donnée réelle."""
from contextlib import closing
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import httpx
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import text,create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_reprises_provisions615_isole import (
    application,application099,application098,application097,application093,application092,
    application091,application090,application089,application087,migration,dotation,corps,demande,PATH)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_logo_societe import image_data


def preparer_source(api):
    ok(api.patch('/api/societe/moi',json={'raison_sociale':'RECETTE FICTIVE <B>& C','logo_url':image_data('PNG')}))
    a=dotation(api);aid=a['id'];c=corps(api,aid)
    s=ok(api.post(f'{PATH}/{aid}',json=c));r=s['reprises'][0]
    ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider"))
    s=ok(api.post(f"{PATH}/{aid}/{r['id']}/annuler",json={'date':'2026-02-02','motif':'Annulation documentaire fictive617'}))
    ok(api.post(f"/api/ecritures/{s['reprises'][0]['inverse_id']}/valider"))
    c=corps(api,aid,demande('200',date='2026-02-03',reference='=1+1',justification='=SUM(1,1) <literal> '+('texte fictif '*25)))
    ok(api.post(f'{PATH}/{aid}',json=c))
    return aid


def preparation(api,aid):return ok(api.get(f'{PATH}/{aid}/preparation'))


@pytest.mark.parametrize('fmt',['pdf','xlsx'])
def test_617_fichiers_exacts_logo_statuts_et_absence_mutation(application,fmt,tmp_path):
    with closing(client(application)[0]) as api:
        aid=preparer_source(api);avant=donnees_metier(application)
        d=preparation(api,aid);assert preparation(api,aid)==d
        empreinte=d.pop('empreinte_sha256')
        assert hashlib.sha256(json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==empreinte
        r=api.get(f'{PATH}/{aid}/export/{fmt}',params={'empreinte':empreinte})
        assert r.status_code==200,r.text
        assert f'suivi_reprises_provision_{aid}.{fmt}' in r.headers['content-disposition']
        assert donnees_metier(application)==avant
        (tmp_path/f'reprises617.{fmt}').write_bytes(r.content)
        if fmt=='pdf':
            p=PdfReader(BytesIO(r.content));texte='\n'.join(x.extract_text() or '' for x in p.pages)
            assert any(x.images for x in p.pages)
            for t in ['RECETTE FICTIVE <B>& C','1000.00','800.00','200.00','=1+1','<literal>',empreinte,'Libérée à la date de l’inverse','Brouillon']:
                assert t in texte,(t,texte)
        else:
            w=load_workbook(BytesIO(r.content));s=w['Synthèse'];p=w['Reprises']
            assert (s['B12'].value,s['B13'].value,s['B14'].value,s['B15'].value)==(1000,0,200,800)
            assert s['B17'].value==empreinte and p['G2'].value=='=1+1' and p['G2'].data_type=='s'
            assert p['F2'].value.startswith('=SUM(1,1) <literal>') and p['F2'].data_type=='s'
            assert p.row_dimensions[2].height>=90 and p['M3'].value=='Libérée à la date de l’inverse'
            assert 'Logo société' in w.sheetnames and w['Logo société']._images
            with ZipFile(BytesIO(r.content)) as z:assert any(n.startswith('xl/media/') for n in z.namelist())


@pytest.mark.parametrize('changement',['validation','annulation','societe','logo','compte'])
def test_617_apercu_perime_refuse_sans_mutation(application,changement):
    with closing(client(application)[0]) as api:
        aid=preparer_source(api);d=preparation(api,aid);r=d['source']['reprises'][0]
        if changement=='validation':ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider"))
        elif changement=='annulation':ok(api.post(f"{PATH}/{aid}/{r['id']}/annuler",json={'date':'2026-02-04','motif':'Autre fictif617'}))
        elif changement=='societe':ok(api.patch('/api/societe/moi',json={'raison_sociale':'Autre identité fictive617'}))
        elif changement=='logo':ok(api.patch('/api/societe/moi',json={'logo_url':''}))
        else:
            sid=ok(api.get('/api/societe/moi'))['id']
            with application['engine'].begin() as db:db.execute(text("UPDATE comptes_societe SET libelle='Libellé fictif617 modifié' WHERE societe_id=:s AND numero='1518'"),{'s':sid})
        avant=donnees_metier(application)
        for fmt in ('pdf','xlsx'):
            r=api.get(f'{PATH}/{aid}/export/{fmt}',params={'empreinte':d['empreinte_sha256']})
            assert r.status_code==409,r.text
        assert donnees_metier(application)==avant
        assert preparation(api,aid)['empreinte_sha256']!=d['empreinte_sha256']


def test_617_societes_lecture_et_source_orpheline(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        aid=preparer_source(api);d=preparation(api,aid)
        assert autre.get(f'{PATH}/{aid}/preparation').status_code==404
        assert autre.get(f'{PATH}/{aid}/export/pdf',params={'empreinte':d['empreinte_sha256']}).status_code==404
        email='lecture617-'+uuid4().hex[:8]+'@example.com';password='LectureFictive617!'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecture617','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        with httpx.Client(base_url=application['api_url']) as lecteur:
            token=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token'];lecteur.headers['Authorization']='Bearer '+token
            avant=donnees_metier(application)
            assert preparation(lecteur,aid)==d
            for fmt in ('pdf','xlsx'):assert lecteur.get(f'{PATH}/{aid}/export/{fmt}',params={'empreinte':d['empreinte_sha256']}).status_code==200
            assert donnees_metier(application)==avant
        a=dotation(api)
        with application['engine'].begin() as db:db.execute(text('UPDATE ajustements_inventaire SET ecriture_id=NULL WHERE id=:a'),{'a':a['id']})
        d=preparation(api,a['id']);assert d['source']['diagnostic']
        for fmt in ('pdf','xlsx'):
            r=api.get(f"{PATH}/{a['id']}/export/{fmt}",params={'empreinte':d['empreinte_sha256']})
            assert r.status_code==200,r.text


def test_617_grand_montant_excel_conserve_texte_exact(application):
    with closing(client(application)[0]) as api:
        a=dotation(api,valider=False)
        with application['engine'].begin() as db:db.execute(text("UPDATE ajustements_inventaire SET montant='9249999999999999.98' WHERE id=:a"),{'a':a['id']})
        d=preparation(api,a['id']);assert d['source']['diagnostic']
        r=api.get(f"{PATH}/{a['id']}/export/xlsx",params={'empreinte':d['empreinte_sha256']});assert r.status_code==200,r.text
        c=load_workbook(BytesIO(r.content))['Synthèse']['B12']
        assert c.value=='9249999999999999.98' and c.data_type=='s'


def test_617_auth_et_preparation_partagent_une_connexion(application):
    from database import get_db
    from routers.cloture_reprises import router
    from routers.auth import router as auth_router
    api,email,password=client(application)
    with closing(api):
        aid=preparer_source(api)
        engine=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'),pool_size=1,max_overflow=0,pool_timeout=1)
        app=FastAPI();app.include_router(router,prefix='/api/cloture');app.include_router(auth_router)
        def session():
            with Session(engine) as db:yield db
        app.dependency_overrides[get_db]=session
        try:
            with TestClient(app,raise_server_exceptions=False) as local:
                token=ok(local.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
                headers={'Authorization':'Bearer '+token}
                r=local.get(f'{PATH}/{aid}/preparation',headers=headers)
                assert r.status_code==200,r.text
                d=r.json();assert d['source']['disponible']=='800.00'
                r=local.get(f'{PATH}/{aid}/export/pdf',params={'empreinte':d['empreinte_sha256']},headers=headers)
                assert r.status_code==200,r.text
            assert engine.pool.checkedout()==0
        finally:engine.dispose()


def test_617_snapshot_ro_rr_pendant_validation_et_identite(application,monkeypatch):
    import services.reprises_provisions_export_service as service
    from database import get_db
    from routers.cloture_reprises import router
    from routers.auth import router as auth_router
    lu,continuer=Event(),Event();original=service.lecture_source
    api,email,password=client(application)
    with closing(api):
        aid=preparer_source(api);avant=preparation(api,aid)
        engine=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'))
        app=FastAPI();app.include_router(router,prefix='/api/cloture');app.include_router(auth_router)
        def session():
            with Session(engine) as db:yield db
        app.dependency_overrides[get_db]=session
        def suspendre(db,sid,a):
            result=original(db,sid,a);lu.set()
            assert continuer.wait(20),'Synchronisation de recette expirée'
            return result
        monkeypatch.setattr(service,'lecture_source',suspendre)
        try:
            with TestClient(app) as local,ThreadPoolExecutor(1) as pool:
                token=ok(local.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
                futur=pool.submit(local.get,f'{PATH}/{aid}/preparation',headers={'Authorization':'Bearer '+token})
                assert lu.wait(10)
                try:
                    r=avant['source']['reprises'][0]
                    ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider"))
                    ok(api.patch('/api/societe/moi',json={'raison_sociale':'Identité concurrente fictive617','logo_url':''}))
                finally:continuer.set()
                rep=futur.result(20);assert rep.status_code==200,rep.text
                assert rep.json()==avant
            nouveau=preparation(api,aid)
            assert nouveau['empreinte_sha256']!=avant['empreinte_sha256']
            assert nouveau['societe']['raison_sociale']=='Identité concurrente fictive617'
            assert nouveau['source']['reprises'][0]['est_validee']
        finally:continuer.set();engine.dispose()
