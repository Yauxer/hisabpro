# Avoirs — concurrence et conservation — lot438

## Anomalies reproduites

Six courses vente/achat réellement exécutées sur PostgreSQL nonce, avec deux
requêtes authentifiées utilisant le même jeton réel :

| Course | Avant correction | Résultat attendu et obtenu après correction |
|---|---|---|
| Deux comptabilisations | Deux200 etdeux écrituresAV pour le même avoir |200puis409,une seule écritureAV |
| Deux annulations | Deux200 etdeux contrepassationsANN avec IDs distincts |Deux200,idempotence :mêmeID,une seuleANN |
| Consommation30 puis annulation | Deux200,avoirannulé avec un usage encoreactif |Consommation200,annulation409,crédit disponible30sur60 |
| Annulation puis consommation | Sens inverse ajouté àla vérification finale |Annulation200,consommation409,aucun usage actif |

La correction ajoute seulement `FOR UPDATE OF avoirs` àla lecture du parent
dans `comptabiliser_avoir` et`annuler_avoir`. Les contrôles existants se font
après acquisition du verrou. La jointure de lecture des lignes reste disponible,
sans verrou du côté nullable. Aucune écriture validée ni règle fiscale modifiée.

## Exécution réelle

57 tests connexes réussis, zéro échec, erreur ou ignoré, 195.368 s ; six courses ciblées réussies en17.21s ; compilation2fichiers code0.

Commande connexe :`Test/run_unit_tests.py
Test/test_concurrence_avoirs_runtime_postgres.py
Test/test_permissions_acomptes_avoirs_postgres.py
Test/test_permissions_documents_commerciaux_postgres.py
Test/test_factG_acomptes_avoirs.py Test/test_avoirs_ras_societe_postgres.py
Test/test_e2e_acompte_imputation_isole.py Test/test_e2e_acompte_fournisseur_isole.py
Test/test_e2e_avoir_fournisseur_isole.py`.

Le nouveau banc place un verrou de ligne de laboratoire, lance deux clientsAPI
indépendants etobserve leurs attentes réelles dans pg_stat_activity avant de
libérer le verrou. La libération est enfinally,avant la fermeture du pool de
threads. Pas de mock métier,d’authentification ou de permission ;SQL sous LOGIN
hisabpro nonpropriétaire. Quatre courses ×vente/achat =huit cas finaux.
Les colonnes des écritures etlignes déjàdéfinitives sont photographiées et
comparées après les courses,puis après validation des nouvelles pièces.

Premier essai :six erreurs de fixture nonimportée,0.96s,sans résultat métier.
Après correction du seul support :six échecs réels18.60s,dont AV2,ANN2 et
avoirannulé avec usageactif. Après correction applicative :six réussis17.21s.
Le sens inverse complète la connexe ;ces suites ne sont pas additionnées.

## Limites

Courses déterministes sur deux requêtes du même utilisateur réel de laboratoire,
pas un test de charge ni une matrice exhaustive de tous les rôles simultanés.
Les autres variantes de stock,qualifications fiscales etarchives gardent leurs
propres preuves. Aucun PostgreSQL réel,aucune migration supplémentaire.
Recette utilisateur etproduction nonvalidées ;globale430antérieure àce lot.
