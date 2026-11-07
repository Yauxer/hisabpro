# Non-regression globale du 8 octobre 2026, 12:31 UTC

Commande executee : `Test/run_unit_tests.py Test --tb=short --show-capture=no --junitxml=.codex-tests/global_20261008_1231.xml`, avec PYTHON_DOTENV_DISABLED=1.

Resultat reel : **2255 passes, 1 echec, 0 erreur, 0 ignore**, 32 avertissements, 1615.64 secondes. Les tests PostgreSQL utilisent uniquement leurs environnements isoles ; aucun test contre la base utilisateur.

Echec : `test_procedure_python_restore_compile_sans_connexion` attend le chemin historique complet des pieces dans la procedure. La racine configurable avait ete documentee, mais la mention complete du chemin par defaut avait disparu. Correction documentaire distincte dans le lot255 ; les 24 tests du cahier ont ensuite passe (code de sortie0). Aucun test metier ne doit etre presente comme remplace par cette relance ciblee.

Cette execution precede les corrections253/254/256/257 et la recette252 ; une nouvelle consolidation complete reste necessaire. Les logs/XML restent locaux, hors ZIP.
