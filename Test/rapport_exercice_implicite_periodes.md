# Lot318 — exercices implicites et périodes persistées

## Problème réellement reproduit

Une écriture de capital fictif datée31/12/2025 pouvait répondre500 lorsque
l'exercice2025 n'avait pas été créé explicitement. La création implicite d'un
exercice antérieur est pourtant prévue par `trouver_exercice_pour_date`.

La régression utilise une vraie inscription HTTP, la vraie API d'écritures et
un cluster PostgreSQL éphémère vérifié URL/dossier/nonce. Elle ne prépare pas
l'exercice antérieur pour masquer le problème. Le journal de la vraie API
conserve le traceback :

```text
psycopg2.errors.RaiseException:
Aucune période comptable ne couvre la date 2025-12-31 de l'exercice 2025
CONTEXT: PL/pgSQL function hisabpro_verifier_periode_ecriture() line30 at RAISE
routers/ecritures.py, creer_ecriture, db.flush()
```

`SessionLocal` désactive l'autoflush. `ensure_exercice` persistait l'exercice,
mais ses douze périodes restaient dans la session avant l'insertion de
l'écriture. Le contrôle applicatif acceptait une période absente, puis le
trigger PostgreSQL refusait l'insertion. Un exercice existant sans périodes
ou un calendrier partiel ne couvrant pas la date pouvait également répondre500.

## Correction minimale

Seul le service métier `services/exercices_service.py` change :

- les périodes nouvellement créées sont flushées dans la transaction courante,
  avant le contrôle et l'insertion de l'écriture ; aucun commit ajouté ;
- après le refus d'exercice clôturé, un exercice sans aucune période bénéficie
  de la préparation déjà prévue par `ensure_exercice` ;
- si un calendrier existant ne couvre pas la date, une erreur métier explicite
  est levée ; la route d'écritures la traduit en423.

Un calendrier partiel reste intact. Les périodes fermées ne sont jamais
rouvertes par ce flux. Aucun trigger, migration ou historique comptable modifié.

## Tests exécutés

Toutes les commandes utilisent `PYTHON_DOTENV_DISABLED=1` et le runner isolé.

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_exercice_implicite_periodes_postgres.py -vv --tb=short --junitxml=.codex-tests/exercice_implicite_318_avant.xml
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_exercice_implicite_periodes_postgres.py -vv --tb=short --junitxml=.codex-tests/exercice_implicite_318_apres.xml
```

Avant correction : **5échecs, 3réussites, 25avertissements, 26,45 s, code1**.
Quatre erreurs applicatives500 sont reproduites : création implicite, exercice
existant sans périodes, parcours multi-société et calendrier partiel.
Le cinquième échec était une attente incorrecte du test : une écriture
déséquilibrée est déjà refusée422 par Pydantic avant le service ; l'attente400
a été corrigée sans modifier ce comportement. XML et journaux API authentiques
restent conservés en cache, dont `exercice_implicite_318_api_echec_f4491fb1d1.log`.

Après correction : **8réussites, 25avertissements, 24,57 s, code0**.

Les huit cas vérifient :

- exercice antérieur absent, puis exercice existant sans aucune période :201,
  douze périodes ouvertes persistées et écriture initialement en brouillon ;
- validation explicite du capital1000 :5141 débit1000, 1111 crédit1000,
  mêmes lignes et montants après validation ;
- mauvaise balance422 et compte hors plan400 : aucune création durable
  d'exercice, période, écriture, ligne ou audit de période ;
- période fermée et exercice clôturé :423 et photographie inchangée ;
- deuxième société : aucune création d'exercice ni d'écriture, validation de
  l'écriture de la première société refusée404 ;
- exercice historique avec seule périodejanvier : écrituredécembre423,
  aucun ajout de onze périodes et aucune mutation.

Compilation Python des deux fichiers modifiés : **code0**, 0,47 s.

Suite ciblée et connexe : **60réussites, 25avertissements, 41,79 s, code0**,
dont les huit nouveaux cas et52cas connexes, neuf modules :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_exercice_implicite_periodes_postgres.py Test/test_patch04b_exercices.py Test/test_patch055_plan_societe_exercices_decales.py Test/test_session132_admin_exercices_lecture.py Test/test_patch04_cloture_service.py Test/test_patch085_ecritures_sans_reference_inventaire_cloture.py Test/test_inventaire_comptage_complet.py Test/test_patch069_stock_services.py Test/test_session133_cloture_postgres.py --tb=short --junitxml=.codex-tests/exercice_implicite_318_connexes.xml
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile hisabpro-backend/services/exercices_service.py Test/test_exercice_implicite_periodes_postgres.py
```

Les connexes couvrent les dates décalées, la lecture administrative des exercices,
la clôture, les justificatifs d'inventaire, le comptage et les services de stock,
ainsi que la clôture sur PostgreSQL nonce.

## Limites

Tous les chiffres et états de fermeture sont exclusivement fictifs, dans le
cluster appartenant à la fixture. Aucune base PostgreSQL utilisateur appelée,
aucune donnée comptable réelle ni migration modifiée. Aucun contournement
du trigger d'intégrité. La recette navigateur et la recette annuelle utilisateur
ne sont pas déclarées validées par ces tests API.
