# Non-régression globale — 8 octobre 2026

Ce rapport distingue les exécutions complètes et les tests ciblés. Aucun test ne vise le PostgreSQL réel de l'utilisateur. Les tests PostgreSQL et navigateur utilisent exclusivement les clusters éphémères gardés du dépôt.

## Première exécution après les lots jusqu'à 217

Commande du principal, lancée à 04:57 UTC :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test --tb=short --show-capture=no --junitxml=.codex-tests/global_20261008_0458.xml
```

Sortie : **2019 réussis, 7 échoués, 31 erreurs, aucun ignoré, 29 avertissements, 1168,76 secondes ; code de sortie 1**. La collecte comporte 2057 tests. Les tests annuels et de concurrence ajoutés pendant cette exécution ne font pas partie de cette collecte. Cette exécution ne valide pas la suite globale.

Les sept échecs concernent des bancs anciens : libellé « Échéance », centralisation ETIC dans la liasse, lecture des comptes inactifs, dépendances RAS manquantes dans trois tests Node extrayant une fonction React, et imports de présentation de la liasse absents du banc d'export. Les contrôles métier, l'ordre sauvegarde/actualisation et les ventilations financières doivent être conservés lors de leur correction.

Les 31 erreurs proviennent d'une même fixture historique de permissions : elle importe les compléments du manifeste consolidé, qui comprend désormais 077, puis vérifie des interdictions censées précéder 077. Le correctif doit séparer les phases du banc, sans modifier les migrations ni réduire les contrôles d'accès.

Le runner exclut explicitement `Test/test_patch07b3_postgres_sequences.py`, ancien banc susceptible de viser une base non isolée. Cette exclusion est une mesure d'isolation, distincte d'un test exécuté ou ignoré par pytest. Les avertissements de dépréciation ne sont pas des validations réglementaires.

## Correctifs et seconde exécution complète

Les lots221 et223 corrigent les bancs, sans modifier les droits SQL ou affaiblir les contrôles financiers :32tests de permissions et37tests connexes réussis par les agents. Le lot222 corrige les réponses tardives du lettrage ; son test strict et les deux cycles connectés passent. Le lot224 conserve l'oracle annuel indépendant figé avant le premier test ; ses deux tests passent également.

Le principal a relancé la même commande, avec `--junitxml=.codex-tests/global_20261008_0531.xml` et sortie `.codex-tests/global_20261008_0531.log` : **2060 réussis, aucun échec, aucune erreur, aucun ignoré, 29 avertissements, 1233,35 secondes ; code de sortie0**. Les trois nouveaux cas sont l'oracle annuel, son parcours connecté et le test de concurrence du lettrage. Le test des notes de devis225, ajouté après cette collecte, a ses deux parcours ciblés réussis séparément ; il n'est pas ajouté au total2060.

Les avertissements proviennent de Pydantic et python_multipart. Les suites ciblées se recouvrent avec cette collecte ; leurs nombres ne sont pas additionnés au total global.

## Limite temporelle de cette validation

Cette seconde exécution porte sur les sources stabilisées avant les nouveaux lots de paie226 et suivants. Les tests avant correction des paramètres de paie ont été exécutés séparément après la collecte ; ils ont reproduit des mutations invalides et des erreurs de lecture historiques. Ils ne font pas partie des2060cas. Une nouvelle consolidation sera consignée après les correctifs numériques et de traçabilité.

La recette annuelle est un scénario réduit de laboratoire, distinct des218cas du cahier utilisateur. La recette utilisateur, les données historiques réelles, la qualification réglementaire et la mise en production restent à valider séparément.
