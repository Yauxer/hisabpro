"""Installation102 exclusivement sur cluster nonce appartenant au banc, sans URL externe."""
import argparse
from pathlib import Path
from sqlalchemy import text
import recette_installation_vierge_100 as precedent
import recette_installation_vierge_consolidee as socle
from recette_installation_vierge import BACK
from recette_restauration_consolidee_084 import schema,verifier_schema,empreintes_tables
from postgres_isole import verifier_cible_isolee

REPORT=Path(__file__).with_name('rapport_installation_vierge_102.md')
SQLS=('101_societes_liees.sql','102_factures_correspondantes.sql')
TABLES=('societes_liees','societes_liees_retraits','factures_correspondantes')
FONCTIONS=('hisabpro_societes_liees_controle()','hisabpro_factures_correspondantes_controle()')


def extension(engine,runtime,cible,resultat,appliquer):
    precedent.extension(engine,runtime,cible,resultat,appliquer)
    assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
    from test_restauration_runtime_acl_089 import catalogue_acl
    avant=empreintes_tables(engine);acl=catalogue_acl(engine)
    for nom in SQLS:appliquer(BACK/nom,'extension_102')
    apres=empreintes_tables(engine);structure=schema(engine);droits=catalogue_acl(engine)
    assert set(apres)-set(avant)==set(TABLES) and all(apres[t]==v for t,v in avant.items())
    assert all(apres[t]['nombre']==0 for t in TABLES)
    assert all(all(v in droits[k] for v in vs) for k,vs in acl.items())
    for nom in SQLS:appliquer(BACK/nom,'rejeu_102')
    verifier_schema(schema(engine),structure)
    assert empreintes_tables(engine)==apres and catalogue_acl(engine)==droits
    with runtime.connect() as db:
        assert db.scalar(text('SELECT current_user'))=='hisabpro'
        for t in TABLES:
            for p in ('SELECT','INSERT'):assert db.scalar(text('SELECT has_table_privilege(current_user,:t,:p)'),{'t':t,'p':p})
            for p in ('UPDATE','DELETE','TRUNCATE'):assert not db.scalar(text('SELECT has_table_privilege(current_user,:t,:p)'),{'t':t,'p':p})
            assert db.scalar(text("SELECT has_sequence_privilege(current_user,:s,'USAGE')"),{'s':t+'_id_seq'})
        for f in FONCTIONS:assert db.scalar(text("SELECT has_function_privilege(current_user,:f,'EXECUTE')"),{'f':f})
        assert not db.scalar(text("SELECT has_schema_privilege(current_user,'public','CREATE')"))
        assert not db.scalar(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)'))
    with engine.connect() as db:
        for f in FONCTIONS:
            assert not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE p.oid=to_regprocedure(:f) AND a.grantee=0 AND a.privilege_type='EXECUTE')"),{'f':f})
        ts=db.execute(text("SELECT t.tgname,t.tgenabled FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE c.relname IN ('societes_liees','societes_liees_retraits','factures_correspondantes') AND NOT t.tgisinternal ORDER BY t.tgname")).all()
        assert len(ts)==9 and all(x.tgenabled=='O' for x in ts)
    assert len(apres)==80 and len(resultat['appliquees'])==122 and len({r['fichier'] for r in resultat['appliquees']})==93
    resultat['zero_final'].update({t:0 for t in TABLES})
    resultat.update({'102_tables_anterieures_preservees':77,'102_rejeu_schema_acl_donnees_sequences_identiques':True,'102_acl_runtime_public_sequences_controlees':True,'102_triggers_actifs':9,'statut':'93_SQL_et_29_rejeux_valides_chaine102_runtime_partiel'})


def executer(rapport=REPORT):
    code=socle.executer(controle_complementaire=extension,rapport=rapport)
    p=Path(rapport);t=p.read_text(encoding='utf8').replace('# Installation vierge consolidee : experience isolee','# Installation vierge consolidée102 — expérience isolée',1)
    t+='''

## Portée102

Socle100 inchangé, puis101 et102 appliquées et rejouées :93SQL distincts,
29rejeux,122exécutions,80tables ;77anciennes préservées, trois nouveaux
registres vides. Schéma/ACL/séquences/données identiques au rejeu. LOGIN
hisabpro non propriétaire :SELECT/INSERT, séquences USAGE, pas UPDATE/DELETE/
TRUNCATE/CREATEschéma ; PUBLIC ne peut exécuter les nouvelles fonctions.
Neuf nouveaux triggers actifs. Aucune société liée ou facture fictive injectée
par le CLI ; les parcours API/Edge et la restauration80tables sont qualifiés
séparément dans le rapport635. Les anciennes migrations/CLI/rapports restent
inchangés. Ce programme refuse toute URL externe et ne migre pas la base active.
Installation réelle, recette humaine et production non validées. RH/paie différées.
'''
    p.write_text(t,encoding='utf8');return code


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rapport',type=Path,default=REPORT)
    raise SystemExit(executer(p.parse_args().rapport))
