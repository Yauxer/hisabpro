"""Le même exercice de restauration relit aussi le nouveau snapshot fiscal."""
from pathlib import Path
import json
from sqlalchemy import text
from test_paie909_bases_isole import (
    application,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,preparer,calcul_fiscal,ok)
import test_paie907_restauration_isole as recette
from services.paie_bases_fiscales_service import lire

R=Path(__file__).resolve().parents[1]


def test_909_restauration_native_bases_fiscales_et_sources(application,equipe,monkeypatch):
    eq=equipe;eid,_,_,s,_=preparer(eq);r=calcul_fiscal(eq,eid,s);lectures=[];original=recette.lire_ir
    def verifier(db,user,ident):
        fiscal=lire(db,user,r['id']);assert fiscal['contenu']==r['contenu'] and fiscal['empreinte']==r['empreinte']
        assert fiscal['contenu']['totaux']['revenu_avant_frais_autres_deductions']=='9240.11'
        assert fiscal['contenu']['totaux']['revenu_net_imposable'] is None
        lectures.append(True);return original(db,user,ident)
    monkeypatch.setattr(recette,'lire_ir',verifier)
    # Le scénario907 attribue sa propre habilitation dédiée ; clôturer celle du montage909 par l'API.
    with application['engine'].connect() as db:
        h=db.scalar(text("SELECT id FROM personnel_habilitations WHERE societe_id=:s AND utilisateur_id=:u AND capacite='personnel.valider_regles_paie' AND revoquee_at IS NULL"),{'s':eq['sid'],'u':eq['bid']})
    ok(eq['a'].post(f'/api/employes/securite/habilitations/{h}/revoquer',json={'motif':'Fin du montage fictif909 avant scénario de restauration'}))
    preuve907=R/'.codex-tests/paie907_restauration_preuve.json';ancienne=preuve907.read_bytes() if preuve907.exists() else None
    try:
        recette.test_907_restauration_native_qualifications_et_snapshots(application,equipe)
        assert lectures
        preuve=json.loads(preuve907.read_text(encoding='utf8'));preuve.update(nouveau_snapshot_fiscal_restitue=True,lecture_fiscale_runtime_limite=True)
        (R/'.codex-tests/paie909_restauration_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
    finally:
        if ancienne is not None:preuve907.write_bytes(ancienne)
