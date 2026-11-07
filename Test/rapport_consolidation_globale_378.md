# Consolidation globale après377 — lot378

Commande réellement exécutée à la racine : `python -X utf8 Test/run_unit_tests.py Test -vv --tb=short --junitxml=.codex-tests/consolidation378_globale.xml`, dans le wrapper d'empreintes, avec `.env` désactivé.

Résultat : **3241 réussites**, **0 échec, 0 erreur, 0 ignoré**, durée **3877.960 s**, code **0**. Les avertissements figurent dans le journal brut `.codex-tests/consolidation378_globale.log` ; ils ne sont pas des réussites supplémentaires.

**697 fichiers sources/SQL/tests/configurations/assets** figés et identiques avant/après. Python et Node sont consignés dans `.sources.json`. Le runner exclut explicitement le banc07b3 susceptible de travailler sur un schéma non isolé. Les tests PostgreSQL/E2E exécutés utilisent leurs cibles temporaires protégées ; aucun accès au PostgreSQL ou aux données comptables réelles de l'utilisateur.

Avant la globale,11tests ciblés de clôture/menu/admin ont réussi en111,37s. Leurs résultats se recoupent avec cette suite et ne sont pas additionnés.

Cette preuve couvre les fichiers présents **après377, avant379/381**. Les nouveaux travaux ont été développés dans une copie isolée pendant le gel. Leur intégration ne commence qu'après la fin de cette suite. Une consolidation connexe distincte385 doit contrôler les versions finales ; elle ne remplace pas une nouvelle globale de tous modules.

La précédente globale373,3235réussis/4échecs, reste une preuve échouée conservée dans son rapport. Elle n'est pas requalifiée par cette exécution.

Développement global partiel. Recette utilisateur à effectuer ; paie définitive et EDI restent soumis à leurs preuves officielles. Point6 en attente de l'utilisateur, aucune préparation de production engagée. Aucune migration ou réparation historique dans ce lot.
