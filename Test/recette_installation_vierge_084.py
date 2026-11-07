"""Extension explicite082→083→084, exclusivement sur un cluster nonce neuf.

Aucune URL, aucun seed fiscal, aucune réparation historique. Ce banc contrôle
le schéma et les droits à vide ; les cycles avec pièces restent des tests séparés.
"""
import argparse
import hashlib
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

import recette_installation_vierge_consolidee as socle
from postgres_isole import verifier_cible_isolee

REPORT = Path(__file__).with_name('rapport_installation_vierge_084.md')
EXTENSIONS = ('083_ras_reglements.sql', '084_rapprochement_ventilations.sql')
TABLES = ('ras_reglement_captures', 'ras_reglement_annulations', 'rapprochement_ventilations')
TRIGGERS = {
    'ras_reglement_captures': ('trg_ras_immutable', 'trg_ras_truncate', 'trg_ras_liens'),
    'ras_reglement_annulations': ('trg_ras_immutable', 'trg_ras_truncate', 'trg_ras_liens'),
    'ecritures': ('trg_ras_ledger_lie',),
    'lignes_ecriture': ('trg_ras_ligne_liee',),
    'rapprochement_ventilations': ('trg_hisabpro_rapprochement_ventilation',
        'trg_hisabpro_ventilation_commit', 'trg_hisabpro_no_truncate_ventilation'),
    'rapprochement_lignes': ('trg_hisabpro_releve_ventilation',
        'trg_hisabpro_guard_rapprochement_comptable', 'trg_hisabpro_rapprochement_exercice_cloture'),
}


def catalogue(engine):
    with engine.connect() as db:
        contraintes = {table: [dict(r._mapping) for r in db.execute(text(
            "SELECT conname,contype,pg_get_constraintdef(oid) AS definition "
            "FROM pg_constraint WHERE conrelid=to_regclass(:table) ORDER BY conname"), {'table': table})]
            for table in TABLES}
        triggers = {table: [dict(r._mapping) for r in db.execute(text(
            "SELECT tgname,tgenabled,tgdeferrable,tginitdeferred,pg_get_triggerdef(oid) AS definition "
            "FROM pg_trigger WHERE tgrelid=to_regclass(:table) AND NOT tgisinternal ORDER BY tgname"),
            {'table': table})] for table in TRIGGERS}
        fonction = dict(db.execute(text("SELECT p.prosecdef,p.proconfig,r.rolname AS proprietaire "
            "FROM pg_proc p JOIN pg_roles r ON r.oid=p.proowner "
            "WHERE p.oid='public.hisabpro_ras_trace_liens()'::regprocedure")).one()._mapping)
    for table, names in TRIGGERS.items():
        assert set(names) <= {r['tgname'] for r in triggers[table]}, table
        assert all(r['tgenabled'] == 'O' for r in triggers[table]), table
    commit = next(r for r in triggers['rapprochement_ventilations']
                  if r['tgname'] == 'trg_hisabpro_ventilation_commit')
    assert commit['tgdeferrable'] and commit['tginitdeferred']
    assert fonction['prosecdef'] and fonction['proprietaire'] != 'hisabpro'
    assert fonction['proconfig'] == ['search_path=pg_catalog, public']
    assert all(any(r['contype'] == 'f' for r in rows) for rows in contraintes.values())
    return {'contraintes': contraintes, 'triggers': triggers, 'fonction_liens_ras': fonction}


def droits(runtime):
    with runtime.connect() as db:
        result = {table: {op: db.scalar(text('SELECT has_table_privilege(current_user,:table,:op)'),
            {'table': table, 'op': op}) for op in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE')}
            for table in TABLES}
        sequences = {table: {op: db.scalar(text('SELECT has_sequence_privilege(current_user,:seq,:op)'),
            {'seq': table+'_id_seq', 'op': op}) for op in ('USAGE','SELECT','UPDATE')}
            for table in TABLES[:2]}
    for table, acl in result.items():
        assert acl == {'SELECT': True, 'INSERT': True, 'UPDATE': False,
                       'DELETE': table == 'rapprochement_ventilations', 'TRUNCATE': False}, (table, acl)
    assert all(v == {'USAGE': True,'SELECT': True,'UPDATE': False} for v in sequences.values())
    return {'tables': result, 'sequences': sequences}


def extension(engine, runtime, cible, resultat, appliquer):
    def garde():
        assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    def vides():
        garde()
        counts = socle.tables_vides(engine, cible)
        with engine.connect() as db:
            counts.update({t: db.scalar(text(f'SELECT count(*) FROM public.{t}')) for t in TABLES})
        assert len(counts) == 25 and not any(counts.values()), counts
        return counts
    garde()
    with engine.connect() as db:
        assert all(db.scalar(text('SELECT to_regclass(:table)'), {'table': table}) is None for table in TABLES)
    resultat['extensions_absentes_avant_application'] = True
    for nom in EXTENSIONS:
        appliquer(socle.BACK / nom, 'extension_explicite_083_084')
    resultat['zero_extension_initial'] = vides()
    initial = catalogue(engine)
    acl = droits(runtime)
    for nom in EXTENSIONS:
        appliquer(socle.BACK / nom, 'rejeu_extensions_083_084')
        vides()
    assert catalogue(engine) == initial and droits(runtime) == acl
    resultat['catalogue_extension'] = initial
    resultat['droits_extension'] = acl
    resultat['extension_identique_apres_rejeu'] = True
    refus = []
    def refuser(connexion, sql, code, controle):
        garde()
        with connexion.connect() as db:
            try:
                db.execute(text(sql))
                db.commit()
            except DBAPIError as exc:
                assert exc.orig.pgcode == code, (controle, str(exc))
                db.rollback()
            else:
                raise AssertionError('Instruction autorisée : '+controle)
        refus.append({'controle': controle, 'code': code})
        vides()
    for table in TABLES:
        # La capture est référencée par l'annulation : inclure les deux
        # évite que le contrôle FK masque le déclencheur de conservation.
        cible_truncate = ('public.ras_reglement_captures,public.ras_reglement_annulations'
                          if table == 'ras_reglement_captures' else 'public.'+table)
        refuser(engine, f'TRUNCATE {cible_truncate}', '23514', 'owner_truncate_'+table)
        refuser(runtime, f'TRUNCATE public.{table}', '42501', 'runtime_truncate_'+table)
        refuser(runtime, f'UPDATE public.{table} SET societe_id=1', '42501', 'runtime_update_'+table)
    for table in TABLES[:2]:
        refuser(runtime, f'DELETE FROM public.{table}', '42501', 'runtime_delete_'+table)
        refuser(runtime, f"SELECT setval('public.{table}_id_seq',1,false)", '42501', 'runtime_setval_'+table)
    refuser(runtime, 'CREATE TABLE public.recette_084_interdite(id integer)', '42501', 'runtime_ddl')
    refuser(runtime, "INSERT INTO public.ras_reglement_captures "
        "(societe_id,reglement_id,facture_id,ecriture_id,montant,date_operation,reference,compte_destination,created_by) "
        "VALUES(1,1,1,1,10,'2026-01-01','FICTIF-REFUSE','3453',1)", '23514', 'capture_acteur_absent')
    refuser(runtime, "INSERT INTO public.ras_reglement_annulations "
        "(capture_id,societe_id,ecriture_id,date_operation,motif,created_by) "
        "VALUES(1,1,1,'2026-01-01','FICTIF-REFUSE',1)", '23514', 'annulation_acteur_absent')
    refuser(runtime, "INSERT INTO public.rapprochement_ventilations "
        "(releve_id,ecriture_ligne_id,societe_id,operation_id) "
        "VALUES(1,1,1,'00000000-0000-0000-0000-000000000001')", '23514', 'ventilation_liens_absents')
    resultat['refus_extension'] = refus
    resultat['zero_final'] = vides()
    noms = {x['fichier'] for x in resultat['appliquees']}
    assert len(noms) == 75 and len(resultat['appliquees']) == 86
    for row in resultat['appliquees']:
        assert hashlib.sha256((socle.BACK / row['fichier']).read_bytes()).hexdigest() == row['sha256']
    resultat['statut'] = '75_SQL_et_11_rejeux_valides_installation_runtime_incomplete'


def executer(rapport=REPORT):
    code = socle.executer(controle_complementaire=extension, rapport=rapport)
    p = Path(rapport)
    contenu = p.read_text(encoding='utf-8')
    contenu = contenu.replace('# Installation vierge consolidee : experience isolee',
        '# Installation vierge consolidée084 — expérience isolée')
    contenu = contenu.replace('Test/recette_installation_vierge_consolidee.py`',
                              'Test/recette_installation_vierge_084.py`')
    contenu = contenu.replace('## Resultats exacts',
        'Extension explicite :083 puis084, puis leur rejeu ;les résultats ci-dessous '
        'couvrent le socle et cette extension.\n\n## Resultats exacts')
    contenu += '''\n## Extension explicite084\n
Après le socle082, application manuelle explicite de083 puis084 et rejeu dans ce même ordre.
Le banc historique082 conserve son comportement par défaut et son propre rapport.
Les champs JSON donnent les objets, droits et refus réellement observés ;un échec arrête la recette.
La recette à vide ne remplace pas les cycles avec documents ni une migration de base existante.
Aucun bootstrap, SQL métier, rôle de production ou donnée réelle modifié.
La matrice exhaustive de droits de tous les modules reste à qualifier.\n'''
    p.write_text(contenu, encoding='utf-8')
    return code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rapport', type=Path, default=REPORT)
    args = parser.parse_args()
    raise SystemExit(executer(args.rapport))
