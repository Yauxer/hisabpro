# Consolidation connexe règlement / RAS — lot385

Exécution réelle sur les versions intégrées379/381/380/382, **avant la garde de contexte388**. Commande `.codex-tests/consolidation385_connexe.py`, utilisant le runner isolé sur les 21 fichiers listés ci-dessous, `.env` désactivé.

Résultat : **228 réussites**,0échec/erreur/ignoré,26avertissements,691.620s,code0. **701 empreintes** de sources/SQL/tests/assets/configurations identiques avant/après.

Tests unitaires et vraie API/PostgreSQL nonce/Edge selon les bancs ; aucun PostgreSQL ou donnée réelle de l'utilisateur. Les suites se recoupent et ne sont pas additionnées. Cette consolidation connexe n'est pas une globale de tous modules.

## Fichiers exécutés

- `Test/test_annulation_ventilation_isole.py`
- `Test/test_e2e_annee_ventilation_inter_exercices_isole.py`
- `Test/test_e2e_ras_capture_isole.py`
- `Test/test_e2e_ras_editeur_diagnostic_isole.py`
- `Test/test_e2e_ras_indicateurs_inconnus_isole.py`
- `Test/test_e2e_ras_situation_isole.py`
- `Test/test_e2e_ras_solde_lettrage_isole.py`
- `Test/test_e2e_reglement_edition_isole.py`
- `Test/test_e2e_reglements_par_tiers_isole.py`
- `Test/test_lecture_reglements_historiques.py`
- `Test/test_ras_capture_migration_isole.py`
- `Test/test_ras_capture_reglement_postgres.py`
- `Test/test_ras_consommateurs_inconnus_postgres.py`
- `Test/test_ras_estimation_solde_postgres.py`
- `Test/test_ras_historique_annulation_postgres.py`
- `Test/test_ras_lecture_conservation.py`
- `Test/test_ras_taux_finis.py`
- `Test/test_reglements_inter_exercices_isole.py`
- `Test/test_reglements_montants_finis.py`
- `Test/test_reglements_pagination_isole.py`
- `Test/test_reglements_par_tiers_isole.py`

## Portée et suite

La globale378 (3241réussites) couvre l'état après377 et avant379/381. Cette suite385 contrôle leurs consommateurs, mais ne couvre pas le correctif388 découvert ensuite. Les réponses tardives de preview sont reproduites et corrigées dans un lot distinct, puis la consolidation389 doit vérifier les versions finales.

Recette humaine et production non validées ; point6 en attente. Paie définitive/EDI restent bloqués par les preuves applicables, instrument bancaire unique/rapprochement à une ligne encore partiels.
