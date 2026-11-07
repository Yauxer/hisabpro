"""Documents647 : API réelle, PostgreSQL102 nonce et LOGIN limité."""
from contextlib import closing
from datetime import date
from io import BytesIO
from uuid import uuid4
import httpx
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from test_factures_liees635_isole import (
    application,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,
    application089,application087,migration,
)
from test_ras_tva_capture_isole import preparer,capturer
from test_ras_tva_preparation_isole import periode_suivante
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_justificatifs_modeles_runtime_isole import pdf_fictif,original
from test_logo_societe import image_data


def chemins():
    a,m=periode_suivante()
    return f'/api/tva/ras/registre/{date.today().year}',f'/api/tva/ras/preparation/{a}/{m}'


def capture(api,*,annuler=False):
    f,r=preparer(api,nature='achat');c,_=capturer(api,r,nature='achat')
    eid=c['capture']['ecriture_id'];ok(api.post(f'/api/ecritures/{eid}/valider'))
    if annuler:
        ok(api.post(f"/api/reglements/{r['id']}/annuler",json={'motif':'Annulation fictive647','date_annulation':date.today().isoformat()}))
    return f,r,c


def joindre(api,eid,nom='justificatif647.pdf'):
    return ok(api.post(f'/api/attachments/ecriture/{eid}',files={'file':(nom,pdf_fictif(),'application/pdf')}))


def ligne(api,path,cid):
    d=ok(api.get(path));return d,next(x for x in d['lignes'] if x['capture_id']==cid)


def test_647_absence_document_est_explicitement_vide_sans_qualifier_attestation(application):
    with closing(client(application)[0]) as api:
        _,_,c=capture(api);avant=donnees_metier(application)
        for path in chemins():
            d,r=ligne(api,path,c['capture']['id'])
            assert r['documents_od']==[] and r['documents_annulation']==[]
            assert r['reference_attestation'] and r['retenue_tva']=='75.00'
        assert donnees_metier(application)==avant


def test_647_references_fichiers_et_annulation_separes_sans_modifier_od(application):
    with closing(client(application)[0]) as api:
        _,r,c=capture(api,annuler=True);cid=c['capture']['id'];registre,avant=ligne(api,chemins()[0],cid)
        eid=c['capture']['ecriture_id'];inverse=avant['od_annulation_id'];originaux=[original(application,x) for x in (eid,inverse)]
        dossier=ok(api.get(f"/api/reglements/{r['id']}/ras-tva"))['dossier']
        a=joindre(api,eid);b=joindre(api,inverse,'annulation647.pdf')
        ok(api.post(f'/api/ecritures/{eid}/justificatifs',json={'reference':'REF-COMPLEMENT647','date_piece':date.today().isoformat(),'motif':'Complément fictif647'}),201)
        avant_lecture=donnees_metier(application)
        for path in chemins():
            d,x=ligne(api,path,cid)
            assert len(x['documents_od'])==2 and len(x['documents_annulation'])==1
            assert {v['fichier_nom'] for v in x['documents_od']}=={a['nom'],None}
            assert x['documents_annulation'][0]['fichier_nom']==b['nom']
            assert x['documents_od'][-1]['reference']=='REF-COMPLEMENT647'
            assert x['documents_od'][-1]['date_piece']==date.today().isoformat()
            assert x['documents_od'][-1]['prioritaire'] is True
            assert x['retenue_tva']=='75.00' and x['annulation_id']
        assert [original(application,x) for x in (eid,inverse)]==originaux
        assert ok(api.get(f"/api/reglements/{r['id']}/ras-tva"))['dossier']==dossier
        assert donnees_metier(application)==avant_lecture
        assert api.delete(f"/api/attachments/ecriture/{eid}/{a['nom']}").status_code==409


def test_647_documents_changent_empreinte_et_exports_sans_presumer_versement(application):
    with closing(client(application)[0]) as api:
        _,_,c=capture(api);eid=c['capture']['ecriture_id'];cid=c['capture']['id']
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        anciens={p:ok(api.get(p)) for p in chemins()}
        f=joindre(api,eid)
        ok(api.post(f'/api/ecritures/{eid}/justificatifs',json={'reference':'=DOCUMENT647','motif':'Référence fictive, texte Excel'}),201)
        avant=donnees_metier(application)
        for path,ancien in anciens.items():
            d,r=ligne(api,path,cid)
            assert d['empreinte_sha256']!=ancien['empreinte_sha256'] and d['totaux']==ancien['totaux']
            for fmt in ('csv','xlsx','pdf'):
                assert api.get(path+'/export/'+fmt,params={'empreinte':ancien['empreinte_sha256']}).status_code==409
            sorties={fmt:api.get(path+'/export/'+fmt,params={'empreinte':d['empreinte_sha256']}) for fmt in ('csv','xlsx','pdf')}
            assert all(v.status_code==200 for v in sorties.values())
            texte=sorties['csv'].content.decode('utf-8-sig')
            assert f['nom'] in texte and "'=DOCUMENT647" in texte and 'Documents liés' in texte
            w=load_workbook(BytesIO(sorties['xlsx'].content));ws=w['Documents liés']
            assert ws.max_row==3 and len(w['Logo société']._images)==1
            cellule=next(c for row in ws for c in row if c.value=='=DOCUMENT647')
            assert cellule.data_type=='s'
            pdf=PdfReader(BytesIO(sorties['pdf'].content));texte='\n'.join(p.extract_text() or '' for p in pdf.pages)
            assert f['nom'] in texte and '=DOCUMENT647' in texte and any(p.images for p in pdf.pages)
        assert donnees_metier(application)==avant


def test_647_documents_autre_societe_et_lecture_seule(application):
    a,email,password=client(application);b,_,_=client(application)
    with closing(a),closing(b):
        _,_,c=capture(a);eid=c['capture']['ecriture_id'];f=joindre(a,eid)
        email='lecture647-'+uuid4().hex[:8]+'@example.com'
        u=ok(a.post('/api/utilisateurs',json={'nom':'Lecture fictive647','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        with httpx.Client(base_url=application['api_url']) as lecteur:
            token=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token'];lecteur.headers['Authorization']='Bearer '+token
            avant=donnees_metier(application)
            assert ligne(lecteur,chemins()[0],c['capture']['id'])[1]['documents_od'][0]['fichier_nom']==f['nom']
            assert lecteur.get(f['url']).content==pdf_fictif()
            assert lecteur.post(f'/api/attachments/ecriture/{eid}',files={'file':('interdit.pdf',pdf_fictif(),'application/pdf')}).status_code==403
            assert lecteur.delete(f"/api/attachments/ecriture/{eid}/{f['nom']}").status_code==403
            assert b.get(f['url']).status_code==404
            assert b.get(f'/api/attachments/ecriture/{eid}').status_code==404
            assert all(not ok(b.get(p))['lignes'] for p in chemins())
            assert donnees_metier(application)==avant


def test_647_metadonnees_documents_meme_snapshot_ro_rr_connexion_unique(application,monkeypatch):
    from sqlalchemy import create_engine,text
    from sqlalchemy.engine import make_url
    from sqlalchemy.orm import Session
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from database import get_db
    from routers.tva import router
    from routers.auth import router as auth_router
    import services.ras_tva_registre_service as service
    api,email,password=client(application)
    with closing(api):
        _,r,c=capture(api);eid=c['capture']['ecriture_id'];sid=ok(api.get('/api/societe/moi'))['id']
        moteur=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'),pool_size=1,max_overflow=0,pool_timeout=1)
        app=FastAPI();app.include_router(router);app.include_router(auth_router)
        def session():
            with Session(moteur) as db:yield db
        app.dependency_overrides[get_db]=session
        original_completer=service.completer_documents;memo={}
        def pendant(db,s,lignes):
            if s==sid and not memo:
                memo['fichier']=joindre(api,eid)
                assert db.scalar(text('SHOW transaction_read_only'))=='on'
                assert db.scalar(text('SHOW transaction_isolation'))=='repeatable read'
            return original_completer(db,s,lignes)
        monkeypatch.setattr(service,'completer_documents',pendant)
        try:
            with TestClient(app,raise_server_exceptions=False) as local:
                token=ok(local.post('/api/auth/login',json={'email':email,'password':password}))['access_token'];local.headers['Authorization']='Bearer '+token
                d=ok(local.get(chemins()[0]));assert next(x for x in d['lignes'] if x['capture_id']==c['capture']['id'])['documents_od']==[]
                d=ok(local.get(chemins()[0]));assert next(x for x in d['lignes'] if x['capture_id']==c['capture']['id'])['documents_od'][0]['fichier_nom']==memo['fichier']['nom']
        finally:moteur.dispose()
