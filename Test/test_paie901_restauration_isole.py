"""Restauration native de la paie et de ses snapshots,sur une seconde cible nonce."""
from pathlib import Path
import hashlib,json
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from test_paie893_campagnes_isole import (
    application as application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,salarie,rubrique,gain,simuler)
from test_paie899_social_isole import creer,approuver,ok,preparer,calculer
from test_paie901_ir_annuel_isole import application,application117,application116,F,demande
from services.paie_social_service import lire as lire_social
from services.paie_social_calcul_service import lire as lire_calcul
from services.paie_ir_annuel_service import lire as lire_ir
from postgres_isole import cluster_isole,verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables,schema,verifier_schema
from test_restauration_runtime_acl_089 import catalogue_acl
from ops.postgres_sauvegarde import sauvegarder,restaurer_isole
from services.paie_campagnes_service import lire

R=Path(__file__).resolve().parents[1]

def test_901_restauration_native_ir_social_et_campagne(application,equipe):
    app=application;eq=equipe;s=app['cluster'];assert verifier_cible_isolee(s['url'],s['directory'],s['nonce'])
    eid,rid,q,v,b2=preparer(eq);branche=v['branche_id'];calcul=calculer(eq,eid,q);ir=ok(eq['a'].post(F,json=demande()),201)
    with Session(app['personnel_runtime']) as db: social=lire_social(db,{'id':eq['uid'],'societe_id':eq['sid'],'role':'admin'},branche)
    avant=empreintes_tables(app['engine']);structure=schema(app['engine']);droits=catalogue_acl(app['engine'])
    archive=sauvegarder(s['url'],s['directory']/'paie901.dump',s['bin'],inclure_droits=True)
    with cluster_isole() as cible:
        assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce']) and cible['nonce']!=s['nonce']
        restored=create_engine(cible['url']);runtime=None
        try:
            with restored.begin() as db:db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
            restaurer_isole(cible['url'],archive,cible['bin'],cible['directory'],cible['nonce'],inclure_droits=True)
            verifier_schema(schema(restored),structure)
            assert empreintes_tables(restored)==avant and catalogue_acl(restored)==droits
            # Preuve négative :une vraie modification de prédicat doit être
            # détectée,même après normalisation ;cible nonce uniquement.
            with restored.connect() as db:definition=db.scalar(text("SELECT pg_get_indexdef('public.uq_paie_variable_annuelle'::regclass)"))
            try:
                with restored.begin() as db:
                    db.execute(text('DROP INDEX public.uq_paie_variable_annuelle'))
                    db.execute(text("CREATE UNIQUE INDEX uq_paie_variable_annuelle ON public.paie_variables(societe_id,employe_id,annee,rubrique_id) WHERE periodicite='mensuelle' AND statut IN ('BROUILLON','SOUMIS','APPROUVE')"))
                with pytest.raises(AssertionError,match='index'):verifier_schema(schema(restored),structure)
            finally:
                with restored.begin() as db:
                    db.execute(text('DROP INDEX public.uq_paie_variable_annuelle'))
                    with db.connection.driver_connection.cursor() as cur:cur.execute(definition)
            verifier_schema(schema(restored),structure)
            runtime=create_engine(make_url(cible['url']).set(username='hisabpro'))
            user={'id':eq['uid'],'societe_id':eq['sid'],'role':'admin'}
            with Session(runtime) as db:
                assert db.scalar(text('SELECT current_user'))=='hisabpro'
                assert not db.scalar(text("SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls FROM pg_roles WHERE rolname=current_user"))
                r=lire(db,user,q['id']);assert r['contenu']==q['contenu'] and r['empreinte']==q['empreinte']
                assert lire_social(db,user,branche)==social
                controle=lire_ir(db,user,ir['id']);assert controle['contenu']==ir['contenu'] and controle['empreinte']==ir['empreinte']
                assert controle['contenu']['ir_annuel_arithmetique']=='45400.0000' and controle['contenu']['ir_a_declarer'] is None
                calc=lire_calcul(db,user,calcul['id']);assert calc['contenu']==calcul['contenu'] and calc['empreinte']==calcul['empreinte']
                assert calc['contenu']['totaux']['cotisations_salariales']=='354.00' and calc['contenu']['totaux']['net_a_payer'] is None
                assert r['contenu']['totaux']['brut']=='9800.11' and r['contenu']['totaux']['net_a_payer'] is None
            assert empreintes_tables(restored)==avant and empreintes_tables(app['engine'])==avant
        finally:
            if runtime is not None:runtime.dispose()
            restored.dispose()
    assert not cible['directory'].exists()
    preuve={'donnees_reelles':False,'tables':len(avant),'schema_donnees_sequences_acl_identiques':True,'predicat_index_altere_detecte':True,'role_runtime_limite':True,'snapshot_et_empreinte_restitues':True,'source_inchangee':True,'cible_nonce_supprimee':True,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
    (R/'.codex-tests/paie901_restauration_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
