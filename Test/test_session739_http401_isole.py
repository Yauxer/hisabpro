"""Sessions HTTP401739 : parcours connectés et témoins fiscaux indépendants."""
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
from test_balance_etic_tables697_isole import tables,url as tables_url
from test_balance_etic_annexes699_isole import annexes,url as annexes_url
from test_balance_cpc703_isole import body as cpc_body, url as cpc_url
from test_balance_non_valeurs705_isole import creer as creer_nv, body as nv_body, url as nv_url
from test_balance_participations707_isole import creer as creer_b4, body as b4_body, url as b4_url
from test_balance_preparations import api
from test_balance_preparations_postgres import moteur
from test_logo_societe import image_data
from postgres_isole import verifier_cible_isolee

from test_balance_emetteurs709_isole import body as em_body, url as em_url

from test_balance_cessions711_isole import body as cs_body, url as cs_url

from test_balance_mouvements713_isole import body as mv_body, url as mv_url

from test_balance_raccords715_isole import creer as creer_rc, body as rc_body, url as rc_url

from test_balance_resultat_courant721_isole import body as courant_body, url as courant_url

from test_balance_indicateurs723_isole import body as indicateurs_body, url as indicateurs_url

from test_balance_passage_fiscal725_isole import body as b12_body,url as b12_url

from test_balance_tva727_isole import body as b14_body,url as b14_url

from test_balance_comparatif_n2729_isole import creer_source as creer_n2,body as n2_body,url as n2_url

from test_balance_c3_extra731_isole import body as extra_body,url as extra_url

from test_balance_contexte_fiscal735_isole import body as contexte_body,url as contexte_url

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
    v4=ok(api.post(financement_url(v3),json=flux(v3,n1=True)),201)
    v5=ok(api.post(tables_url(v4),json=tables(v4)),201)
    v6=ok(api.post(annexes_url(v5),json=annexes(v5)),201)
    v7=ok(api.post(cpc_url(v6),json=cpc_body(v6)),201)
    v8=ok(api.post(nv_url(v7),json=nv_body(v7)),201)
    v=ok(api.post(b4_url(v8),json=b4_body(v8)),201)
    v=ok(api.post(cs_url(v),json=cs_body(v)),201)
    v=ok(api.post(mv_url(v),json=mv_body(v)),201)
    v=ok(api.post(rc_url(v),json=rc_body(v,vides=True)),201)
    v=ok(api.post(courant_url(v),json=courant_body(v)),201)
    v=ok(api.post(indicateurs_url(v),json=indicateurs_body(v)),201)
    v=ok(api.post(b12_url(v),json=b12_body(v)),201)
    v=ok(api.post(b14_url(v),json=b14_body(v,zeros=True)),201)
    n2=creer_n2(api);v=ok(api.post(n2_url(v),json=n2_body(v,n2)),201)
    v=ok(api.post(indicateurs_url(v),json=indicateurs_body(v)),201)
    v=ok(api.post(extra_url(v),json=extra_body(v,cohab=True)),201)
    v=ok(api.post(indicateurs_url(v),json=indicateurs_body(v)),201)
    v=ok(api.post(contexte_url(v),json=contexte_body(v)),201);doc=ok(joindre(api,v),201)
    b4=creer_b4(api);b4=ok(api.post(b4_url(b4),json=b4_body(b4)),201)
    b4=ok(api.post(em_url(b4),json=em_body(b4)),201)
    autre=creer_nv(api);autre=ok(api.post(nv_url(autre),json=nv_body(autre)),201)
    rc=creer_rc(api);rc=ok(api.post(rc_url(rc),json=rc_body(rc)),201)
    ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
    e=ok(api.post('/api/ecritures',json={'date':date.today().isoformat(),'journal':'BQ',
        'reference':'TEMOIN739','libelle':'Capital fictif indépendant des notes',
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
        (ROOT/'.codex-tests/session739_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        api.close()
        assert preuve['temoin_comptable_versions_notes_pieces_inchanges']
        assert preuve['temoin_dossier_sources_rendus_pieces_identiques']
        assert preuve['sources_et_scripts_figes']


from test_e2e_session401739_isole import client_http

MODULES=('test_e2e_session401739_isole','test_e2e_connexion_chargement_isole','test_e2e_balance_exports677_isole','test_e2e_facturation_isole','test_e2e_catalogue_articles737_isole')

vus=set()
for i,nom in enumerate(MODULES):
    for cle,f in vars(importlib.import_module(nom)).items():
        if cle.startswith('test_') and callable(f):
            identite=f.__module__,f.__qualname__
            if identite not in vus:
                vus.add(identite);globals()[f'test_739_{i}_{cle[5:]}']=f
