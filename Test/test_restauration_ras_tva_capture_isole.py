"""Restauration099 : captures actives/annulées et rejeu HTTP, deux clusters nonce."""
from contextlib import contextmanager
from pathlib import Path
from datetime import date
import json
import httpx
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
import pytest
import test_restauration_justificatifs_acl_isole as recette
from test_ras_tva_capture_isole import preparer, paiement, capturer
from test_permissions_tva_runtime_isole import donnees_metier
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def situation(api, rids):
    resultat=[]
    for rid in rids:
        resultat.append((recette.ok(api.get(f'/api/reglements/{rid}/ras-tva')),
            recette.ok(api.get(f'/api/reglements/{rid}/ras'))))
    return resultat


def test_restauration099_dossiers_actif_annule_acl_et_rejeu_identiques(monkeypatch,tmp_path):
    application_orig=recette.application_isolee
    client_orig=recette.client
    lancer_orig=recette.lancer_cible
    preparer_orig=recette.preparer091
    memo,preuve={}, {'erreur':None}
    ancien=ROOT/'.codex-tests/restauration452_preuve.json'
    historique=ancien.read_bytes() if ancien.exists() else None

    def preparer099(engine,c):
        preparer_orig(engine,c)
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        for nom in sorted(recette.BACK.glob('09*.sql')):
            if 92<=int(nom.name[:3])<=99:
                raw=engine.raw_connection()
                try:
                    raw.autocommit=True
                    with raw.cursor() as cur:cur.execute(nom.read_text(encoding='utf-8'))
                finally:raw.close()

    @contextmanager
    def application099(**kwargs):
        kwargs['preparer_runtime']=preparer099
        with application_orig(**kwargs) as app:yield app

    def client_ras(app):
        api,email,password=client_orig(app)
        if not memo:
            f,r1=preparer(api)
            c1,p1=capturer(api,r1)
            recette.ok(api.post(f"/api/ecritures/{c1['capture']['ecriture_id']}/valider"))
            r2=paiement(api,f,'525.00');c2,p2=capturer(api,r2)
            recette.ok(api.post(f"/api/ecritures/{c2['capture']['ecriture_id']}/valider"))
            recette.ok(api.post(f"/api/reglements/{r2['id']}/annuler",json={
                'motif':'Annulation fictive avant sauvegarde575','date_annulation':date.today().isoformat()}))
            rids=[r1['id'],r2['id']]
            avant=donnees_metier(app)
            dossiers=situation(api,rids)
            assert dossiers[0][1]['captures'][0]['annulation_id'] is None
            assert dossiers[1][1]['captures'][0]['annulation_id'] is not None
            tva=api.get('/api/tva/declaration',params={'exercice':date.today().year})
            assert tva.status_code==409
            assert donnees_metier(app)==avant
            memo.update(email=email,password=password,rids=rids,dossiers=dossiers,corps=[p1,p2],tva=tva.json())
        return api,email,password

    def cible_ras(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        proc,url,log=lancer_orig(c,uploads)
        engine=create_engine(c['url'])
        try:
            with httpx.Client(base_url=url) as api:
                recette.connecter(api,memo['email'],memo['password'])
                avant=donnees_metier({'engine':engine})
                assert situation(api,memo['rids'])==memo['dossiers']
                replay=recette.ok(api.post(f"/api/reglements/{memo['rids'][0]}/ras-tva",json=memo['corps'][0]))
                assert replay['dossier']==memo['dossiers'][0][0]['dossier']
                assert api.post(f"/api/reglements/{memo['rids'][1]}/ras-tva",json=memo['corps'][1]).status_code==409
                tva=api.get('/api/tva/declaration',params={'exercice':date.today().year})
                assert tva.status_code==409 and tva.json()==memo['tva']
                assert donnees_metier({'engine':engine})==avant
            with engine.connect() as db:
                with pytest.raises(DBAPIError) as erreur:
                    db.execute(text('UPDATE ras_tva_reglement_details SET dossier=dossier'))
                assert erreur.value.orig.pgcode=='23514'
                db.rollback()
            assert donnees_metier({'engine':engine})==avant
            preuve['dossiers_restitues_et_rejeu_sans_mutation']=True
            preuve['garde_tva_et_immutabilite_restituees']=True
            return proc,url,log
        except BaseException:
            recette.arreter_processus_cree(proc)
            raise
        finally:engine.dispose()

    monkeypatch.setattr(recette,'application_isolee',application099)
    monkeypatch.setattr(recette,'client',client_ras)
    monkeypatch.setattr(recette,'lancer_cible',cible_ras)
    try:
        recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path)
        p=json.loads(ancien.read_text(encoding='utf-8'))
        assert p['erreur'] is None and p['source_preservee'] and p['cibles_supprimees']
        assert p['tables']==75 and p['schema_donnees_acl_sequences_identiques']
        preuve.update(tables=75,source_preservee=True,cibles_supprimees=True,
            schema_donnees_acl_sequences_identiques=True,dossiers=2)
    except BaseException as exc:
        preuve['erreur']=repr(exc)
        raise
    finally:
        (ROOT/'.codex-tests/restauration575_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf-8')
        if historique is not None:ancien.write_bytes(historique)
