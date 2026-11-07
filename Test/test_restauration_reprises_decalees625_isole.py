"""Le vrai scénario625, ses deux clôtures et son inverse ouvert sont restaurés."""
from pathlib import Path
import json
import httpx
import test_restauration_reprises615_isole as precedente
import test_e2e_reprises_decalees625_isole as scenario
from test_reprises_provisions615_isole import PATH

ROOT=Path(__file__).resolve().parents[1]


def test_625_restaurer_deux_clotures_et_inverse_exercice_suivant(monkeypatch,tmp_path):
    client_orig=precedente.recette.client;lancer_orig=precedente.recette.lancer_cible
    capture_orig=scenario.client;memo={};preuve={'erreur':None}
    historique=ROOT/'.codex-tests/restauration615_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None

    def situation(url):
        with httpx.Client(base_url=url,timeout=30) as api:
            precedente.recette.connecter(api,memo['email'],memo['password'])
            s=precedente.recette.ok(api.get(PATH));assert s['total']==1
            a=s['items'][0];assert a['disponible']=='1000.00'
            assert a['reprises'][0]['exercice']==2026 and a['reprises'][0]['inverse_exercice']==2027
            d=precedente.recette.ok(api.get(f"{PATH}/{a['id']}/preparation"))
            resultat={'suivi':s,'preparation':d}
            for annee in (2025,2026,2027):
                etats=precedente.recette.ok(api.get(f'/api/etats/liasse/{annee}'))['etats']
                resultat[str(annee)]={'cpc':etats['cpc'],'bilan':etats['bilan']}
                assert etats['bilan']['equilibre']
                f=api.get('/api/fec/export',params={'exercice':annee});assert f.status_code==200,f.text
                resultat['FEC'+str(annee)]=f.content
            return resultat

    def capturer_client(app):
        api,email,password=capture_orig(app);memo.update(email=email,password=password)
        return api,email,password

    def client_dataset(app):
        if not memo:
            dossier=tmp_path/'source625';dossier.mkdir()
            # Réutilisation d'un vrai parcours, aucune réponse API remplacée.
            with monkeypatch.context() as m:
                m.setattr(scenario,'client',capturer_client)
                scenario.test_625_source_decalee_deux_clotures_inverse_ouvert_et_exports(app,1440,dossier)
            memo['situation']=situation(app['api_url'])
        return client_orig(app)

    def lancer(c,uploads):
        proc,url,log=lancer_orig(c,uploads)
        try:
            assert situation(url)==memo['situation']
            preuve['trois_exercices_suivi_sha_etats_fec_identiques']=True
            return proc,url,log
        except BaseException:
            precedente.recette.arreter_processus_cree(proc);raise

    monkeypatch.setattr(precedente.recette,'client',client_dataset)
    monkeypatch.setattr(precedente.recette,'lancer_cible',lancer)
    try:
        precedente.test_615_restauration_registre_annulation_reservation_et_acl(monkeypatch,tmp_path)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert p['erreur'] is None and p['tables']==77 and p['source_preservee'] and p['cibles_supprimees']
        preuve.update(p,trois_exercices_suivi_sha_etats_fec_identiques=True)
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration625_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
