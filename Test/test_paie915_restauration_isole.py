from pathlib import Path
import json
from test_paie915_ir_source_isole import (
    application,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,source_annuelle,demande,S,ok)
import test_paie901_restauration_isole as recette
from services.paie_ir_annuel_service import lire

R=Path(__file__).resolve().parents[1]


def test_915_restauration_native_lien_ir_rni_et_precision(application,equipe,monkeypatch):
    eq=equipe;_,_,source=source_annuelle(eq);r=ok(eq['a'].post(S,json=demande(source['id'])),201);original=recette.lire_ir;lectures=[]
    def verifier(db,user,ident):
        a=lire(db,user,r['id']);assert a['contenu']==r['contenu'] and a['empreinte']==r['empreinte']
        assert a['contenu']['source_frais_annuels']['rni_avant_arrondis']=='83881.0200' and a['contenu']['ir_annuel_arithmetique']=='5967.0000'
        lectures.append(True);return original(db,user,ident)
    monkeypatch.setattr(recette,'lire_ir',verifier)
    p=R/'.codex-tests/paie901_restauration_preuve.json';ancien=p.read_bytes() if p.exists() else None
    try:
        recette.test_901_restauration_native_ir_social_et_campagne(application,equipe)
        assert lectures;preuve=json.loads(p.read_text(encoding='utf8'));preuve.update(ir_source_restitue=True,rni_quatre_decimales_restitue=True,lien_annuel_restitue=True)
        (R/'.codex-tests/paie915_restauration_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
    finally:
        if ancien is not None:p.write_bytes(ancien)
