# Lettrage : minimum trois lettres

Les nouveaux codes automatiques commencent à AAA ; les codes saisis doivent comporter 3 à 10 lettres. Les codes historiques courts restent présents et ne sont pas réécrits. Aucun changement de migration.

Commande réelle : `Test/run_unit_tests.py Test/test_lettrage_codes_trois_lettres.py Test/test_lettrage_final.py Test/test_e2e_facturation_isole.py --tb=short --show-capture=no`.

Résultat du 7 octobre 2026 : **18 tests réussis en 42,52 s**, dont quatre API PostgreSQL isolé avec authentification réelle, et deux parcours navigateur vente/achat. Les montants et lignes d'écritures définitives restent identiques avant/après lettrage ; seules les métadonnées de rapprochement changent.

Résultats intermédiaires : les quatre tests du générateur échouaient avant correction ; une première recette utilisait une mauvaise URL (405), puis une relance indiquait un nom de test inexistant et n'a exécuté aucun test. Les tests corrigés passent réellement. PostgreSQL réel et recette utilisateur non exécutés.
