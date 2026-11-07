"""Restauration froide699 : B8/B9, financement, notes, versions et pièces conservés."""
from contextlib import contextmanager
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import hashlib,json
import httpx
from pypdf import PdfReader
from openpyxl import load_workbook
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
import test_restauration_justificatifs_acl_isole as recette
from test_balance_documents691_isole import creer,demande,chemin,BASE,path,joindre,pdf_fictif
from test_logo_societe import image_data
from test_balance_etic_notes693_isole import notes,url as notes_url
from test_balance_financement695_isole import creer,flux,url as financement_url
from test_permissions_tva_runtime_isole import donnees_metier
from postgres_isole import verifier_cible_isolee

from test_balance_etic_tables697_isole import tables,url as tables_url

from test_balance_etic_annexes699_isole import annexes,url as annexes_url

ROOT=Path(__file__).resolve().parents[1]


def test_699_restaurer_financement_notes_et_pieces(monkeypatch,tmp_path):
    application_orig,client_orig,lancer_orig=recette.application_isolee,recette.client,recette.lancer_cible
    preparer_orig=recette.preparer091;memo={};preuve={'erreur':None};supplements={}
    historique=ROOT/'.codex-tests/restauration452_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None

    def preparer104(engine,c):
        preparer_orig(engine,c)
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        for p in sorted(recette.BACK.glob('*.sql')):
            if p.name[:3].isdigit() and 92<=int(p.name[:3])<=104:
                raw=engine.raw_connection()
                try:
                    raw.autocommit=True
                    with raw.cursor() as cur:cur.execute(p.read_text(encoding='utf8'))
                finally:raw.close()

    @contextmanager
    def application104(**kw):
        kw['preparer_runtime']=preparer104
        with application_orig(**kw) as app:yield app

    def situation(url):
        with httpx.Client(base_url=url,timeout=30) as api:
            recette.connecter(api,memo['email'],memo['password'])
            d=recette.ok(api.get(path(memo['v'])));assert len(d['documents'])==1
            r=api.get(path(memo['v'])+f'/{memo["doc"]["id"]}');assert r.status_code==200 and r.content==memo['raw']
            z=api.get(BASE+f'/{memo["v"]["id"]}/zip');assert z.status_code==200,z.text
            with ZipFile(BytesIO(z.content)) as zip:
                assert zip.testzip() is None
                assert json.loads(zip.read('notes_etic_documentaires.json'))['comptage_notes']['renseigne']==1
                assert json.loads(zip.read('financement_documentaire.json'))['tableau']['ecart_controle']==0
                a=json.loads(zip.read('annexes_etic_documentaires.json'))
                assert a['tables'][2]['lignes'][0]['date_contrat']=='2025-12-15'
                assert a['tables'][3]['lignes'][0]['pourcentage']=='66.666666666667'
                tableau=json.loads(zip.read('tables_etic_documentaires.json'))
                assert tableau['tables'][0]['lignes'][0]['montant_couvert']=='12345.67'
                assert tableau['tables'][0]['lignes'][0]['valeur_nette'] is None and len(tableau['alertes'])==1
                m=json.loads(zip.read('MANIFESTE_SHA256.json'))
                assert set(zip.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
                for n,v in m['fichiers'].items():
                    assert len(zip.read(n))==v['taille'] and hashlib.sha256(zip.read(n)).hexdigest()==v['sha256']
                nom='justificatifs/'+memo['doc']['nom_stockage'];assert zip.read(nom)==memo['raw']
                pdf=PdfReader(BytesIO(zip.read('preparation.pdf')));wb=load_workbook(BytesIO(zip.read('preparation.xlsx')))
                return {'documents':d,'sources':{n:zip.read(n).decode('utf8') for n in zip.namelist() if n.endswith(('.csv','.json')) and n!='MANIFESTE_SHA256.json'},
                    'pdf':'\n'.join(p.extract_text() or '' for p in pdf.pages),
                    'images':[hashlib.sha256(i.data).hexdigest() for p in pdf.pages for i in p.images],
                    'xlsx':{ws.title:list(ws.values) for ws in wb},'piece_sha256':hashlib.sha256(zip.read(nom)).hexdigest()}

    def dataset(app):
        if not memo:
            api,email,password=client_orig(app)
            try:
                v1=creer(api);v2=recette.ok(api.post(chemin(v1),json=demande(v1)),201)
                v3=recette.ok(api.post(notes_url(v2),json=notes(v2)),201)
                v4=recette.ok(api.post(financement_url(v3),json=flux(v3)),201)
                v5=recette.ok(api.post(tables_url(v4),json=tables(v4)),201)
                v=recette.ok(api.post(annexes_url(v5),json=annexes(v5)),201);raw=pdf_fictif()
                doc=recette.ok(joindre(api,v,raw=raw),201)
                sid=recette.ok(api.get('/api/auth/me'))['societe_id']
                relatif=f'{sid}/balance_preparation_documents/{v["id"]}/{doc["nom_stockage"]}'
                supplements[relatif]=(len(raw),hashlib.sha256(raw).hexdigest())
                recette.ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
                memo.update(email=email,password=password,v=v,doc=doc,raw=raw)
                avant=donnees_metier(app);memo['situation']=situation(app['api_url']);assert donnees_metier(app)==avant
            finally:api.close()
        return client_orig(app)

    def cible(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        proc,url,log=lancer_orig(c,uploads);runtime=create_engine(make_url(c['url']).set(username='hisabpro'))
        try:
            avant=donnees_metier({'engine':runtime});assert situation(url)==memo['situation']
            assert donnees_metier({'engine':runtime})==avant
            preuve['pieces_octets_traces_dossier_manifestes_logos_identiques']=True
            return proc,url,log
        except BaseException:
            recette.arreter_processus_cree(proc);raise
        finally:runtime.dispose()

    monkeypatch.setattr(recette,'application_isolee',application104)
    monkeypatch.setattr(recette,'client',dataset);monkeypatch.setattr(recette,'lancer_cible',cible)
    try:
        recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path,fichiers_supplementaires=supplements)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert p['erreur'] is None and p['tables']==83 and p['source_preservee'] and p['cibles_supprimees']
        assert p['schema_donnees_acl_sequences_identiques']
        preuve.update(p,pieces_octets_traces_dossier_manifestes_logos_identiques=True)
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration699_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
        elif historique.exists():historique.unlink()
