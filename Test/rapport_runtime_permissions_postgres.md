# Droits PostgreSQL runtime — recette isolée du 7 octobre 2026

## Portée

Les sessions SQL utilisées par la vraie route FastAPI d'écritures se connectent
avec le rôle `hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION
NOBYPASSRLS`. Le propriétaire des objets est le rôle distinct
`hisabpro_recette`, exclusivement dans un nouveau cluster de recette.
`current_user` et `session_user` valent tous deux `hisabpro` : il ne s'agit
pas d'une connexion superuser dont les droits seraient supposés restreints.

Le test contrôle aussi l'absence de propriété sur les tables et fonctions,
d'appartenance au rôle propriétaire et de droit `CREATE` dans `public`.
La fixture révoque `CREATE` à `PUBLIC` dans le seul cluster temporaire.

Le rôle SQL reçoit une liste explicite de droits métier et de séquences,
sans `GRANT ALL` ou `GRANT ... ON ALL TABLES` ajouté par ce test. Le schéma
est créé par les modèles et les migrations déjà utilisées par session132,
complétées par `036`, `027` et `071`. Ce sous-ensemble sert ce parcours ciblé ;
il n'est pas un manifeste complet d'installation.

## Protections réellement vérifiées

- Route API réelle : création d'un brouillon équilibré banque/capital de
  1 000 MAD, validation et numéro `OD-2025-0001`.
- Triggers et fonctions `SECURITY DEFINER` : audit comptable et incrément du
  compteur interne sans permission directe d'écriture sur ces tables.
- Fonction de journalisation applicative : un événement synthétique est
  inscrit, malgré le refus d'INSERT direct sur `audit_actions`.
- Fermeture/réouverture d'une période synthétique : deux traces avec acteur
  dans `audit_periodes_comptables`, malgré le refus d'INSERT direct.
- INSERT versionné permis dans l'archive de liasse et la préparation de balance.
- Refus SQLSTATE `42501` pour UPDATE, DELETE et TRUNCATE sur les trois audits,
  l'archive de liasse et les préparations ; INSERT direct dans les trois audits.
- Refus SQLSTATE `42501` pour création de table, désactivation de triggers,
  suppression d'archive, remplacement de fonction d'audit, écriture directe
  du compteur comptable et adoption du rôle propriétaire.
- Les droits UPDATE/DELETE métier ne permettent pas d'altérer une écriture
  définitive ou ses lignes : refus SQLSTATE `23514` par les vrais triggers.

Chaque refus est contrôlé à partir du code SQLSTATE et suivi d'un rollback.
Une exception SQL indépendante de la protection attendue ne suffit pas à
faire passer le test. Les tests peuvent être lancés séparément : le prérequis
comptable définitif est une fixture dédiée, sans dépendance à l'ordre des cas.

## Sécurité de la cible

`cluster_isole` crée le cluster sous `.codex-tests`, avec nonce et marqueur,
base et rôle de recette dédiés, port différent de 5432 et écoute loopback.
`verifier_cible_isolee` contrôle l'URL propriétaire avant chaque groupe de DDL
et les scripts de migration. L'URL runtime est dérivée de cette seule URL ;
seul le nom du rôle est remplacé. L'API réutilise exclusivement cet engine.
Le contexte arrête le cluster et vérifie la disparition du dossier éphémère.
Aucun `.env`, aucune connexion réelle ni aucun schéma utilisateur existant
n'est utilisé. L'authentification applicative est injectée pour ce banc
TestClient ; ces cas prouvent les permissions SQL, pas une nouvelle recette
d'authentification ou de RBAC HTTP.

## Commandes et résultats

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_runtime_permissions_postgres.py -x
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_runtime_permissions_postgres.py Test/test_session132_bootstrap.py Test/test_fact11_production_hardening.py
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile Test/test_runtime_permissions_postgres.py
```

Premier parcours fonctionnel : **29 réussis, 0 échec, 0 ignoré, 10,76 s**.
Les deux essais initiaux ont échoué dans la fixture à cause d'ajouts de
comptes déjà initialisés par le produit (11,68 s et 11,82 s), puis corrigés
dans le test uniquement. Aucun défaut métier n'a été contourné.

Après ajout du test d'audit de période et du contrôle propriétaire des
fonctions, suite connexe : **51 réussis, 1 échec, 0 ignoré, 13,24 s**.
Les 30 tests runtime et les 10 tests bootstrap ont réussi. L'échec concerne
l'ancien scanner statique RBAC de `test_fact11_production_hardening.py`, qui
classe `/api/auth/mot-de-passe` comme mutation métier exigeant admin/comptable,
alors que cette route personnelle authentifiée doit rester accessible aux
lecteurs. Ce résultat a été remonté au responsable du lot ; il ne doit pas
être présenté comme une suite entièrement verte. Compilation Python : OK.

Après correction ciblée du scanner par le responsable du lot (authentification
personnelle exigée pour l'exception mot de passe), la même suite finale a été
réexécutée : **52 réussis, 0 échec, 0 ignoré, 13,38 s**. La désactivation dotenv
était explicite dans cette commande finale. Aucun changement produit n'a été
nécessaire au parcours SQL runtime.

## Limites et prochaines validations

Ces tests prouvent une configuration précise de droits dans un cluster neuf,
pas les droits effectifs d'un déploiement existant. L'ensemble des tables,
séquences, fonctions, exports et migrations de production reste à inventorier
dans un manifeste revu. Les migrations historiques `005` et `008` accordent
des droits sur toutes les séquences ; le lot ne revendique pas un contrôle
exhaustif du moindre privilège des séquences. Il ne change pas ces migrations.

La migration `027` octroie SELECT/INSERT sans révoquer d'éventuels droits
historiques supplémentaires. Le rôle neuf des 30 tests n'en possède pas.
Une expérience séparée, demandée après ces tests, a reproduit la limite sur
un deuxième cluster neuf : création d'une archive fictive, simulation d'un
droit TRUNCATE historique, puis rejeu de `027`. Le privilège subsiste et le
rôle applicatif non propriétaire peut faire passer le nombre d'archives de
1 à 0 par TRUNCATE, car le trigger couvre UPDATE/DELETE. Le rollback a
préservé cette archive et le cluster a été arrêté/nettoyé ; commande terminée
avec code 0. Cette reproduction ne prouve pas qu'une base existante possède
ces ACL. Une migration additive ciblée de révocation a été proposée au
responsable du lot ; l'ancienne migration n'a pas été modifiée.

Ne pas appliquer les droits de cette fixture comme script global de production.
Conserver un propriétaire/migrateur distinct, vérifier les memberships,
les ACL antérieures, les droits de création du schéma et l'audit effectif.
L'intégration avec un secret de connexion, TLS et le service supervisé
n'est pas couverte par ces tests loopback.
