"""Extension090 àvide :droits secondaires limités,aucune connexion externe."""
import argparse
from pathlib import Path

from sqlalchemy import text

import recette_installation_vierge_089 as precedent
import recette_installation_vierge_consolidee as socle
from recette_installation_vierge import BACK
from recette_installation_vierge_087 import droits
from recette_restauration_consolidee_084 import schema, verifier_schema, empreintes_tables
from postgres_isole import verifier_cible_isolee

REPORT=Path(__file__).with_name('rapport_installation_vierge_090.md')
SQL='090_permissions_multi_societes.sql'


def extension(engine,runtime,cible,resultat,appliquer):
    precedent.extension(engine,runtime,cible,resultat,appliquer)
    assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
    avant_schema=schema(engine);avant_data=empreintes_tables(engine)
    avant,seq_avant=droits(engine)
    for phase in ('permissions_multi_societes090','rejeu_permissions090'):
        appliquer(BACK/SQL,phase)
    apres,seq_apres=droits(engine)
    assert seq_apres==seq_avant
    assert all(avant[t]==apres[t] for t in avant if t!='utilisateurs_societes')
    assert apres['utilisateurs_societes']=={'SELECT':True,'INSERT':True,'UPDATE':False,'DELETE':True,'TRUNCATE':False}
    with runtime.connect() as db:
        colonnes={r[0]:r[1] for r in db.execute(text("SELECT attname,has_column_privilege(current_user,"
            "'utilisateurs_societes',attname,'UPDATE') FROM pg_attribute WHERE "
            "attrelid='utilisateurs_societes'::regclass AND attnum>0 AND NOT attisdropped ORDER BY attname"))}
    assert {k for k,v in colonnes.items() if v}=={'role','actif'}
    verifier_schema(schema(engine),avant_schema)
    assert empreintes_tables(engine)==avant_data
    resultat['090_schema_donnees_sequences_inchanges']=True
    resultat['090_acl_hors_liaisons_inchangees']=True
    resultat['090_update_colonnes']=colonnes
    resultat['droits_tables_avant_090']=resultat['droits_tables']
    correspondance={'SELECT':'lecture','INSERT':'insertion','UPDATE':'modification','DELETE':'suppression','TRUNCATE':'troncature'}
    resultat['droits_tables']=[{'relname':t,**{correspondance[k]:v for k,v in row.items()}} for t,row in apres.items()]
    assert len({r['fichier'] for r in resultat['appliquees']})==81
    assert len(resultat['appliquees'])==98
    resultat['statut']='81_SQL_et_17_rejeux_valides_runtime_cible_partiel'


def executer(rapport=REPORT):
    code=socle.executer(controle_complementaire=extension,rapport=rapport)
    p=Path(rapport)
    contenu=p.read_text(encoding='utf-8').replace('# Installation vierge consolidee : experience isolee',
        '# Installation vierge consolidée090 — expérience isolée').replace(
        'Test/recette_installation_vierge_consolidee.py`','Test/recette_installation_vierge_090.py`')
    contenu=contenu.replace('## Resultats exacts',
        'Extensions084,087,088/089 puis090 et leurs rejeux. La matrice des droits principale '
        'est finale090 ;le détail des deux colonnes modifiables des liaisons figure séparément.\n\n## Resultats exacts')
    contenu+='''\n## Portée090\n
81 SQL distincts,17 rejeux,36 tables métier vides si le statut final réussit.
089 change seulement la fonction de lettrage attendue ;090 ne change aucun
objet de schéma,donnée ou état de séquence. Les seules colonnes UPDATE de
utilisateurs_societes sont role etactif ;aucun UPDATE global ni DELETE de
utilisateurs ajouté. Les droits historiques des séquences sont préservés.
Les anciens bancs restent inchangés. Aucun bootstrap ni migration de base
existante ;outil réservé à son propre cluster nonce,aucune URL externe acceptée.
La restauration090 est vérifiée séparément par le lot447,avec les ACL26colonnes.
Ce banc àvide ne valide ni recette humaine ni production ni tous les modules.\n'''
    p.write_text(contenu,encoding='utf-8')
    return code


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rapport',type=Path,default=REPORT)
    args=parser.parse_args()
    raise SystemExit(executer(args.rapport))
