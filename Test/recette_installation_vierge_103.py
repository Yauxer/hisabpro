"""Installation103 exclusivement sur cluster jetable marqué ; aucune URL externe."""
from pathlib import Path
from sqlalchemy import text
import recette_installation_vierge_102 as precedent
import recette_installation_vierge_consolidee as socle
from recette_installation_vierge import BACK
from recette_restauration_consolidee_084 import empreintes_tables,schema,verifier_schema
from postgres_isole import verifier_cible_isolee

REPORT=Path(__file__).with_name('rapport_installation_vierge_103.md')
SQL='103_ras_rapprochements_versement.sql'
TABLES=('ras_tva_rapprochements','ras_tva_rapprochement_retraits')


def extension(engine,runtime,cible,resultat,appliquer):
    precedent.extension(engine,runtime,cible,resultat,appliquer)
    from test_restauration_runtime_acl_089 import catalogue_acl
    assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
    avant=empreintes_tables(engine);acl=catalogue_acl(engine)
    appliquer(BACK/SQL,'extension_103')
    apres=empreintes_tables(engine);structure=schema(engine);droits=catalogue_acl(engine)
    assert set(apres)-set(avant)==set(TABLES) and all(apres[t]==v for t,v in avant.items())
    assert all(apres[t]['nombre']==0 for t in TABLES)
    assert all(all(v in droits[k] for v in vs) for k,vs in acl.items())
    appliquer(BACK/SQL,'rejeu_103')
    verifier_schema(schema(engine),structure)
    assert empreintes_tables(engine)==apres and catalogue_acl(engine)==droits
    with runtime.connect() as db:
        assert db.scalar(text('SELECT current_user'))=='hisabpro'
        for t in TABLES:
            for p in ('SELECT','INSERT'):assert db.scalar(text('SELECT has_table_privilege(current_user,:t,:p)'),{'t':t,'p':p})
            for p in ('UPDATE','DELETE','TRUNCATE'):assert not db.scalar(text('SELECT has_table_privilege(current_user,:t,:p)'),{'t':t,'p':p})
            assert db.scalar(text("SELECT has_sequence_privilege(current_user,:s,'USAGE')"),{'s':t+'_id_seq'})
            assert not db.scalar(text("SELECT has_sequence_privilege(current_user,:s,'UPDATE')"),{'s':t+'_id_seq'})
    with engine.connect() as db:
        triggers=db.execute(text("SELECT tgname,tgenabled FROM pg_trigger WHERE tgrelid IN (to_regclass('ras_tva_rapprochements'),to_regclass('ras_tva_rapprochement_retraits')) AND NOT tgisinternal")).all()
        assert len(triggers)==6 and all(r.tgenabled=='O' for r in triggers)
        assert not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE p.oid=to_regprocedure('hisabpro_ras_rapprochement_liens()') AND a.grantee=0 AND a.privilege_type='EXECUTE')"))
    resultat['zero_final'].update({t:0 for t in TABLES})
    resultat.update({'103_tables_anterieures_preservees':len(avant),'103_triggers_actifs':6,
        '103_rejeu_schema_acl_donnees_sequences_identiques':True,
        'statut':'94_SQL_et_30_rejeux_valides_chaine103_runtime_partiel'})


def executer(rapport=REPORT):
    return socle.executer(controle_complementaire=extension,rapport=rapport)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rapport',type=Path,default=REPORT)
    args=p.parse_args()
    raise SystemExit(executer(args.rapport))
