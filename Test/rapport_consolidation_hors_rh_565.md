# Qualification financière finale565 — 18 octobre 2026

Cette qualification porte sur les sources finales des lots553–567, sans
développer la RH/paie. Aucun PostgreSQL réel ou donnée comptable réelle utilisé.

## Consolidation principale

Commande réellement exécutée :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
python -u -X utf8 Test/run_unit_tests.py Test/test_consolidation_factures543_isole.py -ra --junitxml=.codex-tests/financier565.xml
```

Résultat : **356 réussis,29 avertissements,1183,64s, code0**.
Aucun test échoué ou ignoré dans cette commande. Les avertissements sont
consignés dans le journal brut, sans être comptés comme des échecs.

Cette suite réutilise les scénarios connectés existants : documents commerciaux,
factures/avoirs, validation, écritures, règlements, lettrage, périodes, clôture,
permissions et concurrence, sous LOGIN applicatif limité sur cluster natif
PostgreSQL nonce098. Le banc vérifie les sources et détruit ses cibles isolées.
Ce regroupement ne remplace pas les cas ciblés des nouvelles fonctions555,
559 et561, exécutés séparément et détaillés dans leurs rapports.

## Suite connexe indépendante

Les25 fichiers sont ceux listés intégralement dans le
[rapport538](rapport_factures_comptabilisation_concurrence_538.md), exécutés après
la fin de la consolidation principale, jamais en parallèle. Ils couvrent la
restauration098, les immobilisations, l'inventaire et les stocks, la fiscalité,
la clôture ainsi que les montants non finis. Les tests de calcul pur restent
distincts des essais PostgreSQL. Les anciens bancs propriétaires ne sont pas
présentés comme une qualification supplémentaire du LOGIN SQL limité.

Résultat connexe : **247 réussis,29 avertissements,218,79s, code0**.
Aucun échec ni test ignoré. Les deux commandes représentent603 exécutions,
sans addition des suites ciblées recouvrantes des lots précédents. Dans chacune,
les29 avertissements concernent la configuration Pydantic historique et un
module anyio déjà importé pour la réécriture des assertions.
Preuves : `.codex-tests/financier565_externes.log`, `.exit` et `.xml`.

## Intégrité de livraison

- 876 fichiers de code figés pendant la qualification principale ; empreintes
  identiques au contrôle après exécution. Aucun code modifié pendant les tests.
- 26 fichiers Python ajoutés ou modifiés compilés avec succès.
- Les sept archives553–567 sont non vides, CRC valides, chemins contrôlés ;
  les32 fichiers de code actuels correspondent aux dernières versions archivées.
- 98 fichiersSQL et115 documents antérieurs de guide/recette conservés.
  Avec AGENTS, le démarrage, les modèles et les fichiers RH protégés :218
  fichiers inchangés. Aucun commit, push ou changement de base utilisateur.
- Les builds des interfaces modifiées ont réussi dans leurs lots respectifs.

Les résultats ciblés et connexes peuvent se recouvrir : ne pas les additionner
pour annoncer un nombre de fonctionnalités ou une couverture exhaustive.

## Limites et reprise

Développement global encore partiel. La simulation RAS TVA ne comptabilise pas
de retenue effective ; le catalogue officiel DGI, les annexes et le mode liasse
seule restent incomplets. Aucun schéma XML/EDI inventé, aucune réparation
silencieuse d'écriture ou des reliquats historiques FEC/ETIC.

La recette utilisateur, les vérifications visuelles sur l'installation cible,
son chemin réel de migration et sa restauration restent à effectuer. La mise
en production et la conformité réglementaire ne sont pas déclarées validées.
Le point6 attend le retour utilisateur. La RH/paie reste différée.

Voir le [plan de finalisation horsRH](../docs/audit/PLAN_FINALISATION_HORS_RH_20261018.md).
