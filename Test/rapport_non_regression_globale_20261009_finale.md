# Non-régression globale du 9 octobre 2026 — sources figées

Exécution réelle par le principal, commencée vers 15:14 UTC après les lots 266–285.
Session outil consign?e dans CODEX_PROGRESS.md ; code retour final **0** conservé dans un fichier local.

Résultat : **2582 réussis, 0 échec, 0 erreur, 0 ignoré ; code retour 0**, sur **2582 cas collectés**.
Résumé pytest exact : `=============== 2582 passed, 32 warnings in 2024.18s (0:33:44) ================`.
XML final relu, tous les cas comptés et comparés au résultat de la commande.

Commande exécutée avec `PYTHON_DOTENV_DISABLED=1` et le Python de la `.venv` backend :

```text
python -X utf8 Test/run_unit_tests.py Test -vv --tb=short --show-capture=no --junitxml=.codex-tests/global_20261009_1404.xml
```

Les logs, XML, code retour et empreintes restent locaux sous `.codex-tests` ;
ils ne sont pas inclus dans le ZIP. Aucun environnement, cache, secret ou dump livré.

Les **625 empreintes** des sources applicatives, tests, SQL et configurations
contrôlées sont identiques avant/après, avec contrôle des fichiers ajoutés/supprimés.
Les documents et livraisons ont pu avancer pendant l'exécution ; aucun code testé
n'a changé. Le périmètre exclut environnements, caches, uploads et dépendances installées.

Cette suite inclut les recettes connectées navigateur, tests API et unitaires.
Les tests PostgreSQL utilisent exclusivement les clusters isolés contrôlés par
les fixtures. Les tests purs et supports synthétiques restent distincts de ces
parcours. L'ancien banc PostgreSQL non isolé est exclu par le runner.
**Aucun PostgreSQL réel ni aucune donnée comptable réelle utilisés.**

L'échec de la globale 264 et les quatre échecs de 278 sont conservés historiquement.
La cause des dates balances de 264 a été reproduite et corrigée dans 266.
Les trois supports simulés 073 ont été complétés dans 285 ; les assertions
restent inchangées. Le diagnostic du mobile 280 préserve désormais l'exception
initiale ; son échec de 278 n'a pas été reproduit seul et sa cause reste non établie.
Le parcours 283 prolonge maintenant les réceptions partielles jusqu'aux deux paiements
et au lettrage. Une réussite ciblée n'a jamais été présentée comme une globale verte.

Développement global partiel ; recette utilisateur à effectuer et mise en production
non validée. Cette exécution ne confirme aucune certification ni conformité officielle.
Les références sociales, XML/EDI applicable et justificatifs historiques manquants
restent soumis aux limites documentées.
