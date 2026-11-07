# Consolidation336 — reprise du10octobre19:39UTC

## Périmètre

Nouvelle preuve générale distincte de325, après les correctifs332–335.
Les sources backend/frontend, tests, SQL, configurations et tous les assets
publics sont figés avant le run. Aucun de ces fichiers ne doit changer durant
la commande. Documentation, ZIPs, environnements, caches, uploads et builds
sont exclus des empreintes. Les 675empreintes de la précédente globale325
ont été vérifiées identiques avant ces nouveaux travaux.

## Commande

```text
python -X utf8 .codex-tests/globale_1939.py figer
python -X utf8 .codex-tests/globale_1939.py run
```

Commande effective :

```text
python -X utf8 Test/run_unit_tests.py Test -vv --tb=short
 --junitxml=.codex-tests/global_HisabPro_20261010_1939_final.xml
```

La preuve neuve utilise les suffixes `.sources.json`, `.log`, `.xml` et `.exit`
du préfixe `global_HisabPro_20261010_1939_final`. Aucun ancien fichier de preuve
n'est écrasé. Le lanceur contrôle les SHA-256 avant et après le processus et
conserve son code effectif, non déduit d'une ligne de succès isolée.

Le runner désactive dotenv, utilise SQLite mémoire pour les tests purs/ORM,
puis les tests API, migrations et navigateurs connectés utilisent leurs
propres PostgreSQL éphémères vérifiés par URL/dossier/nonce. Aucun PostgreSQL
utilisateur ni donnée comptable réelle appelé. Le banc historique non isolé
`test_patch07b3_postgres_sequences.py` reste explicitement exclu ; cela ne
constitue pas une réussite. Certaines anciennes recettes React interceptent
une API synthétique et restent distinguées des parcours vraiment connectés.

## Résultat

Commande lancée le10octobre à20:07:35UTC, achevée à21:15:28UTC.
**3009réussis,0échec,0erreur,0ignoré,32avertissements,4072,44s ; code0.**
Le véritable XML contient3009cas, sans failure/error/skipped, temps4072,330s.
Le log et le code de sortie effectif ont été récupérés par le principal.

Les **680fichiers figés** sont identiques avant/après et lors du contrôle
supplémentaire juste après achèvement. Backend/frontend, SQL, tests,
configurations et tous les assets publics sont couverts par les empreintes.
Il s’agit de la version après332–335 ; une correction livrée ultérieurement
possède ses propres tests et ne doit pas être supposée incluse dans ce run.

Les32avertissements sont les dépréciations préexistantes de multipart et de
la configuration Pydantic. La compilation ciblée335 a réussi ; le dernier
frontend modifié334 a réellement été construit par Vite :139modules,7,89s,
code0. Ses avertissements de chunk volumineux/import mixtexlsx restent visibles.

## Preuves antérieures et limites

La [globale325](rapport_non_regression_reprise_20261010_1434.md) a réellement
réussi2853cas, sans échec/erreur/ignoré, code0, 32avertissements,2973,36s.
Elle reste la preuve de sa version675 avant332–335. La [globale315](rapport_non_regression_globale_inventaire_20261010.md)
échouée et ses [retests327](rapport_retests_globale315.md) ne sont pas requalifiés.

Les suites ciblées superposées ne sont pas additionnées. Les avertissements,
exclusions et anciens incidents restent visibles. Aucun test automatique ne
valide la recette humaine, les justificatifs historiques manquants, la paie
réglementaire complète ou une mise en production. Les processus backend/Vite
de l'utilisateur sont préservés.
