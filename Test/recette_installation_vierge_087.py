"""Installation à vide087, extension explicite sans connexion externe acceptée."""
import argparse
import hashlib
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

import recette_installation_vierge_084 as precedent
from recette_restauration_consolidee_084 import schema, verifier_schema, empreintes_tables
from postgres_isole import verifier_cible_isolee

REPORT = Path(__file__).with_name('rapport_installation_vierge_087.md')
EXTENSIONS = ('085_permissions_documents_commerciaux.sql',
              '086_permissions_acomptes_avoirs.sql', '087_permissions_banque_releves.sql')
CRUD = ('devis', 'lignes_devis', 'bons_commande', 'lignes_bon_commande',
        'bons_livraison', 'lignes_bon_livraison', 'rapprochement_lignes')
SIU = ('acomptes', 'avoirs', 'comptes_bancaires')
TABLES = (*CRUD, *SIU, 'lignes_avoir')
OPS = ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE')


def droits(engine):
    with engine.connect() as db:
        tables = db.execute(text("SELECT relname FROM pg_class WHERE relnamespace='public'::regnamespace "
                                 "AND relkind IN ('r','p') ORDER BY relname")).scalars().all()
        acl = {t: {op: db.scalar(text("SELECT has_table_privilege('hisabpro',:t,:op)"),
                                {'t': t, 'op': op}) for op in OPS} for t in tables}
        sequences = dict(db.execute(text("SELECT relname,has_sequence_privilege('hisabpro',oid,'UPDATE') "
            "FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='S'")).all())
    return acl, sequences


def extension(engine, runtime, cible, resultat, appliquer):
    precedent.extension(engine, runtime, cible, resultat, appliquer)
    def garde():
        assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    def vides():
        garde()
        counts = precedent.socle.tables_vides(engine, cible)
        with engine.connect() as db:
            counts.update({t: db.scalar(text(f'SELECT count(*) FROM public.{t}'))
                           for t in (*precedent.TABLES, *TABLES)})
        assert len(counts) == 36 and not any(counts.values()), counts
        return counts
    garde()
    initial, donnees = schema(engine), empreintes_tables(engine)
    avant, sequences_avant = droits(engine)
    assert all(not avant[t]['INSERT'] for t in TABLES)
    resultat['permissions_087_absentes_avant'] = True
    for nom in EXTENSIONS:
        appliquer(precedent.socle.BACK / nom, 'permissions_explicites_085_087')
        vides()
    apres, sequences_apres = droits(engine)
    assert sequences_apres == sequences_avant
    assert all(apres[t] == avant[t] for t in avant if t not in TABLES)
    for table in TABLES:
        assert apres[table] == {'SELECT': True, 'INSERT': True,
            'UPDATE': table != 'lignes_avoir', 'DELETE': table in CRUD, 'TRUNCATE': False}, table
    with runtime.connect() as db:
        sequences = {t: db.scalar(text("SELECT pg_get_serial_sequence(:t,'id')"), {'t': t}) for t in TABLES}
        for seq in sequences.values():
            for op in ('USAGE', 'SELECT'):
                assert db.scalar(text('SELECT has_sequence_privilege(current_user,:seq,:op)'),
                                 {'seq': seq, 'op': op})
    for nom in EXTENSIONS:
        appliquer(precedent.socle.BACK / nom, 'rejeu_permissions_085_087')
        vides()
    assert droits(engine) == (apres, sequences_apres)
    verifier_schema(schema(engine), initial)
    assert empreintes_tables(engine) == donnees
    resultat['schema_donnees_sequences_inchanges'] = True
    resultat['acl_hors_onze_tables_inchangees'] = True
    resultat['update_sequences_inchanges'] = True
    resultat['droits_087'] = {t: apres[t] for t in TABLES}
    resultat['sequences_087_usage_select'] = sequences
    resultat['permissions_087_identiques_apres_rejeu'] = True
    refus = []
    def refuser(sql, code):
        garde()
        with runtime.connect() as db:
            try:
                db.execute(text(sql))
                db.commit()
            except DBAPIError as exc:
                assert exc.orig.pgcode == code, (sql, str(exc))
                db.rollback()
            else:
                raise AssertionError('Instruction autorisée : ' + sql)
        refus.append({'sql': sql, 'code': code})
        vides()
    for table in TABLES:
        refuser(f'TRUNCATE public.{table}', '42501')
    for table in (*SIU, 'lignes_avoir'):
        refuser(f'DELETE FROM public.{table}', '42501')
    refuser('UPDATE public.lignes_avoir SET quantite=quantite', '42501')
    refuser('CREATE TABLE public.interdit_087(id integer)', '42501')
    assert len(refus) == 17
    assert empreintes_tables(engine) == donnees
    resultat['refus_permissions_087'] = refus
    resultat['zero_final'] = vides()
    # Actualiser la matrice brute du socle : ne pas laisser les anciens droits
    # pré085 être présentés comme les droits finaux de l'installation087.
    resultat['droits_tables_avant_085_087'] = resultat['droits_tables']
    champs = dict(zip(OPS, ('lecture','insertion','modification','suppression','troncature')))
    resultat['droits_tables'] = [{'relname': t, **{champs[op]: val for op, val in row.items()}}
                                for t, row in apres.items()]
    assert len({r['fichier'] for r in resultat['appliquees']}) == 78
    assert len(resultat['appliquees']) == 92
    assert all(hashlib.sha256((precedent.socle.BACK/r['fichier']).read_bytes()).hexdigest() == r['sha256']
               for r in resultat['appliquees'])
    resultat['statut'] = '78_SQL_et_14_rejeux_valides_runtime_cible_non_exhaustif'


def executer(rapport=REPORT):
    code = precedent.socle.executer(controle_complementaire=extension, rapport=rapport)
    p = Path(rapport)
    contenu = p.read_text(encoding='utf-8')
    contenu = contenu.replace('# Installation vierge consolidee : experience isolee',
                              '# Installation vierge consolidée087 — expérience isolée')
    contenu = contenu.replace('Test/recette_installation_vierge_consolidee.py`',
                              'Test/recette_installation_vierge_087.py`')
    contenu = contenu.replace('## Resultats exacts',
        'Extension explicite après le socle082 :083/084 et leur rejeu, puis085/086/087 '
        'et leur rejeu. La matrice de droits principale est actualisée après087.\n\n## Resultats exacts')
    contenu += '''\n## Portée de l'extension087\n
78 SQL distincts,14 rejeux,36 tables métier contrôlées vides si le statut final réussit.
Les trois migrations de permissions ne changent ni schéma, données ou états des séquences.
Le banc historique082 et son extension084 restent inchangés avec leur rapport propre.
Les droits hors des onze tables ciblées et les UPDATE de séquences hérités restent identiques.
Aucun CREATE/TRUNCATE ou nouveau SETVAL accordé. Les droits des traces035/045 ne sont pas retirés.
Les parcours sous LOGIN applicatif sont des preuves séparées436–442 ;aucune recette humaine validée.
Cet outil n'accepte aucune URL externe et n'est pas une migration de base existante.
Une restauration avec tous les rôles/ACL et le provisionnement de tous les modules restent à qualifier.
Les permissions absentes ne justifient jamais un GRANT ALL global. Aucune base réelle utilisée.\n'''
    p.write_text(contenu, encoding='utf-8')
    return code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rapport', type=Path, default=REPORT)
    args = parser.parse_args()
    raise SystemExit(executer(args.rapport))
