"""Installation089 explicite, exclusivement dans un PostgreSQL nonce neuf."""
import argparse
import hashlib
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

import recette_installation_vierge_087 as precedent
from recette_restauration_consolidee_084 import schema, verifier_schema, empreintes_tables
from postgres_isole import verifier_cible_isolee

REPORT = Path(__file__).with_name('rapport_installation_vierge_089.md')
EXTENSIONS = ('088_permissions_cycle_annuel.sql', '089_lettrage_identite_auxiliaire.sql')
TABLES = ('clotures_exercice','bareme_ir','taux_cotisations','deductions_ir')


def extension(engine, runtime, cible, resultat, appliquer):
    precedent.extension(engine, runtime, cible, resultat, appliquer)
    def garde():
        assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
    garde()
    initial, donnees = schema(engine), empreintes_tables(engine)
    avant, seq_avant = precedent.droits(engine)
    appliquer(precedent.precedent.socle.BACK/EXTENSIONS[0], 'permissions_annuelles_088')
    apres088, seq088 = precedent.droits(engine)
    assert seq088 == seq_avant
    assert all(apres088[t] == avant[t] for t in avant if t not in TABLES)
    for t in TABLES:
        assert apres088[t] == {'SELECT':True,'INSERT':t=='clotures_exercice',
                              'UPDATE':False,'DELETE':False,'TRUNCATE':False}
    appliquer(precedent.precedent.socle.BACK/EXTENSIONS[1], 'identite_auxiliaire_089')
    assert precedent.droits(engine) == (apres088,seq088)
    observe = schema(engine)
    fonctions_avant = {(r[0],r[1]):r for r in initial['fonctions']}
    fonctions_apres = {(r[0],r[1]):r for r in observe['fonctions']}
    assert fonctions_avant.keys() == fonctions_apres.keys()
    differences = [k for k in fonctions_avant if fonctions_avant[k] != fonctions_apres[k]]
    assert differences == [('hisabpro_guard_lettrage_comptable','')],differences
    assert fonctions_avant[differences[0]][3] == fonctions_apres[differences[0]][3]
    sans_fonctions = {k:v for k,v in initial.items() if k!='fonctions'}
    verifier_schema(observe,sans_fonctions)
    assert empreintes_tables(engine) == donnees
    for nom in EXTENSIONS:
        appliquer(precedent.precedent.socle.BACK/nom, 'rejeu_extensions_088_089')
    verifier_schema(schema(engine),observe)
    assert empreintes_tables(engine) == donnees
    assert precedent.droits(engine) == (apres088,seq088)
    refus=[]
    def refuser(sql):
        garde()
        with runtime.connect() as db:
            try:
                db.execute(text(sql));db.commit()
            except DBAPIError as exc:
                assert exc.orig.pgcode=='42501',(sql,str(exc))
                db.rollback()
            else:
                raise AssertionError('Instruction autorisée :'+sql)
        refus.append(sql)
    for t in TABLES:
        for op in ('UPDATE','DELETE','TRUNCATE'):
            refuser(f'UPDATE {t} SET id=id' if op=='UPDATE' else f'{op} {"FROM " if op=="DELETE" else ""}{t}')
    for t in TABLES[1:]:
        refuser(f'INSERT INTO {t} DEFAULT VALUES')
    refuser('CREATE TABLE public.interdit089(id integer)')
    refuser('ALTER FUNCTION public.hisabpro_guard_lettrage_comptable() OWNER TO hisabpro')
    assert len(refus)==17
    assert empreintes_tables(engine)==donnees
    resultat['refus_088_089']=refus
    resultat['fonction_089_seule_difference_schema']=[list(x) for x in differences]
    resultat['proprietaire_fonction_089_inchange']=True
    resultat['donnees_et_sequences_088_089_inchangees']=True
    resultat['acl_hors_quatre_tables_088_inchangees']=True
    resultat['rejeu_088_089_identique']=True
    resultat['droits_088']={t:apres088[t] for t in TABLES}
    resultat['droits_tables_avant_088_089']=resultat['droits_tables']
    champs=dict(zip(precedent.OPS,('lecture','insertion','modification','suppression','troncature')))
    resultat['droits_tables']=[{'relname':t,**{champs[op]:val for op,val in row.items()}}
                             for t,row in apres088.items()]
    assert len({r['fichier'] for r in resultat['appliquees']})==80
    assert len(resultat['appliquees'])==96
    assert all(hashlib.sha256((precedent.precedent.socle.BACK/r['fichier']).read_bytes()).hexdigest()==r['sha256']
               for r in resultat['appliquees'])
    resultat['statut']='80_SQL_et_16_rejeux_valides_runtime_annuel_partiel'


def executer(rapport=REPORT):
    code=precedent.precedent.socle.executer(controle_complementaire=extension,rapport=rapport)
    p=Path(rapport)
    contenu=p.read_text(encoding='utf-8').replace(
        '# Installation vierge consolidee : experience isolee',
        '# Installation vierge consolidée089 — expérience isolée')
    contenu=contenu.replace('Test/recette_installation_vierge_consolidee.py`',
                            'Test/recette_installation_vierge_089.py`')
    contenu=contenu.replace('## Resultats exacts',
        'Extension explicite084 puis087 puis088/089, avec leurs rejeux. '
        'Les données/états des séquences restent identiques ;la seule fonction '
        'de lettrage évolue en089. La matrice de droits principale est finale089.\n\n## Resultats exacts')
    contenu+='''\n## Portée089\n
80 SQL distincts,16 rejeux et36 tables métier vides si le statut final réussit.
Les contrôles087 de schéma inchangé portent uniquement sur085–087 ;089 modifie
explicitement une fonction,conserve son propriétaire et tous les autres objets.
Les quatre ACL088 restent fermées et le rejeu préserve les données intégrales.
Les taux sociaux sont seulement lus, sans modification ou qualification nouvelle.
Les anciens bancs082/084/087 restent inchangés. Aucune URL externe acceptée,
aucune base réelle migrée. Ce banc n'est pas un installateur de production.
Les droits des autres modules et la restauration avec ACL restent à qualifier.
Les parcours Edge444 sont distincts de cette expérience à vide.\n'''
    p.write_text(contenu,encoding='utf-8')
    return code


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rapport',type=Path,default=REPORT)
    args=parser.parse_args()
    raise SystemExit(executer(args.rapport))
