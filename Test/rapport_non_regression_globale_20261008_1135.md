# Consolidation globale HisabPro — 8 octobre 2026, reprise11:16UTC

## Résultat réellement exécuté par le principal

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test --tb=short --show-capture=no --junitxml=.codex-tests/global_20261008_1135.xml > .codex-tests/global_20261008_1135.log 2>&1
```

Session de commande97748 : **code0,2199réussis,0échec,0erreur,0ignoré**,
1422,89secondes (23min42s),32avertissements des dépendances. Le XML réel est
relu : tests2199,failures0,errors0,skipped0. L'exécution termine avant les
changements commerciaux suivants ; leur validation est distincte.

## Périmètre

Sources applicatives stabilisées après227/228 (preuves documentaires paie),
230 (protections082 au démarrage),231 (installation),232 (annexe de recette)
et233 (édition cohérente des règlements). Les agents ne modifient aucune
source applicative pendant cette commande. Les empreintes enregistrées
localement sur2995fichiers sources sont identiques à la fin. Ce contrôle
n'est pas un commit Git : le dossier n'a pas de dépôt Git.

La liste réelle des cas du XML ne contient pas les nouveaux fichiers ajoutés
après collecte : erreurs d'écriture237, sauvegardeGRH239, sortie d'immobilisation
243, diagnostic stock des devis et pièces de réception client. Les trois
premiers ont leurs commandes ciblées réellement réussies dans leurs rapports.
Leurs nombres ne sont pas ajoutés à2199. Les deux derniers sont encore en cours
à cette consolidation et ne sont pas déclarés validés ici.

Le résultat global antérieur218 (2060cas) reste historique, avant226et suivants.
Les premières exécutions échouées et erreurs de préparation des lots ciblés
sont conservées dans leurs rapports ; elles ne sont pas transformées en succès.

## Isolation et limites

Le runner désactive dotenv et protège les imports unitaires. Les tests
PostgreSQL utilisent exclusivement leurs clusters éphémères avec nonce,
répertoire et URL vérifiés ; les navigateurs parlent aux API de ces laboratoires.
Le vieux banc `test_patch07b3_postgres_sequences.py`, pouvant muter une cible
non isolée, reste explicitement exclu du runner, pas exécuté puis caché comme
un test ignoré. Aucune donnée comptable réelle ni processus utilisateur utilisé.

Ce succès valide la collecte et les scénarios exécutés. Il ne valide pas
automatiquement la recette utilisateur, les justificatifs réels, les taux
sociaux officiels, les formats DGI ou la mise en production. Les nouvelles
pièces de réception client et alertes de devis nécessitent leurs propres
tests puis une consolidation sur leurs sources finales.
