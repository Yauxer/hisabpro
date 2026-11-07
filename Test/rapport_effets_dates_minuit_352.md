# Lot352 — dates futures des tests d'effets après minuit

La globale346 conserve ses deux échecs de date future. Le banc calculait
`date.today() + timedelta(days=1)` à l'import, avant une suite de plus d'une
heure traversant minuit. Au moment du test, cette date était devenue
aujourd'hui : le backend avait raison de ne pas la refuser comme future.

Reproduction déterministe : deux tests ORM mémoire figent l'horloge Python
au jour précédemment calculé et réutilisent les assertions du banc original.
Avant correction : **2 échoués,25 avertissements,1,25s,code1**, échec
`DID NOT RAISE HTTPException`, preuves `effets352_avant.xml/.log` conservées.

Correction uniquement du banc : paramètres identifiés par « avant_reception »
et « demain », date calculée au moment de l'exécution. Les règles métier et
les assertions 400/aucune écriture/statut inchangé sont conservées.

Commande réelle : `Test/run_unit_tests.py Test/test_effets_dates_minuit.py
Test/test_effets_dates_operations.py Test/test_patch02c_reglement_date_effective.py
-vv --tb=short --junitxml=.codex-tests/effets352_final.xml`.
Résultat : **24 réussis,25 avertissements,1,67s,code0** ; compilation des deux
fichiers modifiés réussie. Tests ORM/structure ; aucun PostgreSQL réel ou
isolé pour cette sélection, aucun parcours navigateur. Les tests de dates
locales navigateur sont un lot distinct351.

La globale346 reste échouée ; une nouvelle consolidation est nécessaire.
