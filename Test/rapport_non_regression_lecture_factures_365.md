# Consolidation de la lecture qualifiée — lot365

## Résultat réellement exécuté

3170 passed, 32 warnings in 3998.11s (1:06:38)

Code retour du runner et du wrapper :0. JUnit :3170tests,0échec,
0erreur,0ignoré ; durée XML 3997.747secondes.
Sources application/tests/SQL/config/assets figées :690avant et690après,
aucun changement de SHA256. Nodev24.17.0.

## Commande et banc

Python du venv backend `-X utf8 Test/run_unit_tests.py Test -vv --tb=short`
avec `--junitxml=.codex-tests/global_HisabPro_20261011_lecture363.xml`,
dotenv désactivé, log et code retour dédiés. Le wrapper
`.codex-tests/globale_lecture363.py` vérifie les empreintes avant/après.

Les recettes API/navigateur, migrations et restaurations concernent uniquement
PostgreSQL éphémère nonce gardé. SQLite mémoire reste réservé aux fonctions
pures. L'ancien banc07b3 non isolé est explicitement exclu.
Aucune connexion à la base comptable réelle de l'utilisateur.

## Portée et limites

La consolidation comprend les sources363 et ses28nouveaux tests de lecture
historique ; elle conserve les parcours commerciaux connectés, permissions,
clôture, exports et tests de restauration présents dans le dépôt.
Les échecs initiaux359, les résultats ciblés363 et la globale354 restent
des preuves distinctes : ils ne s'additionnent pas à ces3170tests.

Cette exécution précède la correction des règlements368. Ses modifications
doivent avoir leurs propres tests ciblés ; cette consolidation ne les valide
pas par anticipation. Le guide, les contrôles documentaires, la recette
humaine et la préparation de production restent distincts.

Prochaine étape : appliquer et tester la projection des règlements historiques,
actualiser la couverture et livrer le cumulatif de session.
