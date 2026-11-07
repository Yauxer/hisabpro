"""Qualification104 : socle annuel, balances, justificatifs et témoins non vides."""
from pathlib import Path
from io import BytesIO
from datetime import date
from zipfile import ZipFile
import hashlib,importlib,json
import pytest
from pypdf import PdfReader
from openpyxl import load_workbook
from sqlalchemy import text
import test_consolidation_ras_documents651_isole as precedent
from test_balance_documents691_isole import (
    application as application104,application103,application102,application101,application100,
    application099,application098,application097,application093,application092,application091,
    application090,application089,application087,migration,client,ok,creer,demande,chemin,BASE,path,joindre,pdf_fictif)
from test_balance_preparations import api
from test_balance_preparations_postgres import moteur
from test_session132_balance_navigateur import bundle,page_recette
from test_e2e_facturation_isole import application as application_absente
from test_logo_societe import image_data
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application104):
    app=application104;c=app['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']) and app['role_sql']=='hisabpro'
    api,_,_=client(app)
    v1=creer(api);v2=ok(api.post(chemin(v1),json=demande(v1)),201)
    raw=pdf_fictif();doc=ok(joindre(api,v2,raw=raw),201)
    ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
    e=ok(api.post('/api/ecritures',json={'date':date.today().isoformat(),'journal':'BQ',
        'reference':'TEMOIN691-INDEPENDANT','libelle':'Capital fictif indépendant des balances',
        'lignes':[{'compte':'5141','debit':333},{'compte':'1111','credit':333}]}),201)
    ok(api.post(f'/api/ecritures/{e["id"]}/valider'));sid=ok(api.get('/api/auth/me'))['societe_id']
    def photo():
        with app['engine'].connect() as db:
            r={t:db.execute(text(f'SELECT row_to_json(x)::text FROM {t} x WHERE societe_id=:s ORDER BY 1'),{'s':sid}).scalars().all()
               for t in ('ecritures','liasse_balances_preparation','liasse_balance_documents')}
            r['lignes']=db.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s ORDER BY l.id'),{'s':sid}).scalars().all()
            return r
    def vue():
        z=api.get(BASE+f'/{v2["id"]}/zip');assert z.status_code==200,z.text
        with ZipFile(BytesIO(z.content)) as zip:
            m=json.loads(zip.read('MANIFESTE_SHA256.json'))
            assert set(zip.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
            for n,v in m['fichiers'].items():assert hashlib.sha256(zip.read(n)).hexdigest()==v['sha256'] and len(zip.read(n))==v['taille']
            fichier='justificatifs/'+doc['nom_stockage'];assert zip.read(fichier)==raw
            wb=load_workbook(BytesIO(zip.read('preparation.xlsx')));pdf=PdfReader(BytesIO(zip.read('preparation.pdf')))
            return {'sources':{n:zip.read(n).decode('utf8') for n in zip.namelist() if n.endswith(('.json','.csv')) and n!='MANIFESTE_SHA256.json'},
                    'pdf':'\n'.join(p.extract_text() or '' for p in pdf.pages),
                    'images':[hashlib.sha256(i.data).hexdigest() for p in pdf.pages for i in p.images],
                    'xlsx':{ws.title:list(ws.values) for ws in wb},'piece_sha256':hashlib.sha256(zip.read(fichier)).hexdigest()}
    initial,lecture=photo(),vue()
    historique=ROOT/'.codex-tests/consolidation651_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None
    interdits={ROOT/'.codex-tests/baseline645.json',ROOT/'.codex-tests/cumul649_preuve.json'}
    lire=Path.read_text
    def portable(path,*a,**kw):
        if path.resolve() in interdits:raise FileNotFoundError('Baseline privée interdite dans une recette livrée.')
        return lire(path,*a,**kw)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path,'read_text',portable)
        banc=precedent.application.__wrapped__(app);demarre=False
        try:
            next(banc);demarre=True;yield app
        finally:
            try:
                banc.close()
                if demarre:
                    preuve=json.loads(historique.read_text(encoding='utf8'))
                    preuve.update(schema_manuel=104,lectures_baselines_privees_interdites=True,
                        temoin_preparations_documents_dossier_inchanges=photo()==initial and vue()==lecture,
                        temoin_preparation_sha256=hashlib.sha256(json.dumps(initial,sort_keys=True).encode()).hexdigest(),
                        role_sql='hisabpro',dossier_cluster=str(c['directory']),dossier_application=str(app['directory']))
                    (ROOT/'.codex-tests/session691_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
                    assert preuve['temoin_preparations_documents_dossier_inchanges']
            finally:
                api.close()
                if ancien is not None:historique.write_bytes(ancien)
                elif historique.exists():historique.unlink()


MODULES=(
    'test_session681_consolidee_isole','test_balance_exports677','test_balance_detail679',
    'test_balance_preparations','test_balance_preparation_pdf','test_balance_preparations_postgres',
    'test_e2e_balance_exports677_isole','test_e2e_balance_detail679_isole','test_session132_balance_navigateur',
    'test_balance_echeances687_isole','test_e2e_balance_echeances687_isole','test_recette_echeances687',
    'test_balance_dossier689_isole','test_e2e_balance_dossier689_isole',
    'test_balance_documents691_isole','test_e2e_balance_documents691_isole',
    'test_installation_vierge_104','test_restauration_balance_documents691_isole',
)
vus=set()
for i,nom in enumerate(MODULES):
    for cle,f in vars(importlib.import_module(nom)).items():
        if cle.startswith('test_') and callable(f):
            identite=f.__module__,f.__qualname__
            if identite not in vus:
                vus.add(identite);globals()[f'test_691_{i}_{cle[5:]}']=f
