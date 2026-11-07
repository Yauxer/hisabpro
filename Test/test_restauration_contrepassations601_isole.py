"""Les liens/statuts d'ouverture survivent au dump/restore natif existant."""
from pathlib import Path
import json
import test_restauration_prorata_inventaire_isole as precedente

ROOT=Path(__file__).resolve().parents[1]


def test_601_suivi_restitue_identique_et_sources_preservees(monkeypatch,tmp_path):
    lecture_orig=precedente.lecture
    historique=ROOT/'.codex-tests/restauration_prorata595_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None
    memo=[];preuve={'erreur':None}
    def lecture_suivi(api):
        resultat=lecture_orig(api)
        r=api.get('/api/cloture/contrepassations?exercice=2026')
        assert r.status_code==200,r.text
        d=r.json()
        assert (d['total'],d['a_valider'],d['validees'])==(1,1,0)
        assert d['items'][0]['source_validee']
        assert d['items'][0]['debit']==d['items'][0]['credit']=='5934.07'
        if memo:assert d==memo[0]
        memo.append(d)
        return resultat
    monkeypatch.setattr(precedente,'lecture',lecture_suivi)
    try:
        precedente.test_595_calcul_et_ajustement_restitues_sans_mutation(monkeypatch,tmp_path)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert len(memo)==2 and p['erreur'] is None
        preuve.update(p,suivi_contrepassations_source_cible_identique=True)
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration_contrepassations601_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
