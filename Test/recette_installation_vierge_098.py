"""Qualification de la chaîne existante098, exclusivement sur son cluster nonce.

Ce programme n'accepte aucune URL de base existante et ne modifie aucun SQL.
Le socle090 reste inchangé ;091–098 sont appliquées puis rejouées dans l'ordre.
"""
import argparse
from pathlib import Path
from sqlalchemy import text

import recette_installation_vierge_090 as precedent
import recette_installation_vierge_consolidee as socle
from recette_installation_vierge import BACK
from recette_restauration_consolidee_084 import schema, verifier_schema, empreintes_tables
from postgres_isole import verifier_cible_isolee

REPORT = Path(__file__).with_name('rapport_installation_vierge_098.md')
EXTENSIONS = (
    '091_permissions_affectation_resultat.sql', '092_modeles_avances_personnel.sql',
    '093_permissions_parametres_tva.sql', '094_protection_parametres_tva_clotures.sql',
    '095_registre_avances_salaries.sql', '096_verrou_parametres_tva.sql',
    '097_verrou_tva_trace_cloture.sql', '098_verrou_journal_cloture.sql',
)


def lignes(engine, table):
    assert table in ('modeles_ecritures', 'lignes_modele')
    with engine.connect() as c:
        return {r[0]: r[1] for r in c.execute(text(
            f'SELECT id,row_to_json(t)::text FROM {table} t ORDER BY id'))}


def extension(engine, runtime, cible, resultat, appliquer):
    precedent.extension(engine, runtime, cible, resultat, appliquer)
    assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    # Import tardif : le socle a déjà imposé DATABASE_URL=nonce avant tout modèle.
    from test_restauration_runtime_acl_089 import catalogue_acl
    avant = empreintes_tables(engine)
    references = {t: lignes(engine, t) for t in ('modeles_ecritures', 'lignes_modele')}
    for nom in EXTENSIONS:
        appliquer(BACK / nom, 'extensions_091_098')
    apres = empreintes_tables(engine)
    for table, valeurs in avant.items():
        if table not in references:
            assert apres[table] == valeurs, table
    for table in apres.keys() - avant.keys():
        assert apres[table]['nombre'] == 0, table
    for table, existantes in references.items():
        nouvelles = lignes(engine, table)
        assert all(nouvelles[i] == valeur for i, valeur in existantes.items()), table
    # Seul092 ajoute cinq modèles de référence déjà livrés, pas de paie ni pièce.
    assert apres['modeles_ecritures']['nombre'] - avant['modeles_ecritures']['nombre'] == 5
    assert apres['lignes_modele']['nombre'] - avant['lignes_modele']['nombre'] == 10
    structure, droits = schema(engine), catalogue_acl(engine)
    for nom in EXTENSIONS:
        appliquer(BACK / nom, 'rejeu_091_098')
    verifier_schema(schema(engine), structure)
    assert catalogue_acl(engine) == droits
    assert empreintes_tables(engine) == apres
    with runtime.connect() as c:
        assert c.scalar(text('SELECT current_user')) == 'hisabpro'
        assert not c.scalar(text("SELECT has_schema_privilege(current_user,'public','CREATE')"))
        assert c.scalar(text("SELECT has_table_privilege(current_user,'decisions_affectation_resultat','SELECT')"))
        assert c.scalar(text("SELECT has_table_privilege(current_user,'decisions_affectation_resultat','INSERT')"))
        for table in ('audit_actions', 'audit_periodes_comptables', 'liasses_fiscales_archives', 'livres_inventaire_archives'):
            for privilege in ('UPDATE', 'DELETE', 'TRUNCATE'):
                assert not c.scalar(text('SELECT has_table_privilege(current_user,:t,:p)'), {'t': table, 'p': privilege})
        assert c.scalar(text("SELECT has_table_privilege(current_user,'tva_parametres_exercice','SELECT')"))
        assert c.scalar(text("SELECT has_column_privilege(current_user,'tva_parametres_exercice','credit_ouverture','UPDATE')"))
        assert not c.scalar(text("SELECT has_column_privilege(current_user,'tva_parametres_exercice','societe_id','UPDATE')"))
        assert not c.scalar(text("SELECT has_sequence_privilege(current_user,'tva_parametres_exercice_id_seq','UPDATE')"))
        avances = c.scalar(text('SELECT count(*) FROM grh_avances_affectations'))
        assert avances == 0
    assert len({r['fichier'] for r in resultat['appliquees']}) == 89
    assert len(resultat['appliquees']) == 114
    resultat.update({
        '098_rejeu_schema_acl_donnees_sequences_identiques': True,
        '098_historiques_et_modeles_existants_preserves': True,
        '098_ajouts_reference_092': {'modeles_ecritures': 5, 'lignes_modele': 10},
        '098_tables_hors_references_inchangees': len(avant) - 2,
        '098_ddl_sources': list(EXTENSIONS),
        '098_acl_runtime_controlees': True,
        'statut': '89_SQL_et_25_rejeux_valides_chaine098_runtime_partiel',
    })
    resultat['zero_final']['grh_avances_affectations'] = avances


def executer(rapport=REPORT):
    code = socle.executer(controle_complementaire=extension, rapport=rapport)
    p = Path(rapport)
    contenu = p.read_text(encoding='utf8').replace(
        '# Installation vierge consolidee : experience isolee',
        '# Installation vierge consolidée098 — expérience isolée')
    contenu = contenu.replace('Test/recette_installation_vierge_consolidee.py`', 'Test/recette_installation_vierge_098.py`')
    contenu += '''\n## Portée098\n
La chaîne090 est conservée et complétée par091–098, puis les huit scripts sont
rejoués dans le même ordre.89SQL distincts,25rejeux :114exécutions si tous les
contrôles réussissent. Les réparations historiques065/067/068/070 ne sont pas
exécutées. Les cinq modèles de référence092 et leurs dix lignes sont les seuls
ajouts attendus aux données ; aucun modèle existant n'est écrasé et aucun
mouvement comptable, salarié ou bulletin n'est créé. Le rejeu préserve schéma,
séquences, ACL et empreintes de toutes les tables.

Ce programme qualifie une installation dans son propre cluster éphémère. Il
ne migre aucune base existante, n'accepte aucune URL externe et ne démontre
ni un déploiement utilisateur, ni une restauration, ni une recette complète.
RH/paie restent différées : leurs fichiers SQL déjà livrés ne sont pas modifiés.
'''
    p.write_text(contenu, encoding='utf8')
    return code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rapport', type=Path, default=REPORT)
    raise SystemExit(executer(parser.parse_args().rapport))
