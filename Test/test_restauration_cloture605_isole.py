"""Dossier civil clôturé et CP validée : dump/restore natifs, ancien banc préservé."""
from pathlib import Path
import json
from decimal import Decimal
import test_restauration_ras_tva_capture_isole as precedente
from test_ajustements_inventaire_isole import exercice
from test_e2e_prorata_inventaire_isole import ecriture
from test_e2e_annee_connectee_isole import ORACLE as PROFIL
from test_prorata_inventaire import faits

ROOT=Path(__file__).resolve().parents[1]


def test_605_dossier_clos_fec_an_cp_restitues(monkeypatch,tmp_path):
    preparer_orig,situation_orig=precedente.preparer,precedente.situation
    historique=ROOT/'.codex-tests/restauration575_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None
    memo=[];preuve={'erreur':None}
    ok=precedente.recette.ok
    def preparer_clos(api,*args,**kwargs):
        resultat=preparer_orig(api,*args,**kwargs)
        exercice(api)
        ok(api.patch('/api/societe/moi',json={'forme_juridique':'SARL','regime_fiscal':'is','exercice_debut':2020,'capital_social':20000}))
        ok(api.put('/api/fiscalite/is/2025/parametres',json=PROFIL['profil']['parametres_is']))
        ecriture(api,'2025-01-02',[('5141','20000',0),('1111',0,'20000')],'CAPITAL-FICTIF605-RESTORE')
        ecriture(api,'2025-10-01',[('6125','12000',0),('5141',0,'12000')],'BASE-FICTIVE605-RESTORE')
        calc=ok(api.post('/api/cloture/ajustements/calcul-prorata?exercice=2025',json=faits(base='autre')))
        a=ok(api.post('/api/cloture/ajustements?exercice=2025',json={'type':'cca','montant':calc['montant_reporte'],
            'libelle':calc['libelle_propose'],'compte_activite':'6125','compte_contrepartie':'3491'}))
        ok(api.post(f"/api/ecritures/{a['ecriture_id']}/valider"))
        clos=ok(api.post('/api/cloture/cloturer?exercice=2025'))
        assert Decimal(str(clos['resultat_net']))==Decimal('-9065.93')
        ok(api.post(f"/api/ecritures/{a['contrepassation_id']}/valider"))
        return resultat
    def situation_close(api,rids):
        resultat=situation_orig(api,rids)
        suivi=ok(api.get('/api/cloture/contrepassations?exercice=2026'))
        assert (suivi['total'],suivi['a_valider'],suivi['validees'])==(1,0,1)
        assert suivi['items'][0]['source_validee'] and suivi['items'][0]['est_validee']
        assert suivi['items'][0]['debit']==suivi['items'][0]['credit']=='5934.07'
        ajustements=ok(api.get('/api/cloture/ajustements?exercice=2025'))
        assert len(ajustements)==1 and ajustements[0]['contrepassation_validee']
        fec=api.get('/api/fec/export?exercice=2025')
        assert fec.status_code==200,fec.text
        assert b'CALCUL-IS-2025' in fec.content and b'CLOTURE-2025' in fec.content
        etats=ok(api.get('/api/etats/liasse/2025'))['etats']
        assert etats['bilan']['equilibre']
        assert Decimal(str(etats['cpc']['resultat_net']))==Decimal('-9065.93')
        donnees=(suivi,ajustements,fec.content,etats['cpc'],etats['bilan'])
        if memo:assert donnees==memo[0]
        memo.append(donnees)
        (tmp_path/'FEC605_clos_restitue_fictif.txt').write_bytes(fec.content)
        return resultat
    monkeypatch.setattr(precedente,'preparer',preparer_clos)
    monkeypatch.setattr(precedente,'situation',situation_close)
    try:
        precedente.test_restauration099_dossiers_actif_annule_acl_et_rejeu_identiques(monkeypatch,tmp_path)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert len(memo)==2 and p['erreur'] is None
        preuve.update(p,dossier_clos_fec2025_octets_cp_validee_etats_identiques=True)
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration_cloture605_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
