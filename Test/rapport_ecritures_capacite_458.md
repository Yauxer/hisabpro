# Montants finis hors capacité de stockage — lot 458

## Défaut reproduit et correction

Des débits/crédits équilibrés de `1e16` ou `1e20` passent le contrôle « fini » mais
dépassent les colonnes `NUMERIC(18,2)` existantes. Création et PATCH renvoyaient
500 à l'insertion des lignes. Le rollback préservait bien les lignes et l'en-tête.
La capacité est confirmée par le catalogue PostgreSQL et deux casts natifs
refusés avec SQLSTATE 22003, sur le seul cluster nonce.

Le helper monétaire partagé vérifie maintenant la capacité après la quantification
`ROUND_HALF_UP` déjà utilisée. Un dépassement renvoie 422 avec une erreur de saisie,
avant l'insertion ; il n'est ni tronqué ni plafonné. Le contrôle après arrondi
refuse aussi `9999999999999999.995`, qui franchit la borne en s'arrondissant.

Aucune migration, aucun modèle ni schéma Pydantic modifié. Les valeurs Decimal
valides jusqu'à `9999999999999999.99`, et `100.105` → `100.11`, gardent le résultat
existant. Il s'agit d'une capacité technique, pas d'un plafond fiscal ou légal.

## Tests réellement exécutés

Vrai `main:app`, PostgreSQL nonce 091 et LOGIN SQL limité. Toutes les valeurs et
écritures sont des fixtures techniques fictives, pas des opérations réelles.

- Avant : **7 échecs, 4 réussis en 22,41 s** : quatre réponses 500 et trois
  dépassements non refusés par le helper. Rollbacks vérifiés avant assertion HTTP.
- Après : **11 réussis en 19,13 s**, 29 avertissements,
  zéro échec/erreur/ignoré.
- Création/PATCH refusés en 422 : données brutes et nombre d'écritures inchangés.
- Les deux limites Decimal valides et l'arrondi existant passent. PostgreSQL
  confirme précision 18/échelle 2 et les erreurs natives de dépassement.
- Une valeur flottante représentable juste sous la borne SQL est réellement
  enregistrée et validée. Les lectures balance/grand livre retournent 200.
- Suite connexe : **79 réussis en 193,37 s**, 29 avertissements,
  zéro échec/erreur/ignoré. Inclut les anciens tests NaN/non finis et booléens,
  création/PATCH, les nouvelles bornes, modèles choisis/détectés, rôles Journal,
  erreurs de saisie et les exports réels des balances.
- Compilation Python du router et du test : code 0. Aucun frontend modifié dans
  ce lot ; le build 457 s'applique aux mêmes sources frontend.

Preuves locales exclues du ZIP : `capacite458_avant.*`, `capacite458_apres.*`,
`capacite458_connexes.*`. Les suites recouvrantes ne s'additionnent pas.

## Limites et suite

L'API conserve son type flottant existant. Ce lot ne migre pas toutes les entrées
et sorties en Decimal et ne revendique pas la précision de tous les centimes aux
extrêmes des flottants JavaScript/Python. La validation en lecture des données
historiques n'est pas restreinte par un nouveau validateur de schéma.

Aucune donnée réelle ni écriture définitive historique modifiée. Recette
utilisateur et production non prévalidées, point 6 en attente. Suite : regrouper
les parcours de cette reprise sur une installation commune, contrôler les
invariants finaux, puis mettre à jour couverture et livrer le cumulatif.
