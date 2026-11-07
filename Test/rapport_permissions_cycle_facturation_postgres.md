# Permissions applicatives du cycle direct de facturation

Migration additive `077_permissions_cycle_facturation.sql`. Tests exécutés uniquement sur PostgreSQL éphémère marqué ; aucun PostgreSQL utilisateur ni donnée comptable réelle utilisé. Les anciens scripts et rapports d'installation restent inchangés.

## Cause et correction

L'installation consolidée 001–076 laisse `hisabpro` sans SELECT/INSERT sur sociétés, utilisateurs, tiers et factures. Le défaut est reproduit avant 077 par SELECT sociétés refusé 42501. Un manifeste fermé de tables et droits rend possible l'inscription et le cycle direct de facturation sous un rôle LOGIN réellement distinct du propriétaire.

| Tables | Droits ajoutés par 077 | Justification |
|---|---|---|
| societes, utilisateurs, modules_actifs, comptes_societe, exercices_comptables, periodes_comptables | SELECT, INSERT, UPDATE | Inscription, paramètres, activation, préparation plan/exercice |
| tiers, familles_articles, articles | SELECT, INSERT, UPDATE, DELETE | Routes existantes des référentiels |
| factures, lignes_facture, reglements, ecritures, lignes_ecriture | SELECT, INSERT, UPDATE, DELETE | Brouillons et mutations contrôlées existantes |
| mouvements_stock | SELECT, INSERT | Sous-ledger utilisé par les mouvements, sans ajout UPDATE/DELETE |
| utilisateurs_societes, plan_comptable_cgnc_reference, clotures_exercice, facturation_sequences | SELECT | Authentification et contrôles de contexte/numérotation |
| devis, lignes_devis, bons_commande, lignes_bon_commande, bons_livraison, lignes_bon_livraison | SELECT | Sources documentaires optionnelles consultées par les factures |
| avoirs, lignes_avoir, acomptes, imputations_acomptes, utilisations_avoirs | SELECT | Calcul du solde et contrôles des dépendances |
| comptes_bancaires, tva_parametres_exercice, modeles_ecritures, lignes_modele | SELECT | Résolution des comptes et paramètres associés |

USAGE du schéma est explicite. USAGE/SELECT des séquences est attribué uniquement via `pg_get_serial_sequence` des quinze tables insérables listées. Aucun GRANT ALL, ALL TABLES, ALL SEQUENCES, DEFAULT PRIVILEGES, CREATE, TRUNCATE ou UPDATE de séquence n'est ajouté. Aucun rôle ni rattachement historique n'est créé, aucun trigger/CHECK n'est modifié. Audits et archives conservent leurs permissions/protections des migrations précédentes.

## Exécution réelle

```powershell
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m pytest Test/test_permissions_cycle_facturation_postgres.py -q
```

Résultat final : **18 réussis en 22,95 s**, code de sortie 0, aucun échec, aucun ignoré. 28 avertissements de dépréciation provenant des imports existants.

L'environnement API utilise les vrais routeurs FastAPI et une dépendance `get_db` connectée sous `hisabpro`. L'authentification, les mots de passe et JWT ne sont pas remplacés. Le middleware global de journalisation HTTP de l'application complète n'est pas installé dans cette application ciblée ; il n'est donc pas validé par ce test.

Le premier cluster prépare le socle ORM, applique les 64 candidats historiques jusqu'à 073, puis 074/075/076 et 077 deux fois. Les tables métier restent vides pendant ces phases ; le catalogue des CHECK/triggers est identique avant/après 077. Le second cluster vérifie 077 seul deux fois sans rôle applicatif. Les deux clusters sont arrêtés et leur suppression vérifiée par le helper isolé.

Parcours réellement exécuté sous rôle LOGIN non propriétaire :

1. Inscription d'une société et de son administrateur fictifs ; préparation du plan comptable et exercice de l'année courante par les routes existantes.
2. Connexion réelle, récupération du JWT, lecture `/auth/me` et paramètres société.
3. Configuration de l'identité fictive ; création d'un client particulier et d'une prestation non stockable, compte vente 7121.
4. Facture au 15 mai : 100 MAD HT, TVA 20 MAD, TTC 120 MAD ; validation définitive et comptabilisation.
5. Règlement virement de 120 MAD ; écriture de règlement créée, facture affichée `payee`.
6. Validation explicite des deux écritures du journal.

Calcul indépendant vérifié sur les lignes SQL :

| Compte | Débit MAD | Crédit MAD |
|---|---:|---:|
| 3421 Client | 120 | 120 |
| 4455 TVA facturée | 0 | 20 |
| 5141 Banque | 120 | 0 |
| 7121 Vente de prestation | 0 | 100 |
| Total | 240 | 240 |

Autres contrôles réels : audit écritures effectivement rempli par les triggers ; mot de passe incorrect et JWT invalide refusés 401 ; seconde société inscrite et authentifiée ne voyant pas la première facture, validation croisée refusée 404. Le rôle runtime n'est ni superutilisateur ni membre du propriétaire, ne possède aucune relation du schéma, n'a pas CREATE public ni TRUNCATE sur les tables du cycle.

UPDATE/DELETE des écritures et lignes définitives refusés 23514 ; UPDATE des lignes d'une facture validée refusé P0001. DELETE SQL de la facture **payée** refusé par la clé étrangère règlement 23503 ; DELETE API de cette facture validée refusé 409. Cette preuve ne doit pas être assimilée à un trigger général de DELETE sur toute facture validée : 029 protège le parent en INSERT/UPDATE et ses lignes, et la suppression directe d'une facture validée sans règlement reste un point d'audit distinct.

UPDATE/DELETE/TRUNCATE des trois audits et des quatre tables d'archives/compléments refusés 42501 sous runtime. INSERT direct dans les audits non autorisé ; SELECT/INSERT sur les archives/compléments conservés. Une archive liasse purement synthétique est insérée pour vérifier les droits, puis son contenu et SHA sont identiques après rejeu 077. Ce n'est pas une finalisation fiscale annuelle.

```powershell
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m pytest Test/test_patch04b1_auth_role.py Test/test_factB_identites_dates.py -q
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m py_compile Test/test_permissions_cycle_facturation_postgres.py
```

Résultats : **7 réussis en 0,28 s**, puis compilation code de sortie 0.

## Commandes précédentes et corrections de la recette

Les exécutions avec arrêt au premier échec ont révélé des hypothèses incorrectes du nouveau test, corrigées sans changer une règle produit :

- 14,29 s : données de test facture envoyées sous `prix_unitaire_ht`, refusées 422 car le schéma exige `prix_unitaire`.
- 12,51 s : 1 réussi, 1 échec ; attente erronée d'absence UPDATE sur les séquences déjà autorisées par 005/008. Remplacée par comparaison réelle des droits avant/après 077.
- 14,03 s : 6 réussis, 1 échec ; SQLSTATE attendu 23514 pour lignes facture, alors que le trigger existant retourne P0001.
- 13,31 s : 7 réussis, 1 échec ; DELETE facture payée refusé par FK23503, pas par le trigger supposé P0001.
- 24,31 s : 17 réussis, 1 échec ; tentative de préparer tous les anciens SQL sans rôle applicatif, arrêt réel sur 012 qui exige ce rôle. Le test rôle absent porte désormais uniquement sur le nouveau contrat conditionnel 077 ; le prérequis historique n'est pas masqué.

## Limites restant visibles

Les migrations 005 et 008 attribuent historiquement USAGE/SELECT/**UPDATE** sur ALL SEQUENCES. Le nouveau 077 ne normalise pas ces anciens droits. Le test compare les droits UPDATE de toutes les séquences avant/après et confirme qu'il n'en ajoute aucun ; il ne prétend pas que SETVAL est globalement interdit et n'exécute aucun SETVAL. Une normalisation future nécessite un manifeste global audité, distinct de ce lot.

Le rôle `hisabpro` doit être précréé pour l'installation historique complète, notamment 012. Le succès conditionnel de 077 sans rôle n'est pas une preuve d'installation de tous les anciens scripts sans bootstrap.

Ce manifeste est limité au parcours direct testé ; aucune permission exhaustive des autres modules, paie, immobilisations, stock complet, devis/BC/BL en écriture, clôture, fiscalité ou sauvegarde/restauration n'est déclarée validée. Les droits antérieurs sur les tables ne sont pas globalement révoqués. Aucun déploiement, PostgreSQL réel, recette navigateur ou préparation complète à la production n'est validé ici.

La garde SQL DELETE du parent facture validée est traitée séparément par le lot 078 de l'agent principal. Installer 077 avec ce complément après sa validation et sa livraison ; les résultats ci-dessus portent strictement sur 077 et ne prouvent pas encore 078.
