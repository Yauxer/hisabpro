"""Restauration du schéma consolidé084 sur deux PostgreSQL nonce distincts.

Ne reçoit aucune connexion externe et ne conserve aucun dump hors du bac.
Le socle reste une installation à vide, avec les référentiels du SQL existant.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

import recette_installation_vierge_084 as installation
from postgres_isole import cluster_isole, verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ops.postgres_sauvegarde import sauvegarder, restaurer_isole

REPORT = Path(__file__).with_name('rapport_restauration_consolidee_084.md')


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    default=str).encode('utf-8')).hexdigest()


def schema(engine):
    queries = {
        'colonnes': "SELECT c.relname,a.attnum,a.attname,format_type(a.atttypid,a.atttypmod),"
            "a.attnotnull,pg_get_expr(d.adbin,d.adrelid) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid "
            "LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum "
            "WHERE n.nspname='public' AND c.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped "
            "ORDER BY c.relname,a.attnum",
        'contraintes': "SELECT c.relname,k.conname,k.contype,k.convalidated,pg_get_constraintdef(k.oid) "
            "FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' "
            "ORDER BY c.relname,k.conname",
        'index': "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' "
            "ORDER BY tablename,indexname",
        'triggers': "SELECT c.relname,t.tgname,t.tgenabled,pg_get_triggerdef(t.oid) "
            "FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND NOT t.tgisinternal "
            "ORDER BY c.relname,t.tgname",
        'fonctions': "SELECT p.proname,pg_get_function_identity_arguments(p.oid),pg_get_functiondef(p.oid),"
            "r.rolname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
            "JOIN pg_roles r ON r.oid=p.proowner WHERE n.nspname='public' AND p.prokind IN ('f','p') "
            "ORDER BY p.proname,pg_get_function_identity_arguments(p.oid)",
        'sequences': "SELECT sequencename,data_type,start_value,min_value,max_value,increment_by,cycle,cache_size "
            "FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename",
    }
    with engine.connect() as db:
        result = {name: [list(row) for row in db.execute(text(sql))] for name, sql in queries.items()}
        # pg_dump/restore peut redistribuer les casts d'un ARRAY dans un
        # CHECK (varchar[]::text[] devient ARRAY[varchar::text,...]).
        # Reparser chaque CHECK avec PostgreSQL sur une table TEMP vide
        # fournit la même représentation logique, sans retirer les casts,
        # les prédicats ni NOT VALID. Les autres contraintes restent exactes.
        result['checks_reparses'] = []
        for table in sorted({row[0] for row in result['contraintes'] if row[2] == 'c'}):
            quote = '"'+table.replace('"','""')+'"'
            db.execute(text(f'CREATE TEMP TABLE recette_schema_check (LIKE public.{quote}) ON COMMIT DROP'))
            for row in result['contraintes']:
                if row[0] == table and row[2] == 'c':
                    nom = '"'+row[1].replace('"','""')+'"'
                    brut = row[4]
                    # Aucun paramètre DBAPI :les définitions peuvent contenir
                    # des littéraux '%' ou les format('%I') des SQL existants.
                    with db.connection.driver_connection.cursor() as cursor:
                        cursor.execute(f'ALTER TABLE pg_temp.recette_schema_check ADD CONSTRAINT {nom} {brut}')
                    row[4] = db.scalar(text('SELECT pg_get_constraintdef(oid) FROM pg_constraint '
                        "WHERE conrelid='pg_temp.recette_schema_check'::regclass AND conname=:nom"), {'nom': row[1]})
                    result['checks_reparses'].append([table, row[1], brut != row[4]])
            db.execute(text('DROP TABLE pg_temp.recette_schema_check'))
        # Les prédicats d'index partiels subissent le même réarrangement
        # varchar[]::text[] lors de pg_restore. Reparser seulement leur
        # expression avec PostgreSQL ;conserver exactement clés,méthode,
        # unicité et options. Aucun index n'est ignoré dans la comparaison.
        result['index_reparses'] = []
        for row in result['index']:
            if ' WHERE ' not in row[2]:
                continue
            prefixe, predicat = row[2].split(' WHERE ', 1)
            quote = '"'+row[0].replace('"','""')+'"'
            db.execute(text(f'CREATE TEMP TABLE recette_schema_index (LIKE public.{quote}) ON COMMIT DROP'))
            with db.connection.driver_connection.cursor() as cursor:
                cursor.execute('ALTER TABLE pg_temp.recette_schema_index ADD CONSTRAINT recette_predicat CHECK ('+predicat+')')
            definition = db.scalar(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='pg_temp.recette_schema_index'::regclass AND conname='recette_predicat'"))
            assert definition.startswith('CHECK ')
            normalise = prefixe+' WHERE '+definition[len('CHECK '):]
            result['index_reparses'].append([row[0],row[1],row[2]!=normalise])
            row[2] = normalise
            db.execute(text('DROP TABLE pg_temp.recette_schema_index'))
        result['etats_sequences'] = []
        for seq in result['sequences']:
            nom = '"'+seq[0].replace('"','""')+'"'
            row = db.execute(text(f'SELECT last_value,is_called FROM public.{nom}')).one()
            result['etats_sequences'].append([seq[0], *row])
    return result


def empreintes_tables(engine):
    with engine.connect() as db:
        tables = db.execute(text("SELECT c.relname FROM pg_class c JOIN pg_namespace n "
            "ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p') "
            "ORDER BY c.relname")).scalars().all()
        result = {}
        for table in tables:
            nom = '"'+table.replace('"','""')+'"'
            rows = db.execute(text(f'SELECT row_to_json(t)::text FROM public.{nom} t '
                                   'ORDER BY row_to_json(t)::text')).scalars().all()
            result[table] = {'nombre': len(rows), 'sha256': sha(rows)}
    return result


def verifier_schema(observe, attendu):
    for nom, rows in attendu.items():
        if nom in {'checks_reparses', 'index_reparses'}:
            continue  # Diagnostic de sérialisation, pas définition du contrôle.
        if observe[nom] != rows:
            difference = next(((a,b) for a,b in zip(observe[nom],rows) if a != b),
                              ('longueur', (len(observe[nom]),len(rows))))
            raise AssertionError(f'Schéma différent :{nom} ;première différence :{difference}')


def restauration(engine, runtime_source, source, resultat, appliquer):
    installation.extension(engine, runtime_source, source, resultat, appliquer)
    avant_schema, avant_tables = schema(engine), empreintes_tables(engine)
    preuve = {'cible_supprimee': False, 'erreur': None}
    resultat['restauration'] = preuve
    cible = None
    try:
        with cluster_isole() as cible:
            def garde():
                for c in (source, cible):
                    assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
            garde()
            assert source['nonce'] != cible['nonce'] and source['port'] != cible['port']
            preuve['clusters_distincts'] = True
            archive = sauvegarder(source['url'], source['directory']/'consolidee084.dump', source['bin'])
            preuve['taille_dump'] = archive.stat().st_size
            preuve['sha256_dump'] = hashlib.sha256(archive.read_bytes()).hexdigest()
            garde()
            restaurer_isole(cible['url'], archive, cible['bin'], cible['directory'], cible['nonce'])
            restauree = create_engine(cible['url'])
            runtime = None
            try:
                apres_schema = schema(restauree)
                verifier_schema(apres_schema, avant_schema)
                assert empreintes_tables(restauree) == avant_tables
                preuve['schema_et_donnees_identiques'] = True
                preuve['tables'] = avant_tables
                preuve['schema'] = {nom: {'nombre': len(rows), 'sha256': sha(rows)}
                                   for nom, rows in avant_schema.items() if nom != 'checks_reparses'}
                preuve['normalisation_checks_source'] = avant_schema['checks_reparses']
                preuve['normalisation_checks_cible'] = apres_schema['checks_reparses']
                with restauree.begin() as db:
                    assert not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro')"))
                    db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB '
                                    'NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
                runtime = create_engine(make_url(cible['url']).set(username='hisabpro'))
                with runtime.connect() as db:
                    role = db.execute(text('SELECT current_user,session_user,rolcanlogin,rolsuper,rolcreatedb,'
                        'rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user')).one()
                    assert tuple(role) == ('hisabpro','hisabpro',True,False,False,False,False,False)
                    assert not db.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
                    assert not db.scalar(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)'))
                    assert not db.scalar(text('SELECT count(*) FROM pg_proc WHERE proowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)'))
                    preuve['role_runtime'] = list(role)
                    preuve['droits_absents_avant_rejeu'] = {
                        table: db.scalar(text('SELECT has_table_privilege(current_user,:table,\'SELECT\')'),
                                         {'table': table}) for table in installation.TABLES}
                assert not any(preuve['droits_absents_avant_rejeu'].values())
                for nom in installation.EXTENSIONS:
                    garde()
                    with restauree.begin() as db:
                        with db.connection.driver_connection.cursor() as cursor:
                            cursor.execute((installation.socle.BACK/nom).read_text(encoding='utf-8'))
                assert installation.catalogue(restauree) == resultat['catalogue_extension']
                assert installation.droits(runtime) == resultat['droits_extension']
                preuve['droits_083_084_restitues'] = True
                preuve['refus'] = []
                for connexion, sql, code, nom in (
                    (restauree,'TRUNCATE ras_reglement_captures,ras_reglement_annulations','23514','conservation_ras'),
                    (restauree,'TRUNCATE rapprochement_ventilations','23514','conservation_ventilation'),
                    (runtime,'UPDATE ras_reglement_captures SET id=id','42501','runtime_ras_update'),
                    (runtime,'DELETE FROM ras_reglement_annulations','42501','runtime_ras_delete'),
                    (runtime,'TRUNCATE rapprochement_ventilations','42501','runtime_ventilation_truncate'),
                    (runtime,'CREATE TABLE public.restauration_interdite(id integer)','42501','runtime_ddl')):
                    garde()
                    with connexion.connect() as db:
                        try:
                            db.execute(text(sql)); db.commit()
                        except DBAPIError as exc:
                            assert exc.orig.pgcode == code, (nom, str(exc))
                            db.rollback()
                        else:
                            raise AssertionError('Opération autorisée :'+nom)
                    preuve['refus'].append({'controle': nom, 'code': code})
                try:
                    garde()
                    restaurer_isole(cible['url'], archive, cible['bin'], cible['directory'], cible['nonce'])
                except ValueError as exc:
                    assert 'doit être vide' in str(exc)
                    preuve['cible_non_vide_refusee'] = True
                else:
                    raise AssertionError('Restauration sur cible non vide autorisée')
                verifier_schema(schema(restauree), avant_schema)
                verifier_schema(schema(engine), avant_schema)
                assert empreintes_tables(restauree) == avant_tables == empreintes_tables(engine)
                preuve['source_et_cible_inchangees'] = True
            finally:
                if runtime is not None:
                    runtime.dispose()
                restauree.dispose()
    except Exception as exc:
        preuve['erreur'] = (str(exc) or repr(exc))[:3000]
        raise
    finally:
        preuve['cible_supprimee'] = cible is not None and not cible['directory'].exists()
    assert preuve['cible_supprimee']
    resultat['statut'] = 'installation_084_restauree_schema_donnees_acl_limitees_valides'


def executer(rapport=REPORT):
    code = installation.socle.executer(controle_complementaire=restauration, rapport=rapport)
    p = Path(rapport)
    contenu = p.read_text(encoding='utf-8').replace(
        '# Installation vierge consolidee : experience isolee',
        '# Sauvegarde et restauration de l’installation consolidée084')
    contenu = contenu.replace('Test/recette_installation_vierge_consolidee.py`',
                              'Test/recette_restauration_consolidee_084.py`')
    contenu += '''\n## Périmètre exact\n
Socle082, extension explicite083/084 puis dump/restauration sur un second cluster nonce vide.
Comparaison de toutes les tables publiques, colonnes, contraintes, index, fonctions,
déclencheurs et séquences. Pour les CHECK, PostgreSQL reparse la définition dans
une table TEMP vide avant comparaison :le dump peut redistribuer les casts ARRAY
sans changer le prédicat. Aucune suppression de cast ou de NOT VALID ;les deux
diagnostics de normalisation sont conservés. Les autres définitions restent exactes.
Le dump ne restitue pas les rôles/ACL ;seuls les droits083/084
sont rétablis par leurs SQL existants. Aucune initialisation d’un rôle de production.
Cette recette est à vide pour les tables métier contrôlées par433 ;les référentiels
présents dans le SQL existant sont conservés et comparés. Elle complète les tests
séparés de restauration083/084avec pièces ;elle ne les remplace pas.
Fichiers externes, tous les droits applicatifs et reprise de production restent distincts.
Les deux clusters et le dump temporaire sont supprimés par les contextes du banc.\n'''
    p.write_text(contenu, encoding='utf-8')
    return code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rapport', type=Path, default=REPORT)
    args = parser.parse_args()
    raise SystemExit(executer(args.rapport))
