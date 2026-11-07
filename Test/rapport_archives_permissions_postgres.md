# Migration 073 — archives fiscales et anciennes permissions

Recette réalisée le 7 octobre 2026, exclusivement sur des clusters PostgreSQL
éphémères marqués. Aucun accès à une base réelle ou fichier `.env`.

## Défaut reproduit et correction testée

La migration historique `027` autorise SELECT/INSERT mais ne révoque pas
d'anciens droits supplémentaires. Son trigger UPDATE/DELETE ne couvre pas
TRUNCATE. Les tests reproduisent trois anciennes ACL, dans trois clusters
distincts : droit direct de `hisabpro`, droit reçu de `PUBLIC` et droit hérité
du groupe `anciennes_archives`. Après rejeu de `027`, le vrai rôle applicatif
non propriétaire peut tronquer deux archives fictives. Cette démonstration
est annulée par rollback et les archives sont conservées.

La nouvelle migration additive `073_archives_fiscales_permissions.sql`
(développée par le responsable du lot) révoque UPDATE/DELETE/TRUNCATE à
`PUBLIC` et `hisabpro`, puis ajoute un trigger BEFORE TRUNCATE par statement,
réutilisant la fonction d'immutabilité existante. Aucun changement de données
ou réécriture de la migration `027`.

## Cas réellement exécutés

| Cas | Résultat après deux applications de 073 |
| --- | --- |
| Ancien droit direct | UPDATE/DELETE/TRUNCATE absents ; refus SQLSTATE 42501 |
| Ancien droit PUBLIC | UPDATE/DELETE/TRUNCATE absents ; refus SQLSTATE 42501 |
| Ancien droit hérité d'un groupe | Droits hérités toujours visibles ; mutations refusées par les triggers, SQLSTATE P0001 |
| Propriétaire conservant le trigger actif | TRUNCATE refusé, SQLSTATE P0001 |
| Rôle applicatif absent | Migration et rejeu réussis ; TRUNCATE propriétaire refusé |

Dans les trois scénarios runtime, SELECT et INSERT sont conservés. Une
troisième version synthétique est insérée après correction, tandis que
les deux versions originales restent strictement identiques. Les comparaisons
contrôlent id, société, exercice, version, contenu, empreinte SHA256,
date de finalisation et utilisateur de finalisation avant/après migrations,
rejeux et refus. Le trigger statement est confirmé présent et activé.

Chaque scénario utilise `cluster_isole` avec rôle propriétaire distinct,
port loopback différent de 5432, nom de base unique et marqueur/nonce.
La garde est contrôlée avant le DDL et les mutations. L'URL runtime est
dérivée de cette seule URL isolée. Le nettoyage à la sortie est vérifié.

## Commandes exécutées

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_archives_permissions_postgres.py -x
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile Test/test_archives_permissions_postgres.py
```

**5 réussis, 0 échec, 0 ignoré, 53,99 s**. Compilation Python : OK.

## Limites

La migration protège cette table d'archives fiscales. Elle ne certifie pas
les ACL des autres tables, les archives de livre d'inventaire ou le schéma
complet d'une installation réelle. Les droits provenant d'un groupe ne sont
pas supprimés par une révocation visant uniquement `PUBLIC` et `hisabpro` ;
le trigger assure le refus du TRUNCATE tant qu'il reste activé.

Un propriétaire ou superuser pouvant supprimer/désactiver les triggers reste
un acteur d'administration privilégié. Ces tests n'annoncent pas une protection
contre un administrateur PostgreSQL malveillant. Conserver une séparation
du rôle de migration et du rôle applicatif, et examiner leurs memberships.
L'application de 073 à une installation existante reste une opération de
déploiement distincte ; aucune application sur une base réelle n'a eu lieu.
