# Paramètres TVA — verrou du statut d'exercice

Le setter contrôlait l'état de l'exercice sans verrou. Une décision de statut
non encore confirmée n'était pas attendue ; dans l'ordre inverse, le statut
pouvait être clôturé pendant qu'une sauvegarde ayant déjà lu « ouvert » était
encore bloquée sur sa ligne de paramètres.

La correction ajoute uniquement `with_for_update()` à la lecture de la ligne
`ExerciceComptable` existante. Le verrou est conservé jusqu'au commit de la
sauvegarde. Après attente, un statut clôturé provoque 409 avant toute mutation ;
une décision annulée permet la sauvegarde. Si celle-ci détient déjà le verrou,
le changement de statut attend sa fin. Aucun taux, formule ou migration ajouté.

## Tests natifs, sans simulation d'API

Trois scénarios utilisent de vrais appels HTTP, des transactions concurrentes
et `pg_stat_activity` pour observer les attentes effectives de verrou :

1. Statut clôturé en transaction non confirmée, PUT en attente, confirmation :
   refus 409, crédit/prorata d'origine 20/80 conservés.
2. Même attente, puis annulation de la décision : PUT 200, valeurs 30/85.
3. Sauvegarde déjà engagée et bloquée sur le paramètre, puis clôture de statut :
   cette dernière attend le verrou d'exercice ; après libération, sauvegarde
   puis clôture aboutissent. Un nouveau PUT est refusé 409, valeurs 30/85 gardées.

Les changements de statut sont effectués par le propriétaire du seul cluster
nonce, sur des sociétés fictives ; ils ne constituent pas une clôture annuelle
complète. Aucun contrôle SQL n'est désactivé. Toutes les tables métier hors
paramètres et statut de l'exercice sont comparées avant/après ; les traces HTTP
append-only restent conservées. Aucune écriture comptable définitive n'est altérée.

Avant correction : **3 échecs en 27,92 s**. Après : **3 réussis en 28,36 s**.
Puis **33 réussis, zéro échec/erreur/ignoré, 29 avertissements, 122,86 s**, code 0,
pour la concurrence, les droits et l'UI TVA, les montants invalides, les services
TVA et le parcours E2E de clôture/à-nouveaux/verrouillage existant.

```powershell
python -X utf8 Test/run_unit_tests.py Test/test_tva_verrou_exercice_isole.py Test/test_permissions_tva_runtime_isole.py Test/test_tva_parametres_montants.py Test/test_patch02_tva_service.py Test/test_patch02b_tva_service.py Test/test_e2e_cloture_isole.py -ra
```

Compilation du routeur et du test exécutée avant livraison. Le frontend est
inchangé dans ce lot ; son dernier build 474 reste réussi en 7,39 s.

## Limites explicites

Cette qualification porte sur la sauvegarde API et la ligne d'exercice
existante. Une ligne absente, les écritures SQL directes, tout le calcul effectué
avant le changement de statut dans une clôture annuelle, les autres opérations
et tous les modes d'isolation ne sont pas déclarés protégés par ce seul verrou.
La migration 093 reste nécessaire au rôle limité pour les paramètres, et n'a
pas été appliquée à la base utilisateur. Aucun PostgreSQL réel n'est utilisé.
Point 6, recette humaine et production restent en attente.
