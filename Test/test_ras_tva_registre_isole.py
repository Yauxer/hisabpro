"""Registre579 : données réelles de laboratoire, droits, exactitude et exports."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from io import BytesIO
import csv
import json
import uuid
import httpx
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import create_engine, text
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
from test_tva_verrou_exercice_isole import attendre_verrou

BASE='/api/tva/ras/registre/'


def jeu(api):
    f,r1=preparer(api);c1,_=capturer(api,r1)
    ok(api.post(f"/api/ecritures/{c1['capture']['ecriture_id']}/valider"))
    r2=paiement(api,f,'525');c2,_=capturer(api,r2)
    ok(api.post(f"/api/reglements/{r2['id']}/annuler",json={'motif':'Annulation fictive579','date_annulation':date.today().isoformat()}))
    _,r3=preparer(api,nature='achat');c3,_=capturer(api,r3,nature='achat')
    return c1,c2,c3


def test_579_totaux_par_nature_et_etat_sans_compensation_ni_mutation(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        c1,c2,c3=jeu(api)
        avant=donnees_metier(application)
        d=ok(api.get(BASE+str(date.today().year)))
        assert d['disponible'] and len(d['lignes'])==3
        assert [r['capture_id'] for r in d['lignes']]==[c3['capture']['id'],c2['capture']['id'],c1['capture']['id']]
        v=d['totaux']['vente'];a=d['totaux']['achat']
        assert {k:v[k]['montant'] for k in v}=={'declarees':'150.00','actives':'75.00','actives_validees':'75.00','annulees':'75.00','annulations_annee':'75.00'}
        assert a['declarees']['montant']==a['actives']['montant']=='75.00'
        assert a['actives_validees']['montant']=='0.00' and a['annulees']['montant']=='0.00'
        assert ok(autre.get(BASE+str(date.today().year)))['lignes']==[]
        assert ok(api.get(BASE+'2025'))['lignes']==[]
        assert donnees_metier(application)==avant
        assert api.get(BASE+'0').status_code==422
        assert api.get(BASE+'10000').status_code==422


@pytest.mark.parametrize('logo',['PNG','JPEG'])
def test_579_exports_logo_valeurs_et_garde_empreinte(application,logo,tmp_path):
    with closing(client(application)[0]) as api:
        jeu(api);ok(api.patch('/api/societe/moi',json={'logo_url':image_data(logo)}))
        avant=donnees_metier(application)
        d=ok(api.get(BASE+str(date.today().year)));empreinte=d['empreinte_sha256']
        prefix=BASE+str(date.today().year)+'/export/'
        sorties={}
        for fmt in ('csv','xlsx','pdf'):
            r=api.get(prefix+fmt,params={'empreinte':empreinte})
            assert r.status_code==200,r.text[:200]
            assert f'registre_ras_tva_{date.today().year}.{fmt}' in r.headers['content-disposition']
            assert r.headers['access-control-expose-headers']=='Content-Disposition'
            sorties[fmt]=r.content
        w=load_workbook(BytesIO(sorties['xlsx']))
        assert w.sheetnames==['Logo société','Synthèse','Captures'] and len(w['Logo société']._images)==1
        assert w['Synthèse']['C8'].value==75 and w['Synthèse']['D8'].value==0
        assert w['Synthèse']['B9'].value==150 and w['Synthèse']['E9'].value==75
        assert w['Captures'].max_row==4
        pdf=PdfReader(BytesIO(sorties['pdf']));texte='\n'.join(p.extract_text() or '' for p in pdf.pages)
        assert any(p.images for p in pdf.pages) and '75,00' in texte and 'Annulée' in texte
        (tmp_path/f'registre579_{logo}.pdf').write_bytes(sorties['pdf'])
        rows=list(csv.reader(sorties['csv'].decode('utf-8-sig').splitlines(),delimiter=';'))
        assert any(row[:2]==['Total vente — Actives','75.00'] for row in rows)
        assert donnees_metier(application)==avant
        # Un changement d'identité ou de logo invalide l'ancien export.
        ok(api.patch('/api/societe/moi',json={'raison_sociale':'Identité fictive modifiée579'}))
        assert api.get(prefix+'pdf',params={'empreinte':empreinte}).status_code==409


def test_579_references_formules_restent_du_texte(application):
    with closing(client(application)[0]) as api:
        _,r=preparer(api);data=demande();data['justification_quote_part']='@REFERENCE-FICTIVE579'
        a=ok(api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=data))
        ok(api.post(f"/api/reglements/{r['id']}/ras-tva",json={**data,'reference':'=1+2','compte_destination':'3453',
            'empreinte_apercu':a['empreinte_apercu'],'pieces_verifiees':True}))
        d=ok(api.get(BASE+str(date.today().year)));params={'empreinte':d['empreinte_sha256']}
        base=BASE+str(date.today().year)+'/export/'
        w=load_workbook(BytesIO(api.get(base+'xlsx',params=params).content))
        assert w['Captures']['J2'].value=='=1+2' and w['Captures']['J2'].data_type=='s'
        contenu=api.get(base+'csv',params=params).content.decode('utf-8-sig')
        assert "'=1+2" in contenu and "'@REFERENCE-FICTIVE579" in contenu


def test_579_lecture_exporte_et_anonyme_refuse(application):
    with closing(client(application)[0]) as api:
        jeu(api);email='lecture579-'+uuid.uuid4().hex[:8]+'@example.com';password='LectureFictive579!'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecture579','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        with httpx.Client(base_url=application['api_url']) as lecteur:
            token=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
            lecteur.headers['Authorization']='Bearer '+token
            avant=donnees_metier(application)
            d=ok(lecteur.get(BASE+str(date.today().year)))
            assert len(d['lignes'])==3
            assert lecteur.get(BASE+str(date.today().year)+'/export/pdf',params={'empreinte':d['empreinte_sha256']}).status_code==200
            assert donnees_metier(application)==avant
        with httpx.Client(base_url=application['api_url']) as anonyme:
            assert anonyme.get(BASE+str(date.today().year)).status_code==401


def test_579_une_seule_connexion_pour_auth_et_registre(application):
    from database import get_db
    from routers.tva import router
    from routers.auth import router as auth_router
    api,email,password=client(application)
    with closing(api):
        _,r=preparer(api);capturer(api,r)
        moteur=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'),pool_size=1,max_overflow=0,pool_timeout=1)
        app=FastAPI();app.include_router(router);app.include_router(auth_router)
        def session():
            with Session(moteur) as db:yield db
        app.dependency_overrides[get_db]=session
        try:
            with TestClient(app,raise_server_exceptions=False) as local:
                token=ok(local.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
                data=ok(local.get(BASE+str(date.today().year),headers={'Authorization':'Bearer '+token}))
                assert data['totaux']['vente']['actives']['montant']=='75.00'
            assert moteur.pool.checkedout()==0
        finally:moteur.dispose()


def test_579_lecture_ro_rr_coherente_pendant_validation_et_changement_identite(application):
    with closing(client(application)[0]) as api:
        api.timeout=30
        _,r=preparer(api);c,_=capturer(api,r)
        nom=ok(api.get('/api/societe/moi'))['raison_sociale']
        with application['engine'].connect() as db,ThreadPoolExecutor(1) as pool:
            tx=db.begin();db.execute(text('LOCK TABLE ras_tva_reglement_details IN ACCESS EXCLUSIVE MODE'))
            try:
                futur=pool.submit(api.get,BASE+str(date.today().year))
                attendre_verrou(application,futur,table='ras_tva_reglement_details')
                ok(api.patch('/api/societe/moi',json={'raison_sociale':'Nouvelle identité fictive579'}))
                ok(api.post(f"/api/ecritures/{c['capture']['ecriture_id']}/valider"))
            finally:tx.rollback()
            d=ok(futur.result(timeout=30))
        assert d['societe']['raison_sociale']==nom and d['lignes'][0]['od_validee'] is False
        nouveau=ok(api.get(BASE+str(date.today().year)))
        assert nouveau['societe']['raison_sociale']=='Nouvelle identité fictive579' and nouveau['lignes'][0]['od_validee'] is True
        assert nouveau['empreinte_sha256']!=d['empreinte_sha256']
