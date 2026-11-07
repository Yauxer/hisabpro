"""Deux sociétés, factures/écritures et retraits restaurés sous LOGIN, deux nonce."""
from contextlib import contextmanager
from pathlib import Path
from datetime import date
from io import BytesIO
import hashlib,json
import httpx
from pypdf import PdfReader
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
import test_restauration_justificatifs_acl_isole as recette
from test_factures_liees635_isole import vente,demande,chemin,PATH
from test_permissions_tva_runtime_isole import donnees_metier
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def test_635_restaurer_liaison_retiree_factures_et_deux_journaux(monkeypatch,tmp_path):
    application_orig,client_orig,lancer_orig=recette.application_isolee,recette.client,recette.lancer_cible
    preparer_orig=recette.preparer091
    memo={};preuve={'erreur':None}
    historique=ROOT/'.codex-tests/restauration452_preuve.json';ancien=historique.read_bytes() if historique.exists() else None

    def preparer102(engine,c):
        preparer_orig(engine,c)
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        for p in sorted(recette.BACK.glob('*.sql')):
            if p.name[:3].isdigit() and 92<=int(p.name[:3])<=102:
                raw=engine.raw_connection()
                try:
                    raw.autocommit=True
                    with raw.cursor() as cur:cur.execute(p.read_text(encoding='utf8'))
                finally:raw.close()

    @contextmanager
    def application102(**kw):
        kw['preparer_runtime']=preparer102
        with application_orig(**kw) as app:yield app

    def situation(url):
        with httpx.Client(base_url=url,timeout=30) as api:
            recette.connecter(api,memo['email'],memo['password'])
            s=recette.ok(api.get(f'{PATH}/factures/{memo["fid"]}/correspondance'))
            assert not s['liaison_active'] and s['vente']['comptabilisee'] and s['achat']['comptabilisee'] and s['ecarts']==[]
            vue=recette.ok(api.get(f'{PATH}/{memo["liaison"]}/correspondances'))
            assert vue['total']==1 and not vue['active']
            assert all(vue['items'][0][c]['finances']['solde_restant']=='600.00' for c in ('vente','achat'))
            r={'suivi':s,'liaisons':recette.ok(api.get(PATH)),'suivi_regroupe':vue}
            for sid,fid in ((memo['sid'],memo['fid']),(memo['bid'],memo['achat'])):
                api.headers['Authorization']='Bearer '+recette.ok(api.post(f'/api/societes/switcher/{sid}'))['access_token']
                etats=recette.ok(api.get(f'/api/etats/liasse/{date.today().year}'))['etats'];assert etats['bilan']['equilibre']
                fec=api.get('/api/fec/export',params={'exercice':date.today().year});assert fec.status_code==200,fec.text
                pdf=api.get(f'/api/factures/{fid}/pdf');assert pdf.status_code==200,pdf.text
                pages=PdfReader(BytesIO(pdf.content)).pages
                r[str(sid)]={'cpc':etats['cpc'],'bilan':etats['bilan'],'fec':fec.content,'pdf_texte':'\n'.join(p.extract_text() for p in pages),'pdf_images':[hashlib.sha256(i.data).hexdigest() for p in pages for i in p.images]}
            return r

    def client_dataset(app):
        if not memo:
            a,b,ids=vente(app,logos=True)
            try:
                corps=demande(a,ids);s=recette.ok(a.post(chemin(ids),json=corps),201);fid=s['facture_achat_id']
                recette.ok(b.post(f'/api/factures/{fid}/valider'))
                for api,f in ((a,ids['fid']),(b,fid)):
                    eid=recette.ok(api.post(f'/api/factures/{f}/comptabiliser'))['ecriture_id'];recette.ok(api.post(f'/api/ecritures/{eid}/valider'))
                recette.ok(a.post(f'{PATH}/{ids["liaison"]}/retirer',json={'motif':'Retrait fictif avant restauration635'}))
                memo.update(ids,achat=fid,corps=corps)
                memo['situation']=situation(app['api_url'])
            finally:a.close();b.close()
        return client_orig(app)

    def cible(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        proc,url,log=lancer_orig(c,uploads);runtime=create_engine(make_url(c['url']).set(username='hisabpro'))
        try:
            assert situation(url)==memo['situation']
            with httpx.Client(base_url=url) as api:
                recette.connecter(api,memo['email'],memo['password'])
                avant=donnees_metier({'engine':runtime})
                assert recette.ok(api.post(chemin(memo),json=memo['corps']),201)==memo['situation']['suivi']
                assert api.post(chemin(memo),json={**memo['corps'],'cle':'11111111-1111-4111-8111-111111111111'}).status_code==409
                assert donnees_metier({'engine':runtime})==avant
            preuve['deux_societes_journaux_fec_pdf_logos_suivi_retrait_identiques']=True
            return proc,url,log
        except BaseException:
            recette.arreter_processus_cree(proc);raise
        finally:runtime.dispose()

    monkeypatch.setattr(recette,'application_isolee',application102)
    monkeypatch.setattr(recette,'client',client_dataset)
    monkeypatch.setattr(recette,'lancer_cible',cible)
    try:
        recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert p['erreur'] is None and p['tables']==80 and p['source_preservee'] and p['cibles_supprimees'] and p['schema_donnees_acl_sequences_identiques']
        preuve.update(p,deux_societes_journaux_fec_pdf_logos_suivi_retrait_identiques=True)
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration635_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
