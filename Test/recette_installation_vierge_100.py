"""Chaîne100, cluster nonce exclusivement ; aucune URL de base externe acceptée."""
import argparse
from pathlib import Path
from sqlalchemy import text
import recette_installation_vierge_099 as precedent
import recette_installation_vierge_consolidee as socle
from recette_installation_vierge import BACK
from recette_restauration_consolidee_084 import schema,verifier_schema,empreintes_tables
from postgres_isole import verifier_cible_isolee

REPORT=Path(__file__).with_name('rapport_installation_vierge_100.md')
SQL='100_reprises_provisions.sql'
TABLES=('reprises_provisions','reprises_provisions_annulations')
FONCTIONS=('hisabpro_reprise_piece_protegee(integer)','hisabpro_reprise_liens()',
    'hisabpro_reprise_annulation_liens()','hisabpro_reprise_journal_protection()')


def extension(engine,runtime,cible,resultat,appliquer):
    precedent.extension(engine,runtime,cible,resultat,appliquer)
    assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
    # Import applicatif seulement après initialisation du cluster nonce par le socle.
    from test_restauration_runtime_acl_089 import catalogue_acl
    avant=empreintes_tables(engine);anciens_droits=catalogue_acl(engine)
    appliquer(BACK/SQL,'extension_100')
    apres=empreintes_tables(engine)
    assert set(apres)-set(avant)==set(TABLES)
    assert all(apres[t]==v for t,v in avant.items())
    assert all(apres[t]['nombre']==0 for t in TABLES)
    structure,droits=schema(engine),catalogue_acl(engine)
    assert all(all(v in droits[k] for v in vs) for k,vs in anciens_droits.items())
    appliquer(BACK/SQL,'rejeu_100')
    verifier_schema(schema(engine),structure)
    assert catalogue_acl(engine)==droits and empreintes_tables(engine)==apres
    with runtime.connect() as db:
        assert db.scalar(text('SELECT current_user'))=='hisabpro'
        for t in TABLES:
            for p in ('SELECT','INSERT'):assert db.scalar(text('SELECT has_table_privilege(current_user,:t,:p)'),{'t':t,'p':p})
            for p in ('UPDATE','DELETE','TRUNCATE'):assert not db.scalar(text('SELECT has_table_privilege(current_user,:t,:p)'),{'t':t,'p':p})
        for fonction in FONCTIONS:
            assert db.scalar(text('SELECT has_function_privilege(current_user,:f,\'EXECUTE\')'),{'f':fonction})
        for sequence in ('reprises_provisions_id_seq','reprises_provisions_annulations_id_seq'):
            assert db.scalar(text("SELECT has_sequence_privilege(current_user,:s,'USAGE')"),{'s':sequence})
        assert not db.scalar(text("SELECT has_schema_privilege(current_user,'public','CREATE')"))
        assert not db.scalar(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)'))
    with engine.connect() as db:
        assert not db.scalar(text("""SELECT EXISTS(SELECT 1 FROM pg_proc p
            CROSS JOIN LATERAL aclexplode(p.proacl) a
            WHERE p.proname LIKE 'hisabpro_reprise_%' AND a.grantee=0 AND a.privilege_type='EXECUTE')"""))
        triggers=db.execute(text("""SELECT t.tgname,t.tgenabled FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
            WHERE t.tgname LIKE 'trg_reprise_%' AND NOT t.tgisinternal ORDER BY t.tgname""")).all()
        assert len(triggers)==9 and all(r.tgenabled=='O' for r in triggers)
    assert len(apres)==77 and len(resultat['appliquees'])==118
    assert len({r['fichier'] for r in resultat['appliquees']})==91
    resultat['zero_final'].update({t:0 for t in TABLES})
    resultat.update({'100_tables_anterieures_preservees':len(avant),
        '100_rejeu_schema_acl_donnees_sequences_identiques':True,'100_acl_runtime_et_public_controlees':True,
        '100_triggers_actifs':len(triggers),'statut':'91_SQL_et_27_rejeux_valides_chaine100_runtime_partiel'})


def executer(rapport=REPORT):
    code=socle.executer(controle_complementaire=extension,rapport=rapport)
    p=Path(rapport);t=p.read_text(encoding='utf8')
    t=t.replace('# Installation vierge consolidee : experience isolee','# Installation vierge consolidée100 — expérience isolée',1)
    t+='''\n## Portée100\n
Socle099 conservé, puis100 appliquée/rejouée :91SQL distincts,27rejeux,
118exécutions.77tables au total ; les75anciennes conservent leurs données,
deux registres vides ajoutés. Schéma/ACL/séquences/données identiques au rejeu.
LOGIN hisabpro non propriétaire :SELECT/INSERT sur registres, pas UPDATE/DELETE/
TRUNCATE/CREATEschéma ; fonctions non exécutables parPUBLIC,9triggers actifs.
Les migrations historiques et les rapports099 restent intacts. Les données de
référence du socle restent celles déjà qualifiées, aucune nouvelle évolutionRH.

Le programme refuse toute URL externe ; aucun.env ou PostgreSQL utilisateur.
Ce banc ne vaut pas migration de production, validation fiscale ou recette
humaine. La restauration des77tables et la reprise des flux sont couvertes
séparément par615/617/621. L’installation réelle100 reste une étape distincte.
'''
    p.write_text(t,encoding='utf8');return code


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rapport',type=Path,default=REPORT)
    raise SystemExit(executer(p.parse_args().rapport))
