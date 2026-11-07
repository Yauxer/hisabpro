"""Restauration froide103 : données/ACL/séquences et traces actives/retirées."""
from contextlib import contextmanager
from pathlib import Path
from io import BytesIO
import hashlib,json
import httpx
from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
import test_restauration_justificatifs_acl_isole as recette
from test_ras_rapprochements681_isole import capture,versement,corps,chemin
from test_logo_societe import image_data
from test_permissions_tva_runtime_isole import donnees_metier
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def test_681_restaurer103_rapprochements_retraits_pdf_et_droits(monkeypatch,tmp_path):
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
            d=recette.ok(api.get(chemin(memo['cid'])))
            assert len(d['items'])==2 and d['total_rapproche']=='30.00' and d['capacite_documentaire']=='45.00'
            assert len([r for r in d['items'] if r['retire_le']])==1
            r=api.get(chemin(memo['cid'])+'/pdf');assert r.status_code==200,r.text
            pdf=PdfReader(BytesIO(r.content))
            return {'data':d,'pdf_texte':'\n'.join(p.extract_text() for p in pdf.pages),
                'images':[hashlib.sha256(i.data).hexdigest() for p in pdf.pages for i in p.images],
                'options':recette.ok(api.get(chemin(memo['cid'])+'/options'))}

    def dataset(app):
        if not memo:
            api,email,password=client_orig(app)
            try:
                _,_,c=capture(api);cid=c['capture']['id'];e=versement(api)
                b1,b2=corps(e,'30.00'),corps(e,'45.00')
                recette.ok(api.post(chemin(cid),json=b1),201)
                d=recette.ok(api.post(chemin(cid),json=b2),201)
                recette.ok(api.post(chemin(cid)+f'/{d["items"][0]["id"]}/retirer',json={'motif':'Retrait fictif avant sauvegarde681'}))
                recette.ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
                memo.update(email=email,password=password,cid=cid,b1=b1)
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
                assert recette.ok(api.post(chemin(memo['cid']),json=memo['b1']),201)==memo['situation']['data']
            preuve['rapprochements_pdf_logos_retraits_options_idempotence_identiques']=True
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
        assert p['erreur'] is None and p['tables']==82 and p['source_preservee'] and p['cibles_supprimees'] and p['schema_donnees_acl_sequences_identiques']
        preuve.update(p,rapprochements_pdf_logos_retraits_options_idempotence_identiques=True)
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration681_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
        elif historique.exists():historique.unlink()
