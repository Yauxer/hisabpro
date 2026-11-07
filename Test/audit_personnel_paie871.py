"""Inventaire Lot 0 sans import applicatif, connexion SQL ni lecture de .env.

Exécution depuis le dépôt : python Test/audit_personnel_paie871.py --output CHEMIN.
Les chemins, symboles et empreintes proviennent des sources ; aucune fonctionnalité
proposée dans le master n'est assimilée à une implémentation.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'
MODELES = {
    'Employe', 'AbsenceRH', 'EvenementAbsenceRH', 'PaieReferentielVersion',
    'BaremeIR', 'TauxCotisation', 'DeductionIR', 'Societe', 'Utilisateur',
    'UtilisateurSociete', 'Ecriture', 'LigneEcriture', 'Reglement',
    'CompteBancaire', 'RapprochementLigne', 'ExerciceComptable',
    'PeriodeComptable', 'CompteSociete', 'AuditAction',
}
FICHIERS = [
    'docs/HISABPRO_PERSONNEL_PAIE_CODEX_MASTER.md',
    'hisabpro-backend/models.py', 'hisabpro-backend/schemas.py',
    'hisabpro-backend/auth.py', 'hisabpro-backend/main.py',
    'hisabpro-backend/routers/employes.py', 'hisabpro-backend/routers/grh.py',
    'hisabpro-backend/routers/avances_salaries.py',
    'hisabpro-backend/routers/ecritures.py', 'hisabpro-backend/routers/commercial.py',
    'hisabpro-backend/routers/banque.py', 'hisabpro-backend/routers/rapprochement.py',
    'hisabpro-backend/routers/parametres.py', 'hisabpro-backend/routers/societe.py',
    'hisabpro-backend/services/paie_service.py',
    'hisabpro-backend/services/paie_referentiel_service.py',
    'hisabpro-backend/services/parametres_paie_service.py',
    'hisabpro-backend/services/grh_bootstrap_service.py',
    'hisabpro-backend/services/exercices_service.py',
    'hisabpro-backend/services/exercice_verrou_service.py',
    'hisabpro-backend/services/auxiliaire_service.py',
    'hisabpro-backend/services/plan_comptable.py',
    'hisabpro-backend/services/grh_registre_pdf.py',
    'hisabpro-backend/attachments.py', 'ops/postgres_sauvegarde.py',
    'hisabpro-backend/080_dossiers_employes.sql',
    'hisabpro-backend/081_grh_absences.sql',
    'hisabpro-backend/082_paie_referentiels.sql',
    'hisabpro-backend/092_modeles_avances_personnel.sql',
    'hisabpro-backend/095_registre_avances_salaries.sql',
    'src/pages/CNSS.jsx', 'src/components/AvancesSalaries.jsx',
    'src/components/Sidebar.jsx', 'src/App.jsx', 'src/data/ModulesContext.jsx',
    'Test/e2e_isole_support.py', 'Test/postgres_isole.py',
    'Test/test_paie_grh_service.py', 'Test/test_paie_grh_postgres.py',
    'Test/test_paie_referentiel_service.py', 'Test/test_paie_referentiel_postgres.py',
    'Test/test_grh_absences_service.py', 'Test/test_grh_absences_postgres.py',
    'Test/test_parametres_paie_finis.py',
    'Test/test_e2e_paie_grh_isole.py', 'Test/test_e2e_paie_referentiel_isole.py',
    'Test/test_e2e_grh_absences_isole.py',
    'Test/test_demarrage_grh_base_existante_postgres.py',
    'Test/test_avances_salaries_isole.py',
]


def lire(path):
    return (ROOT / path).read_text(encoding='utf-8-sig')


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def inventaire():
    arbres = {p: ast.parse(lire(p)) for p in FICHIERS if p.endswith('.py')}
    tables = []
    for node in arbres['hisabpro-backend/models.py'].body:
        if not isinstance(node, ast.ClassDef) or node.name not in MODELES:
            continue
        champs = {}
        table = None
        contraintes = []
        for enfant in node.body:
            if isinstance(enfant, ast.Assign):
                for cible in enfant.targets:
                    if not isinstance(cible, ast.Name):
                        continue
                    if cible.id == '__tablename__':
                        table = ast.literal_eval(enfant.value)
                    elif cible.id == '__table_args__':
                        contraintes.append(ast.unparse(enfant.value))
                    elif isinstance(enfant.value, ast.Call) and ast.unparse(enfant.value.func) == 'Column':
                        champs[cible.id] = ast.unparse(enfant.value)
        tables.append({'classe': node.name, 'table': table, 'ligne': node.lineno,
                       'colonnes': champs, 'contraintes_orm': contraintes})
    routes = []
    for path in ['hisabpro-backend/routers/employes.py', 'hisabpro-backend/routers/grh.py',
                 'hisabpro-backend/routers/avances_salaries.py']:
        arbre = arbres[path]
        prefixe = ''
        for node in arbre.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if ast.unparse(node.value.func) == 'APIRouter':
                    prefixe = next(ast.literal_eval(k.value) for k in node.value.keywords if k.arg == 'prefix')
        # Le routeur d'avances est inclus par employes.router, vérifié dans sa source.
        if path.endswith('/avances_salaries.py'):
            assert 'router.include_router(avances_router)' in lire('hisabpro-backend/routers/employes.py')
            prefixe = '/api/employes' + prefixe
        for node in arbre.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for deco in node.decorator_list:
                if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute) and deco.func.attr in {'get', 'post', 'put', 'patch', 'delete'}:
                    routes.append({'fichier': path, 'ligne': node.lineno,
                                   'fonction': node.name, 'methode': deco.func.attr.upper(),
                                   'chemin': prefixe + ast.literal_eval(deco.args[0]),
                                   'signature': ast.unparse(node.args)})
    sql = []
    for p in sorted(BACK.glob('*.sql')):
        if re.match(r'^\d+_', p.name):
            sql.append({'fichier': p.relative_to(ROOT).as_posix(),
                        'sha256': sha(p.relative_to(ROOT).as_posix()),
                        'numero': int(p.name.split('_', 1)[0])})
    return {
        'lot': '0', 'date_audit': '2026-10-27',
        'nature': 'Constats de sources, aucune connexion SQL et aucune validation réglementaire.',
        'specification': {'chemin': FICHIERS[0], 'sha256': sha(FICHIERS[0])},
        'fichiers_sources': {p: sha(p) for p in FICHIERS},
        'tables_orm': tables,
        'table_sql_sans_modele_orm_dedie': {
            'nom': 'grh_avances_affectations',
            'source': 'hisabpro-backend/095_registre_avances_salaries.sql',
        },
        'routes_personnel_existantes': routes,
        'migrations_numerotees': sql,
        'maximum_migration_constate': max(v['numero'] for v in sql),
        'limites': ['Un AST ne prouve pas le schéma installé ni les permissions effectives.',
                    'Les campagnes exécutées sont décrites séparément dans le rapport de tests.',
                    'Aucun état réel de salarié ni identifiant personnel n’est collecté.'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    cible = Path(args.output).resolve()
    if not cible.is_relative_to(ROOT.resolve()):
        parser.error('La sortie doit rester dans le dépôt.')
    data = inventaire()
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(f"Inventaire : {len(data['tables_orm'])} tables ORM, {len(data['routes_personnel_existantes'])} routes, {len(data['fichiers_sources'])} sources ; aucune base contactée.")


if __name__ == '__main__':
    main()
