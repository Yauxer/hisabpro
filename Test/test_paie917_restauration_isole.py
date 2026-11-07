from pathlib import Path
from io import BytesIO
import json
from sqlalchemy import text
from pypdf import PdfReader
from openpyxl import load_workbook
from test_paie917_documents_isole import (
    application,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,source_annuelle,demande,S,ok,exporter,image_data)
import test_paie901_restauration_isole as recette
from services.paie_ir_annuel_service import lire
from services.paie_frais_annuels_service import lire as lire_frais
from services import paie_ir_documents_service as doc

R=Path(__file__).resolve().parents[1]


def test_917_restauration_native_documents_logo_et_evenements(application,equipe,monkeypatch):
    eq=equipe;_,_,source=source_annuelle(eq);r=ok(eq['a'].post(S,json=demande(source['id'])),201)
    societe=ok(eq['a'].patch('/api/societe/moi',json={'logo_url':image_data()}))
    for fmt in ['pdf','xlsx']:assert exporter(eq,r['id'],fmt).status_code==200
    attendu=doc.sections(r,source,societe);original=recette.lire_ir;lectures=[]
    def verifier(db,user,ident):
        a=lire(db,user,r['id']);f=lire_frais(db,user,source['id']);s=dict(db.execute(text('SELECT raison_sociale,ice,identifiant_fiscal,logo_url FROM societes WHERE id=:s'),{'s':eq['sid']}).mappings().one())
        assert doc.sections(a,f,s)==attendu and s['logo_url']==image_data()
        raw=doc.pdf(a,f,s);p=PdfReader(BytesIO(raw));assert sum(len(x.images) for x in p.pages)==1 and '5967.0000' in '\n'.join(x.extract_text() or '' for x in p.pages)
        (R/'.codex-tests/paie917_document_restitue.pdf').write_bytes(raw)
        raw=doc.xlsx(a,f,s);w=load_workbook(BytesIO(raw));assert len(w['Logo société']._images)==1 and w['Sources mensuelles'].max_row==13
        (R/'.codex-tests/paie917_document_restitue.xlsx').write_bytes(raw)
        assert db.scalar(text("SELECT count(*) FROM personnel_evenements WHERE societe_id=:s AND employe_id=:e AND nature='CONTROLE_IR_EXPORTE'"),{'s':eq['sid'],'e':a['contenu']['source_frais_annuels']['employe_id']})==2
        lectures.append(True);return original(db,user,ident)
    monkeypatch.setattr(recette,'lire_ir',verifier)
    p=R/'.codex-tests/paie901_restauration_preuve.json';ancien=p.read_bytes() if p.exists() else None
    try:
        recette.test_901_restauration_native_ir_social_et_campagne(application,equipe)
        assert lectures;preuve=json.loads(p.read_text(encoding='utf8'));preuve.update(documents_regeneres_depuis_snapshots=True,logo_restitue=True,deux_evenements_export_restitues=True)
        (R/'.codex-tests/paie917_restauration_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
    finally:
        if ancien is not None:p.write_bytes(ancien)
