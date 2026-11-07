"""Qualification bornée des dossiers, exports et contextes sans baseline privée."""
from pathlib import Path
from io import BytesIO
from datetime import date
from zipfile import ZipFile
import hashlib,importlib,json
import pytest
from pypdf import PdfReader
from openpyxl import load_workbook
from sqlalchemy import text
from test_balance_dossier689_isole import (
    application as application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,demande,chemin,BASE,verifier_bundle)
from test_balance_preparations import api
from test_consolidation_ras_documents651_isole import empreintes_application
from test_logo_societe import image_data
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application103):
    app=application103;c=app['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']) and app['role_sql']=='hisabpro'
    api,_,_=client(app)
    try:
        v1=creer(api);v2=ok(api.post(chemin(v1),json=demande(v1)),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        e=ok(api.post('/api/ecritures',json={'date':date.today().isoformat(),'journal':'BQ',
            'reference':'TEMOIN689-INDEPENDANT','libelle':'Capital fictif indépendant des balances',
            'lignes':[{'compte':'5141','debit':333},{'compte':'1111','credit':333}]}),201)
        ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
        sid=ok(api.get('/api/auth/me'))['societe_id']
        def photo():
            with app['engine'].connect() as db:
                r={t:db.execute(text(f'SELECT row_to_json(x)::text FROM {t} x WHERE societe_id=:s ORDER BY 1'),{'s':sid}).scalars().all()
                   for t in ('ecritures','liasse_balances_preparation')}
                r['lignes']=db.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s ORDER BY l.id'),{'s':sid}).scalars().all()
                return r
        def dossier():
            response=api.get(BASE+f'/{v2["id"]}/zip');assert response.status_code==200,response.text
            verifier_bundle(response.content,v2)
            with ZipFile(BytesIO(response.content)) as z:
                wb=load_workbook(BytesIO(z.read('preparation.xlsx')));pdf=PdfReader(BytesIO(z.read('preparation.pdf')))
                return {'sources':{n:z.read(n).decode('utf8') for n in z.namelist() if n.endswith(('.json','.csv')) and n!='MANIFESTE_SHA256.json'},
                    'pdf':'\n'.join(p.extract_text() or '' for p in pdf.pages),
                    'images':[hashlib.sha256(i.data).hexdigest() for p in pdf.pages for i in p.images],
                    'xlsx':{ws.title:list(ws.values) for ws in wb}}
        initial,vue,sources=photo(),dossier(),empreintes_application()
        try:yield app
        finally:
            fin,relue,actuelles=photo(),dossier(),empreintes_application()
            preuve={'sources_inchangees':sources==actuelles,'sources':sources,
                'temoin_comptable_versions_inchanges':initial==fin,'dossier_sources_rendus_logos_inchanges':vue==relue,
                'temoin_sha256':hashlib.sha256(json.dumps(initial,sort_keys=True).encode()).hexdigest(),
                'schema':103,'role_sql':app['role_sql'],'dossier_cluster':str(c['directory']),
                'dossier_application':str(app['directory'])}
            (ROOT/'.codex-tests/session689_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
            assert preuve['sources_inchangees'] and preuve['temoin_comptable_versions_inchanges'] and preuve['dossier_sources_rendus_logos_inchanges']
    finally:api.close()


for nom in ('test_balance_dossier689_isole','test_e2e_balance_dossier689_isole',
    'test_e2e_balance_echeances687_isole','test_balance_exports677','test_balance_detail679',
    'test_e2e_balance_exports677_isole','test_e2e_balance_detail679_isole',
    'test_e2e_ras_rapprochements681_isole','test_e2e_ras_cle681_isole'):
    m=importlib.import_module(nom)
    for name,fonction in vars(m).items():
        if name.startswith('test_') and callable(fonction):
            assert name not in globals(),name
            globals()[name]=fonction
