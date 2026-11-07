# Correction du démarrage GRH sur base existante — 8 octobre 2026

## Cause et correction

Le démarrage appelait `Base.metadata.create_all()` alors qu'une ancienne table `employes` pouvait ne pas posséder `UNIQUE(id, societe_id)`. SQLAlchemy ignore une table déjà présente et ne complète pas ses contraintes. La création de `grh_absences`, qui référence cette clé composite, échouait donc avec PostgreSQL42830. Une base vierge ne reproduisait pas ce défaut.

Le nouveau helper de démarrage prépare les deux clés composites employes/absences avant `create_all()`. Il applique ensuite les scripts existants080 et081 : colonnes optionnelles, contraintes et protections de l'historique GRH. Ces scripts sont inchangés. Les contrats et personnes à charge inconnus restent NULL ; aucune ligne salariale ou comptable n'est corrigée automatiquement. Les ajouts sont rejouables.

Ce flux s'exécute uniquement lorsque la politique existante autorise la création du schéma au démarrage. En production, elle reste désactivée par défaut ; les migrations doivent être appliquées séparément avec le rôle prévu. Aucun droit global nouveau n'est introduit.

## Tests exécutés par le principal

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_demarrage_grh_base_existante_postgres.py Test/test_session132_bootstrap.py --tb=short
```

**14 réussis en48,52s** : ancienne table avec et sans rôle applicatif, reproduction réelle42830 avant correction, reprise/rejeu, base vierge, schéma GRH partiel, politique de production et vrai import de `main` dans un sous-processus suivi d'un HTTP200 sur `/api/health`. Aucun doublage de `create_all`, de SQLAlchemy ou de PostgreSQL.

```text
python -X utf8 Test/run_unit_tests.py Test/test_grh_absences_postgres.py Test/test_paie_grh_postgres.py Test/test_grh_absences_service.py --tb=short
```

**40 connexes réussis en65,56s**,25avertissements des dépendances. Après ajout au scénario historique d'une écriture définitive fictive équilibrée100/100, les quatre régressions de démarrage sont relancées : **4réussis en52,43s**. Chaque colonne de l'écriture et de ses lignes, ainsi que toutes les valeurs historiques du salarié, est comparée avant/après. Ces quatre cas sont déjà compris dans les54cas distincts ; leurs relances ne sont pas ajoutées au total.

Compilation Python de `main.py`, du helper et du test : code0. Build frontend : code0,139modules,6,26s ; avertissements existants SheetJS et taille des bundles.

Toutes les connexions de recette utilisent un cluster PostgreSQL éphémère gardé par URL loopback, répertoire et nonce. `.env` désactivé dans les tests. Aucun PostgreSQL réel utilisé, aucune donnée comptable réelle lue ou modifiée.

## Application du correctif

Dans le dépôt courant, les fichiers sont déjà corrigés. Relancer la commande habituelle depuis `hisabpro-backend` :

```text
python main.py
```

Le démarrage de développement ajoute les prérequis manquants et les compléments GRH ; aucune réinitialisation de base n'est nécessaire. Les scripts080/081 doivent rester présents dans le dossier backend. La validation sur la base réelle est à effectuer par l'utilisateur lors de sa relance ; elle n'est pas déduite des tests isolés. Les nouveaux travaux de traçabilité de paie restent séparés et non livrés à ce stade.
