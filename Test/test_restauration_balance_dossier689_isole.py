"""Dossier ZIP reconstitué après restauration réelle, sans égalité binaire présumée."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import json,hashlib
import httpx
from pypdf import PdfReader
from openpyxl import load_workbook
import test_restauration_justificatifs_acl_isole as recette
from test_restauration_balance_echeances687_isole import test_687_restauration_versions_complements_et_exports as restaurer687
from test_balance_dossier689_isole import creer,demande,chemin,BASE,verifier_bundle
from test_logo_societe import image_data
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def test_689_dossier_zip_restitue_apres_restauration(monkeypatch,tmp_path):
    client_orig,lancer_orig=recette.client,recette.lancer_cible
    memo={};preuve={'erreur':None}
    historique=ROOT/'.codex-tests/restauration687_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None

    def situation(url):
        with httpx.Client(base_url=url,timeout=30) as api:
            recette.connecter(api,memo['email'],memo['password'])
            r=api.get(BASE+f'/{memo["v"]["id"]}/zip');assert r.status_code==200,r.text
            verifier_bundle(r.content,memo['v'])
            with ZipFile(BytesIO(r.content)) as z:
                wb=load_workbook(BytesIO(z.read('preparation.xlsx')))
                pdf=PdfReader(BytesIO(z.read('preparation.pdf')))
                # Les rendus peuvent porter de nouvelles dates/ID techniques.
                # Les données, textes et images doivent être les mêmes ; le
                # nouveau manifeste est vérifié contre les vrais octets du ZIP.
                return {'sources':{n:z.read(n).decode('utf8') for n in z.namelist() if n.endswith(('.csv','.json')) and n!='MANIFESTE_SHA256.json'},
                    'pdf':'\n'.join(p.extract_text() or '' for p in pdf.pages),
                    'images':[hashlib.sha256(i.data).hexdigest() for p in pdf.pages for i in p.images],
                    'xlsx':{ws.title:list(ws.values) for ws in wb}}

    def dataset(app):
        if not memo:
            api,email,password=client_orig(app)
            try:
                v1=creer(api);v=recette.ok(api.post(chemin(v1),json=demande(v1)),201)
                recette.ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
                memo.update(email=email,password=password,v=v)
                memo['situation']=situation(app['api_url'])
            finally:api.close()
        return client_orig(app)

    def cible(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        proc,url,log=lancer_orig(c,uploads)
        try:
            assert situation(url)==memo['situation']
            preuve['dossier_sources_pdf_xlsx_logos_manifestes_valides_apres_restauration']=True
            return proc,url,log
        except BaseException:
            recette.arreter_processus_cree(proc);raise

    monkeypatch.setattr(recette,'client',dataset)
    monkeypatch.setattr(recette,'lancer_cible',cible)
    try:
        restaurer687(monkeypatch,tmp_path)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert p['erreur'] is None and p['tables']==82 and p['source_preservee'] and p['cibles_supprimees']
        preuve.update(p,dossier_sources_pdf_xlsx_logos_manifestes_valides_apres_restauration=True)
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration689_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
        elif historique.exists():historique.unlink()
