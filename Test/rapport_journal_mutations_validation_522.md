# Lot522 — Modification ou suppression pendant validation

## Cause et correction minimale

La modification et la suppression pouvaient lire un ancien état « brouillon »
pendant la validation de la même écriture. Les protections SQL conservaient
l'intangibilité, mais la demande concurrente aboutissait à une erreur500
plutôt qu'au refus métier423 déjà prévu par le Journal.

Les deux lectures du parent sont désormais verrouillées avec relecture de
l'état ORM avant le contrôle existant. Pour la modification, les lignes sont
chargées après la prise du verrou du parent. Une validation terminée est donc
observée avant toute modification ou suppression. Une attente transactionnelle
est possible ; les règles de validation, période, montant et intangibilité
restent inchangées. Un seul fichier produit modifié, aucune migration.

## Six scénarios API/PostgreSQL

- Validation individuelle puis modification/suppression et validation par lot
  puis modification/suppression : quatre refus423 avec invitation à la
  contrepassation. Lignes, référence et libellé initial conservés ; numéro et
  date de validation présents, une seule trace de validation et aucune trace
  de modification/suppression acceptée. Audit antérieur conservé.
- Modification commencée avant validation : validation des nouvelles lignes
  équilibrées200, avec leur nouveau libellé, après achèvement de la modification.
- Suppression du brouillon commencée avant validation : suppression204,
  validation404, audit antérieur conservé. Aucune définitive supprimée.
- Pour chaque cas : clôture−3000 et export FEC, sur des opérations de bilan
  fictives ; CM3000 déjà présente conservée, sans qualification fiscale réelle.

Premier passage : **5échecs/1réussite,29avertissements,53,44s**, code1.
Quatre erreurs500 de produit ; le cinquième échec concernait le repère du test
de suppression : la requête bloquée était le DELETE des lignes, non celui de
l'en-tête. Repère corrigé pour observer les deux, sans modifier le scénario
attendu. Ne pas présenter cet échec de test comme un cinquième défaut produit.

Qualification ciblée : **63réussites,29avertissements,143,99s**, code0 :
six nouveaux cas natifs, neuf cas520 et48régressions de montants. Les tests
de schémas/calculs sont distincts des tests API réellement exécutés sur
PostgreSQL isolé. Aucun passage successif additionné comme cas distinct.

Qualification finale : **385réussites,29avertissements,658.07s**, code0,
aucun échec/erreur/ignoré :331oracles520,6cas522 et48régressions de montants.
Scénarios du wrapper principal sous rôle LOGIN non propriétaire PostgreSQL18.3,
sources figées vérifiées ; Edge ordinateur/mobile, vente/achat,
factures→règlements→lettrage, PDF/XLSX/impression, fiscalité et clôtures inclus.

Restauration098 :74tables, source préservée, cibles supprimées, trois fonctions
identiques et refus409/reprise conservés. Invariants comptables0 : pièces
déséquilibrées, montants non finis, définitives sans numéro/date.
Trois Python du lot et30du cumulatif compilés ;98SQL/115guides,
main/models/AGENTS et autres sources produit inchangés. Frontend inchangé.

Commande : liste de la consolidation520 avec
`Test/test_consolidation_journal522_isole.py` comme wrapper et ajout de
`Test/test_session133_ecritures_montants.py`, avec `-ra` via
`Test/run_unit_tests.py`.


## Installation et limites

Installer `routers/ecritures.py` à jour522 sur la version520, puis redémarrer
l'API. Aucune nouvelle migration ni intervention sur les données réelles.
Conserver les protections SQL existantes. Une écriture définitive reste
corrigeable uniquement par le flux de contrepassation prévu.

Les opérations simultanées testées passent par les endpoints Journal. Les
autres générateurs, les accès SQL/Python directs et les changements simultanés
de dates d'exercice ne sont pas garantis par ce lot. Recette utilisateur,
production et point6 humain restent en attente.
