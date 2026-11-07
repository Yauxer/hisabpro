from pathlib import Path
import json
from test_paie921_mensuel_isole import (
    application,application123,application122,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,preparation,demande,M,ok)
import test_paie901_restauration_isole as recette
from services.paie_ir_mensuel_service import lire

R=Path(__file__).resolve().parents[1]

def test_921_restauration_native_controle_mensuel_et_fractions(application,equipe,monkeypatch):
    eq=equipe;eid,_,p=preparation(eq);r=ok(eq['a'].post(M,json=demande(p['id'],eid)),201);original=recette.lire_ir;lectures=[]
    def verifier(db,user,ident):
        a=lire(db,user,r['id']);assert a['contenu']==r['contenu'] and a['empreinte']==r['empreinte']
        assert a['contenu']['rni_arithmetique']=='6990.08' and a['contenu']['ir_mensuel_arithmetique']=='497.0240' and a['contenu']['retenue_a_operer'] is None
        lectures.append(True);return original(db,user,ident)
    monkeypatch.setattr(recette,'lire_ir',verifier)
    p=R/'.codex-tests/paie901_restauration_preuve.json';ancien=p.read_bytes() if p.exists() else None
    try:
        recette.test_901_restauration_native_ir_social_et_campagne(application,equipe)
        assert lectures;a=json.loads(p.read_text(encoding='utf8'));a.update(controle_mensuel_restitue=True,fractions_exactes_restituees=True,source_preparation_restituee=True)
        (R/'.codex-tests/paie921_restauration_preuve.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
    finally:
        if ancien is not None:p.write_bytes(ancien)
