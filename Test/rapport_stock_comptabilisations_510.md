# Lot510 — Une seule régularisation de stock à la fois

## Défauts reproduits

Deux demandes concurrentes produisaient deux brouillons distincts portant la
même référence STOCK-CLOTURE-2025. La lecture SQL a confirmé deux pièces de
débit=crédit160MAD chacune, pour une photographie de stock160MAD : après
validation des deux, le stock comptable aurait été320MAD au lieu de160MAD.
Les deux brouillons sont observés réellement ; cette validation erronée n'est
pas effectuée dans le scénario avant correctif.

Un nouveau comptage pouvait aussi être confirmé pendant la génération d'une
écriture basée sur la photographie précédente, et réciproquement. Le contrôle
de clôture signalait ensuite l'écart, mais les opérations avaient déjà été
acceptées ensemble.

## Correction minimale

Les deux endpoints de comptage et de comptabilisation prennent une exclusion
transactionnelle non bloquante par société/exercice. Ils prennent d'abord le
verrou partagé avec la clôture508, puis le verrou exclusif propre au stock.
Les dates/périodes sont contrôlées après relecture de l'exercice.
Un conflit renvoie409, sans deuxième pièce ni nouveau comptage. Les autres
sociétés/exercices restent disponibles. Pas de nouvelle migration ni de
changement de valorisation, de comptes ou de fiscalité.

Un utilisateur peut toujours régénérer explicitement un brouillon après la fin
de la première opération : il reste une seule écriture courante. Une pièce
définitive est refusée et conservée avec toutes ses lignes. L'opération
invalide libère ses verrous ; elle ne bloque pas les demandes suivantes.

## Oracles et tests réels

- Photographie8×20=160MAD ; deux générations simultanées : première200,
  seconde409, une seule pièce3111D160/6114C160.
- Génération160 en cours puis recomptage10×20 : recomptage409, photographie
  toujours160 et une seule écriture160.
- Recomptage200 en cours puis génération : génération409 ; après confirmation,
  reprise explicite et une seule écriture3111D200/6114C200.
- Pour les trois cas : validation effective, rapprochement à zéro, clôture/FEC ;
  résultat de laboratoire160−3000=−2840 ou200−3000=−2800, avec la CM existante.
  Cette CM n'est pas une qualification fiscale d'une entreprise réelle.
- Isolation société/exercice, refus sans inventaire puis reprise, régénération
  explicite d'un brouillon et conservation d'une définitive.

Avant correctif :4échecs/2réussites,29avertissements,39,42s. Trois courses et
un contrat d'isolation non encore implémenté ; les deux comportements existants
de refus/régénération passent déjà. Preuve SQL ciblée du doublon :1échec,
5désélectionnés,29avertissements,28,90s.

Après correctif : **10réussites,29avertissements,66,30s**, code0 :six nouveaux
cas510 et quatre régressions508, sur deux modules PostgreSQL temporaires.
Les passages successifs ne sont pas additionnés comme des cas distincts.

Qualification finale : **164réussites,29avertissements,380.36s**, code0,
aucun échec/erreur/ignoré. Oracles508 et précédents, quatre parcours Edge
d'inventaire desktop/mobile,25historiques,15purs et restauration098 conservés.
Sources figées vérifiées. Restauration :74tables, source préservée/cibles
supprimées, fonctions098 et refus409/reprise intacts. Invariants comptables0 :
pièces déséquilibrées, montants non finis, définitives sans numéro/date.
Quatre Python du lot et quinze du cumulatif compilés ;98SQL/115guides,
main/models/AGENTS et services de calcul de stock/exercices intacts.

Commande finale : `Test/run_unit_tests.py Test/test_consolidation_stock510_isole.py Test/test_restauration_journal098_isole.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py Test/test_patch05c_reconciliation_historique.py Test/test_patch05d1_reconciliation_amortissements.py Test/test_patch05_livre_inventaire.py Test/test_e2e_cloture_isole.py Test/test_inventaire_comptage_complet.py Test/test_inventaire_nombres_historique_postgres.py -ra`.

## Installation et limites

Installer ensemble `routers/inventaire.py` et
`services/exercice_verrou_service.py` à jour510, puis redémarrer l'API.
Aucune migration supplémentaire ni réparation des anciens doublons validés.
Une anomalie historique exige un traitement séparé, justifié et traçable.

Ce lot concerne les deux endpoints de comptage/comptabilisation. Les autres
mouvements de stock, le SQL ou Python direct et les modifications simultanées
du Journal restent distincts. Frontend inchangé ; quatre parcours d'inventaire
desktop/mobile sont repris dans la consolidation. Recette utilisateur,
production et point6 non validés.
