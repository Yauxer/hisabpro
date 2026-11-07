# Recette regroupée de la reprise 451–458 — lot 459

La commande regroupe les fonctions et oracles déjà livrés, sans les modifier,
sur une même installation PostgreSQL nonce 091 et le vrai `main:app` sous LOGIN
`hisabpro` non propriétaire. La restauration conserve ses deux clusters isolés
propres ; les tests monétaires purs Node/Python n'utilisent pas PostgreSQL.

## Résultat réel

**61 tests réussis en 161,47 s**, 29 avertissements de dépendances,
zéro échec, erreur ou cas ignoré. Code de sortie 0.

Le jeu fictif de l'application commune contient à la fin :

| Élément | Nombre |
|---|---:|
| Sociétés fictives | 31 |
| Écritures | 63 |
| Lignes comptables | 168 |
| Clôtures | 2 |
| Liens de lettrage | 20 |
| Références justificatives | 15 |

Contrôles finaux en lecture seule : zéro pièce déséquilibrée, zéro montant non
fini, zéro écriture définitive sans numéro/date de validation. Les ACL sont
identiques à celles du début malgré les injections de refus SQL. Les 16 sources
de produit et de test suivies sont identiques avant/après la commande.

Les sources finales couvrent pièces/références, refus SQL et validation concurrente,
téléchargements 404/401, modèles choisis et détectés, lettrage/FEC, chèques/effets,
impayés/frais, clôture/à-nouveaux, consultation seule et capacités monétaires.
La restauration conjointe indépendante vérifie aussi 73 tables, quatre PDF,
droits natifs et décision 091 avec son PV fictif.

Les dossiers négatifs conservent volontairement des brouillons et références
manquantes : ce contrôle ne signifie pas que toutes les sociétés fictives sont
prêtes à exporter un FEC ou à déposer une liasse. Les 500 de refus SQL injectés
dans les deux tests documentaires sont attendus, pas masqués.

## Reproduction et preuves

```powershell
$env:PYTHON_DOTENV_DISABLED = '1'
& '.\hisabpro-backend\.venv\Scripts\python.exe' -X utf8 '.\Test\run_unit_tests.py' '.\Test\test_consolidation_reprise_20261015.py' --junitxml='.codex-tests\consolidation459.xml'
```

Commande réellement exécutée. Preuves locales : `consolidation459.log`, `.xml`,
`.exit`, `consolidation459_preuve.json`. Les contrôles du footer ne suffisent pas
à déclarer la suite réussie : le XML et le code de sortie sont vérifiés séparément.
Les fixtures vérifient aussi l'arrêt de leurs processus et la suppression de
leurs répertoires nonce. Compilation Python du banc : code 0.

Ce n'est pas la suite globale du dépôt. Les commandes individuelles et connexes
précédentes se recouvrent avec ces 61 cas : ne pas additionner leurs résultats.
Aucun résultat de recette humaine ni dossier fiscal réel n'est prévalidé.

## Suite et limites

Mettre à jour la matrice, le registre et les procédures avec ces preuves, puis
livrer le cumulatif différentiel de la reprise depuis le lot 450. Les sources
officielles manquantes et les justificatifs historiques restent nécessaires.
Précision monétaire aux extrêmes, autres modules/modèles complexes et variantes
annuelles restent à étendre. Point 6 en attente du retour utilisateur.

Aucun PostgreSQL réel, fichier réel, migration ou donnée comptable historique
modifié. Développement global partiel, tests qualifiés dans leurs périmètres,
recette utilisateur à effectuer et production non validée.
