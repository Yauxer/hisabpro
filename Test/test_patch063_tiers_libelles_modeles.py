# -*- coding: utf-8 -*-
"""Non-régression : auto-entrepreneur, libellés contextuels et modèles de capital."""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'


def lire(path):
    return path.read_text(encoding='utf-8')


def test_063_autoentrepreneur_compatible_api_et_profils_client_fournisseur():
    # Le module d'authentification (python-jose) n'est pas installé en CI ;
    # vérifier le validateur et le schéma via l'AST sans simuler l'API réelle.
    api = lire(BACK / 'routers/tiers.py')
    tree = ast.parse(api)
    modele = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'TiersCreate')
    champs = {n.target.id for n in modele.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}
    assert {'type', 'categorie_fiscale', 'assujetti_tva'} <= champs
    validateur = next(n for n in modele.body if isinstance(n, ast.FunctionDef) and n.name == 'categorie_fiscale_valide')
    categories = {elt.value for n in ast.walk(validateur) if isinstance(n, ast.Set)
                  for elt in n.elts if isinstance(elt, ast.Constant)}
    assert categories == {'professionnel', 'autoentrepreneur', 'particulier', 'indetermine'}
    ui = lire(ROOT / 'src/pages/Tiers.jsx')
    assert '<option value="autoentrepreneur">Auto-entrepreneur</option>' in ui
    # Le champ régime TVA reste indépendant de la catégorie fiscale.
    assert 'assujetti_tva:' in ui
    assert 'ne détermine pas à lui seul son régime de TVA' in ui


def test_063_migration_tiers_ne_change_pas_les_regimes_tva():
    sql = lire(BACK / '063_tiers_autoentrepreneur_modeles_capital.sql')
    assert "'autoentrepreneur'" in sql
    assert 'DROP CONSTRAINT IF EXISTS ck_tiers_categorie_fiscale' in sql
    assert 'ADD CONSTRAINT ck_tiers_categorie_fiscale' in sql
    assert 'UPDATE tiers' not in sql
    assert 'UPDATE factures' not in sql
    assert 'assujetti_tva =' not in sql
    assert 'BEGIN;' in sql and 'COMMIT;' in sql


def test_063_libelles_contextuels_visibles_et_non_simples_constantes_mortes():
    ui = lire(ROOT / 'src/components/FormulaireEcriture.jsx')
    assert 'LIBELLES_PAR_JOURNAL[journal].map' in ui
    assert 'aria-label="Choisir un libellé type pour ce journal"' in ui
    assert "setLibelleAuto(false)" in ui
    assert "Libération du capital par banque" in ui
    assert "Libération du capital en espèces" in ui
    assert "Libération du capital par apport en nature" in ui
    assert "Souscription ou appel du capital" in ui
    assert "if (debit('514') && (credit('1111') || credit('3461') || credit('3462')))" in ui
    assert "if (debit('5161') && (credit('1111') || credit('3461')))" in ui
    assert "SA: { libelle: 'Rémunérations du personnel'" in ui
    assert "label: 'Rémunérations'" in lire(ROOT / 'src/data/donnees.js')


def test_063_formulaire_sans_notes_grises_mais_conserve_alertes_metier():
    ui = lire(ROOT / 'src/components/FormulaireEcriture.jsx')
    assert 'styles.fieldHint' not in ui
    assert 'styles.aiHint' not in ui
    assert 'styles.metaNotice' not in ui
    assert 'styles.alertesZone' in ui
    assert 'styles.alerteDoublon' in ui
    assert 'Brouillon non numéroté' in ui


def test_063_modeles_capital_distinguent_souscription_appel_et_liberations():
    sql = lire(BACK / '063_tiers_autoentrepreneur_modeles_capital.sql')
    assert "code = 'capital_souscription'" in sql
    assert "code = 'capital_liberation'" in sql
    assert "'capital_liberation_especes', 1, '5161'" in sql
    assert "'capital_liberation_materiel', 1, '2355'" in sql
    assert "'capital_appel_actionnaires', 1, '3462'" in sql
    assert "'capital_appel_actionnaires', 2, '1119'" in sql
    assert "'capital_versement_actionnaires', 2, '3462'" in sql
    assert "'capital_liberation_especes', 2, '3461'" in sql
    assert "journal = 'SA', libelle_auto = 'Rémunérations du personnel — {ref}'" in sql
    assert 'UPDATE ecritures' not in sql
    assert 'DELETE FROM ecritures' not in sql
    assert 'UPDATE lignes_ecriture' not in sql
    assert 'NOT EXISTS (' in sql  # relance sans créer de doublon dans la bibliothèque


def test_063_python_files_syntax_correcte():
    for fichier in [BACK / 'routers/tiers.py', BACK / 'models.py']:
        ast.parse(lire(fichier))


def test_063_bibliotheque_existante_55_modeles_structure_coherente():
    """Audit structurel : tous les modèles connus ont au moins débit, crédit et comptes référencés."""
    import re
    from collections import defaultdict

    sql = lire(BACK / '037_compta2_modeles_ecritures.sql')
    entetes = sql.split('-- Remplace uniquement', 1)[0]
    modeles = re.findall(r"VALUES \('([^']+)', '(?:[^']|'')*', '([A-Z]{2})', '([^']*)'", entetes)
    lignes = re.findall(
        r"SELECT id, (\d+), '([0-9]+)', '(?:[^']|'')*', '(debit|credit)'[\s\S]{0,125}?WHERE code = '([^']+)';",
        sql,
    )
    assert len(modeles) == 55
    assert len({code for code, _, _ in modeles}) == len(modeles)
    assert {code for _, _, _, code in lignes} == {code for code, _, _ in modeles}
    plan = set(re.findall(r"compte: '([0-9]+)'", lire(ROOT / 'src/data/planComptes.js')))
    par_modele = defaultdict(list)
    for ordre, compte, sens, code in lignes:
        assert compte in plan, f'Compte introuvable dans le référentiel statique : {code}/{compte}'
        par_modele[code].append((ordre, sens))
    for code, valeurs in par_modele.items():
        assert len(valeurs) >= 2, code
        assert len({ordre for ordre, _ in valeurs}) == len(valeurs), code
        assert {'debit', 'credit'} <= {sens for _, sens in valeurs}, code
