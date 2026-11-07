"""Sauvegarde froide et reprise du registre renseigné, deux clusters nonce."""
from pathlib import Path
from contextlib import closing
import hashlib
import json
import httpx
import test_restauration_justificatifs_acl_isole as recette
from postgres_isole import verifier_cible_isolee
from test_avances_salaries_isole import employe,mouvement,affecter,PATH
from test_multi_societes_runtime_isole import ok
from test_ras_lecture_conservation import client

ROOT=Path(__file__).resolve().parents[1]


def test_restauration095_registre_historique_soldes_et_reprise(monkeypatch,tmp_path):
    preparer=recette.preparer091
    enrichir=recette._affecter_perte_fictive
    lancer=recette.lancer_cible
    preuve={}
    def preparer095(engine,cluster):
        assert verifier_cible_isolee(cluster['url'],cluster['directory'],cluster['nonce'])
        preparer(engine,cluster)
        raw=engine.raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:
                for nom in ('092_modeles_avances_personnel.sql','093_permissions_parametres_tva.sql',
                            '094_protection_parametres_tva_clotures.sql','095_registre_avances_salaries.sql'):
                    cur.execute((recette.BACK/nom).read_text(encoding='utf8'))
        finally:raw.close()
    def enrichir095(app):
        enrichir(app)
        api,email,password=client(app)
        with closing(api):
            p=employe(api,'Salarié restauration fictive095')
            _,d=mouvement(api,900);_,c=mouvement(api,300,credit=True);_,reste=mouvement(api,100,credit=True)
            affecter(api,p,d);ancien=affecter(api,p,c)['id']
            ok(api.post(PATH+f'/{ancien}/annuler',json={'motif':'Correction fictive095'}));affecter(api,p,c)
            attendu=ok(api.get(PATH));assert attendu['soldes'][0]['solde']==600 and len(attendu['historique'])==3
            preuve.update(email=email,password=password,employe=p,reste=reste,attendu=attendu)
    def lancer095(cluster,uploads):
        proc,url,log=lancer(cluster,uploads)
        # Lire puis poursuivre via le même LOGIN non propriétaire sur la copie.
        try:
            with httpx.Client(base_url=url) as api:
                recette.connecter(api,preuve['email'],preuve['password'])
                assert ok(api.get(PATH))==preuve['attendu']
                nouveau=affecter(api,preuve['employe'],preuve['reste'])['id']
                assert nouveau>max(a['id'] for a in preuve['attendu']['historique'])
                r=ok(api.get(PATH));assert r['soldes'][0]['solde']==500 and r['non_affectes']==0
                assert len(r['historique'])==4 and len([a for a in r['historique'] if a['annule_at']])==1
                preuve['registre_restitue_et_repris']=True
            return proc,url,log
        except BaseException:
            recette.arreter_processus_cree(proc);raise
    monkeypatch.setattr(recette,'preparer091',preparer095)
    monkeypatch.setattr(recette,'_affecter_perte_fictive',enrichir095)
    monkeypatch.setattr(recette,'lancer_cible',lancer095)
    # Conserver toutes les assertions de452 : données/schéma/ACL/séquences,
    # quatre pièces, FEC annuel, source au repos, cibles isolées nettoyées.
    recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path)
    p=json.loads((ROOT/'.codex-tests/restauration452_preuve.json').read_text(encoding='utf8'))
    p.update(extension095=True,registre_restitue_et_repris=preuve['registre_restitue_et_repris'],
        solde_avant=600,solde_apres_reprise=500,
        migration095_sha256=hashlib.sha256((recette.BACK/'095_registre_avances_salaries.sql').read_bytes()).hexdigest())
    (ROOT/'.codex-tests/restauration482_preuve.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
