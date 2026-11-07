"""Sauvegarde froide097, quatre fonctions/droits et conflit409 après copie."""
from contextlib import contextmanager
from datetime import date
from pathlib import Path
import hashlib,json
import httpx
from sqlalchemy import create_engine,text
import test_restauration_justificatifs_acl_isole as recette
from test_restauration_avances095_isole import test_restauration095_registre_historique_soldes_et_reprise as scenario095
from test_avances_salaries_isole import appliquer
from test_consolidation_tva097_isole import fonctions
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def test_restauration097_fonctions_conflit409_reprise_et_registre(monkeypatch,tmp_path):
    application=recette.application_isolee;lancer=recette.lancer_cible;memo={}
    preuve095=ROOT/'.codex-tests/restauration482_preuve.json'
    ancien=preuve095.read_bytes() if preuve095.exists() else None
    @contextmanager
    def source097(**kwargs):
        with application(**kwargs) as app:
            appliquer(app,'096_verrou_parametres_tva.sql');appliquer(app,'097_verrou_tva_trace_cloture.sql')
            memo['fonctions']=fonctions(app['engine']);assert len(memo['fonctions'])==4
            yield app
    def cible097(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        engine=create_engine(c['url']);proc=None
        try:
            assert fonctions(engine)==memo['fonctions']
            proc,url,log=lancer(c,uploads)
            with engine.connect() as db:
                sid,email=db.execute(text("SELECT e.societe_id,u.email FROM employes e JOIN utilisateurs u ON u.societe_id=e.societe_id WHERE e.nom='Salarié restauration fictive095' AND u.role='admin'")).one()
            annee=date.today().year-2
            with httpx.Client(base_url=url) as api:
                recette.connecter(api,email)
                with engine.connect() as db:
                    tx=db.begin()
                    try:
                        db.execute(text('INSERT INTO clotures_exercice(societe_id,exercice,resultat_net) VALUES(:s,:a,0)'),{'s':sid,'a':annee})
                        r=api.put(f'/api/tva/parametres/{annee}',json={'credit_ouverture':12,'prorata_deduction_pct':80})
                        assert r.status_code==409,r.text
                    finally:tx.rollback()
                r=api.put(f'/api/tva/parametres/{annee}',json={'credit_ouverture':12,'prorata_deduction_pct':80})
                assert r.status_code==200,r.text
                assert api.get(f'/api/tva/parametres/{annee}').json()['credit_ouverture']==12
            memo['conflit409_et_reprise200']=True
            return proc,url,log
        except BaseException:
            if proc is not None:recette.arreter_processus_cree(proc)
            raise
        finally:engine.dispose()
    monkeypatch.setattr(recette,'application_isolee',source097)
    monkeypatch.setattr(recette,'lancer_cible',cible097)
    try:
        scenario095(monkeypatch,tmp_path)
        preuve=json.loads(preuve095.read_text(encoding='utf8'))
        preuve.update(extension097=True,quatre_fonctions_identiques=True,
            conflit409_et_reprise200=memo['conflit409_et_reprise200'],
            migration097_sha256=hashlib.sha256((recette.BACK/'097_verrou_tva_trace_cloture.sql').read_bytes()).hexdigest())
        (ROOT/'.codex-tests/restauration487_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
    finally:
        if ancien is not None:preuve095.write_bytes(ancien)
