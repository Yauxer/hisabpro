# Variante annuelle connectée — ventilation 2025, report et règlement 2026

Lot 380 : extension de la recette automatisée, sans changement des règles métier. Le scénario ne remplace pas le cahier de recette utilisateur complet de 218 cas.

## Données et oracle

Société fictive de laboratoire, capital 1 000 MAD, exercices 2025/2026. Deux factures clients et deux factures fournisseurs : HT 100/200, TVA 20/40, TTC 120/240 dans chaque sens. Aucun stock ni relevé bancaire fictif n'est déduit de ces paiements.

La ventilation 2025 règle 120 MAD sur chaque facture, soit 240 MAD par tiers. Les factures TTC 240 gardent donc chacune 120 MAD de solde. L'oracle indépendant est livré dans `docs/recette/oracle_annee_ventilation_2025_2026.json`.

- Avant impôt : **9 écritures, 22 lignes, débit = crédit = 2 200 MAD** ; clients 120, fournisseurs 120, banque 1 000.
- TVA à l'encaissement du laboratoire : collectée 40, récupérable 40, solde 0.
- Clôture : impôt de laboratoire 3 000 selon le paramétrage existant de l'oracle annuel. Ceci ne qualifie pas l'imposition réelle d'une société.
- À-nouveaux 2026 : **débit = crédit = 4 180 MAD**, avec rattachement natif des deux tiers.
- Compléments 2026 : 120 MAD client et 120 MAD fournisseur, validation puis lettrage avec les lignes reportées.
- Balance 2026 exportée : **totaux nets débit = crédit = 4 060 MAD** ; collectifs clients/fournisseurs soldés.

## Parcours réellement exécuté dans la copie

Préconditions par API réelle ; ventilation dans Edge, validation des neuf brouillons dans le journal, refus de lettrage déséquilibré, lettrage des premières factures soldées, déclaration TVA, clôture dans Edge, à-nouveaux, règlements 2026 et validation dans Edge, lettrage des reports, visibilité des factures 2025 depuis les règlements 2026, contrôles et téléchargements FEC 2025/2026, téléchargement Excel de la balance.

Les écritures sources définitives sont photographiées et comparées après clôture et paiements suivants. La cible est un PostgreSQL temporaire isolé par nonce ; aucun PostgreSQL réel de l'utilisateur.

## Résultats

- Première exécution : **1 réussite / 1 échec**, 26 avertissements, 26,95 s. La fixture remplaçait la facture par la réponse de validation, qui ne contient pas son identifiant ; correction de la fixture en conservant l'identifiant de création.
- Relance : **2 réussites**, 26 avertissements, 27,88 s, code 0, oracle et parcours connecté.
- Connexes annulation 381 : les deux tests repassent dans la suite de **53 réussites**, 154,78 s. Effectifs non additionnés.

## Limites

Le scénario requiert la projection inter-exercices du lot 379. Ni production, ni recette humaine, ni conformité réglementaire ne sont validées automatiquement. Le rapprochement d'un paiement ventilé avec une seule ligne bancaire et la représentation d'un instrument bancaire unique restent à traiter séparément.

Fichiers intégrés après la consolidation378.

## Contrôle final dans le dépôt courant

2 tests réussis,0échec/erreur/ignoré,25.987s,code0,à la racine intégrée sur cibles nonce. Suites copie distinctes non additionnées.

La globale378 précède ce changement. Les consommateurs règlement/RAS finaux seront consolidés séparément dans385.
