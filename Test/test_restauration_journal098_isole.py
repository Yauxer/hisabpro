"""Sauvegarde/restauration froide098, gardes et conflit HTTP409 conservés."""
from contextlib import contextmanager
from datetime import date
from pathlib import Path
import hashlib
import json
import httpx
from sqlalchemy import create_engine,text
import test_restauration_justificatifs_acl_isole as recette
from test_restauration_tva097_isole import test_restauration097_fonctions_conflit409_reprise_et_registre as scenario097
from test_avances_salaries_isole import appliquer
from test_consolidation_journal098_isole import fonctions098
from test_journal_cloture_concurrente_isole import donnees, executer_annule, VERROU
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def test_restauration098_journal_conflit_et_reprise(monkeypatch,tmp_path):
    application=recette.application_isolee; lancer=recette.lancer_cible; memo={}
    preuve097=ROOT/'.codex-tests/restauration487_preuve.json'
    ancien=preuve097.read_bytes() if preuve097.exists() else None
    @contextmanager
    def source098(**kwargs):
        with application(**kwargs) as app:
            for nom in ['096_verrou_parametres_tva.sql','097_verrou_tva_trace_cloture.sql','098_verrou_journal_cloture.sql']:
                appliquer(app,nom)
            memo['fonctions']=fonctions098(app['engine']); assert len(memo['fonctions'])==3
            yield app
    def cible098(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        engine=create_engine(c['url']); proc=None
        try:
            assert fonctions098(engine)==memo['fonctions']
            proc,url,log=lancer(c,uploads)
            with engine.connect() as db:
                sid,email=db.execute(text("SELECT e.societe_id,u.email FROM employes e JOIN utilisateurs u ON u.societe_id=e.societe_id WHERE e.nom='Salarié restauration fictive095' AND u.role='admin'")).one()
            annee=date.today().year
            with httpx.Client(base_url=url) as api:
                recette.connecter(api,email)
                with engine.connect() as db:
                    tx=db.begin()
                    try:
                        db.execute(text(VERROU),{'s':sid,'a':annee})
                        r=api.post('/api/ecritures',json=donnees(annee))
                        assert r.status_code==409,r.text
                    finally:tx.rollback()
                sql="INSERT INTO ecritures(societe_id,exercice,date,journal,libelle,est_validee) VALUES(:s,:a,:d,'OD','Fictif restauration098',false)"
                assert executer_annule(engine,sql,{'s':sid,'a':annee,'d':date(annee,12,31)})=='ok'
            memo['conflit409_et_reprise']=True
            return proc,url,log
        except BaseException:
            if proc is not None:recette.arreter_processus_cree(proc)
            raise
        finally:engine.dispose()
    monkeypatch.setattr(recette,'application_isolee',source098)
    monkeypatch.setattr(recette,'lancer_cible',cible098)
    try:
        scenario097(monkeypatch,tmp_path)
        preuve=json.loads(preuve097.read_text(encoding='utf8'))
        preuve.update(extension098=True,trois_fonctions098_identiques=True,
            journal409_et_reprise=memo['conflit409_et_reprise'],
            migration098_sha256=hashlib.sha256((recette.BACK/'098_verrou_journal_cloture.sql').read_bytes()).hexdigest())
        (ROOT/'.codex-tests/restauration490_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
    finally:
        if ancien is not None:preuve097.write_bytes(ancien)
