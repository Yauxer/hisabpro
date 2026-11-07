# Recette connectée du dégressif existant — lot 382

Ce lot ajoute uniquement un oracle et des tests. Les coefficients, calculs, règles fiscales, modèles et migrations existants ne sont pas modifiés. La recette du produit ne vaut pas qualification fiscale d'un investissement réel.

## Oracle indépendant

`docs/recette/oracle_degressif_60000_5_ans.json` : bien fictif HT 60 000 MAD, TVA 12 000, TTC 72 000, durée cinq ans, coefficient existant 2, taux 40 %, acquisition au 1er janvier. Les cinq années utilisées par le test précèdent l'année courante, afin de ne pas traiter une dotation future comme déjà échue.

| Année du plan | Dotation MAD | Cumul MAD | VNC MAD |
|---|---:|---:|---:|
| 1 | 24 000 | 24 000 | 36 000 |
| 2 | 14 400 | 38 400 | 21 600 |
| 3 | 8 640 | 47 040 | 12 960 |
| 4 | 6 480 | 53 520 | 6 480 |
| 5 | 6 480 | 60 000 | 0 |

Le calcul indépendant compare annuellement 40 % de la valeur restante et la valeur restante divisée par les années résiduelles. La bascule linéaire est donc attendue en année 4. Le test de l'oracle n'appelle aucun service de production.

## Parcours réel

Edge crée l'immobilisation, sélectionne le dégressif et contrôle le tableau annuel. L'acquisition est validée par API puis photographiée. Les cinq dotations sont générées dans l'interface, une par exercice, et validées dans le journal.

Acquisition exacte : débit 2355 = 60 000, débit 34551 = 12 000, crédit 4481 = 72 000. Cinq dotations débit 61935/crédit 28355, cumul 60 000. **Six écritures validées**, débit = crédit = **132 000 MAD**. L'acquisition définitive est conservée ; une nouvelle génération de la dernière année produit zéro écriture et ne modifie aucune source.

Cible PostgreSQL nonce temporaire, API réelle et Edge ; aucun PostgreSQL réel ni donnée comptable de l'utilisateur.

## Exécutions

- Premier passage : **14 réussites / 1 échec**, 26 avertissements, 22,94 s. La fixture comparait le Decimal sérialisé `60000.00` à un entier ; comparaison corrigée en Decimal exact.
- Relance oracle, Edge et tests purs d'amortissement : **15 réussites**, 26 avertissements, 25,52 s, code 0.
- Oracle et Edge dégressif, acquisition linéaire et sorties existantes : **5 réussites**, 26 avertissements, 72,81 s, code 0. Ces suites se recoupent ; effectifs non additionnés.

La réévaluation, les acquisitions réelles, les pièces justificatives et l'éligibilité fiscale restent hors de ce test. Recette utilisateur et point 6 en attente. Nouveaux fichiers intégrés après consolidation378.

## Contrôle final dans le dépôt courant

2 tests réussis,0échec/erreur/ignoré,21.159s,code0,à la racine intégrée sur cibles nonce. Suites copie distinctes non additionnées.

La globale378 précède ce changement. Les consommateurs règlement/RAS finaux seront consolidés séparément dans385.
