# Consolidation générale325 — reprise du10octobre,14:34UTC

## Version et environnement

Nouvelle preuve distincte de315, après les corrections318/320/324/326/330.
Le premier gel674 a précédé le diagnostic330 et n’a lancé aucune suite.
Il est conservé comme point de préparation. Le gel final **675fichiers**
comprend sources backend/frontend, SQL, tests, configurations et **tous les
assets publics**, notamment les fontes/CSS/licences. Documentation, ZIPs,
environnements, caches, pièces et fichiers de build sont exclus des empreintes.

Python3.11.9, pytest9.1.1, Node24.17.0. Début réel de commande15:05UTC.
Les675empreintes sont identiques juste avant l’exécution. Aucune modification
applicative ou des tests n’est autorisée avant achèvement et contrôle final.

## Commande réellement lancée

```text
python -X utf8 .codex-tests/globale_1434.py figer
python -X utf8 .codex-tests/globale_1434.py run
```

Le lanceur capture la commande effective :

```text
python -X utf8 Test/run_unit_tests.py Test -vv --tb=short
 --junitxml=.codex-tests/global_HisabPro_20261010_1434_final.xml
```

Fichiers neufs : `.codex-tests/global_HisabPro_20261010_1434_final`
avec suffixes `.sources.json`, `.log`, `.xml`, `.exit`. La commande refuse
d’écraser une preuve. Elle vérifie les empreintes avant/après et enregistre
le code effectif du processus pytest, jamais déduit d’un message partiel.

Le runner désactive dotenv via l’environnement du lanceur, utilise SQLite
mémoire pour les tests purs et les vrais modèles, puis les fixtures API/migrations
navigateur ouvrent leurs propres clusters **PostgreSQL éphémères nonce**
vérifiés. Il exclut explicitement `test_patch07b3_postgres_sequences.py`,
ancien banc non isolé ; cette exclusion ne constitue pas un test réussi.
Les tests PostgreSQL ne sont pas remplacés par SQLite. Certains tests anciens
de page React interceptent une API synthétique : ils restent distincts des
E2E réellement connectés.

## Résultat

**2 853 réussis, 0 échec, 0 erreur, 0 ignoré ; 32 avertissements ; code retour 0.**
Durée : 2 973,36 secondes (49 min 33 s). Fin réelle : 15:54:50 UTC.
Le XML confirme 2 853 cas, sans échec ni erreur ni cas ignoré.
Le résultat a été récupéré après interruption de quota, puis vérifié le
10 octobre à 19:39 UTC : code effectif 0 et **675/675 empreintes identiques**.
La vérification a été répétée à 19:44 UTC, sans changement. Les preuves
historiques échouées restent conservées ci-dessous.

## Preuves historiques distinctes

315 reste une suite échouée :2742réussites49échecs5erreurs,653empreintes
inchangées, fichier exit non récupéré. Les incidents Node/driver avaient
une cause système profonde non établie. [Rapport315](rapport_non_regression_globale_inventaire_20261010.md).
327 conserve les retests, dont53réussites/1échec après326 et la trace d’alerte
de succèsBR après début de navigation. [Rapport327](rapport_retests_globale315.md).
Le correctif330 a passé quatre Edge avant cette nouvelle consolidation ;
aucun ancien résultat n’est requalifié. Les suites ciblées superposées ne
sont pas additionnées aux2853cas de ce run.

## Limites

Aucune base utilisateur, donnée comptable réelle, configuration utilisateur
ou migration réelle modifiée. Les backend/Vite démarrés par l’utilisateur
sont préservés. Les résultats automatisés ne remplissent ni la recette
humaine ni les conditions réglementaires/production. Toute modification
postérieure au gel doit disposer de ses propres tests et être distinguée
de cette version675 ; la réussite de325 ne la couvrirait pas rétroactivement.
