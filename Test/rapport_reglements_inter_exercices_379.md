# Règlements de factures d'un exercice précédent — lot 379

## Cause et correction

La liste des règlements était filtrée sur l'année du paiement, mais son dictionnaire de factures ne contenait que les factures de cette même année. Un paiement 2026 d'une facture 2025 était donc éliminé du cycle achat/vente dans l'interface.

La lecture des règlements expose cinq informations issues de leur facture native : type, numéro, exercice, statut et qualification des montants. La recherche reste strictement limitée à la société active et aux identifiants réellement liés. Le frontend utilise cette projection seulement lorsque la facture manque dans son dictionnaire de l'année courante. Les calculs et diagnostics restent ceux de la lecture métier des factures.

Aucune migration, écriture ou réparation de données historiques. Un lien absent ou étranger ne reçoit aucune information de facture.

## Exécutions dans la copie isolée

Commandes via `Test/run_unit_tests.py`, avec `PYTHON_DOTENV_DISABLED=1`, PostgreSQL éphémère protégé par nonce et Edge réel. Les sources originales restent figées pour la consolidation 378.

- Avant correction : un scénario Edge vente reproduit l'absence du règlement, **1 échec**, 30,35 s.
- Première relance : **28 réussites / 8 échecs**, 158,64 s. Le contrôle de présence des lignes passe ; les huit échecs proviennent du numéro récupéré avant validation de la facture. La fixture conserve ensuite le numéro réel attribué à la validation.
- `test_reglements_inter_exercices_isole.py`, lecture historique et pagination : **36 réussites**, 26 avertissements, 161,17 s, code 0.
- Version finale, avec les deux refus de projection étrangère/absente, et ventilation par tiers : **43 réussites**, 26 avertissements, 150,31 s, code 0.

Ces suites se recoupent : leurs effectifs ne sont pas additionnés.

Les dix nouveaux cas couvrent achat/vente, bureau 1365 px/mobile 390 px, paiement partiel ou complet, statut exact, changement de cycle, seconde société et conservation des sources à la lecture.

## Vérification utilisateur

Dans une société de recette isolée : facture validée 2025 TTC 120 MAD, règlement 2025 de 60 MAD puis règlement 2026 de 60 MAD. Sélectionner 2026, **Cycle commercial → Vente → Règlements** : le paiement 2026 apparaît avec le numéro de la facture 2025 et le statut Soldée. Vérifier aussi le sens achat et le statut Partiel avec un complément de seulement 20 MAD.

La recette humaine et PostgreSQL de l'utilisateur ne sont pas exécutés par cette livraison. Aucun accès à ses données réelles.

## Intégration dans le dépôt

Intégration explicite après fin de la globale378 et vérification des empreintes, sans écraser une source concurrente.

## Contrôle final dans le dépôt courant

10 tests réussis,0échec/erreur/ignoré,37.406s,code0,à la racine intégrée sur cibles nonce. Suites copie distinctes non additionnées.

La globale378 précède ce changement. Les consommateurs règlement/RAS finaux seront consolidés séparément dans385.
