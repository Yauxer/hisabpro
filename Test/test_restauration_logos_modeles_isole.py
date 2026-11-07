"""Extension du scénario natif452, mêmes oracles plus logos et catalogue092."""
from datetime import date
from io import BytesIO
from pathlib import Path
import json
from pypdf import PdfReader
import test_restauration_justificatifs_acl_isole as recette
from postgres_isole import verifier_cible_isolee
from test_logo_societe import image_data
from test_multi_societes_runtime_isole import ok

ROOT=Path(__file__).resolve().parents[1]


def test_restauration092_logo_catalogue_et_exports_runtime(monkeypatch,tmp_path):
    preparer_origine=recette.preparer091
    client_origine=recette.client
    connecter_origine=recette.connecter
    controles=[];migrations=[];sources=set()
    def preparer092(engine,c):
        preparer_origine(engine,c)
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        raw=engine.raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:
                for nom in ('092_modeles_avances_personnel.sql','093_permissions_parametres_tva.sql'):
                    cur.execute((recette.BACK/nom).read_text(encoding='utf-8'))
                    migrations.append(nom)
        finally:raw.close()
    def client_avec_logo(app):
        api,email,password=client_origine(app)
        sources.add(str(api.base_url))
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data()}))
        return api,email,password
    def connecter_et_controler(api,email,*args,**kwargs):
        valeur=connecter_origine(api,email,*args,**kwargs)
        societe=ok(api.get('/api/societe/moi'))
        if not societe.get('logo_url') and str(api.base_url) in sources:
            # Préparer aussi le logo de la société annuelle fictive AVANT dump.
            # La cible restaurée n'appartient jamais à cet ensemble d'URL.
            societe=ok(api.patch('/api/societe/moi',json={'logo_url':image_data()}))
        assert societe['logo_url']==image_data()
        catalogue=ok(api.get('/api/modeles'))
        assert len(catalogue)==64
        assert sum(m['code'].startswith(('paie_avance_','paie_recuperation_','paie_remboursement_')) for m in catalogue)==5
        ex=date.today().year
        r=api.get('/api/ecritures/reporting/balance/pdf',params={'exercice':ex,'date_from':f'{ex}-01-01','date_to':f'{ex}-12-31'})
        assert r.status_code==200,r.text
        assert len(PdfReader(BytesIO(r.content)).pages[0].images)==1
        controles.append({'api':str(api.base_url),'societe_id':societe['id'],'modeles':64,'image_pdf':True})
        return valeur
    monkeypatch.setattr(recette,'preparer091',preparer092)
    monkeypatch.setattr(recette,'client',client_avec_logo)
    monkeypatch.setattr(recette,'connecter',connecter_et_controler)
    # Schéma,73tables,droits,séquences,4pièces,FEC et repriseAPI : assertions452
    # inchangées. Seuls la préparation et les contrôles supplémentaires diffèrent.
    recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path)
    assert migrations==['092_modeles_avances_personnel.sql','093_permissions_parametres_tva.sql']
    assert len(controles)>=3
    preuve=json.loads((ROOT/'.codex-tests/restauration452_preuve.json').read_text(encoding='utf-8'))
    preuve.update(extension092=True,extension093=True,controles_logo_catalogue=controles)
    (ROOT/'.codex-tests/restauration468_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf-8')
