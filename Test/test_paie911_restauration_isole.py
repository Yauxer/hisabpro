from pathlib import Path
import json
from test_paie911_arrondi_annuel_isole import (
    application,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,equipe)
import test_paie901_restauration_isole as recette

R=Path(__file__).resolve().parents[1]


def test_911_restauration_native_comparaison_annuelle(application,equipe,monkeypatch):
    original=recette.lire_ir;lectures=[]
    def verifier(db,user,ident):
        r=original(db,user,ident);c=r['contenu']['controle_arrondi_base']
        assert c['base_arrondie']=='200000.00' and c['ir_apres_reduction']=='45400.0000' and c['versement'] is None
        assert r['contenu']['referentiel']['arrondi_base_annuelle']['unite']=='10.00'
        lectures.append(True);return r
    monkeypatch.setattr(recette,'lire_ir',verifier)
    p=R/'.codex-tests/paie901_restauration_preuve.json';ancien=p.read_bytes() if p.exists() else None
    try:
        recette.test_901_restauration_native_ir_social_et_campagne(application,equipe)
        assert lectures
        preuve=json.loads(p.read_text(encoding='utf8'));preuve.update(comparaison_arrondi_annuel_restituee=True)
        (R/'.codex-tests/paie911_restauration_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
    finally:
        if ancien is not None:p.write_bytes(ancien)
