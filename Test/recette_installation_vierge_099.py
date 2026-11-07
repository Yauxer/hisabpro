"""Chaîne099 sur son seul cluster nonce ; aucune URL externe acceptée."""
import argparse
from pathlib import Path
from sqlalchemy import text
import recette_installation_vierge_098 as precedent
import recette_installation_vierge_consolidee as socle
from recette_installation_vierge import BACK
from recette_restauration_consolidee_084 import schema, verifier_schema, empreintes_tables
from postgres_isole import verifier_cible_isolee

REPORT = Path(__file__).with_name('rapport_installation_vierge_099.md')
SQL = '099_ras_tva_details.sql'


def extension(engine, runtime, cible, resultat, appliquer):
    precedent.extension(engine, runtime, cible, resultat, appliquer)
    assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    from test_restauration_runtime_acl_089 import catalogue_acl
    avant = empreintes_tables(engine)
    appliquer(BACK/SQL, 'extension_099')
    apres = empreintes_tables(engine)
    assert all(apres[t] == contenu for t,contenu in avant.items())
    assert set(apres)-set(avant) == {'ras_tva_reglement_details'}
    assert apres['ras_tva_reglement_details']['nombre'] == 0
    structure, droits = schema(engine), catalogue_acl(engine)
    appliquer(BACK/SQL, 'rejeu_099')
    verifier_schema(schema(engine), structure)
    assert catalogue_acl(engine) == droits
    assert empreintes_tables(engine) == apres
    with runtime.connect() as c:
        assert c.scalar(text('SELECT current_user')) == 'hisabpro'
        for privilege in ('SELECT','INSERT'):
            assert c.scalar(text("SELECT has_table_privilege(current_user,'ras_tva_reglement_details',:p)"), {'p':privilege})
        for privilege in ('UPDATE','DELETE','TRUNCATE'):
            assert not c.scalar(text("SELECT has_table_privilege(current_user,'ras_tva_reglement_details',:p)"), {'p':privilege})
        assert c.scalar(text("SELECT has_function_privilege(current_user,'hisabpro_ras_tva_details_liens()','EXECUTE')"))
        assert not c.scalar(text("SELECT has_schema_privilege(current_user,'public','CREATE')"))
    with engine.connect() as c:
        assert not c.scalar(text("""SELECT EXISTS(SELECT 1 FROM pg_proc p
            CROSS JOIN LATERAL aclexplode(p.proacl) a
            WHERE p.proname='hisabpro_ras_tva_details_liens' AND a.grantee=0 AND a.privilege_type='EXECUTE')"""))
    assert len(resultat['appliquees']) == 116
    assert len({r['fichier'] for r in resultat['appliquees']}) == 90
    resultat['zero_final']['ras_tva_reglement_details'] = 0
    resultat.update({
        '099_rejeu_schema_acl_donnees_sequences_identiques': True,
        '099_tables_anterieures_preservees': len(avant),
        '099_acl_runtime_controlees': True,
        'statut': '90_SQL_et_26_rejeux_valides_chaine099_runtime_partiel',
    })


def executer(rapport=REPORT):
    code = socle.executer(controle_complementaire=extension, rapport=rapport)
    p = Path(rapport)
    contenu = p.read_text(encoding='utf-8').replace(
        '# Installation vierge consolidee : experience isolee',
        '# Installation vierge consolidée099 — expérience isolée')
    contenu += '''\n## Portée099\n
Chaîne098 existante conservée, puis099 appliquée et rejouée :90SQL distincts,
26rejeux,116exécutions. Les données de toutes les tables antérieures sont
conservées ; la nouvelle table de détails RAS TVA reste vide. Schéma,
séquences et ACL identiques au rejeu. LOGIN limité :SELECT/INSERT uniquement,
sans droit de création de schéma ni modification des dossiers. Aucune ancienne
migration ou donnée comptable réelle modifiée. Les seuls ajouts de référence
sont ceux déjà qualifiés dans098, sans nouveau développement RH/paie.

Ce programme n'accepte aucune URL externe et ne qualifie pas une migration
de production. L'administrateur doit vérifier sa propre installation après
sauvegarde. Le traitement déclaratif des retenues reste partiel.
'''
    p.write_text(contenu,encoding='utf-8')
    return code


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rapport',type=Path,default=REPORT)
    raise SystemExit(executer(parser.parse_args().rapport))
