# Recette Edge sous LOGIN PostgreSQL applicatif — lot 442

Le support E2E accepte une préparation facultative avant le lancement de l'API.
La connexion reste exclusivement dérivée du cluster nonce créé par le banc,
avec le seul rôle hisabpro. Aucun serveur de production ou URL externe reçu.
Le comportement par défaut du support est conservé.

La préparation explicite exécute 78 SQL distincts : les 64 candidats historiques
001–073 (exclusions conservées), 074–082, puis 083–087. Chaque application est
précédée et suivie d'un contrôle de tables métier vides. Les empreintes des SQL
sont conservées en mémoire et recontrôlées avant arrêt. Aucun traitement de
réparation historique, seed paie, migration réelle ou donnée réelle.

## Résultats réellement exécutés

Cinq parcours Edge réussis en 59.66 s, puis 15 tests connexes réussis en 234.142 s
(durée XML), zéro échec, erreur ou ignoré. Compilation des trois fichiers
Python modifiés/ajoutés : code 0. Avertissements de dépréciation existants.
Ces suites se recouvrent : ne pas additionner leurs résultats.

- Factures vente et achat saisies dans l'interface, validation, comptabilisation,
  règlements partiels 400 puis 800, validation du Journal et lettrage des trois
  lignes du collectif. Trois pièces, débit=crédit=2400, collectif soldé.
- Import d'un CSV bancaire de 1200, soldes, pointage explicite, rechargement et
  doublon. L'écriture définitive d'apport fictif reste intégralement inchangée.
- Propositions bureau1365/mobile390 : ligne bancaire de240 pour deux lignes120
  et paiement simple60 ; sélection partielle, confirmation, recalcul puis
  rechargement. Origines comptables conservées, aucune nouvelle écriture créée.
- Refus du préparateur si rôle SUPERUSER ou membre du migrateur, et exception
  volontaire pendant préparation : serveur non exposé, répertoires nonce nettoyés.
- Les anciens parcours par défaut administration, facturation, rapprochement
  et téléchargements CSV bureau/mobile restent exécutés dans la suite connexe.

Le serveur est réellement `main:app` sous DATABASE_URL hisabpro, avec
HISABPRO_CREATE_TABLES=false et dotenv désactivé. Aucune route, authentification
ou opération métier n'est interceptée. Le rôle LOGIN est contrôlé avant le
serveur : ni propriétaire d'objet/fonction, ni membre du migrateur, ni SUPERUSER,
CREATEDB, CREATEROLE, REPLICATION ou BYPASSRLS. Des connexions hisabpro réelles
sont constatées via pg_stat_activity avant la fermeture. Serveurs et bacs arrêtés.

Commande connexe : `Test/run_unit_tests.py` avec
`test_e2e_runtime_consolide_isole.py`, `test_support_e2e_runtime.py`,
`test_e2e_facturation_isole.py`, `test_e2e_administration_isole.py`,
`test_e2e_rapprochement_isole.py` et `test_e2e_csv_partage_isole.py`.
Preuves locales : runtime442_cibles et runtime442_connexes XML/log/exit.

## Limites

Le banc utilise des sociétés et pièces fictives sur PostgreSQL jetable.
La préparation n'est pas une procédure de migration d'une base existante.
Les droits des autres modules restent à qualifier ; aucun déploiement réel,
recette humaine, contrôle réglementaire officiel ou restauration de production
validé. Aucun changement du code produit/main/models/schemas ou SQL pendant442.
Point 6 toujours en attente. Prochaine étape : recette d'installation consolidée
087 et maintien explicite des limites de restauration/provisionnement.
