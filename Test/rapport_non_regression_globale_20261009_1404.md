# Non-régression globale du 9 octobre 2026 — sources figées

Exécution réelle par le principal, commencée vers 14:26 UTC après les lots 266–280.
Session outil 47789 ; code retour final **1** conservé dans un fichier local.

Résultat : **2575 réussis, 4 échec, 0 erreur, 0 ignoré ; code retour 1**, sur **2579 cas collectés**.
Résumé pytest exact : `========== 4 failed, 2575 passed, 32 warnings in 2079.35s (0:34:39) ===========`.
XML final relu, tous les cas comptés et comparés au résultat de la commande.

Commande exécutée avec `PYTHON_DOTENV_DISABLED=1` et le Python de la `.venv` backend :

```text
python -X utf8 Test/run_unit_tests.py Test -vv --tb=short --show-capture=no --junitxml=.codex-tests/global_20261009_1404.xml
```

Les logs, XML, code retour et empreintes restent locaux sous `.codex-tests` ;
ils ne sont pas inclus dans le ZIP. Aucun environnement, cache, secret ou dump livré.

Les **623 empreintes** des sources applicatives, tests, SQL et configurations
contrôlées sont identiques avant/après, avec contrôle des fichiers ajoutés/supprimés.
Les documents et livraisons ont pu avancer pendant l'exécution ; aucun code testé
n'a changé. Le périmètre exclut environnements, caches, uploads et dépendances installées.

Cette suite inclut les recettes connectées navigateur, tests API et unitaires.
Les tests PostgreSQL utilisent exclusivement les clusters isolés contrôlés par
les fixtures. Les tests purs et supports synthétiques restent distincts de ces
parcours. L'ancien banc PostgreSQL non isolé est exclu par le runner.
**Aucun PostgreSQL réel ni aucune donnée comptable réelle utilisés.**

L'échec de la globale 264 est conservé historiquement. Sa cause de dates balances
a été reproduite et corrigée dans 266 ; le cas comparatif figure dans cette nouvelle
exécution. Une réussite ciblée ancienne n'a jamais été présentée comme une globale verte.

Développement global partiel ; recette utilisateur à effectuer et mise en production
non validée. Cette exécution ne confirme aucune certification ni conformité officielle.
Les références sociales, XML/EDI applicable et justificatifs historiques manquants
restent soumis aux limites documentées.

## Échecs réellement observés

- Test.test_e2e_cycle_achat_reception_partielle_isole::test_cycle_reception_partielle_stock_br[390]
- Test.test_patch073_actualisation_edition_facture::test_073_sauvegarde_simulee_et_ordre_des_evenements[succes]
- Test.test_patch073_actualisation_edition_facture::test_073_sauvegarde_simulee_et_ordre_des_evenements[erreur_patch]
- Test.test_patch073_actualisation_edition_facture::test_073_sauvegarde_simulee_et_ordre_des_evenements[attente_actualisation]
