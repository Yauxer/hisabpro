# Consolidation après correction des dates — lot354

Reprise11octobre2026,08:11UTC, budget10:11UTC. Corrections350351352
livrées avant cette consolidation,686sources/SQL/tests/configurations/assets
publics figés. Nodev24.17.0. Nouveau préfixe de preuve
`.codex-tests/global_HisabPro_20261011_0811_final`, aucun ancien résultat écrasé.

Commandes : `.codex-tests/globale_0811.py figer`, puis `run`, avec le Python
du venv backend et `-X utf8`. Le wrapper appelle
`Test/run_unit_tests.py Test -vv --tb=short
--junitxml=.codex-tests/global_HisabPro_20261011_0811_final.xml`, dotenv
désactivé, contrôle SHA avant/après et conservation du véritable code retour.
Début11octobre08:22UTC, session95112. La commande et son wrapper sont
terminés avec le code **0** : **3 126 tests réussis, 0 échec, 0 erreur,
0 ignoré**, en 3 866,88 secondes. Le JUnit, le log complet et le véritable
code retour ont été relus. Les 32 avertissements sont des dépréciations
Starlette/python-multipart et Pydantic ; ils restent visibles.

Le contrôle SHA exécuté par le wrapper après les tests, puis relancé
séparément, confirme **686 fichiers avant et après, aucun changement**.
Ce résultat porte sur les corrections350351352. Il précède le lot357
du formulaire bancaire, qui doit conserver ses propres preuves ciblées
et son build ; ce rapport ne lui attribue aucune consolidation ultérieure.

SQLite mémoire pour les tests purs ; API, migrations et Edge connectés
sur PostgreSQL éphémères gardés par URL/répertoire/nonce. L'ancien banc07b3
non isolé est explicitement exclu, jamais déclaré réussi. Pas de .env,
PostgreSQL réel, migration nouvelle ou écriture comptable réelle modifiée.

Les résultats27ciblés350,24ciblés352 et63connexes351 sont distincts et
non additionnés à la globale. La globale346 conserve3105réussis/7échoués
et son code1. Les reproductions de minuit et dates locales sont conservées
avec leurs échecs initiaux. La cause du délai de connexion devis n'est
toujours pas établie ; aucune relance automatique ou assertion assouplie.

Développement global partiel ; recette utilisateur et ouverture Office
à effectuer ; production et conformité réglementaire non validées.
