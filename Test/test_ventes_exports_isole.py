"""Exports serveur du relevé affiché : vrais PDF/XLSX,PGnonce,empreinte contrôlée."""
from contextlib import closing
from datetime import date
from io import BytesIO
import copy
import uuid
import pytest
from pypdf import PdfReader
from openpyxl import load_workbook
from sqlalchemy import text
from services.ventes_preparation_export_service import xlsx,pdf
from test_ventes_preparation_isole import application,facture,ok,preparation,photographie,cible
from test_ras_lecture_conservation import client


def export(api,data,format):
    return api.get(f"/api/etats/ventes/preparation/{data['exercice']}/export/{format}",params={'empreinte':data['empreinte_sha256']})


@pytest.mark.parametrize('format',['pdf','xlsx'])
def test_export_reel_totaux_et_source_immutable(application,format):
    with closing(client(application)[0]) as api:
        f,_=facture(api,100,nom='=CLIENT FICTIF EXPORT')
        facture(api,200)
        ok(api.post('/api/avoirs',json={'facture_id':f['id'],'date':f'{date.today().year}-03-15',
            'motif':'Correction fictive','lignes':[{'facture_ligne_id':f['lignes'][0]['id'],'quantite':0.3}]}),201)
        avant=photographie(application);data=ok(preparation(api))
        r=export(api,data,format);assert r.status_code==200,r.text
        assert f'.{format}' in r.headers['content-disposition']
        if format=='pdf':
            pages=PdfReader(BytesIO(r.content)).pages;texte='\n'.join(p.extract_text() or '' for p in pages)
            assert 'PRÉPARATION INTERNE' in texte and '270,00' in texte and '324,00' in texte
            assert '=CLIENT FICTIF EXPORT' in texte and '001234567890123' in texte
            assert data['empreinte_sha256'] in texte
        else:
            w=load_workbook(BytesIO(r.content));assert w.sheetnames==['Synthèse','Sources','Comptabilité']
            assert [w['Synthèse'].cell(i,2).value for i in range(12,15)]==[270,54,324]
            assert w['Sources']['E2'].value=='=CLIENT FICTIF EXPORT' and w['Sources']['E2'].data_type=='s'
            assert w['Sources']['F2'].value=='001234567890123' and w['Sources']['F2'].data_type=='s'
            assert len(list(w['Sources'].rows))==4
            assert not any(c.data_type=='f' for s in w for row in s for c in row)
        assert photographie(application)==avant


@pytest.mark.parametrize('format',['pdf','xlsx'])
def test_sources_modifiees_refuse_export_ancien_sans_mutation(application,format):
    with closing(client(application)[0]) as api:
        facture(api,100);data=ok(preparation(api));facture(api,200)
        avant=photographie(application)
        assert export(api,data,format).status_code==409
        assert photographie(application)==avant
        fresh=ok(preparation(api));assert fresh['empreinte_sha256']!=data['empreinte_sha256']
        assert export(api,fresh,format).status_code==200
        assert photographie(application)==avant


@pytest.mark.parametrize('format',['pdf','xlsx'])
def test_montants_inconnus_exportes_comme_inconnus(application,format):
    with closing(client(application)[0]) as api:
        f,_=facture(api,50,valider=False)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text("UPDATE lignes_facture SET quantite='NaN' WHERE facture_id=:id"),{'id':f['id']})
            db.execute(text("UPDATE factures SET est_validee=true,numero=:n WHERE id=:id"),{'id':f['id'],'n':f"HIST-EXPORT-{f['id']}"})
        data=ok(preparation(api));avant=photographie(application)
        r=export(api,data,format);assert r.status_code==200,r.text
        if format=='pdf':
            texte='\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(r.content)).pages)
            assert 'Total complet : HT À vérifier' in texte and 'Partie connue uniquement' in texte
        else:
            w=load_workbook(BytesIO(r.content))
            assert w['Synthèse']['B12'].value=='À vérifier' and w['Sources']['H2'].value=='À vérifier'
        assert photographie(application)==avant


def test_export_empreinte_etrangere_auth_et_format_refuses(application):
    a,_,_=client(application);b,_,_=client(application)
    try:
        facture(a,100);facture(b,100)
        data=ok(preparation(a));avant=photographie(application)
        assert export(b,data,'pdf').status_code==409
        assert a.get(f"/api/etats/ventes/preparation/{data['exercice']}/export/pdf",params={'empreinte':'invalide'}).status_code==422
        assert export(a,data,'xml').status_code==422
        assert a.get(f"/api/etats/ventes/preparation/{data['exercice']}/export/pdf",params={'empreinte':data['empreinte_sha256']},headers={'Authorization':''}).status_code==401
        assert photographie(application)==avant
    finally:a.close();b.close()


@pytest.mark.parametrize('format',['pdf','xlsx'])
def test_lecture_autorisee_export_sans_mutation(application,format):
    with closing(client(application)[0]) as api:
        facture(api,100)
        email='lecture-export-'+uuid.uuid4().hex[:8]+'@example.com'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecture export fictive','email':email,
            'mot_de_passe':'LectureVentes2026!','role':'lecture'}),201)
        token=ok(api.post('/api/auth/login',json={'email':email,'password':'LectureVentes2026!'}))['access_token']
        headers={'Authorization':'Bearer '+token}
        data=ok(api.get(f'/api/etats/ventes/preparation/{date.today().year}',headers=headers))
        avant=photographie(application)
        path=f"/api/etats/ventes/preparation/{data['exercice']}/export/{format}"
        r=api.get(path,headers=headers,params={'empreinte':data['empreinte_sha256']})
        assert r.status_code==200,r.text
        assert r.headers['access-control-expose-headers']=='Content-Disposition'
        assert api.post(path,headers=headers,json={}).status_code==405
        assert photographie(application)==avant


def test_xlsx_precision_et_textes_preserves_sans_formules():
    data={'exercice':2026,'societe':{'raison_sociale':'=FICTIF','ice':'001','identifiant_fiscal':None},
        'societe_id':1,'date_debut':'2026-01-01','date_fin':'2026-12-31','empreinte_sha256':'a'*64,
        'note':'Interne','documents':[], 'exclusions':{},'nb_montants_inconnus':0,
        'totaux':{'ht':'1234567890123456.78','tva':'0.01','ttc':'1234567890123456.79'},
        'totaux_partie_connue':{'ht':'1234567890123456.78','tva':'0.01','ttc':'1234567890123456.79'}}
    avant=copy.deepcopy(data);w=load_workbook(BytesIO(xlsx(data)))
    assert w['Synthèse']['B12'].value=='1234567890123456.78' and w['Synthèse']['B12'].data_type=='s'
    assert w['Synthèse']['B13'].value==0.01
    assert w['Synthèse']['B2'].value=='=FICTIF' and w['Synthèse']['B2'].data_type=='s'
    assert data==avant


def test_pdf_multipages_sources_completes_et_texte_dans_page():
    import fitz
    documents=[{'nature':'facture','id':i,'numero':f'FICTIF-{i:03d}',
        'date':'2026-03-15','tiers':'Client fictif & contrôle <sans balise>',
        'ice':'001234567890123','identifiant_fiscal':'01234567',
        'ht':'100.00','tva':'20.00','ttc':'120.00','comptabilisee':False,
        'diagnostics':['Pièce non comptabilisée.']} for i in range(1,121)]
    data={'exercice':2026,'societe_id':1,'societe':{'raison_sociale':'Société fictive PDF'},
        'date_debut':'2026-01-01','date_fin':'2026-12-31','note':'Préparation interne, sans formulaire fiscal officiel.',
        'empreinte_sha256':'a'*64,'documents':documents,'exclusions':{'brouillons':0},
        'totaux':{'ht':'12000.00','tva':'2400.00','ttc':'14400.00'},
        'totaux_partie_connue':{'ht':'12000.00','tva':'2400.00','ttc':'14400.00'}}
    avant=copy.deepcopy(data)
    with fitz.open(stream=pdf(data),filetype='pdf') as document:
        assert len(document)>1
        texte='\n'.join(page.get_text() for page in document)
        for i in range(1,121):assert texte.count(f'FICTIF-{i:03d}')==1
        assert '12000,00' in texte and '14400,00' in texte and 'a'*64 in texte
        for page in document:
            assert 'Client figé' in page.get_text()
            for bloc in page.get_text('dict')['blocks']:
                for ligne in bloc.get('lines',[]):
                    for span in ligne['spans']:
                        x0,y0,x1,y1=span['bbox']
                        assert 0<=x0<x1<=page.rect.width and 0<=y0<y1<=page.rect.height
    assert data==avant
