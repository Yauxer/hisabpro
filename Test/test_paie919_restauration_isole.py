from pathlib import Path
import json
from sqlalchemy import text
from test_paie919_rattachement_isole import (
    application,application122,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,salarie,rubrique,envoyer,submit,choix,V,ok,simuler,declaration)
import test_paie901_restauration_isole as recette
from services.paie_variables_service import lire as lire_variable
from services.paie_campagnes_service import lire as lire_brut

R=Path(__file__).resolve().parents[1]

def test_919_restauration_native_rattachement_et_snapshots(application,equipe,monkeypatch):
    eq=equipe;eid,_=salarie(eq,m='RATT919');rid=rubrique(eq,'RATTACHEMENT_FICTIF919')
    v=envoyer(eq,eid,rid,rattachement_revenus=declaration());submit(eq,v['id']);ok(eq['b'].post(f'{V}/{v["id"]}/approuver',json=choix()));q=simuler(eq,[eid]);original=recette.lire_ir;lectures=[]
    def verifier(db,user,ident):
        a=lire_variable(db,user,v['id']);assert a['donnees']['rattachement_revenus']==declaration() and a['statut']=='APPROUVE'
        b=lire_brut(db,user,q['id']);assert b['contenu']==q['contenu'] and b['empreinte']==q['empreinte']
        assert db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='aaa_paie_reference123' AND tgenabled='O')"))
        lectures.append(True);return original(db,user,ident)
    monkeypatch.setattr(recette,'lire_ir',verifier)
    p=R/'.codex-tests/paie901_restauration_preuve.json';ancien=p.read_bytes() if p.exists() else None
    try:
        recette.test_901_restauration_native_ir_social_et_campagne(application,equipe)
        assert lectures;a=json.loads(p.read_text(encoding='utf8'));a.update(rattachement_restitue=True,dates_separees_restituees=True,snapshot_brut_restitue=True,garde123_restitue=True)
        (R/'.codex-tests/paie919_restauration_preuve.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
    finally:
        if ancien is not None:p.write_bytes(ancien)
