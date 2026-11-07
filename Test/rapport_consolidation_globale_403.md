# Consolidation globale403 — 11 octobre2026

Nouvelle exécution réelle des sources finales401, avant les nouveaux lots404/405/406. Aucun test historique simplement recopié comme résultat courant. Commande : Python Test/run_unit_tests.py Test -vv --tb=short, JUnit local. Le banc07b3 non isolé reste exclu par le lanceur existant.

3320 cas exécutés :3320 réussis,0 échecs,0 erreurs,0 ignorés ;4071.765s ;713 empreintes stables.

Aucune défaillance dans cette exécution.

Les preuves391 antérieures (un délai de connexion puis8tests isolés réussis) restent conservées dans leur rapport ; cette nouvelle exécution ne réécrit pas leur résultat. Les nouveaux lots404/405/406 ne sont pas couverts par403 : leur suite finale410 est distincte et les résultats ne doivent pas être additionnés.

Sources, SQL, tests, configurations et assets figés avant la commande puis contrôlés identiques. Bases PostgreSQL éphémères nonce et navigateurs Edge uniquement ; aucun PostgreSQL réel, aucune donnée comptable réelle. Caches log/XML/exit/sources.json sous.codex-tests non livrés. Aucune migration ou réparation de données par ce lot. Recette utilisateur et production non validées ;point6 reste en attente.
