"""Documents RAS et exports restaurés en PostgreSQL102 natif et fichiers nonce."""
from contextlib import contextmanager
from pathlib import Path
from io import BytesIO
from datetime import date
import hashlib,json
import httpx
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
import test_restauration_justificatifs_acl_isole as recette
from test_ras_documents647_isole import capture,joindre,chemins,ligne
from test_permissions_tva_runtime_isole import donnees_metier
from test_logo_societe import image_data
from test_justificatifs_modeles_runtime_isole import pdf_fictif
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def test_647_restauration102_documents_et_exports_actifs_annules_identiques(monkeypatch,tmp_path):
    application_orig,client_orig,lancer_orig=recette.application_isolee,recette.client,recette.lancer_cible
    preparer_orig=recette.preparer091
    memo={};supplements={};preuve={'erreur':None}
    historique=ROOT/'.codex-tests/restauration452_preuve.json';ancien=historique.read_bytes()

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

    def lire(url):
        with httpx.Client(base_url=url,timeout=30) as api:
            recette.connecter(api,memo['email'],memo['password'])
            resultat={}
            for path in chemins():
                d=recette.ok(api.get(path));assert len(d['lignes'])==2
                assert len([x for x in d['lignes'] if x['annulation_id']])==1
                assert sum(len(x['documents_od'])+len(x['documents_annulation']) for x in d['lignes'])==4
                sorties={fmt:api.get(path+'/export/'+fmt,params={'empreinte':d['empreinte_sha256']}) for fmt in ('csv','xlsx','pdf')}
                assert all(v.status_code==200 for v in sorties.values())
                w=load_workbook(BytesIO(sorties['xlsx'].content));pdf=PdfReader(BytesIO(sorties['pdf'].content))
                assert w['Documents liés'].max_row==5 and len(w['Logo société']._images)==1
                assert any(p.images for p in pdf.pages)
                fichiers={}
                for r in d['lignes']:
                    for cle,eid in [('documents_od',r['ecriture_id']),('documents_annulation',r['od_annulation_id'])]:
                        for j in r[cle]:
                            if j['fichier_nom']:
                                fichier=api.get(f"/api/attachments/ecriture/{eid}/download/{j['fichier_nom']}")
                                assert fichier.status_code==200 and fichier.content==pdf_fictif()
                                fichiers[j['fichier_nom']]=hashlib.sha256(fichier.content).hexdigest()
                assert len(fichiers)==3
                resultat[path]=(d,sorties['csv'].content,{s.title:list(s.values) for s in w},
                    '\n'.join(p.extract_text() or '' for p in pdf.pages),fichiers)
            resultat['dossiers']=[recette.ok(api.get(f'/api/reglements/{rid}/ras-tva')) for rid in memo['rids']]
            return resultat

    def client_dataset(app):
        if not memo:
            api,email,password=client_orig(app)
            try:
                sid=recette.ok(api.get('/api/societe/moi'))['id']
                def document(eid,nom):
                    f=joindre(api,eid,nom)
                    supplements[f"{sid}/ecriture/{eid}/{f['nom']}"]=(len(pdf_fictif()),hashlib.sha256(pdf_fictif()).hexdigest())
                rids=[];eids=[]
                for annuler in (False,True):
                    _,r,c=capture(api,annuler=annuler);rids.append(r['id']);eid=c['capture']['ecriture_id'];eids.append(eid)
                    document(eid,f'capture647_{eid}.pdf')
                    if annuler:
                        _,l=ligne(api,chemins()[0],c['capture']['id']);document(l['od_annulation_id'],'contrepassation647.pdf')
                recette.ok(api.post(f'/api/ecritures/{eids[0]}/justificatifs',json={'reference':'COMPLEMENT-RESTORE647','motif':'Document fictif avant sauvegarde'}),201)
                recette.ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
                memo.update(email=email,password=password,rids=rids)
                avant=donnees_metier(app);memo['situation']=lire(app['api_url']);assert donnees_metier(app)==avant
            finally:api.close()
        return client_orig(app)

    def cible(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        proc,url,log=lancer_orig(c,uploads);runtime=create_engine(make_url(c['url']).set(username='hisabpro'))
        try:
            avant=donnees_metier({'engine':runtime})
            assert lire(url)==memo['situation']
            assert donnees_metier({'engine':runtime})==avant
            preuve['registre_preparation_empreintes_exports_documents_octets_identiques']=True
            return proc,url,log
        except BaseException:
            recette.arreter_processus_cree(proc);raise
        finally:runtime.dispose()

    monkeypatch.setattr(recette,'application_isolee',application102)
    monkeypatch.setattr(recette,'client',client_dataset)
    monkeypatch.setattr(recette,'lancer_cible',cible)
    try:
        recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path,fichiers_supplementaires=supplements)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert p['erreur'] is None and p['tables']==80 and p['source_preservee'] and p['cibles_supprimees'] and p['schema_donnees_acl_sequences_identiques']
        preuve.update(p,registre_preparation_empreintes_exports_documents_octets_identiques=True)
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration647_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        historique.write_bytes(ancien)
