# Lot528 — Contrepassation simultanée du même original

## Défaut reproduit et correction minimale

Deux demandes simultanées pouvaient constater l'absence de contrepassation,
puis la seconde échouer500 sur la contrainte d'unicité. Une répétition normale
devait déjà retrouver la correction existante200 ; ce contrat reste inchangé.

Une seule lecture produit modifiée : le parent est verrouillé et relu avant
de rechercher la correction existante. La seconde transaction attend la
première, puis retrouve la même correction avec `deja_existante=true`, sans
nouvel impact comptable. Original et lignes restent intangibles. L'unicité
SQL, les règles de période, de motif et de numérotation sont conservées.
Aucune nouvelle migration ni nouvelle obligation de saisie.

## Six scénarios API/PostgreSQL

- Quatre courses : original client encore sur exercice ouvert ou original de
  bilan sur exercice clôturé, avec dates demandées identiques ou différentes.
  Les deux réponses200 retrouvent le même identifiant/numéro/date ; seule la
  première crée la correction. Son motif/date ne sont pas remplacés par la
  seconde demande, conformément au contrat existant.
- Une seule correction définitive, une seule réservation supplémentaire de
  numéro, une seule transition de validation dans l'audit.
- En-tête, lignes et audit de l'original inchangés. Débit/crédit inversés,
  tiers, nature et comptes/libellés auxiliaires recopiés à l'identique.
  Exports FEC effectifs sur l'exercice cible.
- Brouillon refusé409, tables métier intactes, puis validation et
  contrepassation possibles ; absence de verrou résiduel.
- Date demandée dans l'exercice clos refusée423, tables métier intactes,
  puis reprise dans l'exercice suivant ouvert.

Données fictives : original de bilan100 ; original client1200=1000+200,
avec hypothèse de TVA20% de laboratoire, sans qualification réglementaire.
L'original de bilan est clôturé avant sa correction sur N+1 ; les scénarios
clients vérifient la correction et le FEC, sans prétendre clore un dossier réel.

Avant correction : **5échecs/1réussite,29avertissements,45,10s**, code1.
Quatre erreurs500 réelles ; le cinquième échec provenait du test attendant409
au lieu du423 existant pour une période clôturée. Assertion corrigée, sans
changement du code métier de refus.

Qualification ciblée : **12réussites,29avertissements,45,10s**, code0 :
six cas natifs et six régressions de numérotation. Les passages successifs
ne sont pas additionnés comme des cas distincts.

Qualification finale : **416réussites,29avertissements,789.31s**, code0,
aucun échec/erreur/ignoré :410oracles526 et6cas528.
Scénarios du wrapper principal sous rôle LOGIN non propriétaire PostgreSQL18.3,
sources figées vérifiées ; Edge ordinateur/mobile, vente/achat,
factures→règlements→lettrage, PDF/XLSX/impression, fiscalité et clôtures inclus.

Restauration098 :74tables, source préservée, cibles supprimées, trois fonctions
identiques et refus409/reprise conservés. Invariants comptables0 : pièces
déséquilibrées, montants non finis, définitives sans numéro/date.
Trois Python du lot et36du cumulatif compilés ;98SQL/115guides,
main/models/AGENTS et autres sources produit inchangés. Frontend inchangé.

Commande : même liste que la consolidation526 avec
`Test/test_consolidation_contre528_isole.py` comme wrapper, avec `-ra` via
`Test/run_unit_tests.py`.


## Installation et limites

Installer `routers/ecritures.py` à jour528, puis redémarrer l'API.
Aucune nouvelle migration ou intervention sur les données réelles.
Une répétition de demande retrouve la correction existante : elle ne change
pas son motif, sa date ni ses lignes. Toute nouvelle correction doit suivre
le flux comptable déjà prévu, sans réécrire l'original.

Ce lot concerne l'endpoint de contrepassation. Accès directs hors API,
autres générateurs et changements de dates d'exercices simultanés distincts.
Recette utilisateur, production et point6 humain restent en attente.
