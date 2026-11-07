# Banque et relevés sous rôle applicatif — lot 441

La migration additive manuelle 087 complète uniquement les droits des routes
existantes : SELECT/INSERT/UPDATE sur comptes_bancaires ; les mêmes droits et
DELETE sur rapprochement_lignes. La suppression publique d'une banque reste
une désactivation. Les états 048 et ventilations 084 conservent leurs droits.
Les deux séquences reçoivent USAGE/SELECT, sans nouveau UPDATE/SETVAL.
Les droits historiques de séquence 005 restent inchangés, sans prétendre qu'ils
sont absents. Aucun TRUNCATE, CREATE, rôle ou donnée métier ajouté.
SHA256 du SQL : `84f8b3fa99a50ff9faafbbb0be818673d8563b78d11cae313ce2c4de4cec0686`.

## Tests réellement exécutés

Neuf tests ciblés réussis en 43.604 s, puis 93 tests connexes réussis en 411.476 s
(durées XML), zéro échec, erreur ou ignoré. Compilation Python : code 0.
Les suites se recouvrent et ne s'additionnent pas. Les avertissements de
dépréciation Pydantic/multipart restent présents.

Les nouveaux cas utilisent une vraie connexion LOGIN hisabpro non propriétaire
et de vrais JWT. Seule la connexion de base est injectée dans FastAPI ; aucune
authentification ou opération métier n'est remplacée.

- Vente/achat, simple/lot : deux factures de 120 ; paiement de 120 ou 240,
  restes respectifs 0/120 ou 0/0 ; chaque pièce équilibrée et définitive.
  Trois pièces débit=crédit=360 ou quatre pièces débit=crédit=480.
- Banque créée, modifiée, sélectionnée par son nom ; relevé importé, doublon
  ignoré ; soldes initiaux 0 et finaux +120/+240 ou −120/−240.
- Proposition exacte unique, confirmation, aperçu rejoué refusé 409,
  dépointage puis nouveau pointage ; deux lignes comptables pour le lot.
- Relevé rapproché : modification/suppression refusées ; banque désactivée
  sans suppression des règlements. Écritures/lignes définitives comparées
  intégralement avant/après : aucune modification ni création par le pointage.
- CRUD des relevés non rapprochés, import invalide atomiquement refusé,
  lecteur 403, autre société 404 et garde d'exercice clos 409.
- ACL de toutes les autres tables et UPDATE des séquences inchangés ; rejeu
  sur neuf tables documentaires/comptables avec JSON intégral identique.
  Rôle absent : double application sans création de rôle ou d'objet.

Commande connexe : `Test/run_unit_tests.py` sur les fichiers
`test_permissions_banque_releves_postgres.py`,
`test_permissions_documents_commerciaux_postgres.py`,
`test_permissions_acomptes_avoirs_postgres.py`,
`test_concurrence_avoirs_runtime_postgres.py`,
`test_rapprochement_ventilation_isole.py`,
`test_rapprochement_propositions_isole.py`,
`test_e2e_rapprochement_isole.py`,
`test_e2e_rapprochement_ventilation_isole.py`,
`test_e2e_rapprochement_propositions_isole.py`.

## Échecs conservés et limites

Avant 087 : cinq échecs réels en 45.13 s, INSERT refusés SQL42501 sur les
deux tables. Premier passage après : six réussites/trois échecs en 42.65 s ;
le banc photo supposait à tort une colonne id sur la table de ventilation
à clé composite. Tri par JSON complet corrigé ; aucun correctif métier supplémentaire.
Les XML/logs/exit avant, après et v2 sont conservés dans le bac de session.
Un diagnostic de processus séparé a lu le cluster nonce actif et rencontré
un ancien nonce arrêté (timeout) ; il n'est pas compté comme test réussi.

PostgreSQL nonce uniquement ; aucun PostgreSQL réel ni donnée réelle.
Les neuf nouveaux cas API sont sous LOGIN applicatif ; les E2E connexes
historiques utilisent encore le migrateur nonce. La prochaine étape les
exercera sous LOGIN applicatif, avec la vraie application complète.
087 doit être appliquée manuellement par le migrateur après le schéma/048/084,
en complément de 077 et des autres permissions requises ; aucun bootstrap modifié.
Pas de nouvelle règle fiscale, restauration de production, recette humaine
ou conformité officielle validée. Point 6 toujours en attente.
