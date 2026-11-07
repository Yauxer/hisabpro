# Personnel & Paie — Lot 0 : tests exécutés et reprise

Date :27/10/2026. Tous les tests sont réellement exécutés dans cette session. Les caractérisations constatent l’existant ; les futurs critères du master ne sont pas déclarés satisfaits.

| Campagne | Cas | Échecs / erreurs / ignorés | Durée JUnit |
|---|---:|---|---:|
| personnel871_unitaires | 69 | 0 / 0 / 0 | 12.05s |
| personnel871_api_pg | 132 | 0 / 0 / 0 | 159.0s |
| personnel871_navigateur | 7 | 0 / 0 / 0 | 118.53s |
| personnel871_constats | 3 | 0 / 0 / 0 | 27.48s |
| personnel871_dependances | 30 | 0 / 0 / 0 | 163.85s |

Total : **241 réussis**. Répartition :105unitaires/validations de schéma,127cas API/SQL/bootstrap sur PostgreSQL natif éphémère,9parcours Edge avec API/PG réellement connectés. La campagne132 comprend36validations de schéma et96cas API/PG ;les30dépendances comprennent28cas API/SQL/bootstrap et2Edge. Les9Edge utilisent aussi PostgreSQL :ils ne sont pas additionnés une seconde fois dans les127.

Build Vite :code0,11,51s ;temps total de la commande16,66s. Avertissements existants :taille des chunks et import statique/dynamique de xlsx. Ce build est un état de référence ;aucun composant frontend n’a été modifié.

Compilation :les deux nouveaux scripts Python sont compilés avec py_compile. L’inventaire est régénéré et comparé à l’identique. MatriceRBAC :25capacités uniques,9colonnes et valeursH/M/- vérifiées. Ces contrôles documentaires ne sont pas comptés comme de nouveaux cas pytest.

## Sécurité des exécutions

python-dotenv désactivé avec PYTHON_DOTENV_DISABLED=1. DATABASE_URL du processus de collecte fixé à une URL fictive injoignable127.0.0.1:1 ;les fixtures ouvrent exclusivement leurs clusters PostgreSQL natifs temporaires,avec nonce et ports dédiés. Les serveurs/applications de test sont séparés de main.py et du PostgreSQL utilisateur ;le test de démarrage main est exécuté uniquement dans son processus et cluster isolés. Aucun fichier.env n’est lu pour configurer ces tests.

Les tests utilisent des paramètres pédagogiques explicites et vérifient leur arithmétique ;ils ne constituent pas une confirmation réglementaire des taux. Le registre095,les clés composites,la concurrence et les permissions sont testés sur PostgreSQL natif ;SQLite ne sert pas de substitut. Aucune restauration nouvelle de paie complète n’est revendiquée ici.

## Reproduire les campagnes

Depuis la racine,sous un environnement de test avec PYTHON_DOTENV_DISABLED=1 et une DATABASE_URL sentinelle injoignable :

```text
.\hisabpro-backend\.venv\Scripts\python.exe -m pytest Test/test_paie_grh_service.py Test/test_grh_absences_service.py Test/test_paie_referentiel_service.py -q
```

```text
.\hisabpro-backend\.venv\Scripts\python.exe -m pytest Test/test_paie_grh_postgres.py Test/test_grh_absences_postgres.py Test/test_paie_referentiel_postgres.py Test/test_parametres_paie_finis.py -q
```

```text
.\hisabpro-backend\.venv\Scripts\python.exe -m pytest Test/test_e2e_paie_grh_isole.py Test/test_e2e_paie_referentiel_isole.py Test/test_e2e_grh_absences_isole.py -q
```

```text
.\hisabpro-backend\.venv\Scripts\python.exe -m pytest Test/test_audit_personnel_paie871_isole.py -q
```

```text
.\hisabpro-backend\.venv\Scripts\python.exe -m pytest Test/test_demarrage_grh_base_existante_postgres.py Test/test_avances_salaries_isole.py -q
```

## Preuves et limites

[Preuve structurée](../../Test/PREUVE_PERSONNEL_PAIE_LOT0_871.json) ;JUnit et constats dans Test/preuves_personnel871. Les cas C01/C02 constatent des écarts à corriger au Lot1 ;C03 confirme le refus commercial hors facture. Lors du basculement1A,remplacer les attentes AS-IS de C01/C02 par les nouveaux refus/masques et conserver ce rapport comme historique.

Les463sources du candidat865,le master et les migrations existantes restent inchangés. PostgreSQL utilisateur,environnement de déploiement,recette humaine et règles réglementaires applicables ne sont pas validés par cette session. Aucune nouvelle route/section/sidebar ou fonction de paie n’est annoncée comme livrée.

## Point de reprise exact

Lot0A/B/C documenté ;prochaine action :examiner les choixD01àD08 dans LOT0_CONCEPTION.md,en particulier le périmètre d’habilitations du pilote,puis lancer uniquement LOT1A_PLAN.md. Ne pas démarrer le moteur de paie ou les neuf écrans en bloc. Avant1A,relire le journal,l’état du dépôt,le master et vérifier les numéros de migrations libres.
