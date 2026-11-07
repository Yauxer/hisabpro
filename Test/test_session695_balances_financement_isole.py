"""Financement695 : balances, notes ETIC et témoin comptable documentaire indépendant."""
from datetime import date
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import hashlib,importlib,json
import pytest
from pypdf import PdfReader
from openpyxl import load_workbook
from sqlalchemy import text
from test_balance_etic_notes693_isole import (
    application as application104,application103,application102,application101,application100,
    application099,application098,application097,application093,application092,application091,
    application090,application089,application087,migration,client,ok,creer,demande,chemin,BASE,
    joindre,notes,url)
from test_balance_financement695_isole import creer,flux,url as financement_url
from test_balance_preparations import api
from test_balance_preparations_postgres import moteur
from test_logo_societe import image_data
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def empreintes():
    paths=list((ROOT/'src').rglob('*'))+list((ROOT/'hisabpro-backend').glob('*.py'))+list((ROOT/'hisabpro-backend').glob('*.sql'))
    for d in ('services','routers'):paths+=list((ROOT/'hisabpro-backend'/d).rglob('*.py'))
    paths+=list((ROOT/'Test').glob('*.py'))
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


@pytest.fixture(scope='module')
def application(application104):
    app=application104;c=app['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    api,_,_=client(app)
    v1=creer(api);v2=ok(api.post(chemin(v1),json=demande(v1)),201)
    v3=ok(api.post(url(v2),json=notes(v2)),201)
    v=ok(api.post(financement_url(v3),json=flux(v3,n1=True)),201);doc=ok(joindre(api,v),201)
    ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
    e=ok(api.post('/api/ecritures',json={'date':date.today().isoformat(),'journal':'BQ',
        'reference':'TEMOIN695','libelle':'Capital fictif indépendant des notes',
        'lignes':[{'compte':'5141','debit':333},{'compte':'1111','credit':333}]}),201)
    ok(api.post(f'/api/ecritures/{e["id"]}/valider'));sid=ok(api.get('/api/auth/me'))['societe_id']
    def photo():
        with app['engine'].connect() as db:
            r={t:db.execute(text(f'SELECT row_to_json(x)::text FROM {t} x WHERE societe_id=:s ORDER BY 1'),{'s':sid}).scalars().all()
               for t in ('ecritures','liasse_balances_preparation','liasse_balance_documents')}
            r['lignes']=db.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s ORDER BY l.id'),{'s':sid}).scalars().all()
            return r
    def fichiers():
        rep=api.get(BASE+f'/{v["id"]}/zip');assert rep.status_code==200
        with ZipFile(BytesIO(rep.content)) as z:
            m=json.loads(z.read('MANIFESTE_SHA256.json'));result={}
            for n,h in m['fichiers'].items():
                raw=z.read(n);assert len(raw)==h['taille'] and hashlib.sha256(raw).hexdigest()==h['sha256']
                # Les rendus sont régénérés : métadonnées PDF/XLSX et date du
                # paquet varient normalement, sans changement du snapshot.
                # Le manifeste vérifie néanmoins chaque octet de chaque export.
                if n.endswith('.pdf'):
                    pdf=PdfReader(BytesIO(raw))
                    result[n]={'texte':[p.extract_text() for p in pdf.pages],
                               'images':[hashlib.sha256(i.data).hexdigest() for p in pdf.pages for i in p.images]}
                elif n.endswith('.xlsx'):
                    wb=load_workbook(BytesIO(raw))
                    with ZipFile(BytesIO(raw)) as archive:
                        result[n]={'cellules':{ws.title:list(ws.values) for ws in wb},
                            'images':{p:hashlib.sha256(archive.read(p)).hexdigest() for p in archive.namelist() if p.startswith('xl/media/')}}
                elif n=='LIRE_MOI.txt':
                    result[n]=[line for line in raw.decode('utf8').splitlines() if not line.startswith('Généré le : ')]
                else:
                    result[n]=hashlib.sha256(raw).hexdigest()
            return result
    avant,paquet,figees=photo(),fichiers(),empreintes()
    try:yield app
    finally:
        preuve={'role_sql':app['role_sql'],'schema':104,'erreur':None,
                'source_cluster':str(c['directory']),'source_application':str(app['directory']),
                'temoin_comptable_versions_notes_pieces_inchanges':photo()==avant,
                'temoin_dossier_sources_rendus_pieces_identiques':fichiers()==paquet,
                'sources_et_scripts_figes':empreintes()==figees,'empreintes_sources_et_scripts':figees}
        (ROOT/'.codex-tests/session695_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        api.close()
        assert preuve['temoin_comptable_versions_notes_pieces_inchanges']
        assert preuve['temoin_dossier_sources_rendus_pieces_identiques']
        assert preuve['sources_et_scripts_figes']


MODULES=(
    'test_balance_etic_notes693_isole','test_e2e_balance_etic_notes693_isole',
    'test_balance_exports677','test_balance_detail679','test_balance_preparations',
    'test_balance_preparation_pdf','test_balance_preparations_postgres',
    'test_e2e_balance_exports677_isole','test_e2e_balance_detail679_isole',
    'test_balance_echeances687_isole','test_e2e_balance_echeances687_isole',
    'test_balance_dossier689_isole','test_e2e_balance_dossier689_isole',
    'test_balance_documents691_isole','test_e2e_balance_documents691_isole',
    'test_balance_financement695_isole','test_e2e_balance_financement695_isole',
    'test_restauration_balance_financement695_isole',
)
vus=set()
for i,nom in enumerate(MODULES):
    for cle,f in vars(importlib.import_module(nom)).items():
        if cle.startswith('test_') and callable(f):
            identite=f.__module__,f.__qualname__
            if identite not in vus:
                vus.add(identite);globals()[f'test_695_{i}_{cle[5:]}']=f
