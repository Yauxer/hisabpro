# Sauvegarde/restauration GRH et provenance paie082 — 8 octobre 2026

Extension des tests de sauvegarde existants, sans changement de l'outil
`ops/postgres_sauvegarde.py`, du backend, des migrations ou des droits historiques.
Deux clusters PostgreSQL distincts sont créés et gardés par URL loopback,
répertoire et nonce ; aucune connexion utilisateur ou PostgreSQL réel.

## Données et contrôles

Socle ORM, scripts structurels001–082 selon le manifeste existant, hors scripts
de réparation historiques et sans seed de paramètres sociaux. Fixtures isolées :
salarié avec contrat NULL et personnes à charge non renseignées, demande d'absence
avec événement historique, version de provenance contenant JSON de laboratoire
explicitement non vérifié, écriture OD validée de100MAD au débit et100au crédit.
Les taux fictifs JSON ne constituent aucun référentiel réglementaire.

`pg_dump` au format custom puis `pg_restore` réellement exécutés. Toutes les
colonnes des huit tables sélectionnées sont comparées, dates/décimaux et JSON
canoniques compris : sociétés, utilisateurs, employés, demandes, événements,
versions de provenance, écritures et lignes. Source inchangée après sauvegarde,
restauration, tests de protection et reprovisionnement082.

Contrat historique NULL, validation et équilibre100/100 restaurés. Quatre
triggers d'immuabilité GRH/provenance restaurés et activés `O`. UPDATE, DELETE
et TRUNCATE des événements et versions refusés au propriétaire23514 ; instantané
inchangé. Deuxième restauration sur cible non vide refusée avant toute suppression.

## ACL et reprovisionnement

L'outil emploie `--no-owner --no-privileges` : sauvegarde ne transportant pas les
ACL ni rôles, elle n'est pas une procédure complète de provisionnement runtime.
Le test crée un rôleLOGIN non propriétaire uniquement dans la cible isolée et
prouve l'absence initiale SELECT sur les versions. Rejeu de082 ensuite :
SELECT/INSERT de table et USAGE/SELECT de séquence autorisés, connexion runtime
et INSERT réel d'une deuxième version réussis, puis rollback de cette preuve.
UPDATE/DELETE/TRUNCATE runtime restent refusés42501 ; huit tables identiques.
Le manifeste exhaustif des droits des autres modules reste à définir ; aucun
GRANT global ni nouvelle permission n'est inventé pour rendre la recette verte.

## Tests réellement exécutés

```text
PYTHON_DOTENV_DISABLED=1 python -X utf8 Test/run_unit_tests.py Test/test_sauvegarde_paie_grh_postgres.py Test/test_session132_sauvegarde_postgres.py --tb=short
```

Premier essai :1échoué et5réussis en29,02s. Fixture arrêtée avant sauvegarde :
une ancienne migration exigeait le rôlehisabpro. Création explicite du rôle
NOLOGIN dans le cluster source ajoutée comme dans l'installation consolidée.
Les cinq contrôles existants de sauvegarde sont réellement réussis.

Relance du nouveau test après correction :1réussi en31,02s. Une dernière
relance après ajout de la preuve INSERT runtime avec rollback : **1réussi en
22,90s**, aucun ignoré. Compilation du nouveau fichier Python : code0.

## Limites

Cette recette ne remplace pas une restauration utilisateur ni un déploiement
complet. Aucun dump n'est livré : archive et deux clusters temporaires supprimés
à la fin. Aucun processus utilisateur, donnée comptable réelle ou ancien rapport
de sauvegarde150 modifié. Le référentiel social global reste une limite distincte.
