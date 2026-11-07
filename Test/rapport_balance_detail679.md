# Lot679 — Bilan et comptes sources dans la préparation conservée

La consultation reprend la même présentation serveur que les exports677,
depuis un snapshot relu et vérifié. Actif/passif, brut/amortissements/net,
comparatif, sous-postes pour mémoire et comptes sources sont disponibles dans
l’interface. N/N-1, filtre et pagination50comptes limitent les longues listes.
Le tableau du bilan dispose d’un défilement local sur mobile.

Une vraie erreur ne devient pas une liste vide. La reprise utilise un nouveau
GET et les réponses anciennes sont écartées après changement de version,
fermeture ou changement de jeton. Aucun schéma/migration ni calcul fiscal changé.

## Tests

- Premier ciblé :2réussites/1échec en42,14s. Le select encapsulé avait un nom
  accessible comprenant ses options ; ajout de noms explicites dans l’UI.
- Reprise :5réussites/1échec en43,79s. Le banc vérifiait sa liste d’attente
  avant la fin du vrai GET ; synchronisation sur événement navigateur ajoutée,
  sans augmentation des délais et sans réponse métier fabriquée.
- Ciblés corrigés :**10réussites en62,47s**, code0, zéro échec/erreur/ignoré.
  Deux contrats API unitaires SQLite et huit cas natifs sur PostgreSQL091 nonce,
  sous LOGIN applicatif non propriétaire et Edge réel.
- Couverture native :1440/390, avec/sans N-1, actif/passif, mêmes montants que
  les exports, recherche et73comptes sur deux pages, réponse200 réelle retenue
  puis libérée après version/fermeture/jeton ; REVOKE/GRANT SELECT réels dans le
  seul bac et reprise sans F5 ; invitation Lecture et refus d’une autre société.
- Toutes les photographies métier et ACL avant/après les lectures sont égales.
  Les préparations restent immuables et l’écriture témoin333MAD validée reste
  intacte. L’oracle677 reste inchangé : actif brut50000, amortissements300,
  net49700, netN-1 24850 et CPC5000.

Campagne commune finale : **72réussites en150,05s**, 30avertissements,
zéro échec/erreur/ignoré, code0. Elle reprend les62cas677 et les10cas679,
sans additionner les exécutions ciblées précédentes. Build Vite : **7,73s**,
code0 ; avertissements préexistants sur XLSX/bundles conservés. Compilation
Python du routeur et des deux nouveaux fichiers de tests réussie.

Captures mobiles inspectées : comptes/commandes dans la largeur et colonnes
de droite du bilan accessibles par le défilement local ; le contrôle natif
vérifie aussi la visibilité du titre NetN-1 après déplacement horizontal.
Les106fichiers protégés restent inchangés.

## Limites

Aucun accès au PostgreSQL réel. Les bancs unitaires SQLite ne remplacent pas
les parcours natifs. Le changement de jeton testé utilise deux vrais comptes
fictifs ; aucune réparation de données n’est effectuée. La fiscalité/ETIC
autonome et la recette utilisateur restent à compléter, RH/paie différées.

[Mode d’emploi679](../docs/LIASSE_BALANCES_CONSULTATION_679.md).
