"""Après dump/restore natifs : données, PDF, cellules Excel et logos identiques."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import re
import httpx
from openpyxl import load_workbook
from pypdf import PdfReader
import test_restauration_reprises615_isole as precedente
from test_logo_societe import image_data
from test_reprises_provisions615_isole import PATH

ROOT=Path(__file__).resolve().parents[1]


def empreintes(api,aid,ok):
    d=ok(api.get(f'{PATH}/{aid}/preparation'));preuves={'donnees':d}
    for fmt in ('pdf','xlsx'):
        r=api.get(f'{PATH}/{aid}/export/{fmt}',params={'empreinte':d['empreinte_sha256']})
        assert r.status_code==200,r.text
        if fmt=='pdf':
            p=PdfReader(BytesIO(r.content));preuves['pdf_texte']='\n'.join(x.extract_text() or '' for x in p.pages)
            preuves['pdf_images']=[hashlib.sha256(i.data).hexdigest() for page in p.pages for i in page.images]
            assert preuves['pdf_images']
        else:
            w=load_workbook(BytesIO(r.content));preuves['xlsx']={s.title:[[(c.value,c.data_type) for c in row] for row in s] for s in w}
            preuves['xlsx_images']=[hashlib.sha256(i._data()).hexdigest() for s in w for i in s._images]
            assert preuves['xlsx_images']
    return preuves


def test_617_exports_et_logo_apres_restauration_natifs(monkeypatch,tmp_path):
    ok_orig=precedente.recette.ok;client_orig=precedente.recette.client
    memo=[];preuve={'erreur':None};historique=ROOT/'.codex-tests/restauration615_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None
    def client_logo(app):
        api,email,password=client_orig(app)
        ok_orig(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        return api,email,password
    def controle(r,status=200):
        data=ok_orig(r,status)
        if re.fullmatch(re.escape(PATH)+r'/[0-9]+',r.request.url.path) and isinstance(data,dict) and len(data.get('reprises',[]))==2 and data.get('disponible')=='800.00':
            with httpx.Client(base_url=str(r.request.url.copy_with(path='/',query=None)),
                headers={'Authorization':r.request.headers['Authorization']},timeout=25) as api:
                resultat=empreintes(api,data['id'],ok_orig)
            if memo:assert resultat==memo[0]
            memo.append(resultat)
        return data
    monkeypatch.setattr(precedente.recette,'client',client_logo)
    monkeypatch.setattr(precedente.recette,'ok',controle)
    try:
        precedente.test_615_restauration_registre_annulation_reservation_et_acl(monkeypatch,tmp_path)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert p['erreur'] is None and p['tables']==77 and len(memo)>=3
        preuve.update(p,lectures_exports=len(memo),pdf_textes_images_excel_cellules_et_images_identiques=True)
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration617_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
