"""Experience consolidee explicite, sans URL externe ni donnees metier."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import types

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_installation_vierge import BACK, candidats, tables_vides as tables_vides_base

REPORT = Path(__file__).with_name('rapport_installation_vierge_082.md')
COMPLEMENTS = ('074_archives_comptables_immutables.sql', '075_complements_auxiliaires_structure.sql',
              '076_contraintes_etic_archives.sql', '077_permissions_cycle_facturation.sql',
              '078_factures_definitives_suppression.sql', '079_permissions_suppression_brouillons.sql',
              '080_dossiers_employes.sql', '081_grh_absences.sql', '082_paie_referentiels.sql')
CHECKS = {
    'etic_sections_exercice': ('ck_etic_section_code',),
    'liasses_fiscales_archives': ('ck_liasse_archive_sha256',),
    'ligne_auxiliaire_complements': ('ck_ligne_aux_complement_nature',
        'ck_ligne_aux_complement_compte_non_vide', 'ck_ligne_aux_complement_libelle_non_vide'),
    'employes': ('ck_employes_personnes_charge_ir', 'ck_employes_dates'),
    'grh_absences': ('ck_grh_absences_dates', 'ck_grh_absences_type', 'ck_grh_absences_statut'),
    'grh_absence_evenements': ('ck_grh_absence_evenements_statut',),
    'paie_referentiel_versions': ('ck_paie_referentiel_version', 'ck_paie_referentiel_annee',
                                'ck_paie_referentiel_qualification'),
}
TRIGGERS = {
    'livres_inventaire_archives': ('trg_livre_inventaire_immutable', 'trg_livre_inventaire_truncate'),
    'liasse_balances_preparation': ('trg_balance_preparation_immuable', 'trg_balance_preparation_truncate'),
    'ligne_auxiliaire_complements': ('trg_ligne_aux_complements_append_only', 'trg_ligne_aux_complements_no_truncate'),
    'grh_absence_evenements': ('trg_grh_historique_immutable', 'trg_grh_historique_truncate'),
    'paie_referentiel_versions': ('trg_paie_referentiel_immutable', 'trg_paie_referentiel_truncate'),
}


def tables_vides(engine, cible):
    compte = tables_vides_base(engine, cible)
    with engine.connect() as db:
        for nom in ('employes', 'grh_absences', 'grh_absence_evenements', 'paie_referentiel_versions'):
            compte[nom] = db.scalar(text(f'SELECT count(*) FROM {nom}'))
    assert not any(compte.values()), compte
    return compte


def catalogue(engine):
    with engine.connect() as db:
        checks = {table: [dict(row._mapping) for row in db.execute(text(
            'SELECT conname,convalidated,pg_get_constraintdef(oid) AS definition FROM pg_constraint '
            'WHERE conrelid=to_regclass(:table) AND contype=\'c\' ORDER BY conname'), {'table': table})]
            for table in CHECKS}
        triggers = {table: [dict(row._mapping) for row in db.execute(text(
            'SELECT tgname,tgenabled,pg_get_triggerdef(oid) AS definition FROM pg_trigger '
            'WHERE tgrelid=to_regclass(:table) AND NOT tgisinternal ORDER BY tgname'), {'table': table})]
            for table in TRIGGERS}
        uniques_paie = [dict(row._mapping) for row in db.execute(text(
            "SELECT conname,pg_get_constraintdef(oid) AS definition FROM pg_constraint "
            "WHERE conrelid=to_regclass('paie_referentiel_versions') AND contype='u' ORDER BY conname"))]
    assert 'uq_paie_referentiel_version' in {x['conname'] for x in uniques_paie}
    for table, names in CHECKS.items():
        assert set(names) <= {x['conname'] for x in checks[table]}, (table, checks[table])
    for table, names in TRIGGERS.items():
        assert set(names) <= {x['tgname'] for x in triggers[table]}, (table, triggers[table])
        assert all(x['tgenabled'] == 'O' for x in triggers[table])
    return {'checks': checks, 'triggers': triggers, 'uniques_paie': uniques_paie}


def executer(*, controle_complementaire=None, rapport=None):
    """Le défaut reste la recette082 ; une extension explicite utilise sa cible.

    Le callback reçoit les moteurs jetables et l'applicateur déjà protégé.
    Il doit contrôler ses objets supplémentaires ; aucune URL externe acceptée.
    """
    destination = Path(rapport) if rapport is not None else REPORT
    debut = time.monotonic()
    resultat = {'date_utc': datetime.now(timezone.utc).isoformat(), 'statut': 'en_cours',
                'fichier_en_cours': 'socle_ORM', 'erreur': None, 'appliquees': []}
    ancien_url = os.environ.get('DATABASE_URL')
    directory = None
    try:
        with cluster_isole() as cible:
            directory = cible['directory']
            def garde():
                assert verifier_cible_isolee(cible['url'], directory, cible['nonce'])
            garde()
            dotenv = types.ModuleType('dotenv')
            dotenv.load_dotenv = lambda *args, **kwargs: False
            sys.modules['dotenv'] = dotenv
            os.environ['DATABASE_URL'] = cible['url']
            sys.path.insert(0, str(BACK))
            import models
            from database import Base, engine as backend_engine
            assert verifier_cible_isolee(str(backend_engine.url), directory, cible['nonce'])
            engine = create_engine(cible['url'], connect_args={'options': '-c statement_timeout=30000 -c lock_timeout=10000'})
            runtime = None
            try:
                garde()
                with engine.begin() as db:
                    db.execute(text('CREATE ROLE hisabpro NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
                garde()
                Base.metadata.create_all(engine)
                resultat['nombre_tables_orm'] = len(Base.metadata.tables)
                resultat['zero_initial'] = tables_vides(engine, cible)
                def appliquer(fichier, phase):
                    resultat['fichier_en_cours'] = fichier.name
                    garde()
                    tables_vides(engine, cible)
                    raw = engine.raw_connection()
                    try:
                        raw.autocommit = True
                        with raw.cursor() as cursor:
                            cursor.execute(fichier.read_text(encoding='utf-8'))
                    finally:
                        raw.close()
                    resultat['appliquees'].append({'fichier': fichier.name, 'phase': phase,
                        'sha256': hashlib.sha256(fichier.read_bytes()).hexdigest()})
                    (directory / 'installation_registry.json').write_text(
                        json.dumps(resultat['appliquees'], indent=2), encoding='utf-8')
                    tables_vides(engine, cible)
                    print('APPLIQUE ' + fichier.name + ' ' + phase, flush=True)
                for fichier in candidats():
                    appliquer(fichier, 'base_001_073')
                for nom in COMPLEMENTS:
                    appliquer(BACK / nom, 'complements')
                resultat['catalogue'] = catalogue(engine)
                for nom in COMPLEMENTS:
                    appliquer(BACK / nom, 'rejeu_complements')
                assert catalogue(engine) == resultat['catalogue']
                resultat['catalogue_identique_apres_rejeu'] = True
                # LOGIN active uniquement dans ce cluster de test ; aucun GRANT ajoute.
                garde()
                with engine.begin() as db:
                    db.execute(text('ALTER ROLE hisabpro LOGIN'))
                runtime = create_engine(make_url(cible['url']).set(username='hisabpro'))
                garde()
                with runtime.connect() as db:
                    role = db.execute(text('SELECT current_user,session_user,rolcanlogin,rolsuper,rolcreatedb,'
                        'rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user')).one()
                    assert role == ('hisabpro', 'hisabpro', True, False, False, False, False, False)
                    assert not db.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
                    assert db.scalar(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)')) == 0
                    assert db.scalar(text('SELECT count(*) FROM pg_proc WHERE proowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)')) == 0
                    resultat['role_runtime'] = list(role)
                    resultat['runtime_create_public'] = db.scalar(text("SELECT has_schema_privilege(current_user,'public','CREATE')"))
                    resultat['droits_tables'] = [dict(row._mapping) for row in db.execute(text(
                        "SELECT c.relname,has_table_privilege(current_user,c.oid,'SELECT') AS lecture,"
                        "has_table_privilege(current_user,c.oid,'INSERT') AS insertion,"
                        "has_table_privilege(current_user,c.oid,'UPDATE') AS modification,"
                        "has_table_privilege(current_user,c.oid,'DELETE') AS suppression,"
                        "has_table_privilege(current_user,c.oid,'TRUNCATE') AS troncature "
                        "FROM pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relkind='r' ORDER BY c.relname"))]
                    for table in TRIGGERS:
                        for op in ('UPDATE', 'DELETE', 'TRUNCATE'):
                            assert not db.scalar(text('SELECT has_table_privilege(current_user,:table,:op)'), {'table': table, 'op': op})
                    assert db.scalar(text("SELECT has_table_privilege(current_user,'employes','SELECT')"))
                    assert db.scalar(text("SELECT has_table_privilege(current_user,'grh_absences','INSERT')"))
                    assert not db.scalar(text("SELECT has_column_privilege(current_user,'employes','societe_id','UPDATE')"))
                    assert not db.scalar(text("SELECT has_column_privilege(current_user,'grh_absences','employe_id','UPDATE')"))
                    resultat['runtime_grh_colonnes_protegees'] = True
                    assert db.scalar(text("SELECT column_default FROM information_schema.columns WHERE table_schema='public' AND table_name='employes' AND column_name='type_contrat'")) is None
                    resultat['contrat_historique_sans_defaut'] = True
                    for privilege in ('SELECT', 'INSERT'):
                        assert db.scalar(text("SELECT has_table_privilege(current_user,'paie_referentiel_versions',:op)"), {'op': privilege})
                    for privilege in ('USAGE', 'SELECT'):
                        assert db.scalar(text("SELECT has_sequence_privilege(current_user,'paie_referentiel_versions_id_seq',:op)"), {'op': privilege})
                    resultat['runtime_referentiel_lecture_insertion_sequence'] = True
                # TRUNCATE doit etre bloque meme sur des archives encore vides.
                for table in TRIGGERS:
                    for connexion, code in ((engine, '23514' if table in ('ligne_auxiliaire_complements', 'grh_absence_evenements', 'paie_referentiel_versions') else 'P0001'), (runtime, '42501')):
                        garde()
                        with connexion.connect() as db:
                            try:
                                db.execute(text(f'TRUNCATE {table}'))
                            except DBAPIError as exc:
                                assert exc.orig.pgcode == code, exc
                                db.rollback()
                            else:
                                db.rollback()
                                raise AssertionError('TRUNCATE autorise : ' + table)
                resultat['truncate_vides_refuses_owner_runtime'] = True
                resultat['zero_final'] = tables_vides(engine, cible)
                resultat['statut'] = f'{len(candidats())+len(COMPLEMENTS)}_SQL_et_{len(COMPLEMENTS)}_rejeux_valides_installation_runtime_incomplete'
                if controle_complementaire is not None:
                    controle_complementaire(engine, runtime, cible, resultat, appliquer)
            except Exception as exc:
                resultat['statut'] = 'echec_arret_premier_controle'
                resultat['erreur'] = (str(exc) or repr(exc))[:6000]
                print('ECHEC ' + resultat['fichier_en_cours'] + ': ' + resultat['erreur'][:2500], flush=True)
            finally:
                if runtime is not None:
                    runtime.dispose()
                engine.dispose()
                backend_engine.dispose()
    finally:
        if ancien_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = ancien_url
        resultat['duree_secondes'] = round(time.monotonic() - debut, 2)
        resultat['cluster_supprime'] = directory is not None and not directory.exists()
        manque = [x['relname'] for x in resultat.get('droits_tables', []) if not x['lecture'] or not x['insertion']]
        destination.write_text('# Installation vierge consolidee : experience isolee\n\n'
            + 'Commande : `hisabpro-backend/.venv/Scripts/python.exe Test/recette_installation_vierge_consolidee.py`.\n\n'
            + 'Le rapport176 reste historique et inchange. Socle ORM puis64SQL candidats001-073, '
            + 'puis074 à082 et rejeu de ces neuf compléments uniquement. Les rapports176/209 restent historiques. Aucune URL externe acceptee, '
            + 'aucun .env lu, aucun traitement065/067/068/070 ni init/seedpaie. '
            + 'Tables metier verifiees vides avant/apres chaque SQL. Registre SHA local supprime avec le cluster.\n\n'
            + '## Resultats exacts\n\n```json\n' + json.dumps(resultat, ensure_ascii=False, indent=2) + '\n```\n\n'
            + '## Limites de provisionnement\n\n'
            + 'LOGIN active uniquement dans le cluster pour prouver une connexion applicative non proprietaire ; '
            + 'aucun droit global ou GRANT invente. Les permissions insuffisantes observees restent a definir '
            + 'dans un manifeste exhaustif audite : tables sans SELECT ou INSERT = ' + ', '.join(manque) + '.\n\n'
            + 'La matrice brute ci-dessus ne justifie pas des droits CRUD sur toutes les tables : '
            + 'audits et archives demandent des flux controles. Aucun parcours utilisateur ni installation '
            + 'production valide ici ; etat runtime incomplet explicite. Les controles NOT VALID nouveaux '
            + 'ne constituent pas une validation des donnees historiques. Les taux sociaux restent globaux '
            + 'et leurs anciennes permissions ne sont pas modifiees par cette recette ;082 ajoute seulement '
            + 'des versions de provenance propres aux societes.\n', encoding='utf-8')
        print(json.dumps({'statut': resultat['statut'], 'duree': resultat['duree_secondes'],
            'appliquees': len(resultat['appliquees']), 'cluster_supprime': resultat['cluster_supprime'],
            'erreur': resultat['erreur']}, ensure_ascii=True), flush=True)
    return 1 if resultat['erreur'] is not None else 0


if __name__ == '__main__':
    raise SystemExit(executer())
