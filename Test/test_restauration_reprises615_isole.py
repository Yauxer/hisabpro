"""Dump/restauration100 : registre, pièces, ACL, séquences, rejeu ; deux nonce."""
from contextlib import contextmanager
from datetime import date
from pathlib import Path
import json
import httpx
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
import pytest
import test_restauration_justificatifs_acl_isole as recette
from test_reprises_provisions615_isole import dotation,corps,demande,PATH
from test_permissions_tva_runtime_isole import donnees_metier
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def test_615_restauration_registre_annulation_reservation_et_acl(monkeypatch,tmp_path):
    application_orig,client_orig,lancer_orig=recette.application_isolee,recette.client,recette.lancer_cible
    preparer_orig=recette.preparer091
    memo={};preuve={'erreur':None}
    historique=ROOT/'.codex-tests/restauration452_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None

    def preparer100(engine,c):
        preparer_orig(engine,c)
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        for nom in sorted(recette.BACK.glob('*.sql')):
            if nom.name[:3].isdigit() and 92<=int(nom.name[:3])<=100:
                raw=engine.raw_connection()
                try:
                    raw.autocommit=True
                    with raw.cursor() as cur:cur.execute(nom.read_text(encoding='utf8'))
                finally:raw.close()

    @contextmanager
    def application100(**kw):
        kw['preparer_runtime']=preparer100
        with application_orig(**kw) as app:yield app

    def client_source(app):
        api,email,password=client_orig(app)
        if not memo:
            a=dotation(api);aid=a['id'];jour=date.today().isoformat()
            c=corps(api,aid,demande(date=jour))
            s=recette.ok(api.post(f'{PATH}/{aid}',json=c));r=s['reprises'][0]
            recette.ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider"))
            s=recette.ok(api.post(f"{PATH}/{aid}/{r['id']}/annuler",json={'date':jour,'motif':'Annulation fictive restore615'}))
            recette.ok(api.post(f"/api/ecritures/{s['reprises'][0]['inverse_id']}/valider"))
            c2=corps(api,aid,demande('200',date=jour))
            s=recette.ok(api.post(f'{PATH}/{aid}',json=c2))
            assert s['disponible']=='800.00' and s['reservations_brouillons']=='200.00'
            memo.update(email=email,password=password,aid=aid,corps=c,dossier=s)
        return api,email,password

    def cible(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        proc,url,log=lancer_orig(c,uploads)
        runtime=create_engine(make_url(c['url']).set(username='hisabpro'))
        try:
            with httpx.Client(base_url=url) as api:
                recette.connecter(api,memo['email'],memo['password'])
                avant=donnees_metier({'engine':runtime})
                assert recette.ok(api.get(f"{PATH}/{memo['aid']}"))==memo['dossier']
                assert recette.ok(api.post(f"{PATH}/{memo['aid']}",json=memo['corps']))==memo['dossier']
                assert api.post(f"{PATH}/{memo['aid']}",json={**memo['corps'],'montant':'1'}).status_code==409
                assert donnees_metier({'engine':runtime})==avant
            with runtime.connect() as db:
                for sql in ['UPDATE reprises_provisions SET montant=1','DELETE FROM reprises_provisions_annulations']:
                    with pytest.raises(DBAPIError) as exc:db.execute(text(sql))
                    assert exc.value.orig.pgcode=='42501';db.rollback()
            preuve['registre_restitue_rejeu_sans_mutation_et_acl']=True
            return proc,url,log
        except BaseException:
            recette.arreter_processus_cree(proc);raise
        finally:runtime.dispose()

    monkeypatch.setattr(recette,'application_isolee',application100)
    monkeypatch.setattr(recette,'client',client_source)
    monkeypatch.setattr(recette,'lancer_cible',cible)
    try:
        recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert p['erreur'] is None and p['tables']==77
        assert p['source_preservee'] and p['cibles_supprimees'] and p['schema_donnees_acl_sequences_identiques']
        preuve.update(p,reprises=2,annulations=1)
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration615_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
