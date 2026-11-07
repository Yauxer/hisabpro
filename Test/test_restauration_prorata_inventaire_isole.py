"""Calcul595 et ajustement ordinaire après dump/restore natifs, deux nonce."""
from io import BytesIO
from pathlib import Path
import json
from pypdf import PdfReader
import test_restauration_ras_tva_capture_isole as precedente
from test_prorata_inventaire import faits
from test_ajustements_inventaire_isole import exercice
from test_e2e_prorata_inventaire_isole import ecriture
from test_logo_societe import image_data

ROOT=Path(__file__).resolve().parents[1]


def lecture(api):
    data=faits(base='autre')
    d=precedente.recette.ok(api.post('/api/cloture/ajustements/calcul-prorata?exercice=2025',json=data))
    assert d['montant_reporte']=='5934.07'
    r=api.post('/api/cloture/ajustements/calcul-prorata/pdf?exercice=2025',json={**data,'empreinte':d['empreinte_sha256']})
    assert r.status_code==200,r.text[:200]
    pdf=PdfReader(BytesIO(r.content));assert any(p.images for p in pdf.pages)
    texte='\n'.join(p.extract_text() or '' for p in pdf.pages)
    assert d['empreinte_sha256'] in texte and '5934.07' in texte
    ajustements=precedente.recette.ok(api.get('/api/cloture/ajustements?exercice=2025'))
    assert len(ajustements)==1 and ajustements[0]['est_validee'] and not ajustements[0]['contrepassation_validee']
    assert ajustements[0]['libelle']==d['libelle_propose']
    return d,texte,ajustements,r.content


def test_595_calcul_et_ajustement_restitues_sans_mutation(monkeypatch,tmp_path):
    preparer_orig,situation_orig=precedente.preparer,precedente.situation
    historique=ROOT/'.codex-tests/restauration575_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None
    memo,preuve={}, {'erreur':None}
    def preparer_document(api,*args,**kwargs):
        resultat=preparer_orig(api,*args,**kwargs)
        exercice(api);precedente.recette.ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        ecriture(api,'2025-01-02',[('5141','20000',0),('1111',0,'20000')],'CAPITAL-FICTIF595-RESTORE')
        ecriture(api,'2025-10-01',[('6125','12000',0),('5141',0,'12000')],'BASE-FICTIVE595-RESTORE')
        d=precedente.recette.ok(api.post('/api/cloture/ajustements/calcul-prorata?exercice=2025',json=faits(base='autre')))
        a=precedente.recette.ok(api.post('/api/cloture/ajustements?exercice=2025',json={
            'type':'cca','libelle':d['libelle_propose'],'montant':d['montant_reporte'],'compte_activite':'6125','compte_contrepartie':'3491'}))
        precedente.recette.ok(api.post(f"/api/ecritures/{a['ecriture_id']}/valider"))
        return resultat
    def situation_document(api,rids):
        resultat=situation_orig(api,rids);d,texte,ajustements,pdf=lecture(api)
        if not memo:memo.update(d=d,texte=texte,ajustements=ajustements,lectures=1)
        else:
            assert (d,texte,ajustements)==(memo['d'],memo['texte'],memo['ajustements'])
            memo['lectures']+=1;(tmp_path/'prorata595_restaure_fictif.pdf').write_bytes(pdf)
        return resultat
    monkeypatch.setattr(precedente,'preparer',preparer_document)
    monkeypatch.setattr(precedente,'situation',situation_document)
    try:
        precedente.test_restauration099_dossiers_actif_annule_acl_et_rejeu_identiques(monkeypatch,tmp_path)
        p=json.loads(historique.read_text(encoding='utf-8'))
        assert p['erreur'] is None and p['source_preservee'] and p['cibles_supprimees'] and memo['lectures']==2
        preuve.update(p,calcul_json_empreinte_pdf_logo_ajustement_identiques=True,lectures_source_cible=2)
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration_prorata595_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf-8')
        if ancien is not None:historique.write_bytes(ancien)
