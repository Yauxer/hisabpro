"""Compléments documentaires : sauvegarde/restauration froide avec vrais exports."""
from contextlib import contextmanager
from pathlib import Path
from io import BytesIO
import hashlib,json
import httpx
from pypdf import PdfReader
from openpyxl import load_workbook
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
import test_restauration_justificatifs_acl_isole as recette
from test_balance_echeances687_isole import creer,demande,chemin,BASE
from test_logo_societe import image_data
from test_permissions_tva_runtime_isole import donnees_metier
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def test_687_restauration_versions_complements_et_exports(monkeypatch,tmp_path):
    application_orig,client_orig,lancer_orig=recette.application_isolee,recette.client,recette.lancer_cible
    preparer_orig=recette.preparer091
    memo={};preuve={'erreur':None}
    historique=ROOT/'.codex-tests/restauration452_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None

    def preparer103(engine,c):
        preparer_orig(engine,c)
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        for p in sorted(recette.BACK.glob('*.sql')):
            if p.name[:3].isdigit() and 92<=int(p.name[:3])<=103:
                raw=engine.raw_connection()
                try:
                    raw.autocommit=True
                    with raw.cursor() as cur:cur.execute(p.read_text(encoding='utf8'))
                finally:raw.close()

    @contextmanager
    def application103(**kw):
        kw['preparer_runtime']=preparer103
        with application_orig(**kw) as app:yield app

    def situation(url):
        with httpx.Client(base_url=url,timeout=30) as api:
            recette.connecter(api,memo['email'],memo['password'])
            d=recette.ok(api.get(chemin(memo['v2'])))
            assert d['lignes'][0]['reliquat']=='5000.00' and d['lignes'][0]['moins_un_an'] is None
            x=api.get(BASE+f'/{memo["v2"]["id"]}/xlsx');assert x.status_code==200
            wb=load_workbook(BytesIO(x.content))
            r=api.get(BASE+f'/{memo["v2"]["id"]}/pdf');assert r.status_code==200
            pdf=PdfReader(BytesIO(r.content))
            return {'data':d,'parent':recette.ok(api.get(BASE+f'/{memo["v1"]["id"]}')),
                'pdf_texte':'\n'.join(p.extract_text() for p in pdf.pages),
                'images':[hashlib.sha256(i.data).hexdigest() for p in pdf.pages for i in p.images],
                'xlsx':{ws.title:list(ws.values) for ws in wb}}

    def dataset(app):
        if not memo:
            api,email,password=client_orig(app)
            try:
                v1=creer(api);body=demande(v1);v2=recette.ok(api.post(chemin(v1),json=body),201)
                recette.ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
                memo.update(email=email,password=password,v1=v1,v2=v2,body=body)
                avant=donnees_metier(app);memo['situation']=situation(app['api_url']);assert donnees_metier(app)==avant
            finally:api.close()
        return client_orig(app)

    def cible(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        proc,url,log=lancer_orig(c,uploads);runtime=create_engine(make_url(c['url']).set(username='hisabpro'))
        try:
            avant=donnees_metier({'engine':runtime})
            assert situation(url)==memo['situation']
            assert donnees_metier({'engine':runtime})==avant
            with httpx.Client(base_url=url) as api:
                recette.connecter(api,memo['email'],memo['password'])
                assert recette.ok(api.post(chemin(memo['v1']),json=memo['body']),201)==memo['v2']
            preuve['versions_complements_pdf_xlsx_logos_rejeu_identiques']=True
            return proc,url,log
        except BaseException:
            recette.arreter_processus_cree(proc);raise
        finally:runtime.dispose()

    monkeypatch.setattr(recette,'application_isolee',application103)
    monkeypatch.setattr(recette,'client',dataset)
    monkeypatch.setattr(recette,'lancer_cible',cible)
    try:
        recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert p['erreur'] is None and p['tables']==82 and p['source_preservee'] and p['cibles_supprimees']
        assert p['schema_donnees_acl_sequences_identiques']
        preuve.update(p,versions_complements_pdf_xlsx_logos_rejeu_identiques=True)
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration687_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
        elif historique.exists():historique.unlink()
