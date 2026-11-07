# Sauvegarde et restauration des captures RAS explicites

Lot 305 — 10 octobre 2026. Deux clusters PostgreSQL possédés par les fixtures nonce, aucune base réelle. Périmètre : nouvelle recette automatisée et présent rapport ; aucun fichier applicatif, migration, outil de sauvegarde ou historique existant modifié.

## Préparation et oracle

La fixture d’application existante crée une société et un tiers fictifs par API. La facture de vente de laboratoire est validée et comptabilisée : HT 1 000 + TVA 200 = TTC 1 200. Deux virements comptabilisés, 400 puis 700, reçoivent des captures déclaratives explicites de 30 puis 70. Toutes les écritures sont validées par API. Le règlement 700 est ensuite annulé : contrepassation de trésorerie 700 et de capture 70, avec trace d’annulation, puis validation des deux écritures compensatoires.

Oracle après annulation : **reste dû 770**, retenue explicitement imputée **30**, sept écritures définitives et quinze lignes, **débit = crédit 3 170**. Les comptes de destination et les montants sont des données fictives du laboratoire, pas une qualification fiscale automatique. Aucun taux légal nouveau ni justificatif réel inventé.

## Preuves réellement exécutées

- Les deux cibles sont vérifiées par `verifier_cible_isolee`, avec URL, répertoire et nonce propres, avant sauvegarde, restauration et opérations sensibles. URL et nonce source/cible sont distincts.
- `ops/postgres_sauvegarde.py` produit un vrai `pg_dump` custom et restaure dans une cible vide par `pg_restore`. Aucun dump existant écrasé, aucun trigger désactivé.
- Snapshots de **onze tables**, toutes colonnes et identifiants compris : sociétés, utilisateurs, appartenances, tiers, factures, lignes de facture, règlements, écritures, lignes d’écriture, captures et annulations. Identité exacte source avant/après et cible après restauration.
- Les deux tables 083 restent absentes de `Base.metadata`. Aucun DDL automatique n’est introduit par cette recette.
- Deux captures et une annulation restaurées ; huit triggers 083 présents et actifs. UPDATE/DELETE des traces et TRUNCATE conjoint refusés avec code PostgreSQL 23514, même avec le propriétaire de la cible.
- Les services réels relisent la base restaurée via une Session SQLAlchemy : solde 770, montant imputé 30, deux captures dont une annulée, écritures de capture et d’annulation validées. Cette lecture métier cible n’est pas une requête HTTP ni une recette navigateur.
- Le dump `--no-privileges` ne transporte pas les ACL. Un rôle **LOGIN** `hisabpro`, non superutilisateur, est créé sur la cible ; son absence initiale de droit SELECT est vérifiée. Rejeu explicite de **083 uniquement** sur la cible nonce : aucune donnée modifiée.
- Une vraie connexion distincte se présente comme `current_user = hisabpro` et lit effectivement les captures et annulations. Les privilèges SELECT et INSERT sont vérifiés séparément, ainsi que USAGE et SELECT des séquences. UPDATE/DELETE/TRUNCATE de chacune des deux tables sont refusés sous ce rôle, code 42501. Le test ne prétend pas avoir exécuté un INSERT runtime : ses privilèges sont contrôlés ; la preuve d’insertion runtime est du périmètre distinct 293.
- Une seconde restauration sur la cible déjà remplie est refusée avant toute suppression. Snapshots source/cible toujours inchangés ensuite. Connexions fermées et cluster cible supprimé uniquement par son gestionnaire nonce ; le dump temporaire privé n’est pas livré.

## Commandes et résultats

Après confirmation par l’agent backend de la stabilité des renforcements SQL/API 293 :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_sauvegarde_ras_reglements_isole.py --tb=short
```

**1 test réussi en 35,20 s**, sortie 0, aucun échec ou test ignoré. Les 25 avertissements sont les dépréciations Pydantic/python-multipart existantes.

Connexe raisonnable des outils de sauvegarde, exécuté séparément :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_session132_sauvegarde_postgres.py --tb=short
```

**5 tests réussis en 14,70 s**, sortie 0. Cela inclut une autre sauvegarde/restauration PostgreSQL isolée, le refus hors bac, la protection des fichiers et des paramètres de connexion.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_sauvegarde_ras_reglements_isole.py
```

Compilation sortie 0. Au total **6 tests exécutés et réussis**, dans deux commandes distinctes ; leurs durées ne représentent pas une exécution commune. Aucun build frontend nécessaire pour ces deux fichiers de test/documentation.

## Limites

Cette preuve porte sur les traces 083 et la comptabilité fictive associée, avec une vente. Elle ne constitue pas une recette utilisateur, une restauration d’exploitation ou une validation fiscale. Les pièces jointes sont couvertes par le lot 246 distinct, pas restaurées ici. Aucun accès à `.env`, PostgreSQL réel ou processus de l’utilisateur. Journal, revue finale et ZIP différentiel sont gérés par l’agent principal.
