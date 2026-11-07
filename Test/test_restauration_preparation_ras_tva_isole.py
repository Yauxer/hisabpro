"""Préparation mensuelle et exports après pg_dump/pg_restore natifs, deux nonce."""
from datetime import date
from io import BytesIO
from pathlib import Path
import json
from openpyxl import load_workbook
from pypdf import PdfReader
import test_restauration_ras_tva_capture_isole as precedente
from test_logo_societe import image_data

ROOT=Path(__file__).resolve().parents[1]


def lire(api):
    jour=date.today();a,m=(jour.year+1,1) if jour.month==12 else (jour.year,jour.month+1)
    base=f'/api/tva/ras/preparation/{a}/{m}'
    d=precedente.recette.ok(api.get(base))
    assert len(d['lignes'])==2
    assert {k:t['montant'] for k,t in d['totaux']['achat'].items()}=={
        'saisies':'150.00','actives':'75.00','validees':'75.00','annulees':'75.00'}
    sorties={}
    for fmt in ('csv','xlsx','pdf'):
        r=api.get(base+'/export/'+fmt,params={'empreinte':d['empreinte_sha256']})
        assert r.status_code==200,r.text[:200];sorties[fmt]=r.content
    w=load_workbook(BytesIO(sorties['xlsx']));pdf=PdfReader(BytesIO(sorties['pdf']))
    assert len(w['Logo société']._images)==1 and any(p.images for p in pdf.pages)
    texte='\n'.join(p.extract_text() or '' for p in pdf.pages)
    assert '75,00' in texte and 'Annulée' in texte and d['empreinte_sha256'] in texte
    return d,sorties['csv'],{s.title:list(s.values) for s in w},texte,sorties['pdf']


def test_593_preparation_restituee_sans_mutation(monkeypatch,tmp_path):
    preparer_orig,capturer_orig,situation_orig=precedente.preparer,precedente.capturer,precedente.situation
    historique=ROOT/'.codex-tests/restauration575_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None
    memo,preuve={}, {'erreur':None}
    def preparer_achat(api,*args,**kwargs):
        kwargs['nature']='achat';resultat=preparer_orig(api,*args,**kwargs)
        precedente.recette.ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        return resultat
    def capturer_achat(api,*args,**kwargs):
        kwargs['nature']='achat';return capturer_orig(api,*args,**kwargs)
    def situation_mensuelle(api,rids):
        resultat=situation_orig(api,rids)
        d,csv,valeurs,texte,pdf=lire(api)
        if not memo:memo.update(d=d,csv=csv,valeurs=valeurs,texte=texte,lectures=1)
        else:
            assert (d,csv,valeurs,texte)==(memo['d'],memo['csv'],memo['valeurs'],memo['texte'])
            memo['lectures']+=1;(tmp_path/'preparation593_restauree_fictive.pdf').write_bytes(pdf)
        return resultat
    monkeypatch.setattr(precedente,'preparer',preparer_achat)
    monkeypatch.setattr(precedente,'capturer',capturer_achat)
    monkeypatch.setattr(precedente,'situation',situation_mensuelle)
    try:
        precedente.test_restauration099_dossiers_actif_annule_acl_et_rejeu_identiques(monkeypatch,tmp_path)
        p=json.loads(historique.read_text(encoding='utf-8'))
        assert p['erreur'] is None and p['source_preservee'] and p['cibles_supprimees']
        assert memo['lectures']==2
        preuve.update(p,preparation_json_empreinte_csv_pdf_xlsx_logos_identiques=True,lectures_source_cible=2)
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration593_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf-8')
        if ancien is not None:historique.write_bytes(ancien)
